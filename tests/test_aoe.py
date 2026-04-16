import pygame
from systems.gameplayeffect import AreaOfEffect

class FakeTarget:
    def __init__(self, x, y, is_alive=True):
        self.position = pygame.Vector2(x, y)
        self._alive = is_alive

    def alive(self):
        return self._alive

# --- get_targets_in_radius ---
def test_target_within_radius_is_included():
    target = FakeTarget(10, 0)
    aoe = AreaOfEffect((0, 0), [target], radius=50)
    assert target in aoe.get_targets_in_radius()

def test_target_outside_radius_is_excluded():
    target = FakeTarget(100, 0)
    aoe = AreaOfEffect((0, 0), [target], radius=50)
    assert target not in aoe.get_targets_in_radius()

def test_target_exactly_at_radius_edge_is_included():
    target = FakeTarget(50, 0)
    aoe = AreaOfEffect((0, 0), [target], radius=50)
    assert target in aoe.get_targets_in_radius()

def test_ignored_target_is_excluded():
    target = FakeTarget(10, 0)
    aoe = AreaOfEffect((0, 0), [target], radius=50)
    assert target not in aoe.get_targets_in_radius(ignored_targets=[target])

def test_dead_target_is_excluded():
    target = FakeTarget(10, 0, is_alive=False)
    aoe = AreaOfEffect((0, 0), [target], radius=50)
    assert target not in aoe.get_targets_in_radius()

def test_only_in_range_targets_returned_from_mixed_list():
    near = FakeTarget(10, 0)
    far = FakeTarget(200, 0)
    aoe = AreaOfEffect((0, 0), [near, far], radius=50)
    result = aoe.get_targets_in_radius()
    assert near in result
    assert far not in result

def test_no_targets_returns_empty_list():
    aoe = AreaOfEffect((0, 0), [], radius=50)
    assert aoe.get_targets_in_radius() == []
