
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

def test_cmd_kick(fake_server, client):
    """The kick command removes a player"""
    # add 3 players, choose the first to kick
    players = [get_random(5) for i in range(0, 3)]
    for player in players:
        fake_server.player_join(player)
    player = players[0]

    # sanity check, there are 3 players now
    rv = client.get(url_for('cmd.list'))
    j = json.loads(rv.data)
    assert j['count'] == 3

    # kick the player, and confirm player count is 2
    client.post(
        url_for('cmd.kick'),
        content_type='application/json',
        data=json.dumps({'player': player})
    )
    rv = client.get(url_for('cmd.list'))
    j = json.loads(rv.data)
    assert j['count'] == 2

def test_cmd_kick_returns_success_result(fake_server, client):
    """Test kick command response result can be success"""
    # add 3 players, choose the first to kick
    players = [get_random(5) for i in range(0, 3)]
    for player in players:
        fake_server.player_join(player)
    player = players[0]

    # kick the player
    rv = client.post(
        url_for('cmd.kick'),
        content_type='application/json',
        data=json.dumps({'player': player})
    )
    j = json.loads(rv.data)

    assert j['result'] == 'success'

def test_cmd_kick_returns_failure_result(fake_server, client):
    """Test kick command response result can be failure"""
    # add 3 players, choose the first to kick
    players = [get_random(5) for i in range(0, 3)]
    for player in players:
        fake_server.player_join(player)

    # kick a player that isn't in the list of players
    rv = client.post(
        url_for('cmd.kick'),
        content_type='application/json',
        data=json.dumps({'player': get_random(3)})
    )
    j = json.loads(rv.data)

    assert j['result'] == 'failure'
