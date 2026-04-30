import pytest

from ai_headshots.store import store


@pytest.fixture(autouse=True)
def _reset_store():
    store.reset_for_testing()
    yield
    store.reset_for_testing()
