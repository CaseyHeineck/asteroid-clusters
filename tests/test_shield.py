import pygame
from core import constants as C
from entities.shield import Shield

class FakeCombatStats:
    def add_absorbed(self, source, amount): pass

class FakeGame:
    combat_stats = FakeCombatStats()

class FakeOwner:
    def __init__(self):
        self.position = pygame.Vector2(0, 0)
        self.radius = C.PLAYER_RADIUS
        self.collision_damage = C.PLAYER_COLLISION_DAMAGE
        self.game = FakeGame()
        self.shield = True

    def alive(self):
        return True

class FakeSource:
    stat_source = C.PLAYER_SHIELD

def make_shield(max_health=10):
    return Shield(FakeOwner(), FakeSource(), max_health=max_health)

# --- damaged ---
def test_damaged_reduces_health():
    shield = make_shield(max_health=10)
    shield.damaged(3)
    assert shield.health == 7

def test_damaged_sets_hit_flash_timer():
    shield = make_shield()
    shield.damaged(1)
    assert shield.hit_flash_timer > 0

def test_damaged_health_does_not_go_below_zero():
    shield = make_shield(max_health=5)
    shield.damaged(100)
    assert shield.health == 0

def test_damaged_zero_damage_is_no_op():
    shield = make_shield(max_health=10)
    shield.damaged(0)
    assert shield.health == 10
    assert shield.hit_flash_timer == 0

def test_lethal_damage_kills_shield():
    shield = make_shield(max_health=5)
    shield.damaged(5)
    assert not shield.alive()

def test_lethal_damage_clears_owner_shield_flag():
    owner = FakeOwner()
    shield = Shield(owner, FakeSource(), max_health=5)
    shield.damaged(5)
    assert not owner.shield

def test_non_lethal_damage_leaves_shield_alive():
    shield = make_shield(max_health=10)
    pygame.sprite.Group(shield)
    shield.damaged(3)
    assert shield.alive()

# --- update ---
def test_update_decrements_hit_flash_timer():
    shield = make_shield()
    shield.damaged(1)
    timer_before = shield.hit_flash_timer
    shield.update(0.05)
    assert shield.hit_flash_timer < timer_before

def test_update_tracks_owner_position():
    owner = FakeOwner()
    shield = Shield(owner, FakeSource())
    owner.position = pygame.Vector2(100, 200)
    shield.update(0.016)
    assert shield.position == owner.position

# --- damaged: add_absorbed ---
class TrackingCombatStats:
    def __init__(self):
        self.absorbed_calls = []
    def add_absorbed(self, source, amount):
        self.absorbed_calls.append((source, amount))

class TrackingGame:
    def __init__(self):
        self.combat_stats = TrackingCombatStats()

class TrackingOwner(FakeOwner):
    def __init__(self):
        super().__init__()
        self.game = TrackingGame()

def test_damaged_calls_add_absorbed_with_correct_amount():
    owner = TrackingOwner()
    shield = Shield(owner, FakeSource(), max_health=10)
    shield.damaged(4)
    assert (C.PLAYER_SHIELD, 4) in owner.game.combat_stats.absorbed_calls

def test_damaged_zero_damage_does_not_call_add_absorbed():
    owner = TrackingOwner()
    shield = Shield(owner, FakeSource(), max_health=10)
    shield.damaged(0)
    assert owner.game.combat_stats.absorbed_calls == []

# --- block_asteroid ---
class TrackingOwnerForBlock(FakeOwner):
    def __init__(self):
        super().__init__()
        self.block_calls = []
    def apply_collision_to_asteroid(self, asteroid, impact_scale):
        self.block_calls.append((asteroid, impact_scale))

def test_block_asteroid_delegates_to_owner():
    owner = TrackingOwnerForBlock()
    shield = Shield(owner, FakeSource())
    fake_asteroid = object()
    shield.block_asteroid(fake_asteroid, impact_scale=0.5)
    assert (fake_asteroid, 0.5) in owner.block_calls
