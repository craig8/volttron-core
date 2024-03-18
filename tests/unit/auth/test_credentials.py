import dataclasses

import pytest

from volttron.types.auth import Credentials, PKICredentials


def test_credentials_cannot_be_modified():
    foo_cred = Credentials.create(identity="foo")
    assert foo_cred

    pki_foo = PKICredentials.create(identity="foo", secretkey="sec", publickey="pkey")
    assert pki_foo
    assert pki_foo.publickey == "pkey"
    assert pki_foo.secretkey == "sec"

    with pytest.raises(dataclasses.FrozenInstanceError):
        foo_cred.identity = "bar"

    with pytest.raises(dataclasses.FrozenInstanceError):
        pki_foo.secretkey = "pkey2"

    with pytest.raises(dataclasses.FrozenInstanceError):
        pki_foo.pubickey = "sec2"
