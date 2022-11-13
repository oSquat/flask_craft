
import pytest

def test_root_returns_status_200(client):
    """A simple test for sanity"""
    rv = client.get('/')
    assert rv.status_code == 200
