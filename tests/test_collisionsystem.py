import pygame
import pytest
from core import constants as C
from types import SimpleNamespace
from systems.collisionsystem import CollisionSystem
from unittest.mock import MagicMock

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

def make_game(player_pos=(0, 0)):
    game = SimpleNamespace(player=SimpleNamespace(position=pygame.Vector2(*player_pos)),
        essence=FakeEssence(), essence_orbs=[], elemental_essence_orbs=[])
    return game

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

# --- handle_asteroid_collisions ---
class FakeAsteroidCS:
    def __init__(self, x=0, y=0, damage=5, health=10, radius=20):
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, 0)
        self.damage = damage
        self.health = health
        self.radius = radius

    def collides_with(self, other):
        return self.position.distance_to(other.position) <= self.radius + other.radius

    def damaged(self, amount):
        self.health -= amount
        if self.health <= 0:
            return 100
        return 0

class FakeShieldCS:
    def __init__(self, x=0, y=0, damage=3, radius=30):
        self.position = pygame.Vector2(x, y)
        self.radius = radius
        self.damage = damage
        self.stat_source = "shield"
        self.blocked = []
        self.damaged_calls = []

    def block_asteroid(self, asteroid, impact_scale):
        self.blocked.append(asteroid)

    def damaged(self, amount):
        self.damaged_calls.append(amount)

class FakePlayerCS:
    def __init__(self, x=0, y=0, radius=26):
        self.position = pygame.Vector2(x, y)
        self.radius = radius
        self.can_be_damaged = True
        self.collision_damage = C.PLAYER_COLLISION_DAMAGE
        self.game_over = False
        self.stat_source = "player"
        self.collision_calls = []

    def collides_with(self, other):
        return self.position.distance_to(other.position) <= self.radius + other.radius

    def apply_collision_to_asteroid(self, asteroid, impact_scale):
        self.collision_calls.append(asteroid)

    def damaged(self):
        return -50, 2

class FakeProjectileCS:
    def __init__(self, collide=True, score=0):
        self._collide = collide
        self._score = score
        self.hits = []

    def collides_with(self, other):
        return self._collide

    def on_hit(self, asteroid):
        self.hits.append(asteroid)
        return self._score

class FakeHUDCS:
    def __init__(self):
        self.score_updates = []
        self.lives_updates = []

    def update_score(self, delta):
        self.score_updates.append(delta)

    def update_player_lives(self, lives):
        self.lives_updates.append(lives)

def make_ac_game(asteroids=None, shields=None, player=None, projectiles=None):
    hud = FakeHUDCS()
    player = player or FakePlayerCS(x=1000, y=1000)
    game = SimpleNamespace(asteroids=asteroids or [], shields=shields or [],
        player=player, projectiles=projectiles or [], HUD=hud,
        combat_stats=SimpleNamespace(record_damage_event=lambda **kw: None),
        wrap_object=lambda obj: None, on_game_over=MagicMock())
    return game

def test_asteroid_is_wrapped_each_frame():
    wrapped = []
    asteroid = FakeAsteroidCS()
    game = make_ac_game(asteroids=[asteroid])
    game.wrap_object = lambda obj: wrapped.append(obj)
    CollisionSystem(game).handle_asteroid_collisions()
    assert asteroid in wrapped

def test_shield_blocks_asteroid_calls_block_asteroid():
    asteroid = FakeAsteroidCS(x=0, y=0)
    shield = FakeShieldCS(x=0, y=0)
    game = make_ac_game(asteroids=[asteroid], shields=[shield])
    CollisionSystem(game).handle_asteroid_collisions()
    assert len(shield.blocked) == 1

def test_shield_takes_damage_equal_to_asteroid_damage():
    asteroid = FakeAsteroidCS(x=0, y=0, damage=7)
    shield = FakeShieldCS(x=0, y=0)
    game = make_ac_game(asteroids=[asteroid], shields=[shield])
    CollisionSystem(game).handle_asteroid_collisions()
    assert shield.damaged_calls == [7]

def test_shield_block_prevents_player_from_being_damaged():
    asteroid = FakeAsteroidCS(x=0, y=0)
    shield = FakeShieldCS(x=0, y=0)
    player = FakePlayerCS(x=0, y=0)
    damaged_calls = []
    player.damaged = lambda: damaged_calls.append(1) or (-50, 2)
    game = make_ac_game(asteroids=[asteroid], shields=[shield], player=player)
    CollisionSystem(game).handle_asteroid_collisions()
    assert damaged_calls == []

def test_player_collision_called_when_no_shield():
    asteroid = FakeAsteroidCS(x=0, y=0)
    player = FakePlayerCS(x=0, y=0)
    game = make_ac_game(asteroids=[asteroid], player=player)
    CollisionSystem(game).handle_asteroid_collisions()
    assert len(player.collision_calls) == 1

def test_player_not_checked_when_cannot_be_damaged():
    asteroid = FakeAsteroidCS(x=0, y=0)
    player = FakePlayerCS(x=0, y=0)
    player.can_be_damaged = False
    game = make_ac_game(asteroids=[asteroid], player=player)
    CollisionSystem(game).handle_asteroid_collisions()
    assert player.collision_calls == []

def test_player_collision_updates_hud_lives():
    asteroid = FakeAsteroidCS(x=0, y=0)
    player = FakePlayerCS(x=0, y=0)
    game = make_ac_game(asteroids=[asteroid], player=player)
    CollisionSystem(game).handle_asteroid_collisions()
    assert len(game.HUD.lives_updates) == 1

def test_player_collision_reports_score_delta_to_hud():
    asteroid = FakeAsteroidCS(x=0, y=0)
    player = FakePlayerCS(x=0, y=0)
    game = make_ac_game(asteroids=[asteroid], player=player)
    CollisionSystem(game).handle_asteroid_collisions()
    assert any(s != 0 for s in game.HUD.score_updates)

def test_game_over_triggered_when_player_game_over_flag_set():
    asteroid = FakeAsteroidCS(x=0, y=0)
    player = FakePlayerCS(x=0, y=0)
    player.game_over = True
    game = make_ac_game(asteroids=[asteroid], player=player)
    CollisionSystem(game).handle_asteroid_collisions()
    game.on_game_over.assert_called_once()

def test_game_over_not_triggered_when_player_survives():
    asteroid = FakeAsteroidCS(x=0, y=0)
    player = FakePlayerCS(x=0, y=0)
    player.game_over = False
    game = make_ac_game(asteroids=[asteroid], player=player)
    CollisionSystem(game).handle_asteroid_collisions()
    game.on_game_over.assert_not_called()

def test_colliding_projectile_calls_on_hit():
    asteroid = FakeAsteroidCS(x=0, y=0)
    projectile = FakeProjectileCS(collide=True, score=0)
    game = make_ac_game(asteroids=[asteroid], projectiles=[projectile])
    CollisionSystem(game).handle_asteroid_collisions()
    assert asteroid in projectile.hits

def test_projectile_score_reported_to_hud():
    asteroid = FakeAsteroidCS(x=0, y=0)
    projectile = FakeProjectileCS(collide=True, score=200)
    game = make_ac_game(asteroids=[asteroid], projectiles=[projectile])
    CollisionSystem(game).handle_asteroid_collisions()
    assert 200 in game.HUD.score_updates

def test_non_colliding_projectile_is_not_hit():
    asteroid = FakeAsteroidCS(x=0, y=0)
    projectile = FakeProjectileCS(collide=False, score=200)
    game = make_ac_game(asteroids=[asteroid], projectiles=[projectile])
    CollisionSystem(game).handle_asteroid_collisions()
    assert projectile.hits == []

# --- handle_enemy_collisions: enemy-asteroid ---
class FakeEnemyForAsteroid:
    def __init__(self, x=0, y=0, radius=20, weight=20, damage=1):
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, 0)
        self.radius = radius
        self.weight = weight
        self.bounciness = 0.30
        self.damage = damage
        self.health = 30
        self.airspace = None
        self._alive = True
        self.impact_calls = []

    def collides_with(self, other):
        return self.position.distance_to(other.position) <= self.radius + other.radius

    def collide_and_impact(self, other):
        self.impact_calls.append(other)

    def damaged(self, amount, attacker_element=None):
        self.health -= amount
        if self.health <= 0:
            self._alive = False
            return 100, 20
        return 0, 0

    def alive(self):
        return self._alive

class FakeAsteroidForEnemy:
    def __init__(self, x=0, y=0, radius=20, damage=3, health=10, weight=40):
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, 0)
        self.radius = radius
        self.damage = damage
        self.health = health
        self.weight = weight
        self.bounciness = 0.25

    def collides_with(self, other):
        return self.position.distance_to(other.position) <= self.radius + other.radius

    def damaged(self, amount):
        self.health -= amount
        if self.health <= 0:
            return 50
        return 0

def make_enemy_asteroid_game(enemy, asteroid, player=None):
    hud = FakeHUDCS()
    player = player or FakePlayerCS(x=9999, y=9999)
    game = SimpleNamespace(
        enemies=[enemy],
        asteroids=[asteroid],
        projectiles=[],
        shields=[],
        player=player,
        HUD=hud,
        experience=MagicMock(),
        combat_stats=SimpleNamespace(record_damage_event=lambda **kw: None),
        wrap_object=lambda obj: None,
        on_game_over=MagicMock(),
        current_space=None,
    )
    return game

def test_enemy_asteroid_collision_calls_collide_and_impact():
    enemy = FakeEnemyForAsteroid(x=0, y=0)
    asteroid = FakeAsteroidForEnemy(x=0, y=0)
    game = make_enemy_asteroid_game(enemy, asteroid)
    CollisionSystem(game).handle_enemy_collisions()
    assert len(enemy.impact_calls) == 1

def test_enemy_takes_damage_from_asteroid_collision():
    enemy = FakeEnemyForAsteroid(x=0, y=0, damage=1)
    asteroid = FakeAsteroidForEnemy(x=0, y=0, damage=5)
    game = make_enemy_asteroid_game(enemy, asteroid)
    CollisionSystem(game).handle_enemy_collisions()
    assert enemy.health < 30

def test_asteroid_takes_damage_from_enemy_collision():
    enemy = FakeEnemyForAsteroid(x=0, y=0, damage=3)
    asteroid = FakeAsteroidForEnemy(x=0, y=0, damage=1, health=10)
    game = make_enemy_asteroid_game(enemy, asteroid)
    CollisionSystem(game).handle_enemy_collisions()
    assert asteroid.health < 10

def test_enemy_asteroid_no_collision_when_not_overlapping():
    enemy = FakeEnemyForAsteroid(x=0, y=0)
    asteroid = FakeAsteroidForEnemy(x=500, y=500)
    game = make_enemy_asteroid_game(enemy, asteroid)
    initial_health = enemy.health
    CollisionSystem(game).handle_enemy_collisions()
    assert enemy.health == initial_health
    assert enemy.impact_calls == []
