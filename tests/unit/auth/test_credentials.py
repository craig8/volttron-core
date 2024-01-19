import dataclasses

import pytest

from volttron.types.auth import Credentials, PKICredentials


def test_can_modify_credentials():
    foo_cred = Credentials.create(identity="foo")
    assert foo_cred

    pki_foo = PKICredentials.create(identity="foo", publickey="pkey", secretkey="sec")
    assert pki_foo

    with pytest.raises(dataclasses.FrozenInstanceError):
        foo_cred.identity = "bar"

    with pytest.raises(dataclasses.FrozenInstanceError):
        pki_foo.secretkey = "pkey2"

    with pytest.raises(dataclasses.FrozenInstanceError):
        pki_foo.pubickey = "sec2"
