import pygame
import pytest
from core import constants as C
from entities.drone import Drone, ExplosiveDrone, KineticDrone, LaserDrone, PlasmaDrone, SentinelDrone
from entities.projectile import Kinetic, Plasma, Rocket
from ui.visualeffect import MuzzleFlareVE

class FakePlayer:
    def __init__(self):
        self.position = pygame.Vector2(0, 0)

class FakeCombatStats:
    def add_repaired(self, source, amount): pass

class FakeSentinelGame:
    combat_stats = FakeCombatStats()

class FakeSentinelPlayer:
    def __init__(self):
        self.position = pygame.Vector2(0, 0)
        self.radius = C.PLAYER_RADIUS
        self.collision_damage = C.PLAYER_COLLISION_DAMAGE
        self.game = FakeSentinelGame()
        self.shield = False
    def alive(self):
        return True

# --- Drone.collides_with ---
def test_drone_collides_with_always_returns_false():
    drone = LaserDrone(FakePlayer(), [])
    other = LaserDrone(FakePlayer(), [])
    assert not drone.collides_with(other)

# --- LaserDrone.get_charge_ratio ---
def test_charge_ratio_is_1_when_fully_charged():
    drone = LaserDrone(FakePlayer(), [])
    drone.platform.weapons_free_timer = 0
    assert drone.platform.get_charge_ratio() == pytest.approx(1.0, abs=0.001)

def test_charge_ratio_is_0_when_just_fired():
    drone = LaserDrone(FakePlayer(), [])
    drone.platform.weapons_free_timer = drone.platform.weapons_free_timer_max
    assert drone.platform.get_charge_ratio() == pytest.approx(0.0, abs=0.001)

def test_charge_ratio_is_half_at_midpoint():
    drone = LaserDrone(FakePlayer(), [])
    drone.platform.weapons_free_timer = drone.platform.weapons_free_timer_max / 2
    assert drone.platform.get_charge_ratio() == pytest.approx(0.5, abs=0.001)

def test_charge_ratio_is_1_when_timer_max_is_zero():
    drone = LaserDrone(FakePlayer(), [])
    drone.platform.weapons_free_timer_max = 0
    assert drone.platform.get_charge_ratio() == 1

# --- LaserDrone.lerp_color ---
def test_lerp_color_at_0_returns_start():
    drone = LaserDrone(FakePlayer(), [])
    result = drone.platform.lerp_color((0, 0, 0), (255, 255, 255), 0)
    assert result == (0, 0, 0)

def test_lerp_color_at_1_returns_end():
    drone = LaserDrone(FakePlayer(), [])
    result = drone.platform.lerp_color((0, 0, 0), (255, 255, 255), 1)
    assert result == (255, 255, 255)

def test_lerp_color_at_half_returns_midpoint():
    drone = LaserDrone(FakePlayer(), [])
    result = drone.platform.lerp_color((0, 0, 0), (100, 100, 100), 0.5)
    assert result == (50, 50, 50)

def test_lerp_color_clamps_t_below_zero():
    drone = LaserDrone(FakePlayer(), [])
    result = drone.platform.lerp_color((10, 10, 10), (100, 100, 100), -1)
    assert result == (10, 10, 10)

def test_lerp_color_clamps_t_above_one():
    drone = LaserDrone(FakePlayer(), [])
    result = drone.platform.lerp_color((10, 10, 10), (100, 100, 100), 2)
    assert result == (100, 100, 100)

# --- LaserDrone.get_platform_color ---
def test_platform_color_when_fully_charged_is_last_in_sequence():
    drone = LaserDrone(FakePlayer(), [])
    drone.platform.weapons_free_timer = 0
    color = drone.platform.get_platform_color()
    assert color == C.LASER_RED

def test_platform_color_when_uncharged_is_first_in_sequence():
    drone = LaserDrone(FakePlayer(), [])
    drone.platform.weapons_free_timer = drone.platform.weapons_free_timer_max
    color = drone.platform.get_platform_color()
    assert color == C.INDIGO

# --- Drone.acquire_target ---
class FakeAsteroid:
    def __init__(self, x, y, health=10):
        self.position = pygame.Vector2(x, y)
        self.health = health

class FakeEnemy:
    def __init__(self, x, y, health=10, airspace=None):
        self.position = pygame.Vector2(x, y)
        self.health = health
        self.airspace = airspace

class FakeDroneGame:
    def __init__(self, enemies=None, current_space=None):
        self.enemies = enemies or []
        self.current_space = current_space

class FakePlayerWithGame:
    def __init__(self, game=None):
        self.position = pygame.Vector2(0, 0)
        self.game = game or FakeDroneGame()

def test_acquire_target_ignores_asteroids_outside_range():
    drone = LaserDrone(FakePlayer(), [])
    far_asteroid = FakeAsteroid(9999, 9999)
    drone.asteroids = [far_asteroid]
    drone.acquire_target()
    assert drone.target is None

def test_acquire_target_selects_healthiest_in_range():
    player = FakePlayer()
    player.position = pygame.Vector2(0, 0)
    weak = FakeAsteroid(10, 0, health=5)
    strong = FakeAsteroid(10, 0, health=20)
    drone = LaserDrone(player, [weak, strong])
    drone.acquire_target()
    assert drone.target is strong

def test_acquire_target_none_when_no_asteroids():
    drone = LaserDrone(FakePlayer(), [])
    drone.acquire_target()
    assert drone.target is None

# --- Drone.aim_at_target ---
def test_aim_at_target_is_no_op_when_target_is_none():
    drone = LaserDrone(FakePlayer(), [])
    drone.rotation = 42.0
    drone.target = None
    drone.aim_at_target()
    assert drone.rotation == 42.0

def test_aim_at_target_sets_rotation_toward_target():
    drone = LaserDrone(FakePlayer(), [])
    drone.position = pygame.Vector2(0, 0)
    drone.target = FakeAsteroid(0, -100)
    drone.aim_at_target()
    assert drone.rotation == pytest.approx(0.0, abs=0.1)

# --- Drone.orbit_player ---
def test_orbit_player_increments_orbit_angle():
    drone = LaserDrone(FakePlayer(), [])
    initial_angle = drone.orbit_angle
    drone.orbit_player(1.0)
    assert drone.orbit_angle == pytest.approx(initial_angle + C.DRONE_ORBIT_SPEED, abs=0.001)

def test_orbit_player_positions_drone_relative_to_player():
    player = FakePlayer()
    player.position = pygame.Vector2(100, 100)
    drone = LaserDrone(player, [])
    drone.orbit_angle = 0
    drone.orbit_player(0)
    expected = player.position + pygame.Vector2(C.DRONE_ORBIT_RADIUS, 0).rotate(0)
    assert drone.position == expected

# --- Drone.shoot ---
def test_shoot_returns_zero_when_on_cooldown():
    drone = LaserDrone(FakePlayer(), [])
    drone.platform.weapons_free_timer = 1.0
    drone.target = FakeAsteroid(10, 0)
    assert drone.shoot() == 0

def test_shoot_does_not_reset_timer_when_on_cooldown():
    drone = LaserDrone(FakePlayer(), [])
    drone.platform.weapons_free_timer = 1.0
    drone.target = FakeAsteroid(10, 0)
    drone.shoot()
    assert drone.platform.weapons_free_timer == 1.0

def test_shoot_returns_zero_when_no_target():
    drone = LaserDrone(FakePlayer(), [])
    drone.platform.weapons_free_timer = 0
    drone.target = None
    assert drone.shoot() == 0

# --- SentinelDrone.shield_sentinel ---
class FakeShieldProxy:
    health = 10
    max_health = 10
    def alive(self):
        return True

def test_sentinel_shield_create_timer_decrements():
    drone = SentinelDrone(FakeSentinelPlayer(), [])
    drone.shield_create_timer = 1.0
    drone.player_shield = FakeShieldProxy()
    drone.shield_sentinel(0.5)
    assert drone.shield_create_timer == pytest.approx(0.5, abs=0.001)

def test_sentinel_shield_repair_timer_decrements():
    drone = SentinelDrone(FakeSentinelPlayer(), [])
    drone.shield_repair_timer = 1.0
    drone.player_shield = FakeShieldProxy()
    drone.shield_sentinel(0.4)
    assert drone.shield_repair_timer == pytest.approx(0.6, abs=0.001)

def test_sentinel_creates_shield_when_timer_is_zero_and_no_shield():
    drone = SentinelDrone(FakeSentinelPlayer(), [])
    drone.player_shield = None
    drone.shield_create_timer = 0
    drone.shield_sentinel(0)
    assert drone.player_shield is not None

def test_sentinel_sets_player_shield_flag_when_shield_created():
    player = FakeSentinelPlayer()
    drone = SentinelDrone(player, [])
    drone.player_shield = None
    drone.shield_create_timer = 0
    drone.shield_sentinel(0)
    assert player.shield is True

def test_sentinel_repairs_shield_health_when_timer_expired():
    player = FakeSentinelPlayer()
    drone = SentinelDrone(player, [])
    drone.shield_create_timer = 0
    drone.shield_sentinel(0)
    shield = drone.player_shield
    pygame.sprite.Group(shield)
    shield.health = shield.max_health - 3
    drone.shield_repair_timer = 0
    drone.shield_sentinel(0)
    assert shield.health == shield.max_health - 2

def test_sentinel_clears_player_shield_when_shield_dies_externally():
    player = FakeSentinelPlayer()
    drone = SentinelDrone(player, [])
    dead_shield = FakeShieldProxy()
    dead_shield.alive = lambda: False
    drone.player_shield = dead_shield
    drone.shield_create_timer = 1.0
    drone.shield_sentinel(0)
    assert drone.player_shield is None
    assert player.shield is False

# --- KineticDrone.acquire_target (base: closest to player) ---
def test_kinetic_acquire_target_selects_closest_to_player_not_healthiest():
    player = FakePlayer()
    player.position = pygame.Vector2(0, 0)
    close_weak = FakeAsteroid(5, 0, health=1)
    far_strong = FakeAsteroid(200, 0, health=999)
    drone = KineticDrone(player, [close_weak, far_strong])
    drone.acquire_target()
    assert drone.target is close_weak

# --- ExplosiveDrone.platform.fire ---
def test_explosive_drone_fire_sets_launch_animation_timer():
    Rocket.containers = ()
    player = FakeSentinelPlayer()
    drone = ExplosiveDrone(player, [])
    drone.platform.launch_animation_timer = 0
    drone.platform.fire(drone)
    assert drone.platform.launch_animation_timer > 0

def test_explosive_drone_fire_returns_zero():
    Rocket.containers = ()
    player = FakeSentinelPlayer()
    drone = ExplosiveDrone(player, [])
    assert drone.platform.fire(drone) == 0

# --- KineticDrone.platform.fire ---
def test_kinetic_drone_fire_returns_zero():
    Kinetic.containers = ()
    MuzzleFlareVE.containers = ()
    player = FakeSentinelPlayer()
    drone = KineticDrone(player, [])
    assert drone.platform.fire(drone) == 0

# --- PlasmaDrone.platform.fire ---
def test_plasma_drone_fire_returns_zero():
    Plasma.containers = ()
    player = FakeSentinelPlayer()
    drone = PlasmaDrone(player, [])
    assert drone.platform.fire(drone) == 0

# --- Drone.shoot (timer reset after firing) ---
def test_shoot_sets_timer_to_max_after_firing():
    Rocket.containers = ()
    player = FakeSentinelPlayer()
    drone = ExplosiveDrone(player, [])
    drone.platform.weapons_free_timer = 0
    drone.target = FakeAsteroid(10, 0)
    drone.shoot()
    assert drone.platform.weapons_free_timer == drone.platform.weapons_free_timer_max

# --- Drone.update (timer decrement) ---
def test_update_decrements_weapons_free_timer():
    drone = LaserDrone(FakePlayer(), [])
    drone.platform.weapons_free_timer = 1.0
    drone.update(0.4)
    assert drone.platform.weapons_free_timer == pytest.approx(0.6, abs=0.001)

def test_update_clamps_timer_to_zero():
    drone = LaserDrone(FakePlayer(), [])
    drone.platform.weapons_free_timer = 0.1
    drone.update(1.0)
    assert drone.platform.weapons_free_timer == 0.0

# --- ExplosiveDrone.update (launch animation timer) ---
def test_explosive_drone_update_decrements_launch_animation_timer():
    Rocket.containers = ()
    player = FakeSentinelPlayer()
    drone = ExplosiveDrone(player, [])
    drone.platform.launch_animation_timer = 1.0
    drone.update(0.3)
    assert drone.platform.launch_animation_timer == pytest.approx(0.7, abs=0.001)

def test_explosive_drone_update_clamps_launch_timer_to_zero():
    Rocket.containers = ()
    player = FakeSentinelPlayer()
    drone = ExplosiveDrone(player, [])
    drone.platform.launch_animation_timer = 0.1
    drone.update(5.0)
    assert drone.platform.launch_animation_timer == 0.0

# --- KineticDrone.acquire_target (range filtering) ---
def test_kinetic_acquire_target_ignores_asteroids_outside_range():
    player = FakePlayer()
    player.position = pygame.Vector2(0, 0)
    drone = KineticDrone(player, [])
    drone.position = pygame.Vector2(0, 0)
    far = FakeAsteroid(C.KINETIC_DRONE_WEAPONS_RANGE + 100, 0)
    drone.asteroids = [far]
    drone.acquire_target()
    assert drone.target is None

def test_kinetic_acquire_target_picks_asteroid_within_range():
    player = FakePlayer()
    player.position = pygame.Vector2(0, 0)
    drone = KineticDrone(player, [])
    drone.position = pygame.Vector2(0, 0)
    near = FakeAsteroid(10, 0)
    drone.asteroids = [near]
    drone.acquire_target()
    assert drone.target is near

# --- LaserDrone.acquire_target (same-health tiebreaker) ---
def test_laser_acquire_target_picks_closest_to_player_when_health_tied():
    player = FakePlayer()
    player.position = pygame.Vector2(0, 0)
    close = FakeAsteroid(10, 0, health=10)
    far = FakeAsteroid(50, 0, health=10)
    drone = LaserDrone(player, [close, far])
    drone.acquire_target()
    assert drone.target is close

# --- SentinelDrone.shield_sentinel (additional cases) ---
def test_sentinel_does_not_create_shield_when_create_timer_active():
    drone = SentinelDrone(FakeSentinelPlayer(), [])
    drone.player_shield = None
    drone.shield_create_timer = 1.0
    drone.shield_sentinel(0)
    assert drone.player_shield is None

def test_sentinel_does_not_repair_when_shield_at_full_health():
    player = FakeSentinelPlayer()
    drone = SentinelDrone(player, [])
    drone.shield_create_timer = 0
    drone.shield_sentinel(0)
    shield = drone.player_shield
    pygame.sprite.Group(shield)
    assert shield.health == shield.max_health
    drone.shield_repair_timer = 0
    drone.shield_sentinel(0)
    assert shield.health == shield.max_health

def test_sentinel_repair_timer_resets_after_repair():
    player = FakeSentinelPlayer()
    drone = SentinelDrone(player, [])
    drone.shield_create_timer = 0
    drone.shield_sentinel(0)
    shield = drone.player_shield
    pygame.sprite.Group(shield)
    shield.health = shield.max_health - 3
    drone.shield_repair_timer = 0
    drone.shield_sentinel(0)
    assert drone.shield_repair_timer > 0

def test_sentinel_calls_add_repaired_on_combat_stats():
    player = FakeSentinelPlayer()
    drone = SentinelDrone(player, [])
    drone.shield_create_timer = 0
    drone.shield_sentinel(0)
    shield = drone.player_shield
    pygame.sprite.Group(shield)
    shield.health = shield.max_health - 3
    drone.shield_repair_timer = 0
    repaired_calls = []
    player.game.combat_stats.add_repaired = lambda src, amt: repaired_calls.append((src, amt))
    drone.shield_sentinel(0)
    assert len(repaired_calls) == 1
    assert repaired_calls[0][1] == 1

# --- Drone.acquire_target: enemy targeting ---
def test_drone_targets_enemy_over_asteroid_when_both_in_range():
    space = object()
    enemy = FakeEnemy(10, 0, airspace=space)
    game = FakeDroneGame(enemies=[enemy], current_space=space)
    player = FakePlayerWithGame(game)
    asteroid = FakeAsteroid(10, 0)
    drone = KineticDrone(player, [asteroid])
    drone.position = pygame.Vector2(0, 0)
    drone.acquire_target()
    assert drone.target is enemy

def test_drone_falls_back_to_asteroid_when_no_enemy_in_range():
    space = object()
    game = FakeDroneGame(enemies=[], current_space=space)
    player = FakePlayerWithGame(game)
    asteroid = FakeAsteroid(10, 0)
    drone = KineticDrone(player, [asteroid])
    drone.position = pygame.Vector2(0, 0)
    drone.acquire_target()
    assert drone.target is asteroid

def test_drone_ignores_enemy_in_different_airspace():
    space_a = object()
    space_b = object()
    enemy = FakeEnemy(10, 0, airspace=space_a)
    game = FakeDroneGame(enemies=[enemy], current_space=space_b)
    player = FakePlayerWithGame(game)
    asteroid = FakeAsteroid(10, 0)
    drone = KineticDrone(player, [asteroid])
    drone.position = pygame.Vector2(0, 0)
    drone.acquire_target()
    assert drone.target is asteroid

def test_drone_targets_enemy_with_none_airspace_as_same_airspace():
    space = object()
    enemy = FakeEnemy(10, 0, airspace=None)
    game = FakeDroneGame(enemies=[enemy], current_space=space)
    player = FakePlayerWithGame(game)
    drone = KineticDrone(player, [])
    drone.position = pygame.Vector2(0, 0)
    drone.acquire_target()
    assert drone.target is enemy

def test_laser_drone_targets_healthiest_enemy_over_asteroid():
    space = object()
    weak_enemy = FakeEnemy(10, 0, health=5, airspace=space)
    strong_enemy = FakeEnemy(10, 0, health=50, airspace=space)
    game = FakeDroneGame(enemies=[weak_enemy, strong_enemy], current_space=space)
    player = FakePlayerWithGame(game)
    asteroid = FakeAsteroid(10, 0, health=999)
    drone = LaserDrone(player, [asteroid])
    drone.position = pygame.Vector2(0, 0)
    drone.acquire_target()
    assert drone.target is strong_enemy

def test_laser_drone_falls_back_to_asteroid_when_no_enemy_in_range():
    space = object()
    far_enemy = FakeEnemy(9999, 0, airspace=space)
    game = FakeDroneGame(enemies=[far_enemy], current_space=space)
    player = FakePlayerWithGame(game)
    asteroid = FakeAsteroid(10, 0, health=10)
    drone = LaserDrone(player, [asteroid])
    drone.position = pygame.Vector2(0, 0)
    drone.acquire_target()
    assert drone.target is asteroid

def test_laser_drone_ignores_enemy_in_different_airspace():
    space_a = object()
    space_b = object()
    enemy = FakeEnemy(10, 0, health=999, airspace=space_a)
    game = FakeDroneGame(enemies=[enemy], current_space=space_b)
    player = FakePlayerWithGame(game)
    asteroid = FakeAsteroid(10, 0, health=1)
    drone = LaserDrone(player, [asteroid])
    drone.position = pygame.Vector2(0, 0)
    drone.acquire_target()
    assert drone.target is asteroid
