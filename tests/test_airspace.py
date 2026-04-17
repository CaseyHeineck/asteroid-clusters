from core import constants as C
from types import SimpleNamespace
from systems.airspace import AirSpace
from unittest.mock import patch

def make_space_at(gx, gy, portals=None):
    space = object.__new__(AirSpace)
    space.gx = gx
    space.gy = gy
    space.portals = portals or {}
    return space

# --- _update_cell_states ---
def test_own_cell_marked_active():
    space = make_space_at(0, 0)
    states = {}
    space._update_cell_states(states)
    assert states[(0, 0)] == "active"

def test_neighbor_with_portal_becomes_potentially_active():
    space = make_space_at(0, 0, portals={C.NORTH: object()})
    states = {}
    space._update_cell_states(states)
    dx, dy = C.DIRECTION_DELTA[C.NORTH]
    assert states[(0 + dx, 0 + dy)] == C.POTENTIALLY_ACTIVE

def test_neighbor_without_portal_becomes_restricted():
    space = make_space_at(0, 0)
    states = {}
    space._update_cell_states(states)
    dx, dy = C.DIRECTION_DELTA[C.NORTH]
    assert states[(0 + dx, 0 + dy)] == C.RESTRICTED

def test_active_neighbor_not_overwritten():
    space = make_space_at(0, 0)
    dx, dy = C.DIRECTION_DELTA[C.NORTH]
    states = {(0 + dx, 0 + dy): "active"}
    space._update_cell_states(states)
    assert states[(0 + dx, 0 + dy)] == "active"

def test_potentially_active_neighbor_not_downgraded_to_restricted():
    space = make_space_at(0, 0)
    dx, dy = C.DIRECTION_DELTA[C.EAST]
    states = {(0 + dx, 0 + dy): C.POTENTIALLY_ACTIVE}
    space._update_cell_states(states)
    assert states[(0 + dx, 0 + dy)] == C.POTENTIALLY_ACTIVE

def test_multiple_portals_mark_multiple_neighbors():
    space = make_space_at(0, 0, portals={C.NORTH: object(), C.SOUTH: object()})
    states = {}
    space._update_cell_states(states)
    ndx, ndy = C.DIRECTION_DELTA[C.NORTH]
    sdx, sdy = C.DIRECTION_DELTA[C.SOUTH]
    assert states[(0 + ndx, 0 + ndy)] == C.POTENTIALLY_ACTIVE
    assert states[(0 + sdx, 0 + sdy)] == C.POTENTIALLY_ACTIVE

# --- _generate_portals ---
def make_bare_space(gx=0, gy=0):
    space = object.__new__(AirSpace)
    space.gx = gx
    space.gy = gy
    space.portals = {}
    return space

def test_back_direction_always_creates_unlocked_portal():
    space = make_bare_space()
    space._generate_portals(C.NORTH, {}, {}, 0)
    assert C.NORTH in space.portals
    assert space.portals[C.NORTH].unlocked is True

def test_neighbor_in_grid_with_back_portal_unlocks_both_sides():
    space = make_bare_space(gx=0, gy=0)
    back_portal = SimpleNamespace(unlocked=False)
    neighbor = SimpleNamespace(portals={C.NORTH: back_portal})
    grid = {(0, 1): neighbor}
    space._generate_portals(None, grid, {}, 0)
    assert C.SOUTH in space.portals
    assert space.portals[C.SOUTH].unlocked is True
    assert back_portal.unlocked is True

def test_potentially_active_neighbor_state_spawns_portal_without_random():
    space = make_bare_space()
    states = {(0, -1): C.POTENTIALLY_ACTIVE}
    with patch("systems.airspace.random.random", return_value=1.0):
        space._generate_portals(None, {}, states, 0)
    assert C.NORTH in space.portals

def test_restricted_neighbor_state_spawns_no_portal():
    space = make_bare_space()
    states = {(0, -1): C.RESTRICTED}
    with patch("systems.airspace.random.random", return_value=0.0):
        space._generate_portals(None, {}, states, 0)
    assert C.NORTH not in space.portals

def test_unconstrained_neighbor_spawns_portal_when_random_under_threshold():
    space = make_bare_space()
    with patch("systems.airspace.random.random", return_value=C.PORTAL_SPAWN_CHANCE - 0.01):
        with patch("systems.airspace.random.choice", return_value=C.EAST):
            space._generate_portals(None, {}, {}, active_portal_count=1)
    assert C.NORTH in space.portals

def test_unconstrained_neighbor_skips_portal_when_random_at_or_above_threshold():
    space = make_bare_space()
    with patch("systems.airspace.random.random", return_value=C.PORTAL_SPAWN_CHANCE):
        space._generate_portals(None, {}, {}, active_portal_count=1)
    assert not space.portals

def test_forced_portal_added_when_no_locked_outgoing_and_no_active_portals():
    space = make_bare_space()
    with patch("systems.airspace.random.random", return_value=1.0):
        with patch("systems.airspace.random.choice", return_value=C.EAST) as mock_choice:
            space._generate_portals(None, {}, {}, active_portal_count=0)
    assert C.EAST in space.portals
    mock_choice.assert_called_once()

def test_forced_portal_not_added_when_active_portals_exist():
    space = make_bare_space()
    with patch("systems.airspace.random.random", return_value=1.0):
        with patch("systems.airspace.random.choice") as mock_choice:
            space._generate_portals(None, {}, {}, active_portal_count=1)
    mock_choice.assert_not_called()
