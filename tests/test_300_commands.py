
from flask import url_for

def test_cmd_blueprint(client):
    """The cmd blueprint root returns something simple on GET"""
    rv = client.get(url_for('cmd.root'))
    assert rv.status_code == 200

