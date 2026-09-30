"""Pytest entry point for the same offline foundation contract checks."""
from validate_foundation import validate

def test_foundation_contracts():
    failures = [check for check in validate() if not check['passed']]
    assert not failures, failures
