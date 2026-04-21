import pytest
from django.db import connection

@pytest.fixture(scope="session", autouse=True)
def setup_test_db(django_db_setup, django_db_blocker):
    """
    Optional: ensure any session-wide setup happens here.
    """
    pass

@pytest.fixture(autouse=True)
def clear_db_between_tests(db):
    """
    Surgical cleanup for tests that might leave artifacts.
    """
    yield
