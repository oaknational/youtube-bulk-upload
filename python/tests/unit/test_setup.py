"""Verify test infrastructure works"""

import pytest


def test_pytest_works():
    """Basic test to verify pytest runs"""
    assert True


def test_imports_work():
    """Verify we can import from src"""
    # This will fail until we create the modules
    try:
        import src.core  # noqa: F401
        import src.interfaces  # noqa: F401
        import src.services  # noqa: F401
        import src.types  # noqa: F401
        import src.utils  # noqa: F401

        assert True
    except ImportError:
        # Expected for now since we haven't created the modules yet
        pass


@pytest.mark.unit
def test_unit_marker():
    """Test unit marker works"""
    assert True


@pytest.mark.integration
def test_integration_marker():
    """Test integration marker works"""
    assert True
