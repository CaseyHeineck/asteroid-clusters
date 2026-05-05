import pygame
import pytest
from collections import defaultdict
from core import constants as C
from entities.drone import SlayerDrone
from entities.player import Player
from unittest.mock import patch

# --- approach_zero ---
def test_approach_zero_decrements_positive_value():
    p = Player(0, 0)
    assert p.approach_zero(10, 3) == 7

def test_approach_zero_positive_does_not_go_below_zero():
    p = Player(0, 0)
    assert p.approach_zero(2, 10) == 0

def test_approach_zero_increments_negative_value():
    p = Player(0, 0)
    assert p.approach_zero(-10, 3) == -7

def test_approach_zero_negative_does_not_go_above_zero():
    p = Player(0, 0)
    assert p.approach_zero(-2, 10) == 0

def test_approach_zero_returns_zero_when_already_zero():
    p = Player(0, 0)
    assert p.approach_zero(0, 5) == 0

# --- rotate ---
def test_rotate_increments_rotation():
    p = Player(0, 0)
    p.rotation = 0
    p.rotate(1.0)
    assert p.rotation == pytest.approx(C.PLAYER_TURN_SPEED, abs=0.01)

def test_rotate_negative_dt_decrements_rotation():
    p = Player(0, 0)
    p.rotation = 0
    p.rotate(-1.0)
    assert p.rotation == pytest.approx(-C.PLAYER_TURN_SPEED, abs=0.01)

# --- accelerate ---
def test_accelerate_increases_forward_speed():
    p = Player(0, 0)
    p.accelerate(1.0)
    assert p.forward_speed == pytest.approx(C.PLAYER_ACCELERATION_RATE, abs=0.01)

def test_accelerate_negative_decreases_forward_speed():
    p = Player(0, 0)
    p.accelerate(-1.0)
    assert p.forward_speed == pytest.approx(-C.PLAYER_ACCELERATION_RATE, abs=0.01)

# --- strafe ---
def test_strafe_sets_speed_for_right():
    p = Player(0, 0)
    p.strafe(1)
    assert p.strafe_speed == C.PLAYER_STRAFE_SPEED

def test_strafe_sets_speed_for_left():
    p = Player(0, 0)
    p.strafe(-1)
    assert p.strafe_speed == -C.PLAYER_STRAFE_SPEED

# --- apply_movement_decay ---
def test_apply_movement_decay_reduces_forward_speed():
    p = Player(0, 0)
    p.forward_speed = 100
    p.apply_movement_decay(1.0)
    assert p.forward_speed < 100

def test_apply_movement_decay_does_not_make_speed_negative():
    p = Player(0, 0)
    p.forward_speed = 1
    p.apply_movement_decay(10.0)
    assert p.forward_speed == 0

# --- update_damage_cooldown ---
def test_damage_cooldown_off_allows_damage():
    p = Player(0, 0)
    p.damage_cooldown = False
    p.update_damage_cooldown(0.1)
    assert p.can_be_damaged

def test_damage_cooldown_on_blocks_damage():
    p = Player(0, 0)
    p.damage_cooldown = True
    p.update_damage_cooldown(0.1)
    assert not p.can_be_damaged

def test_damage_cooldown_expires_after_full_duration():
    p = Player(0, 0)
    p.damage_cooldown = True
    p.update_damage_cooldown(C.PLAYER_DAMAGE_COOLDOWN_SECONDS)
    assert not p.damage_cooldown
    assert p.can_be_damaged

def test_damage_cooldown_toggles_flash_visible():
    p = Player(0, 0)
    p.damage_cooldown = True
    p.flash_visible = False
    p.update_damage_cooldown(C.PLAYER_BLINK_TIMER)
    assert p.flash_visible

# --- damaged ---
def test_damaged_returns_zero_when_invincible():
    p = Player(0, 0)
    p.can_be_damaged = False
    score_delta, lives = p.damaged()
    assert score_delta == 0
    assert lives == p.lives

def test_damaged_reduces_lives():
    p = Player(0, 0)
    p.can_be_damaged = True
    _, lives = p.damaged()
    assert lives == 2

def test_damaged_starts_cooldown():
    p = Player(0, 0)
    p.can_be_damaged = True
    p.damaged()
    assert p.damage_cooldown

def test_damaged_returns_negative_score_delta():
    p = Player(0, 0)
    p.can_be_damaged = True
    score_delta, _ = p.damaged()
    assert score_delta < 0

def test_damaged_sets_game_over_when_lives_depleted():
    p = Player(0, 0)
    p.can_be_damaged = True
    p.lives = 1
    _, lives = p.damaged()
    assert lives == 0
    assert p.game_over

def test_damaged_lives_never_go_below_zero():
    p = Player(0, 0)
    p.can_be_damaged = True
    p.lives = 1
    _, lives = p.damaged(damage=5)
    assert lives == 0

# --- point_in_triangle ---
def test_point_inside_triangle_returns_true():
    p = Player(0, 0)
    a = pygame.Vector2(0, -10)
    b = pygame.Vector2(-10, 10)
    c = pygame.Vector2(10, 10)
    assert p.point_in_triangle(pygame.Vector2(0, 5), [a, b, c])

def test_point_outside_triangle_returns_false():
    p = Player(0, 0)
    a = pygame.Vector2(0, -10)
    b = pygame.Vector2(-10, 10)
    c = pygame.Vector2(10, 10)
    assert not p.point_in_triangle(pygame.Vector2(0, -20), [a, b, c])

def test_centroid_is_inside_triangle():
    p = Player(0, 0)
    a = pygame.Vector2(0, 0)
    b = pygame.Vector2(30, 0)
    c = pygame.Vector2(15, 30)
    centroid = pygame.Vector2(15, 10)
    assert p.point_in_triangle(centroid, [a, b, c])

# --- distance_point_to_segment ---
def test_distance_to_segment_perpendicular():
    p = Player(0, 0)
    start = pygame.Vector2(0, 0)
    end = pygame.Vector2(10, 0)
    point = pygame.Vector2(5, 3)
    assert p.distance_point_to_segment(point, start, end) == pytest.approx(3.0, abs=0.001)

def test_distance_to_segment_before_start_uses_start_point():
    p = Player(0, 0)
    start = pygame.Vector2(0, 0)
    end = pygame.Vector2(10, 0)
    point = pygame.Vector2(-3, 4)
    assert p.distance_point_to_segment(point, start, end) == pytest.approx(5.0, abs=0.001)

def test_distance_to_segment_beyond_end_uses_end_point():
    p = Player(0, 0)
    start = pygame.Vector2(0, 0)
    end = pygame.Vector2(10, 0)
    point = pygame.Vector2(13, 4)
    assert p.distance_point_to_segment(point, start, end) == pytest.approx(5.0, abs=0.001)

def test_distance_to_zero_length_segment_is_distance_to_point():
    p = Player(0, 0)
    start = pygame.Vector2(0, 0)
    end = pygame.Vector2(0, 0)
    point = pygame.Vector2(3, 4)
    assert p.distance_point_to_segment(point, start, end) == pytest.approx(5.0, abs=0.001)

# --- rebalance_drones ---
class FakeDrone:
    def __init__(self, orbit_angle=0):
        self.orbit_angle = orbit_angle

def test_rebalance_drones_no_op_when_empty():
    p = Player(0, 0)
    p.drones = []
    p.rebalance_drones()

def test_rebalance_single_drone_preserves_angle():
    p = Player(0, 0)
    drone = FakeDrone(orbit_angle=45)
    p.drones = [drone]
    p.rebalance_drones()
    assert drone.orbit_angle == 45

def test_rebalance_two_drones_are_180_degrees_apart():
    p = Player(0, 0)
    d1 = FakeDrone(orbit_angle=0)
    d2 = FakeDrone(orbit_angle=0)
    p.drones = [d1, d2]
    p.rebalance_drones()
    assert abs(d2.orbit_angle - d1.orbit_angle) == pytest.approx(180, abs=0.001)

def test_rebalance_three_drones_are_120_degrees_apart():
    p = Player(0, 0)
    d1 = FakeDrone(orbit_angle=0)
    d2 = FakeDrone(orbit_angle=0)
    d3 = FakeDrone(orbit_angle=0)
    p.drones = [d1, d2, d3]
    p.rebalance_drones()
    assert d2.orbit_angle - d1.orbit_angle == pytest.approx(120, abs=0.001)
    assert d3.orbit_angle - d1.orbit_angle == pytest.approx(240, abs=0.001)

# --- collides_with ---
class FakeCircle:
    def __init__(self, x, y, radius):
        self.position = pygame.Vector2(x, y)
        self.radius = radius

def test_collides_with_returns_false_when_player_has_shield():
    p = Player(0, 0)
    p.shield = True
    other = FakeCircle(0, 0, 5)
    assert not p.collides_with(other)

def test_collides_with_circle_center_inside_triangle_returns_true():
    p = Player(0, 0)
    p.shield = False
    p.rotation = 0
    tip = p.position + pygame.Vector2(0, 1).rotate(p.rotation) * p.radius
    other = FakeCircle(tip.x, tip.y, 1)
    assert p.collides_with(other)

def test_collides_with_far_circle_returns_false():
    p = Player(0, 0)
    p.shield = False
    other = FakeCircle(9999, 9999, 1)
    assert not p.collides_with(other)

def test_collides_with_circle_touching_triangle_edge_returns_true():
    p = Player(0, 0)
    p.shield = False
    p.rotation = 0
    forward = pygame.Vector2(0, 1).rotate(p.rotation)
    tip = p.position + forward * p.radius
    other = FakeCircle(tip.x, tip.y, 3)
    assert p.collides_with(other)

# --- life_regen ---
def run_update(p, dt):
    p._spawn_exhaust_effects = lambda *_: None
    with patch("pygame.key.get_pressed", return_value=defaultdict(int)):
        p.update(dt)

def test_life_regen_timer_accumulates_when_enabled_and_lives_below_max():
    p = Player(0, 0)
    p.life_regen = True
    p.lives = 2
    p.max_lives = 3
    p.life_regen_timer = 0
    run_update(p, 0.5)
    assert p.life_regen_timer > 0

def test_life_regen_adds_life_when_timer_reaches_interval():
    p = Player(0, 0)
    p.life_regen = True
    p.lives = 2
    p.max_lives = 3
    p.life_regen_timer = C.PLAYER_LIFE_REGEN_INTERVAL - 0.01
    run_update(p, 0.02)
    assert p.lives == 3

def test_life_regen_timer_resets_after_adding_life():
    p = Player(0, 0)
    p.life_regen = True
    p.lives = 2
    p.max_lives = 3
    p.life_regen_timer = C.PLAYER_LIFE_REGEN_INTERVAL - 0.01
    run_update(p, 0.02)
    assert p.life_regen_timer == pytest.approx(0.0, abs=0.001)

def test_life_regen_does_not_exceed_max_lives():
    p = Player(0, 0)
    p.life_regen = True
    p.lives = 3
    p.max_lives = 3
    p.life_regen_timer = C.PLAYER_LIFE_REGEN_INTERVAL
    run_update(p, 0.01)
    assert p.lives == 3

def test_life_regen_timer_does_not_advance_when_regen_disabled():
    p = Player(0, 0)
    p.life_regen = False
    p.lives = 2
    p.max_lives = 3
    p.life_regen_timer = 0
    run_update(p, 5.0)
    assert p.life_regen_timer == pytest.approx(0.0, abs=0.001)

# --- brake ---
def test_brake_reduces_forward_speed():
    p = Player(0, 0)
    p.forward_speed = 100
    p.brake(1.0)
    assert p.forward_speed < 100

def test_brake_reduces_perpendicular_speed():
    p = Player(0, 0)
    p.perpendicular_speed = 100
    p.brake(1.0)
    assert p.perpendicular_speed < 100

def test_brake_does_not_make_forward_speed_negative():
    p = Player(0, 0)
    p.forward_speed = 1
    p.brake(100.0)
    assert p.forward_speed == 0

# --- sync_local_speeds_from_velocity ---
def test_sync_local_speeds_sets_forward_speed_from_velocity():
    p = Player(0, 0)
    p.rotation = 0
    p.velocity = pygame.Vector2(0, 10)
    p.sync_local_speeds_from_velocity()
    assert p.forward_speed == pytest.approx(10.0, abs=0.01)

def test_sync_local_speeds_sets_perpendicular_speed_from_velocity():
    p = Player(0, 0)
    p.rotation = 0
    p.velocity = pygame.Vector2(5, 0)
    p.sync_local_speeds_from_velocity()
    assert p.perpendicular_speed == pytest.approx(-5.0, abs=0.01)

def test_sync_local_speeds_zero_velocity_gives_zero_speeds():
    p = Player(0, 0)
    p.velocity = pygame.Vector2(0, 0)
    p.sync_local_speeds_from_velocity()
    assert p.forward_speed == pytest.approx(0.0, abs=0.01)
    assert p.perpendicular_speed == pytest.approx(0.0, abs=0.01)

# --- add_drone ---
def test_add_drone_appends_to_drones_list():
    p = Player(0, 0)
    p.add_drone(SlayerDrone, [])
    assert len(p.drones) == 1

def test_add_drone_returns_new_drone_instance():
    p = Player(0, 0)
    drone = p.add_drone(SlayerDrone, [])
    assert isinstance(drone, SlayerDrone)

def test_add_drone_rebalances_two_drones_180_apart():
    p = Player(0, 0)
    d1 = p.add_drone(SlayerDrone, [])
    d2 = p.add_drone(SlayerDrone, [])
    assert abs(d2.orbit_angle - d1.orbit_angle) == pytest.approx(180, abs=0.001)

# --- apply_collision_to_asteroid ---
class FakeAsteroidPhysics:
    def __init__(self, x, y, radius=20, weight=10):
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, 0)
        self.radius = radius
        self.weight = weight
        self.bounciness = C.ASTEROID_BOUNCINESS

def test_apply_collision_pushes_asteroid_away_from_player():
    p = Player(0, 0)
    p.velocity = pygame.Vector2(0, 50)
    asteroid = FakeAsteroidPhysics(0, p.radius + 30)
    p.apply_collision_to_asteroid(asteroid)
    assert asteroid.velocity.y > 0

def test_apply_collision_no_effect_when_already_moving_apart():
    p = Player(0, 0)
    p.velocity = pygame.Vector2(0, -50)
    asteroid = FakeAsteroidPhysics(0, p.radius + 30)
    asteroid.velocity = pygame.Vector2(0, 100)
    p.apply_collision_to_asteroid(asteroid)
    assert asteroid.velocity.y >= 0

def test_apply_collision_caps_asteroid_speed_at_max():
    p = Player(0, 0)
    p.velocity = pygame.Vector2(0, C.ASTEROID_MAX_SPEED * 100)
    asteroid = FakeAsteroidPhysics(0, p.radius + 30)
    p.apply_collision_to_asteroid(asteroid)
    assert asteroid.velocity.length() <= C.ASTEROID_MAX_SPEED + 0.001
