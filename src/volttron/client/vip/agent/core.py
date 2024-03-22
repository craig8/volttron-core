# -*- coding: utf-8 -*- {{{
# ===----------------------------------------------------------------------===
#
#                 Installable Component of Eclipse VOLTTRON
#
# ===----------------------------------------------------------------------===
#
# Copyright 2022 Battelle Memorial Institute
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
#
# ===----------------------------------------------------------------------===
# }}}

import heapq
import inspect
import logging
import os
import signal
import threading
import time
import urllib.parse
import uuid
import warnings
import weakref
from contextlib import contextmanager
from errno import ENOENT
from urllib.parse import parse_qs, urlsplit, urlunsplit

import gevent.event
from gevent.queue import Queue
from zmq import green as zmq
from zmq.green import EAGAIN, ENOTSOCK, ZMQError
from zmq.utils.monitor import recv_monitor_message

import volttron.client as client
# from volttron.client.agent import utils
# from volttron.client.agent.utils import load_platform_config, get_platform_instance_name
# TODO add back rabbitmq
# from volttron.client.keystore import KeyStore, KnownHostsStore
# from volttron.utils.rmq_mgmt import RabbitMQMgmt
from volttron import utils
from volttron.types.bases import AbstractCore
from volttron.utils import ClientContext as cc
from volttron.utils import get_address
from volttron.utils.keystore import KeyStore, KnownHostsStore
# TODO add back rabbitmq
# from ..rmq_connection import RMQConnection
from volttron.utils.socket import Message

from .decorators import annotate, annotations, dualmethod
from .dispatch import Signal
from .errors import VIPError

# from .. import router

__all__ = ["BasicCore", "Core", "killing"]

if cc.is_rabbitmq_available():
    import pika

    __all__.append("RMQCore")

_log = logging.getLogger(__name__)


class Periodic(object):    # pylint: disable=invalid-name
    """Decorator to set a method up as a periodic callback.

    The decorated method will be called with the given arguments every
    period seconds while the agent is executing its run loop.
    """

    def __init__(self, period, args=None, kwargs=None, wait=0):
        """Store period (seconds) and arguments to call method with."""
        assert period > 0
        self.period = period
        self.args = args or ()
        self.kwargs = kwargs or {}
        self.timeout = wait

    def __call__(self, method):
        """Attach this object instance to the given method."""
        annotate(method, list, "core.periodics", self)
        return method

    def _loop(self, method):
        # pylint: disable=missing-docstring
        # Use monotonic clock provided on hu's loop instance.
        now = gevent.get_hub().loop.now
        period = self.period
        deadline = now()
        if self.timeout != 0:
            timeout = self.timeout or period
            deadline += timeout
            gevent.sleep(timeout)
        while True:
            try:
                method(*self.args, **self.kwargs)
            except (Exception, gevent.Timeout):
                _log.exception("unhandled exception in periodic callback")
            deadline += period
            timeout = deadline - now()
            if timeout > 0:
                gevent.sleep(timeout)
            else:
                # Prevent catching up.
                deadline -= timeout

    def get(self, method):
        """Return a Greenlet for the given method."""
        return gevent.Greenlet(self._loop, method)


class ScheduledEvent(AbstractCore):
    """Class returned from Core.schedule."""

    def __init__(self, function, args=None, kwargs=None):
        self.function = function
        self.args = args or []
        self.kwargs = kwargs or {}
        self.canceled = False
        self.finished = False

    def cancel(self):
        """Mark the timer as canceled to avoid a callback."""
        self.canceled = True

    def __call__(self):
        if not self.canceled:
            self.function(*self.args, **self.kwargs)
        self.finished = True


def findsignal(obj, owner, name):
    parts = name.split(".")
    if len(parts) == 1:
        signal = getattr(obj, name)
    else:
        signal = owner
        for part in parts:
            signal = getattr(signal, part)
    assert isinstance(signal, Signal), "bad signal name %r" % (name, )
    return signal


class BasicCore(object):
    delay_onstart_signal = False
    delay_running_event_set = False

    def __init__(self, owner):
        self.greenlet = None
        self.spawned_greenlets = weakref.WeakSet()
        self._async = None
        self._async_calls = []
        self._stop_event = None
        self._schedule_event = None
        self._schedule = []
        self.onsetup = Signal()
        self.onstart = Signal()
        self.onstop = Signal()
        self.onfinish = Signal()
        self.oninterrupt = None
        self.tie_breaker = 0

        # TODO: HAndle sig int for child process
        # latest gevent does not have gevent.signal_handler()
        # TODO - update based on latest gevent function location
        # SIGINT does not work in Windows.
        # If using the standalone agent on a windows machine,
        # this section will be skipped
        # if python_platform.system() != "Windows":
        #     gevent.signal_handler(signal.SIG_IGN, self._on_sigint_handler)
        #     gevent.signal_handler(signal.SIG_DFL, self._on_sigint_handler)
        # prev_int_signal = gevent.signal_handler(signal.SIGINT)
        # # To avoid a child agent handler overwriting the parent agent handler
        # if prev_int_signal in [None, signal.SIG_IGN, signal.SIG_DFL]:
        #     self.oninterrupt = gevent.signal_handler(
        #         signal.SIGINT, self._on_sigint_handler
        #     )
        self._owner = owner

    def setup(self):
        # Split out setup from __init__ to give oportunity to add
        # subsystems with signals
        try:
            owner = self._owner
        except AttributeError:
            return
        del self._owner
        periodics = []

        def setup(member):    # pylint: disable=redefined-outer-name
            periodics.extend(
                periodic.get(member) for periodic in annotations(member, list, "core.periodics"))
            for deadline, args, kwargs in annotations(member, list, "core.schedule"):
                self.schedule(deadline, member, *args, **kwargs)
            for name in annotations(member, set, "core.signals"):
                findsignal(self, owner, name).connect(member, owner)

        inspect.getmembers(owner, setup)

        def start_periodics(sender, **kwargs):    # pylint: disable=unused-argument
            for periodic in periodics:
                sender.spawned_greenlets.add(periodic)
                periodic.start()
            del periodics[:]

        self.onstart.connect(start_periodics)

    def loop(self, running_event):
        # pre-setup
        yield
        # pre-start
        yield
        # pre-stop
        yield
        # pre-finish
        yield

    def link_receiver(self, receiver, sender, **kwargs):
        greenlet = gevent.spawn(receiver, sender, **kwargs)
        self.spawned_greenlets.add(greenlet)
        return greenlet

    def run(self, running_event=None):    # pylint: disable=method-hidden
        """Entry point for running agent."""

        self._schedule_event = gevent.event.Event()
        self.setup()
        self.greenlet = current = gevent.getcurrent()

        def kill_leftover_greenlets():
            for glt in self.spawned_greenlets:
                glt.kill()

        self.greenlet.link(lambda _: kill_leftover_greenlets())

        def handle_async_():
            """Execute pending calls."""
            calls = self._async_calls
            while calls:
                func, args, kwargs = calls.pop()
                greenlet = gevent.spawn(func, *args, **kwargs)
                self.spawned_greenlets.add(greenlet)

        def schedule_loop():
            heap = self._schedule
            event = self._schedule_event
            cur = gevent.getcurrent()
            now = time.time()
            while True:
                if heap:
                    deadline = heap[0][0]
                    timeout = min(5.0, max(0.0, deadline - now))
                else:
                    timeout = None
                if event.wait(timeout):
                    event.clear()
                now = time.time()
                while heap and now >= heap[0][0]:
                    _, _, callback = heapq.heappop(heap)
                    greenlet = gevent.spawn(callback)
                    cur.link(lambda glt: greenlet.kill())

        self._stop_event = stop = gevent.event.Event()
        self._async = gevent.get_hub().loop.async_()
        self._async.start(handle_async_)
        current.link(lambda glt: self._async.stop())

        looper = self.loop(running_event)
        next(looper)
        self.onsetup.send(self)

        loop = next(looper)
        if loop:
            self.spawned_greenlets.add(loop)
        scheduler = gevent.Greenlet(schedule_loop)
        if loop:
            loop.link(lambda glt: scheduler.kill())
        self.onstart.connect(lambda *_, **__: scheduler.start())
        if not self.delay_onstart_signal:
            self.onstart.sendby(self.link_receiver, self)
        if not self.delay_running_event_set:
            if running_event is not None:
                running_event.set()
        try:
            if loop and loop in gevent.wait([loop, stop], count=1):
                raise RuntimeError("VIP loop ended prematurely")
            stop.wait()
        except (gevent.GreenletExit, KeyboardInterrupt):
            pass

        scheduler.kill()
        next(looper)
        receivers = self.onstop.sendby(self.link_receiver, self)
        gevent.wait(receivers)
        next(looper)
        self.onfinish.send(self)

    def stop(self, timeout=None):

        def halt():
            self._stop_event.set()
            self.greenlet.join(timeout)
            return self.greenlet.ready()

        if gevent.get_hub() is self._stop_event.hub:
            return halt()

        return self.send_async(halt).get()

    def _on_sigint_handler(self, signo, *_):
        """
        Event handler to set onstop event when the agent needs to stop
        :param signo:
        :param _:
        :return:
        """
        _log.debug("SIG interrupt received. Calling stop")
        if signo == signal.SIGINT:
            self._stop_event.set()
            # self.stop()

    def send(self, func, *args, **kwargs):
        self._async_calls.append((func, args, kwargs))
        self._async.send()

    def send_async(self, func, *args, **kwargs):
        result = gevent.event.AsyncResult()
        async_ = gevent.hub.get_hub().loop.async_()
        results = [None, None]

        def receiver():
            async_.stop()
            exc, value = results
            if exc is None:
                result.set(value)
            else:
                result.set_exception(exc)

        async_.start(receiver)

        def worker():
            try:
                results[:] = [None, func(*args, **kwargs)]
            except Exception as exc:    # pylint: disable=broad-except
                results[:] = [exc, None]
            async_.send()

        self.send(worker)
        return result

    def spawn(self, func, *args, **kwargs):
        assert self.greenlet is not None
        greenlet = gevent.spawn(func, *args, **kwargs)
        self.spawned_greenlets.add(greenlet)
        return greenlet

    def spawn_later(self, seconds, func, *args, **kwargs):
        assert self.greenlet is not None
        greenlet = gevent.spawn_later(seconds, func, *args, **kwargs)
        self.spawned_greenlets.add(greenlet)
        return greenlet

    def spawn_in_thread(self, func, *args, **kwargs):
        result = gevent.event.AsyncResult()

        def wrapper():
            try:
                self.send(result.set, func(*args, **kwargs))
            except Exception as exc:    # pylint: disable=broad-except
                self.send(result.set_exception, exc)

        result.thread = thread = threading.Thread(target=wrapper)
        thread.daemon = True
        thread.start()
        return result

    @dualmethod
    def periodic(self, period, func, args=None, kwargs=None, wait=0):
        warnings.warn(
            "Use of the periodic() method is deprecated in favor of the "
            "schedule() method with the periodic() generator. This "
            "method will be removed in a future version.",
            DeprecationWarning,
        )
        greenlet = Periodic(period, args, kwargs, wait).get(func)
        self.spawned_greenlets.add(greenlet)
        greenlet.start()
        return greenlet

    @periodic.classmethod
    def periodic(cls, period, args=None, kwargs=None, wait=0):    # pylint: disable=no-self-argument
        warnings.warn(
            "Use of the periodic() decorator is deprecated in favor of "
            "the schedule() decorator with the periodic() generator. "
            "This decorator will be removed in a future version.",
            DeprecationWarning,
        )
        return Periodic(period, args, kwargs, wait)

    @classmethod
    def receiver(cls, signal):

        def decorate(method):
            annotate(method, set, "core.signals", signal)
            return method

        return decorate

    @dualmethod
    def schedule(self, deadline, func, *args, **kwargs):
        event = ScheduledEvent(func, args, kwargs)
        try:
            it = iter(deadline)
        except TypeError:
            self._schedule_callback(deadline, event)
        else:
            self._schedule_iter(it, event)
        return event

    def get_tie_breaker(self):
        self.tie_breaker += 1
        return self.tie_breaker

    def _schedule_callback(self, deadline, callback):
        deadline = utils.get_utc_seconds_from_epoch(deadline)
        heapq.heappush(self._schedule, (deadline, self.get_tie_breaker(), callback))
        if self._schedule_event:
            self._schedule_event.set()

    def _schedule_iter(self, it, event):

        def wrapper():
            if event.canceled:
                event.finished = True
                return
            try:
                deadline = next(it)
            except StopIteration:
                event.function(*event.args, **event.kwargs)
                event.finished = True
            else:
                self._schedule_callback(deadline, wrapper)
                event.function(*event.args, **event.kwargs)

        try:
            deadline = next(it)
        except StopIteration:
            event.finished = True
        else:
            self._schedule_callback(deadline, wrapper)

    @schedule.classmethod
    def schedule(cls, deadline, *args, **kwargs):    # pylint: disable=no-self-argument
        if hasattr(deadline, "timetuple"):
            # deadline = time.mktime(deadline.timetuple())
            deadline = utils.get_utc_seconds_from_epoch(deadline)

        def decorate(method):
            annotate(method, list, "core.schedule", (deadline, args, kwargs))
            return method

        return decorate


class Core(BasicCore):
    # We want to delay the calling of "onstart" methods until we have
    # confirmation from the server that we have a connection. We will fire
    # the event when we hear the response to the hello message.
    delay_onstart_signal = True
    # Agents started before the router can set this variable
    # to false to keep from blocking. AuthService does this.
    delay_running_event_set = True

    def __init__(
        self,
        owner,
        address=None,
        identity=None,
        context=None,
        publickey=None,
        secretkey=None,
        serverkey=None,
        volttron_home=os.path.abspath(cc.get_volttron_home()),
        agent_uuid=None,
        reconnect_interval=None,
        version="0.1",
        instance_name=None,
        messagebus=None,
    ):
        self.volttron_home = volttron_home

        # These signals need to exist before calling super().__init__()
        self.onviperror = Signal()
        self.onsockevent = Signal()
        self.onconnected = Signal()
        self.ondisconnected = Signal()
        self.configuration = Signal()
        super(Core, self).__init__(owner)
        self.address = address if address is not None else get_address()
        self.identity = str(identity) if identity is not None else str(uuid.uuid4())
        self.agent_uuid = agent_uuid
        self.publickey = publickey
        self.secretkey = secretkey
        self.serverkey = serverkey
        self.reconnect_interval = reconnect_interval
        self._reconnect_attempt = 0
        self.instance_name = instance_name
        self.messagebus = messagebus
        self.subsystems = {"error": self.handle_error}
        self.__connected = False
        self._version = version
        self.socket = None
        self.connection = None

        _log.debug("address: %s", address)
        _log.debug("identity: %s", self.identity)
        _log.debug("agent_uuid: %s", agent_uuid)
        _log.debug("serverkey: %s", serverkey)

    def version(self):
        return self._version

    def get_connected(self):
        return self.__connected

    def set_connected(self, value):
        self.__connected = value

    connected = property(
        fget=lambda self: self.get_connected(),
        fset=lambda self, v: self.set_connected(v),
    )

    def stop(self, timeout=None, platform_shutdown=False):
        # Send message to router that this agent is stopping
        if self.__connected and not platform_shutdown:
            frames = [self.identity]
            self.connection.send_vip("", "agentstop", args=frames, copy=False)
        super(Core, self).stop(timeout=timeout)

    # This function moved directly from the zmqcore agent.  it is included here because
    # when we are attempting to connect to a zmq bus from a rmq bus this will be used
    # to create the public and secret key for that connection or use it if it was already
    # created.
    def _get_keys_from_keystore(self):
        """Returns agent's public and secret key from keystore"""
        if self.agent_uuid:
            # this is an installed agent, put keystore in its agent's directory
            if self.identity is None:
                raise ValueError("Agent's VIP identity is not set")
            keystore_dir = os.path.join(self.volttron_home, "agents", self.identity)
        else:
            if not self.volttron_home:
                raise ValueError("VOLTTRON_HOME must be specified.")
            keystore_dir = os.path.join(self.volttron_home, "keystores", self.identity)

        keystore_path = os.path.join(keystore_dir, "keystore.json")
        keystore = KeyStore(keystore_path)
        return keystore.public, keystore.secret

    def register(self, name, handler, error_handler=None):
        self.subsystems[name] = handler
        if error_handler:
            name_bytes = name

            def onerror(sender, error, **kwargs):
                if error.subsystem == name_bytes:
                    error_handler(sender, error=error, **kwargs)

            self.onviperror.connect(onerror)

    def handle_error(self, message):
        if len(message.args) < 4:
            _log.debug("unhandled VIP error %s", message)
        elif self.onviperror:
            args = message.args
            error = VIPError.from_errno(*args)
            self.onviperror.send(self, error=error, message=message)

    def create_event_handlers(self, state, hello_response_event, running_event):

        def connection_failed_check():
            # If we don't have a verified connection after 10.0 seconds
            # shut down.
            if hello_response_event.wait(10.0):
                return
            _log.error("No response to hello message after 10 seconds.")
            _log.error("Type of message bus used {}".format(self.messagebus))
            _log.error("A common reason for this is a conflicting VIP IDENTITY.")
            _log.error("Another common reason is not having an auth entry on"
                       "the target instance.")
            _log.error("Shutting down agent.")
            _log.error("Possible conflicting identity is: {}".format(self.identity))

            self.stop(timeout=10.0)

        def hello():
            # Send hello message to VIP router to confirm connection with
            # platform
            state.ident = ident = "connect.hello.%d" % state.count
            state.count += 1
            self.spawn(connection_failed_check)
            message = Message(peer="", subsystem="hello", id=ident, args=["hello"])
            self.connection.send_vip_object(message)

        def hello_response(sender, version="", router="", identity=""):
            _log.info(f"Connected to platform: identity: {identity} version: {version}")
            _log.debug("Running onstart methods.")
            hello_response_event.set()
            self.onstart.sendby(self.link_receiver, self)
            self.configuration.sendby(self.link_receiver, self)
            if running_event is not None:
                running_event.set()

        return connection_failed_check, hello, hello_response


@contextmanager
def killing(greenlet, *args, **kwargs):
    """Context manager to automatically kill spawned greenlets.

    Allows one to kill greenlets that would continue after a timeout:

        with killing(agent.vip.pubsub.subscribe(
                'peer', 'topic', callback)) as subscribe:
            subscribe.get(timeout=10)
    """
    try:
        yield greenlet
    finally:
        greenlet.kill(*args, **kwargs)
