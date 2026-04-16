from systems.airspace import AirSpace
from core import constants as C

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
