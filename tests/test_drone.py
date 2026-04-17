import pytest
import pygame
from entities.drone import Drone, ExplosiveDrone, KineticDrone, LaserDrone, PlasmaDrone, SentinelDrone
from entities.projectile import Rocket, Kinetic, Plasma
from ui.visualeffect import MuzzleFlareVE
from core import constants as C

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
# Drones never participate in physical collisions — they are attached to the player
def test_drone_collides_with_always_returns_false():
    drone = LaserDrone(FakePlayer(), [])
    other = LaserDrone(FakePlayer(), [])
    assert not drone.collides_with(other)

# --- LaserDrone.get_charge_ratio ---
def test_charge_ratio_is_1_when_fully_charged():
    drone = LaserDrone(FakePlayer(), [])
    drone.weapons_free_timer = 0
    assert drone.get_charge_ratio() == pytest.approx(1.0, abs=0.001)

def test_charge_ratio_is_0_when_just_fired():
    drone = LaserDrone(FakePlayer(), [])
    drone.weapons_free_timer = drone.weapons_free_timer_max
    assert drone.get_charge_ratio() == pytest.approx(0.0, abs=0.001)

def test_charge_ratio_is_half_at_midpoint():
    drone = LaserDrone(FakePlayer(), [])
    drone.weapons_free_timer = drone.weapons_free_timer_max / 2
    assert drone.get_charge_ratio() == pytest.approx(0.5, abs=0.001)

def test_charge_ratio_is_1_when_timer_max_is_zero():
    drone = LaserDrone(FakePlayer(), [])
    drone.weapons_free_timer_max = 0
    assert drone.get_charge_ratio() == 1

# --- LaserDrone.lerp_color ---
def test_lerp_color_at_0_returns_start():
    drone = LaserDrone(FakePlayer(), [])
    result = drone.lerp_color((0, 0, 0), (255, 255, 255), 0)
    assert result == (0, 0, 0)

def test_lerp_color_at_1_returns_end():
    drone = LaserDrone(FakePlayer(), [])
    result = drone.lerp_color((0, 0, 0), (255, 255, 255), 1)
    assert result == (255, 255, 255)

def test_lerp_color_at_half_returns_midpoint():
    drone = LaserDrone(FakePlayer(), [])
    result = drone.lerp_color((0, 0, 0), (100, 100, 100), 0.5)
    assert result == (50, 50, 50)

def test_lerp_color_clamps_t_below_zero():
    drone = LaserDrone(FakePlayer(), [])
    result = drone.lerp_color((10, 10, 10), (100, 100, 100), -1)
    assert result == (10, 10, 10)

def test_lerp_color_clamps_t_above_one():
    drone = LaserDrone(FakePlayer(), [])
    result = drone.lerp_color((10, 10, 10), (100, 100, 100), 2)
    assert result == (100, 100, 100)

# --- LaserDrone.get_platform_color ---
# Fully charged returns the last (hottest) color; uncharged returns the first
def test_platform_color_when_fully_charged_is_last_in_sequence():
    drone = LaserDrone(FakePlayer(), [])
    drone.weapons_free_timer = 0  # fully charged
    color = drone.get_platform_color()
    assert color == C.LASER_RED

def test_platform_color_when_uncharged_is_first_in_sequence():
    drone = LaserDrone(FakePlayer(), [])
    drone.weapons_free_timer = drone.weapons_free_timer_max  # just fired
    color = drone.get_platform_color()
    assert color == C.INDIGO

# --- Drone.acquire_target ---
# Picks the asteroid closest to the player, not the drone
class FakeAsteroid:
    def __init__(self, x, y, health=10):
        self.position = pygame.Vector2(x, y)
        self.health = health

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
    drone.weapons_free_timer = 1.0
    drone.target = FakeAsteroid(10, 0)
    assert drone.shoot() == 0

def test_shoot_does_not_reset_timer_when_on_cooldown():
    drone = LaserDrone(FakePlayer(), [])
    drone.weapons_free_timer = 1.0
    drone.target = FakeAsteroid(10, 0)
    drone.shoot()
    assert drone.weapons_free_timer == 1.0

def test_shoot_returns_zero_when_no_target():
    drone = LaserDrone(FakePlayer(), [])
    drone.weapons_free_timer = 0
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

# --- ExplosiveDrone.weapons_free ---
def test_explosive_drone_weapons_free_sets_launch_animation_timer():
    Rocket.containers = ()
    player = FakeSentinelPlayer()
    drone = ExplosiveDrone(player, [])
    drone.launch_animation_timer = 0
    drone.weapons_free()
    assert drone.launch_animation_timer > 0

def test_explosive_drone_weapons_free_returns_zero():
    Rocket.containers = ()
    player = FakeSentinelPlayer()
    drone = ExplosiveDrone(player, [])
    assert drone.weapons_free() == 0

# --- KineticDrone.weapons_free ---
def test_kinetic_drone_weapons_free_returns_zero():
    Kinetic.containers = ()
    MuzzleFlareVE.containers = ()
    player = FakeSentinelPlayer()
    drone = KineticDrone(player, [])
    assert drone.weapons_free() == 0

# --- PlasmaDrone.weapons_free ---
def test_plasma_drone_weapons_free_returns_zero():
    Plasma.containers = ()
    player = FakeSentinelPlayer()
    drone = PlasmaDrone(player, [])
    assert drone.weapons_free() == 0
