import pytest

from tests.audits.factories import InterOpsCallFactory


def test_cannot_update():
    call = InterOpsCallFactory()
    call.response_content = {"foo": "bar"}
    with pytest.raises(RuntimeError, match="This model is append-only, you cannot modify existing objects"):
        call.save()
