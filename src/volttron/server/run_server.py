import gevent
from gevent import Greenlet, monkey

from volttron.client.known_identities import (AUTH, CONTROL, CONTROL_CONNECTION, PLATFORM_CONFIG, PLATFORM_HEALTH)
from volttron.services.config_store.config_store_service import \
    ConfigStoreService
from volttron.types.auth.auth_credentials import (CredentialsCreator, CredentialsStore)

monkey.patch_socket()
monkey.patch_ssl()

import argparse
import importlib
import logging
import logging.config
import os
import resource
import sys
from pathlib import Path

from volttron.server.aip import AIPplatform
from volttron.server.containers import service_repo
from volttron.server.decorators import (get_authenticator, get_authorization_manager, get_authorizer,
                                        get_credentials_store)
from volttron.server.server_options import ServerOptions
from volttron.services.control.control_service import ControlService
from volttron.types.bases import MessageBus
from volttron.utils.version import get_version

_log = logging.getLogger(__name__)


def load_volttron_packages():
    from volttron.loader import load_dir

    volttron_path = Path(__file__).parent.parent
    # This doesn't reload it, because it's already been loaded.  This allows us
    # access to the paths associated with the other modules.
    volttron_pkg = importlib.import_module("volttron")

    # Loop over paths that aren't in this package
    for pth in filter(lambda p: p != volttron_path.parent.as_posix, volttron_pkg.__path__):
        _log.debug(f"Loading: {pth}")
        load_dir('volttron', Path(pth))


# Only show debug on the platform when really necessary!
# log_level_info = (
#     'volttron.platform.main',
#     'volttron.platform.vip.zmq_connection',
#     'urllib3.connectionpool',
#     'watchdog.observers.inotify_buffer',
#     'volttron.platform.auth',
#     'volttron.platform.store',
#     'volttron.platform.control',
#     'volttron.platform.vip.agent.core',
#     'volttron.utils',
#     'volttron.platform.vip.router'
# )

# for log_name in log_level_info:
#     logging.getLogger(log_name).setLevel(logging.INFO)

# No need for str after python 3.8
VOLTTRON_INSTANCES = Path("~/.volttron_instances").expanduser().resolve()


def start_volttron_process(options: ServerOptions):
    """Start the main volttron process.

    Typically, this function is used from main.py and just uses the argparser's
    Options arguments as inputs.   It also can be called with a dictionary.  In
    that case the dictionaries keys are mapped into a value that acts like the
    args options.
    """
    from volttron.server.decorators import (get_authservice_class, get_messagebus_class, get_messagebus_instance)
    from volttron.types import Identity
    from volttron.types.auth import AuthService
    from volttron.types.factories import ConnectionBuilder, CoreBuilder
    from volttron.types.known_host import \
        KnownHostProperties as known_host_properties

    server_options = service_repo.resolve(ServerOptions)
    assert server_options.volttron_home == Path(os.environ['VOLTTRON_HOME'])

    # core_builder = service_repo.resolve(CoreBuilder)
    # connection_builder = service_repo.resolve(ConnectionBuilder)

    # with open(server_options.volttron_home / "system", "w") as fp:
    #     fp.write(f"core_builder={core_builder.__module__}.{core_builder.__class__.__name__}\n")
    #     fp.write(f"connection_builder={connection_builder.__module__}.{connection_builder.__class__.__name__}\n")

    auth_service = None

    #try:
    auth_service: AuthService = service_repo.resolve(AuthService)
    # except KeyError:
    #     pass

    if options.auth_enabled and auth_service is None:
        raise ValueError("AuthService not found but auth_enabled in config is specified as True")

    if auth_service:
        required_credentials = (PLATFORM_CONFIG, PLATFORM_HEALTH, CONTROL, AUTH, CONTROL_CONNECTION)

        store: CredentialsStore = service_repo.resolve(CredentialsStore)
        assert store

        creator = service_repo.resolve(CredentialsCreator)
        assert creator

        # Require "Server" credentials as they are required for the server to operate.  For
        # zmq this is the public/secret key for the backend zap connection.  For other external
        # brokers this is the main connection keys for the server to connect to that external
        # broker.
        if not auth_service.has_credentials_for(identity="server"):
            server_creds = creator.create(identity="server")
            store.store_credentials(credentials=server_creds)

            # Add the server credentials to the known host properties.  Note this is how zmq does it
            # there may be different schemes that we put in auth here.
            if hasattr(server_creds, "publickey"):
                known_host_properties.add_property("@", "publickey", server_creds.publickey)
            else:
                known_host_properties.add_property("@", "publickey", None)
            for ip in server_options.address:
                known_host_properties.add_property(ip, "publickey", server_creds.publickey)
            known_host_properties.store(server_options.volttron_home / "known_hosts.json")

        for identity in required_credentials:
            if not auth_service.has_credentials_for(identity=identity):
                store.store_credentials(credentials=creator.create(identity=identity))

    # if isinstance(opts, dict):
    #     opts = type("Options", (), opts)()
    #     # vip_address is meant to be a list so make it so.
    #     if not isinstance(opts.vip_address, list):
    #         opts.vip_address = [opts.vip_address]
    # if opts.log:
    #     opts.log = config.expandall(opts.log)
    # if opts.log_config:
    #     opts.log_config = config.expandall(opts.log_config)

    # TODO: Functionalize This
    # Configure logging
    # level = max(1, opts.verboseness)
    # if opts.monitor and level > logging.INFO:
    #     level = logging.INFO
    #
    # if opts.log is None:
    #     log_to_file(sys.stderr, level)
    # elif opts.log == "-":
    #     log_to_file(sys.stdout, level)
    # elif opts.log:
    #     log_to_file(opts.log, level, handler_class=handlers.WatchedFileHandler)
    # else:
    #     log_to_file(None, 100, handler_class=lambda x: logging.NullHandler())
    #
    # if opts.log_config:
    #     with open(opts.log_config, "r") as f:
    #         for line in f.readlines():
    #             _log.info(line.rstrip())
    #
    #     error = configure_logging(opts.log_config)
    #
    #     if error:
    #         _log.error("{}: {}".format(*error))
    #         sys.exit(1)

    # if opts.secure_agent_users == "True":
    #     _log.info("VOLTTRON starting in secure mode")
    #     os.umask(0o007)
    # else:
    #     opts.secure_agent_users = "False"

    # opts.vip_address = [config.expandall(addr) for addr in opts.vip_address]
    # opts.vip_local_address = config.expandall(opts.vip_local_address)

    # os.environ["MESSAGEBUS"] = opts.message_bus
    #os.environ["SECURE_AGENT_USERS"] = opts.secure_agent_users
    # if opts.instance_name is None:
    #     if len(opts.vip_address) > 0:
    #         opts.instance_name = opts.vip_address[0]

    _log.debug(f"instance name set to: {options.instance_name}")
    # if opts.instance_name:
    #     store_message_bus_config(opts.message_bus, opts.instance_name)
    # else:
    #     # if there is no instance_name given get_platform_instance_name will
    #     # try to retrieve from config or default a value and store it in the config
    #     cc.get_instance_name()

    # Log configuration options
    # if getattr(opts, "show_config", False):
    #     _log.info("volttron version: {}".format(get_version()))
    #     for name, value in sorted(vars(opts).items()):
    #         _log.info("%s: %s" % (name, str(repr(value))))

    # Increase open files resource limit to max or 8192 if unlimited
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_NOFILE)

    except OSError:
        _log.exception("error getting open file limits")
    else:
        if soft != hard and soft != resource.RLIM_INFINITY:
            try:
                limit = 8192 if hard == resource.RLIM_INFINITY else hard
                resource.setrlimit(resource.RLIMIT_NOFILE, (limit, hard))
            except OSError:
                _log.exception("error setting open file limits")
            else:
                _log.debug(
                    "open file resource limit increased from %d to %d",
                    soft,
                    limit,
                )
        _log.debug("open file resource limit %d to %d", soft, hard)

    # AIP is the hook to the file system.  The control service will use this
    # object to control the install runtime and installation of agents on the platform.
    aip = service_repo.resolve(AIPplatform)
    #aip = AIPplatform(options)
    aip.setup()

    # TODO see if there is a bus wide way of doing this.
    #  tracker = Tracker()
    # protected_topics_file = os.path.join(server_options.volttron_home, "protected_topics.json")
    # _log.debug("protected topics file %s", protected_topics_file)
    # external_address_file = os.path.join(server_options.volttron_home, "external_address.json")
    # _log.debug("external_address_file file %s", external_address_file)
    # protected_topics = {}
    # # if opts.agent_monitor_frequency:
    # #     try:
    # #         int(opts.agent_monitor_frequency)
    # #     except ValueError as e:
    # #         raise ValueError("agent-monitor-frequency should be integer "
    # #                          "value. Units - seconds. This determines how "
    # #                          "often the platform checks for any crashed agent "
    # #                          "and attempts to restart. {}".format(e))

    # TODO this will be the last thing done
    # pid_file = os.path.join(server_options.volttron_home, "VOLTTRON_PID")

    # Start up the platform
    spawned_greenlets = []

    # 1. Start the messagebus or create a server connection to the messagebus depending totally
    #    on the type of messagebus
    messagebus = service_repo.resolve(MessageBus)
    assert messagebus

    messagebus.start(server_options)

    # 2. Next we need to have the config store alive.  Note the resolver should auto inject the
    #    authservice into configstore if it's present.
    #
    configstore = service_repo.resolve(ConfigStoreService)
    assert configstore is not None

    # List of greenlets on the server that we require running at all times.
    tasks: list[Greenlet] = []

    event = gevent.event.Event()
    task = gevent.spawn(configstore.core.run, event)
    event.wait()
    del event
    tasks.append(task)

    # authservice = service_repo.resolve(AuthService)
    # assert authservice

    # event = gevent.event.Event()
    # task = gevent.spawn(auth_service.core.run, event)
    # event.wait()
    # del event
    # tasks.append(task)

    # _log.debug(f"Starting {service_name}")
    # #             event = gevent.event.Event()
    # #             task = gevent.spawn(instance.core.run, event)
    # #             event.wait()
    # #             del event

    # if options.auth_enabled:
    #     auth_service = service_repo.resolve(AuthService)
    #     auth_service.start()

    control_service = service_repo.resolve(ControlService)
    assert service_repo.resolve(ControlService)

    event = gevent.event.Event()
    task = gevent.spawn(control_service.core.run, event)
    event.wait()
    del event

    tasks.append(task)

    gevent.wait(tasks, count=1)
    gevent.sleep(50000)

    messagebus.stop()

    # # event = gevent.event.Event()
    # # config_store_task = gevent.spawn(config_store.core.run, event)
    # # event.wait()
    # # del event

    # # spawned_greenlets.append(config_store_task)

    # _log.debug("Starting volttron.services.auth")
    # # event = gevent.event.Event()
    # # auth_task = gevent.spawn(auth_service.core.run, event)
    # # event.wait()
    # # del event
    # # spawned_greenlets.append(auth_task)

    # start_up_services = ("volttron.services.config_store", "volttron.services.auth")

    # for service_name in ObjectManager.get_available_services():
    #     if service_name not in start_up_services:
    #         instance = ObjectManager.get_service(
    #             service_name)    #  service_config.get_service_instance(service_name)
    #         if instance is not None:
    #             _log.debug(f"Starting {service_name}")
    #             event = gevent.event.Event()
    #             task = gevent.spawn(instance.core.run, event)
    #             event.wait()
    #             del event
    #             spawned_greenlets.append(task)

    # _log.info("********************************************Startup Complete")
    # gevent.wait(spawned_greenlets, count=1)

    # mb.stop()

    # # TODO Replace with module level zmq that holds all of the zmq bits in order to start and
    # #  run the message bus regardless of whether it's zmq or rmq.
    # if opts.message_bus == "zmq":
    #     # first service loaded must be the config store
    #     config_store = service_instances[0]
    #     assert type(config_store).__name__ == "ConfigStoreService"
    #     # assert isinstance(config_store, ConfigStoreService)
    #     # start it up before anything else
    #     spawned_greenlets.append(config_store.spawn_in_greenlet())
    #
    #     # If auth service is not found then we have no auth installed, therefore
    #     # a value error is raised and no authentication is available.
    #     try:
    #         auth_index = plugin_names.index("volttron.services.auth")
    #         auth_service = service_instances[auth_index]
    #     except ValueError:
    #         auth_service = None
    #
    #     # if we have an auth service it should be started before the
    #     # zmq router.
    #     if auth_service:
    #         spawned_greenlets.append(auth_service.spawn_in_greenlet())
    #
    #     # Start ZMQ router in separate thread to remain responsive
    #     thread = threading.Thread(target=zmq_router, args=(config_store.core.stop,))
    #     thread.daemon = True
    #     thread.start()
    #
    #     gevent.sleep(0.1)
    #     if not thread.is_alive():
    #         sys.exit()
    # else:
    #     pass
    # TODO: Add rabbit
    # Start RabbitMQ server if not running
    # rmq_config = RMQConfig()
    # if rmq_config is None:
    #     _log.error("DEBUG: Exiting due to error in rabbitmq config file. Please check.")
    #     sys.exit()

    # # If RabbitMQ is started as service, don't start it through the code
    # if not rmq_config.rabbitmq_as_service:
    #     try:
    #         start_rabbit(rmq_config.rmq_home)
    #     except AttributeError as exc:
    #         _log.error("Exception while starting RabbitMQ. Check the path in the config file.")
    #         sys.exit()
    #     except subprocess.CalledProcessError as exc:
    #         _log.error("Unable to start rabbitmq server. "
    #                    "Check rabbitmq log for errors")
    #         sys.exit()

    # Start the config store before auth so we may one day have auth use it.
    # config_store = ConfigStoreService(
    #     address=address,
    #     identity=CONFIGURATION_STORE,
    #     message_bus=opts.message_bus,
    # )
    #
    # thread = threading.Thread(target=rmq_router, args=(config_store.core.stop, ))
    # thread.daemon = True
    # thread.start()
    #
    # gevent.sleep(0.1)
    # if not thread.is_alive():
    #     sys.exit()
    #
    # gevent.sleep(1)
    # event = gevent.event.Event()
    # config_store_task = gevent.spawn(config_store.core.run, event)
    # event.wait()
    # del event
    #
    # # Ensure auth service is running before router
    # auth_file = os.path.join(opts.volttron_home, "auth.json")
    # auth = AuthService(
    #     auth_file,
    #     protected_topics_file,
    #     opts.setup_mode,
    #     opts.aip,
    #     address=address,
    #     identity=AUTH,
    #     enable_store=False,
    #     message_bus="rmq",
    # )
    #
    # event = gevent.event.Event()
    # auth_task = gevent.spawn(auth.core.run, event)
    # event.wait()
    # del event
    #
    # protected_topics = auth.get_protected_topics()
    #
    # # Spawn Greenlet friendly ZMQ router
    # # Necessary for backward compatibility with ZMQ message bus
    # green_router = GreenRouter(
    #     opts.vip_local_address,
    #     opts.vip_address,
    #     secretkey=secretkey,
    #     publickey=publickey,
    #     default_user_id="vip.service",
    #     monitor=opts.monitor,
    #     tracker=tracker,
    #     volttron_central_address=opts.volttron_central_address,
    #     volttron_central_serverkey=opts.volttron_central_serverkey,
    #     instance_name=opts.instance_name,
    #     bind_web_address=opts.bind_web_address,
    #     protected_topics=protected_topics,
    #     external_address_file=external_address_file,
    #     msgdebug=opts.msgdebug,
    #     service_notifier=notifier,
    # )
    #
    # proxy_router = ZMQProxyRouter(
    #     address=address,
    #     identity=PROXY_ROUTER,
    #     zmq_router=green_router,
    #     message_bus=opts.message_bus,
    # )
    # event = gevent.event.Event()
    # proxy_router_task = gevent.spawn(proxy_router.core.run, event)
    # event.wait()
    # del event

    # TODO Better make this so that it removes instances from this file or it will just be an
    #  ever increasing file depending on the number of instances it could get quite large.
    # The instance file is where we are going to record the instance and
    # its details according to
    # instance_file = str(VOLTTRON_INSTANCES)
    # try:
    #     instances = load_create_store(instance_file)
    # except ValueError:
    #     os.remove(instance_file)
    #     instances = load_create_store(instance_file)
    # this_instance = instances.get(command_opts.volttron_home, {})
    # this_instance["pid"] = os.getpid()
    # this_instance["version"] = get_version()
    # # note vip_address is a list
    # this_instance["vip-address"] = command_opts.vip_address
    # this_instance["volttron-home"] = command_opts.volttron_home
    # this_instance["volttron-root"] = os.path.abspath("../../..")
    # this_instance["start-args"] = sys.argv[1:]
    # instances[command_opts.volttron_home] = this_instance
    # instances.async_sync()

    # protected_topics_file = os.path.join(command_opts.volttron_home, "protected_topics.json")
    # _log.debug("protected topics file %s", protected_topics_file)
    # external_address_file = os.path.join(command_opts.volttron_home, "external_address.json")
    # _log.debug("external_address_file file %s", external_address_file)

    # # Auth and config store services have already been run, so we can run the others now.
    # for i, plugin_name in enumerate(plugin_names):
    #     if plugin_name not in ('volttron.services.auth', 'volttron.services.config_store'):
    #         _log.debug(f"spawning {plugin_name}")
    #         spawned_greenlets.append(service_instances[i].spawn_in_greenlet())

    # # Allow auth entry to be able to manage all config store entries.
    # control_service_index = plugin_names.index("volttron.services.control")
    # control_service = service_instances[control_service_index]
    # entry = AuthEntry(
    #     credentials=control_service.core.publickey,
    #     user_id=CONTROL,
    #     capabilities=[
    #         {
    #             "edit_config_store": {
    #                 "identity": "/.*/"
    #             }
    #         },
    #         "allow_auth_modifications",
    #     ],
    #     comments="Automatically added by platform on start",
    # )
    # AuthFile().add(entry, overwrite=True)

    # # # TODO Key discovery agent add in.
    # # # KeyDiscoveryAgent(
    # # #     address=address,
    # # #     serverkey=publickey,
    # # #     identity=KEY_DISCOVERY,
    # # #     external_address_config=external_address_file,
    # # #     setup_mode=opts.setup_mode,
    # # #     bind_web_address=opts.bind_web_address,
    # # #     enable_store=False,
    # # #     message_bus="zmq",
    # # # ),
    # # ]

    # # Begin the webserver based options here.
    # if command_opts.bind_web_address is not None:
    #     if not HAS_WEB:
    #         sys.stderr.write("Web libraries not installed, but bind web address specified\n")
    #         sys.stderr.write("Please install web libraries using python3 bootstrap.py --web\n")
    #         sys.exit(-1)

    #     if command_opts.instance_name is None:
    #         _update_config_file()

    #     if command_opts.message_bus == "rmq":
    #         if (command_opts.web_ssl_key is None or command_opts.web_ssl_cert is None or
    #             (not os.path.isfile(command_opts.web_ssl_key) and not os.path.isfile(command_opts.web_ssl_cert))):
    #             # This is different than the master.web cert which is used for the agent to connect
    #             # to rmq server.  The master.web-server certificate will be used for the platform web
    #             # services.
    #             base_webserver_name = PLATFORM_WEB + "-server"
    #             from volttron.utils.certs import Certs

    #             certs = Certs()
    #             certs.create_signed_cert_files(base_webserver_name, cert_type="server")
    #             command_opts.web_ssl_key = certs.private_key_file(base_webserver_name)
    #             command_opts.web_ssl_cert = certs.cert_file(base_webserver_name)

    #     _log.info("Starting platform web service")
    #     services.append(
    #         PlatformWebService(
    #             serverkey=publickey,
    #             identity=PLATFORM_WEB,
    #             address=address,
    #             bind_web_address=command_opts.bind_web_address,
    #             volttron_central_address=command_opts.volttron_central_address,
    #             enable_store=False,
    #             message_bus=command_opts.message_bus,
    #             volttron_central_rmq_address=command_opts.volttron_central_rmq_address,
    #             web_ssl_key=command_opts.web_ssl_key,
    #             web_ssl_cert=command_opts.web_ssl_cert,
    #             web_secret_key=command_opts.web_secret_key,
    #         ))

    # # ks_platformweb = KeyStore(KeyStore.get_agent_keystore_path(PLATFORM_WEB))
    # # entry = AuthEntry(
    # #     credentials=encode_key(decode_key(ks_platformweb.public)),
    # #     user_id=PLATFORM_WEB,
    # #     capabilities=["allow_auth_modifications"],
    # #     comments="Automatically added by platform on start",
    # # )
    # # AuthFile().add(entry, overwrite=True)

    # # # PLATFORM_WEB did not work on RMQ. Referred to agent as master
    # # # Added this auth to allow RPC calls for credentials authentication
    # # # when using the RMQ messagebus.
    # # ks_platformweb = KeyStore(KeyStore.get_agent_keystore_path('master'))
    # # entry = AuthEntry(credentials=encode_key(decode_key(ks_platformweb.public)),
    # #                   user_id='master',
    # #                   capabilities=['allow_auth_modifications'],
    # #                   comments='Automatically added by platform on start')
    # # AuthFile().add(entry, overwrite=True)

    # health_service_index = plugin_names.index("volttron.services.health")
    # health_service = service_instances[health_service_index]
    # notifier.register_peer_callback(health_service.peer_added, health_service.peer_dropped)
    # # # #services.append(health_service)
    # # events = [gevent.event.Event() for service in service_instances]
    # # # tasks = [gevent.spawn(service.core.run, event) for service, event in zip(services, events)]
    # # # tasks.append(config_store_task)
    # # # tasks.append(auth_task)
    # # # if stop_event:
    # # #     tasks.append(stop_event)
    # # gevent.wait()
    # #
    # # del events

    # # Auto-start agents now that all services are up
    # if command_opts.autostart:
    #     for name, error in command_opts.aip.autostart():
    #         _log.error("error starting {!r}: {}\n".format(name, error))

    # # Done with all start up process write a PID file

    # with open(pid_file, "w+") as f:
    #     f.write(str(os.getpid()))

    # # Wait for any service to stop, signaling exit
    # try:
    #     gevent.wait(spawned_greenlets, count=1)
    # except KeyboardInterrupt:
    #     _log.info("SIGINT received; shutting down")
    # finally:
    #     sys.stderr.write("Shutting down.\n")
    #     if proxy_router_task:
    #         proxy_router.core.stop()
    #     _log.debug("Kill all service agent tasks")
    #     for task in spawned_greenlets:
    #         task.kill(block=False)
    #     gevent.wait(spawned_greenlets)
    # except Exception as e:
    #     _log.error(e)
    #     import traceback
    #
    #     _log.error(traceback.print_exc())
    # finally:
    #     _log.debug("AIP finally")
    #     opts.aip.finish()
    #     instance_file = str(VOLTTRON_INSTANCES)
    #     try:
    #         instances = load_create_store(instance_file)
    #         instances.pop(opts.volttron_home, None)
    #         instances.sync()
    #         if os.path.exists(pid_file):
    #             os.remove(pid_file)
    #     except Exception:
    #         _log.warning(f"Unable to load {VOLTTRON_INSTANCES}")
    #     _log.debug("********************************************************************")
    #     _log.debug("VOLTTRON PLATFORM HAS SHUTDOWN")
    #     _log.debug("********************************************************************")


def build_arg_parser(options: ServerOptions) -> argparse.ArgumentParser:
    """
    Builds and returns an argument parser.

    :return: The argument parser.
    :rtype: argparse.ArgumentParser
    """
    from volttron.server import server_argparser as config
    from volttron.server.log_actions import LogLevelAction

    argv = sys.argv

    # Refuse to run as root
    if not getattr(os, "getuid", lambda: -1)():
        sys.stderr.write("%s: error: refusing to run as root to prevent "
                         "potential damage.\n" % os.path.basename(argv[0]))
        sys.exit(77)

    # Setup option parser
    parser = config.ArgumentParser(
        prog=os.path.basename(argv[0]),
        add_help=False,
        description="VOLTTRON platform service",
        usage="%(prog)s [OPTION]...",
        argument_default=argparse.SUPPRESS,
        epilog="Boolean options, which take no argument, may be inversed by "
        "prefixing the option with no- (e.g. --autostart may be "
        "inversed using --no-autostart).",
    )
    parser.add_argument(
        "-c",
        "--config",
        metavar="FILE",
        action="parse_config",
        ignore_unknown=False,
        sections=[None, "volttron"],
        help="read configuration from FILE",
    )
    parser.add_argument(
        "-l",
        "--log",
        metavar="FILE",
        default=None,
        help="send log output to FILE instead of stderr",
    )
    parser.add_argument(
        "-L",
        "--log-config",
        metavar="FILE",
        help="read logging configuration from FILE",
    )
    parser.add_argument(
        "--log-level",
        metavar="LOGGER:LEVEL",
        action=LogLevelAction,
        help="override default logger logging level",
    )
    parser.add_argument(
        "--monitor",
        action="store_true",
        help="monitor and log connections (implies -v)",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="add_const",
        const=10,
        dest="verboseness",
        help="decrease logger verboseness; may be used multiple times",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="add_const",
        const=-10,
        dest="verboseness",
        help="increase logger verboseness; may be used multiple times",
    )
    parser.add_argument(
        "--verboseness",
        type=int,
        metavar="LEVEL",
        default=logging.WARNING,
        help="set logger verboseness",
    )
    parser.add_argument("--messagebus",
                        type=str,
                        default=options.messagebus,
                        help="The message bus to use during startup.")
    # parser.add_argument("--auth-service",
    #                     type=str,
    #                     default=options.auth_service,
    #                     help="The auth service to use for authentication of clients.")
    # parser.add_argument("--authentication-class",
    #                     type=str,
    #                     default=options.authentication_class,
    #                     help="Class used with the AuthService for authentication")
    # parser.add_argument("--authorization-class",
    #                     type=str,
    #                     default=options.authorization_class,
    #                     help="Class used with the AuthService for authorization")
    # parser.add_argument(
    #    '--volttron-home', env_var='VOLTTRON_HOME', metavar='PATH',
    #    help='VOLTTRON configuration directory')
    parser.add_argument("--auth-enabled",
                        action="store_true",
                        inverse="--auth-disabled",
                        dest="auth_enabled",
                        help=argparse.SUPPRESS)
    parser.add_argument("--auth-disabled", action="store_false", help=argparse.SUPPRESS)
    parser.add_argument("--show-config", action="store_true", help=argparse.SUPPRESS)
    parser.add_help_argument()
    parser.add_version_argument(version="%(prog)s " + str(get_version()))

    agents = parser.add_argument_group("agent options")
    agents.add_argument(
        "--autostart",
        action="store_true",
        inverse="--no-autostart",
        help="automatically start enabled agents and services",
    )
    agents.add_argument(
        "--no-autostart",
        action="store_false",
        dest="autostart",
        help=argparse.SUPPRESS,
    )

    agents.add_argument(
        "--address",
        metavar="MESSAGE_BUS_ADDR",
        action="append",
        default=[],
        help="Address for binding to the message bus.",
    )
    # agents.add_argument(
    #     "--vip-local-address",
    #     metavar="ZMQADDR",
    #     help="ZeroMQ URL to bind for local agent VIP connections",
    # )
    agents.add_argument(
        "--instance-name",
        default=options.instance_name,
        help="The name of the VOLTTRON instance this command is starting up.",
    )
    # agents.add_argument(
    #     "--msgdebug",
    #     action="store_true",
    #     help="Route all messages to an agent while debugging.",
    # )
    # agents.add_argument(
    #     "--setup-mode",
    #     action="store_true",
    #     help="Setup mode flag for setting up authorization of external platforms.",
    # )
    parser.add_argument(
        "--message-bus",
        action="store",
        default="zmq",
        dest="messagebus",
        help="set message to be used. valid values are zmq and rmq",
    )
    agents.add_argument(
        "--agent-monitor-frequency",
        default=600,
        help="How often should the platform check for crashed agents and "
        "attempt to restart. Units=seconds. Default=600",
    )
    agents.add_argument(
        "--agent-isolation-mode",
        default=False,
        help="Require that agents run with their own users (this requires "
        "running scripts/secure_user_permissions.sh as sudo)",
    )

    ipc = "ipc://%s$VOLTTRON_HOME/run/" % ("@" if sys.platform.startswith("linux") else "")

    parser.set_defaults(
        log=None,
        log_config=None,
        monitor=False,
        verboseness=logging.WARNING,
        volttron_home=options.volttron_home,
        autostart=True,
        address=options.address,
    # vip_local_address=ipc + "vip.socket",
        instance_name=options.instance_name,
        resource_monitor=True,
        msgdebug=None,
        setup_mode=False,
        agent_isolation_mode=False)

    return parser


def run_server():
    """
    main entry point for the volttron server.

    :return:
    """
    from volttron.types.blinker import volttron_home_set_evnt

    os.environ['VOLTTRON_SERVER'] = "1"
    volttron_home = Path(os.environ.get("VOLTTRON_HOME", "~/.volttron")).expanduser()
    os.environ["VOLTTRON_HOME"] = volttron_home.as_posix()

    # Raise events that the volttron_home has been set.
    volttron_home_set_evnt.send(run_server)

    if volttron_home.joinpath("config").exists():
        service_repo.add_instance(ServerOptions, ServerOptions(config_file=volttron_home.joinpath("config")))
    else:
        service_repo.add_instance(ServerOptions, ServerOptions(volttron_home=volttron_home))

    server_options: ServerOptions = service_repo.resolve(ServerOptions)
    parser = build_arg_parser(server_options)
    assert service_repo.resolve(ServerOptions) is server_options

    if server_options.messagebus is None:
        raise ValueError("Message Bus Not Found")

    # Create an argparse parser using the server options.
    parser = build_arg_parser(options=server_options)

    # Parse and expand options
    args = sys.argv[1:]
    conf = os.path.join(volttron_home, "config")
    if os.path.exists(conf) and "SKIP_VOLTTRON_CONFIG" not in os.environ:
        # command line args get preference over same args in config file
        args = args + ["--config", conf]

    #logging.getLogger().setLevel(logging.NOTSET)
    opts = parser.parse_args(args)

    # Handle the fact that we don't use store_true and config that requires
    # inverse.  This is not a switch but a mode of operation so we change
    # from the string to a boolean value here.
    opts.agent_isolation_mode = opts.agent_isolation_mode != 'False'

    # Update the server options with the command line parameter options.
    server_options.update(opts)
    server_options.store()
    start_volttron_process(server_options)


def _main():
    """Entry point for scripts."""
    try:
        load_volttron_packages()
        sys.exit(run_server())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    total_count = 0
    for arg in sys.argv:
        vcount = 0

        if arg.startswith("-v"):
            vcount = arg.count("v")
        elif arg == "--verbose":
            vcount = 1
        total_count += vcount

    import coloredlogs
    total_count = logging.WARNING - 10 * total_count
    logging.basicConfig(level=total_count)
    coloredlogs.install(reconfigure=True)
    _main()
