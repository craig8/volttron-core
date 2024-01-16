import os
import shutil
import tempfile

import pytest


def create_volttron_home() -> str:
    """
    Creates a VOLTTRON_HOME temp directory for use within a testing context.
    This function will also set the VOLTTRON_HOME directory such that it
    can be used throughout tests.

    :return: str: the temp directory
    """
    volttron_home = tempfile.mkdtemp(prefix="/tmp/volttron_testing").strip()

    # This is needed to run tests with volttron's secure mode. Without this
    # default permissions for folders under /tmp directory doesn't not have read or execute for
    # group or others
    os.chmod(volttron_home, 0o755)

    # Move volttron_home to be one level below the mkdir so that
    # the volttron.log file is not part of the same folder for
    # observer.
    volttron_home = os.path.join(volttron_home, "volttron_home")
    os.makedirs(volttron_home)

    return volttron_home


@pytest.fixture(scope="function")
def create_volttron_home_fun_scope() -> str:

    volttron_home = create_volttron_home()
    before_fun_fixture = os.environ.get("VOLTTRON_HOME")
    os.environ['VOLTTRON_HOME'] = volttron_home

    yield volttron_home.strip()

    if before_fun_fixture:
        os.environ['VOLTTRON_HOME'] = before_fun_fixture
    else:
        del os.environ['VOLTTRON_HOME']
    shutil.rmtree(volttron_home, ignore_errors=True)


@pytest.fixture(scope="module")
def create_volttron_home_mod_scope():

    volttron_home = create_volttron_home()
    before_mod_fixture = os.environ.get("VOLTTRON_HOME")

    yield volttron_home.strip()
    if before_mod_fixture:
        os.environ['VOLTTRON_HOME']
    else:
        del os.environ['VOLTTRON_HOME']
    shutil.rmtree(volttron_home, ignore_errors=True)
