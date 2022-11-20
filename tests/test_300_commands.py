
import json 

from flask import url_for

from conftest import get_random

def test_cmd_blueprint(client):
    """The cmd blueprint root returns something simple on GET"""
    rv = client.get(url_for('cmd.root'))
    assert rv.status_code == 200

def test_cmd_list(fake_server, client):
    """The list command should return in-game players"""
    players = [get_random(5) for i in range(0,5)]
    for player in players:
        fake_server.player_join(player)
    rv = client.get(url_for('cmd.list'))
    j = json.loads(rv.data)
    for player in j['response']['players']:
        assert player in players
    for player in players:
        assert player in j['response']['players']
