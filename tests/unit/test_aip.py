import sys
from dataclasses import dataclass
from pathlib import Path
from time import sleep

from lagom import Container
from volttron_testutils.fixtures import make_volttron_home_func_scope
from volttron_testutils.testcase import (VolttronRootTestCase, VolttronRootWithNewEnvironment,
                                         VolttronRootWithTestEnvironment)

from volttron.server.aip import AIPplatform, ExecutionEnvironment, PipInstaller
from volttron.server.server_options import ServerOptions
from volttron.types.bases import AgentInstaller


class TestExecutionEnvironment(VolttronRootTestCase):

    def setUp(self):
        super().setUp()

    def test_initialization(self):
        ee = ExecutionEnvironment()
        assert ee is not None
        assert ee.process is None
        assert ee.env is None

    def test_execute(self):
        params = [sys.executable, "-m", "volttron_testutils.fixtures.infinate_loop"]
        ee = ExecutionEnvironment()
        ee.execute(params)
        assert ee.process is not None
        assert ee.process.pid is not None
        original_pid = ee.process.pid
        ee.process.kill()
        sleep(0.1)
        assert ee.process.poll() is not None

        ee = ExecutionEnvironment()
        ee.execute(params, env={'VOLTTRON_HOME': 'foo', 'VOLTTRON_PID': 'bar'})
        assert isinstance(ee.env, dict)
        assert 'foo' == ee.env['VOLTTRON_HOME']
        assert 'bar' == ee.env['VOLTTRON_PID']

        assert ee.process is not None
        assert ee.process.pid is not None
        assert original_pid != ee.process.pid
        ee.process.kill()
        sleep(0.1)
        assert ee.process.poll() is not None


class TestAIPInterface(VolttronRootWithTestEnvironment):

    def setUp(self) -> None:
        super().setUp()
        self.container = Container()
        self.container[ServerOptions] = ServerOptions()
        assert self.container[ServerOptions] is not None
        self.server_options = self.container[ServerOptions]
        assert self.server_options is self.container[ServerOptions]
        self.container[AgentInstaller] = PipInstaller
        self.aip = self.container[AIPplatform]
        self.container[AIPplatform].setup()

    def test_install_agent_from_pypi(self):
        backup = sys.executable
        try:
            sys.executable = self.venv_executable
            uuid = self.aip.install_agent("volttron-listener")
            assert uuid is not None
        finally:
            self.restore_env()
            sys.executable = backup

    def test_install_from_local(self):
        backup = sys.executable
        install_file = Path(__file__).parent.parent / "fixtures/wheels/volttron_listener-0.2.0rc0-py3-none-any.whl"
        try:
            sys.executable = self.venv_executable
            uuid = self.aip.install_agent(install_file.as_posix())
            assert uuid is not None
        finally:
            self.restore_env()
            sys.executable = backup

    def test_install_with_identity(self):
        pass


class AIPTestInitialConditions(VolttronRootTestCase):

    def setUp(self) -> None:
        super().setUp()
        self.container = Container()
        self.container[ServerOptions] = ServerOptions()
        assert self.container[ServerOptions] is not None

    def test_setup_creates_subpaths(self):
        aip = self.container[AIPplatform]
        assert aip is not None
        assert not Path(aip.install_dir).exists()
        assert not Path(aip.run_dir).exists()
        # config_dir is the volttron_home dir, so it should exist before setup, I am not sure why
        # we don't use volttron_home here instead of config_dir.
        assert Path(aip.config_dir).exists()
        aip.setup()
        assert Path(aip.install_dir).exists()
        assert Path(aip.run_dir).exists()
        assert Path(aip.config_dir).exists()

        assert Path(aip.install_dir).is_absolute()
        assert Path(aip.run_dir).is_absolute()
        assert Path(aip.install_dir).is_absolute()

        assert self.container[ServerOptions].instance_name == aip.instance_name

        install_dir = aip.install_dir
        path = aip.get_subpath('foo', "bar")
        assert f"{install_dir}/foo/bar" == path


if __name__ == '__main__':
    import unittest

    unittest.main()
