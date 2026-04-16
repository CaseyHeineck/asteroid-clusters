from types import SimpleNamespace
from systems.mapsystem import MapSystem


def make_portal(unlocked):
    return SimpleNamespace(unlocked=unlocked)


def make_space(*portal_lock_states):
    return SimpleNamespace(portals={i: make_portal(s) for i, s in enumerate(portal_lock_states)})


def make_map_stub(spaces):
    ms = object.__new__(MapSystem)
    ms.grid = {i: space for i, space in enumerate(spaces)}
    return ms


# --- count_locked_portals ---
def test_count_locked_portals_returns_zero_when_grid_empty():
    ms = make_map_stub([])
    assert ms.count_locked_portals() == 0

def test_count_locked_portals_counts_all_locked():
    ms = make_map_stub([make_space(False, False), make_space(False)])
    assert ms.count_locked_portals() == 3

def test_count_locked_portals_counts_none_when_all_unlocked():
    ms = make_map_stub([make_space(True, True), make_space(True)])
    assert ms.count_locked_portals() == 0

def test_count_locked_portals_counts_partial():
    ms = make_map_stub([make_space(False, True), make_space(False, False)])
    assert ms.count_locked_portals() == 3

def test_count_locked_portals_single_locked_portal():
    ms = make_map_stub([make_space(False)])
    assert ms.count_locked_portals() == 1

def test_count_locked_portals_single_unlocked_portal():
    ms = make_map_stub([make_space(True)])
    assert ms.count_locked_portals() == 0
