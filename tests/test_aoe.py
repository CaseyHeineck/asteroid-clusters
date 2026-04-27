import pygame
from core import constants as C
from systems.gameplayeffect import AreaOfEffect, RocketHitAOE
from ui.visualeffect import RocketHitExplosionVE

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

# --- RocketHitAOE.apply ---
class FakeAsteroidAOE:
    def __init__(self, x, y, health=50):
        self.position = pygame.Vector2(x, y)
        self.health = health
        self._alive = True
    def alive(self):
        return self._alive
    def damaged(self, amount):
        self.health -= amount
        return 10 if self.health <= 0 else 0

class FakeEnemyAOE:
    def __init__(self, x, y, health=50):
        self.position = pygame.Vector2(x, y)
        self.health = health
        self._alive = True
    def alive(self):
        return self._alive
    def damaged(self, amount):
        self.health -= amount
        if self.health <= 0:
            self._alive = False
            return 100, 20
        return 0, 0

def test_rocket_hit_aoe_apply_returns_tuple():
    RocketHitExplosionVE.containers = ()
    aoe = RocketHitAOE((0, 0), [], radius=50)
    result = aoe.apply()
    assert isinstance(result, tuple) and len(result) == 2

def test_rocket_hit_aoe_apply_returns_zero_score_with_no_targets():
    RocketHitExplosionVE.containers = ()
    aoe = RocketHitAOE((0, 0), [], radius=50)
    score, xp = aoe.apply()
    assert score == 0 and xp == 0

def test_rocket_hit_aoe_damages_asteroid_in_radius():
    RocketHitExplosionVE.containers = ()
    asteroid = FakeAsteroidAOE(x=10, y=0, health=100)
    aoe = RocketHitAOE((0, 0), [asteroid], radius=50)
    aoe.apply()
    assert asteroid.health < 100

def test_rocket_hit_aoe_damages_enemy_in_radius():
    RocketHitExplosionVE.containers = ()
    enemy = FakeEnemyAOE(x=10, y=0, health=100)
    aoe = RocketHitAOE((0, 0), [enemy], radius=50)
    aoe.apply()
    assert enemy.health < 100

def test_rocket_hit_aoe_returns_score_from_asteroid_kill():
    RocketHitExplosionVE.containers = ()
    asteroid = FakeAsteroidAOE(x=10, y=0, health=1)
    aoe = RocketHitAOE((0, 0), [asteroid], radius=50, damage=999)
    score, _ = aoe.apply()
    assert score == 10

def test_rocket_hit_aoe_returns_score_from_enemy_kill():
    RocketHitExplosionVE.containers = ()
    enemy = FakeEnemyAOE(x=10, y=0, health=1)
    aoe = RocketHitAOE((0, 0), [enemy], radius=50, damage=999)
    score, _ = aoe.apply()
    assert score == 100

def test_rocket_hit_aoe_returns_xp_from_enemy_kill():
    RocketHitExplosionVE.containers = ()
    enemy = FakeEnemyAOE(x=10, y=0, health=1)
    aoe = RocketHitAOE((0, 0), [enemy], radius=50, damage=999)
    _, xp = aoe.apply()
    assert xp == 20

def test_rocket_hit_aoe_xp_zero_for_asteroid_kill():
    RocketHitExplosionVE.containers = ()
    asteroid = FakeAsteroidAOE(x=10, y=0, health=1)
    aoe = RocketHitAOE((0, 0), [asteroid], radius=50, damage=999)
    _, xp = aoe.apply()
    assert xp == 0

def test_rocket_hit_aoe_ignores_target_outside_radius():
    RocketHitExplosionVE.containers = ()
    far_enemy = FakeEnemyAOE(x=500, y=0, health=100)
    aoe = RocketHitAOE((0, 0), [far_enemy], radius=50)
    aoe.apply()
    assert far_enemy.health == 100
