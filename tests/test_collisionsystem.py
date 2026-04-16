import pytest
import pygame
from types import SimpleNamespace
from systems.collisionsystem import CollisionSystem
from core import constants as C


class FakeOrb:
    def __init__(self, x, y, value=5):
        self.position = pygame.Vector2(x, y)
        self.value = value
        self._killed = False

    def kill(self):
        self._killed = True


class FakeEssence:
    def __init__(self):
        self.added = 0
        self.added_elemental = 0

    def add(self, amount):
        self.added += amount

    def add_elemental(self, amount):
        self.added_elemental += amount


class FakeExperience:
    def __init__(self):
        self.added_xp = 0

    def add_xp(self, amount):
        self.added_xp += amount


def make_game(player_pos=(0, 0)):
    game = SimpleNamespace(
        player=SimpleNamespace(position=pygame.Vector2(*player_pos)),
        experience=FakeExperience(),
        essence=FakeEssence(),
        exp_orbs=[],
        essence_orbs=[],
        elemental_essence_orbs=[],
    )
    return game


# --- handle_exp_orb_pickups ---
def test_no_exp_orbs_is_no_op():
    game = make_game()
    cs = CollisionSystem(game)
    cs.handle_exp_orb_pickups()
    assert game.experience.added_xp == 0

def test_nearby_exp_orb_adds_xp():
    game = make_game()
    orb = FakeOrb(0, C.EXP_ORB_PICKUP_RADIUS - 1, value=10)
    game.exp_orbs = [orb]
    cs = CollisionSystem(game)
    cs.handle_exp_orb_pickups()
    assert game.experience.added_xp == 10

def test_nearby_exp_orb_is_killed():
    game = make_game()
    orb = FakeOrb(0, C.EXP_ORB_PICKUP_RADIUS - 1)
    game.exp_orbs = [orb]
    cs = CollisionSystem(game)
    cs.handle_exp_orb_pickups()
    assert orb._killed

def test_distant_exp_orb_is_not_collected():
    game = make_game()
    orb = FakeOrb(0, C.EXP_ORB_PICKUP_RADIUS + 10, value=10)
    game.exp_orbs = [orb]
    cs = CollisionSystem(game)
    cs.handle_exp_orb_pickups()
    assert game.experience.added_xp == 0
    assert not orb._killed

def test_multiple_nearby_exp_orbs_all_collected():
    game = make_game()
    orbs = [FakeOrb(0, 0, value=3), FakeOrb(1, 0, value=7)]
    game.exp_orbs = orbs
    cs = CollisionSystem(game)
    cs.handle_exp_orb_pickups()
    assert game.experience.added_xp == 10
    assert all(o._killed for o in orbs)


# --- handle_essence_orb_pickups ---
def test_no_essence_orbs_is_no_op():
    game = make_game()
    cs = CollisionSystem(game)
    cs.handle_essence_orb_pickups()
    assert game.essence.added == 0

def test_nearby_essence_orb_adds_essence():
    game = make_game()
    orb = FakeOrb(0, C.ESSENCE_ORB_PICKUP_RADIUS - 1, value=4)
    game.essence_orbs = [orb]
    cs = CollisionSystem(game)
    cs.handle_essence_orb_pickups()
    assert game.essence.added == 4

def test_nearby_essence_orb_is_killed():
    game = make_game()
    orb = FakeOrb(0, C.ESSENCE_ORB_PICKUP_RADIUS - 1)
    game.essence_orbs = [orb]
    cs = CollisionSystem(game)
    cs.handle_essence_orb_pickups()
    assert orb._killed

def test_distant_essence_orb_not_collected():
    game = make_game()
    orb = FakeOrb(0, C.ESSENCE_ORB_PICKUP_RADIUS + 10, value=4)
    game.essence_orbs = [orb]
    cs = CollisionSystem(game)
    cs.handle_essence_orb_pickups()
    assert game.essence.added == 0


# --- handle_elemental_essence_orb_pickups ---
def test_no_elemental_orbs_is_no_op():
    game = make_game()
    cs = CollisionSystem(game)
    cs.handle_elemental_essence_orb_pickups()
    assert game.essence.added_elemental == 0

def test_nearby_elemental_orb_adds_elemental_essence():
    game = make_game()
    orb = FakeOrb(0, C.ESSENCE_ORB_PICKUP_RADIUS - 1, value=2)
    game.elemental_essence_orbs = [orb]
    cs = CollisionSystem(game)
    cs.handle_elemental_essence_orb_pickups()
    assert game.essence.added_elemental == 2

def test_nearby_elemental_orb_is_killed():
    game = make_game()
    orb = FakeOrb(0, C.ESSENCE_ORB_PICKUP_RADIUS - 1)
    game.elemental_essence_orbs = [orb]
    cs = CollisionSystem(game)
    cs.handle_elemental_essence_orb_pickups()
    assert orb._killed

def test_distant_elemental_orb_not_collected():
    game = make_game()
    orb = FakeOrb(0, C.ESSENCE_ORB_PICKUP_RADIUS + 10, value=2)
    game.elemental_essence_orbs = [orb]
    cs = CollisionSystem(game)
    cs.handle_elemental_essence_orb_pickups()
    assert game.essence.added_elemental == 0
