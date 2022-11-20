
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
    for player in j['players']:
        assert player in players
    for player in players:
        assert player in j['players']

def test_cmd_list_count(fake_server, client):
    """The list command should return the number of in-game players"""
    # get a random number of players
    n = int(get_random(1, 'num'))
    players = [get_random(5) for i in range(0, n)]
    for player in players:
        fake_server.player_join(player)
    rv = client.get(url_for('cmd.list'))
    j = json.loads(rv.data)
    assert j['count'] == n

def test_cmd_list_max(fake_server, client):
    """The list command should return the maximum player count"""
    # get a random number of players
    rv = client.get(url_for('cmd.list'))
    j = json.loads(rv.data)
    assert j['max'] == 5
