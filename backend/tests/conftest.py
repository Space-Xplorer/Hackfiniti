import pytest


@pytest.fixture
def sample_payload() -> dict:
    return {"ok": True}
