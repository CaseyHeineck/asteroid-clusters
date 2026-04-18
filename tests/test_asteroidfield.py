import pygame
import pytest
from unittest.mock import patch
from core import constants as C
from entities.asteroid import Asteroid
from entities.asteroidfield import AsteroidField

def make_field():
    AsteroidField.containers = ()
    return AsteroidField(pygame.sprite.Group())

# --- spawn_timer ---
def test_spawn_timer_starts_at_zero():
    field = make_field()
    assert field.spawn_timer == 0.0

def test_spawn_timer_increments_with_dt():
    field = make_field()
    field.update(0.1)
    assert field.spawn_timer == pytest.approx(0.1, abs=0.001)

def test_spawn_timer_accumulates_across_multiple_updates():
    field = make_field()
    field.update(0.1)
    field.update(0.2)
    assert field.spawn_timer == pytest.approx(0.3, abs=0.001)

def test_spawn_timer_resets_after_exceeding_spawn_rate():
    field = make_field()
    group = pygame.sprite.Group()
    Asteroid.containers = (group,)
    field.spawn_timer = C.ASTEROID_SPAWN_RATE_SECONDS + 0.01
    field.update(0.0)
    assert field.spawn_timer == pytest.approx(0.0, abs=0.001)
    Asteroid.containers = ()

# --- spawn ---
def test_spawn_creates_asteroid_in_container():
    group = pygame.sprite.Group()
    Asteroid.containers = (group,)
    AsteroidField.containers = ()
    field = make_field()
    field.spawn(1, pygame.Vector2(100, 200), pygame.Vector2(50, 0))
    assert len(group) == 1
    Asteroid.containers = ()

def test_spawn_sets_asteroid_velocity():
    group = pygame.sprite.Group()
    Asteroid.containers = (group,)
    AsteroidField.containers = ()
    field = make_field()
    vel = pygame.Vector2(30, -10)
    field.spawn(1, pygame.Vector2(0, 0), vel)
    asteroid = next(iter(group))
    assert asteroid.velocity == vel
    Asteroid.containers = ()

def test_spawn_creates_asteroid_at_given_position():
    group = pygame.sprite.Group()
    Asteroid.containers = (group,)
    AsteroidField.containers = ()
    field = make_field()
    field.spawn(1, pygame.Vector2(123, 456), pygame.Vector2(0, 0))
    asteroid = next(iter(group))
    assert asteroid.position.x == pytest.approx(123.0)
    assert asteroid.position.y == pytest.approx(456.0)
    Asteroid.containers = ()

def test_spawn_with_elemental_chance_one_assigns_element():
    group = pygame.sprite.Group()
    Asteroid.containers = (group,)
    AsteroidField.containers = ()
    field = make_field()
    with patch("entities.asteroidfield.random.random", return_value=0.0):
        field.spawn(1, pygame.Vector2(0, 0), pygame.Vector2(0, 0))
    asteroid = next(iter(group))
    assert asteroid.element is not None
    Asteroid.containers = ()

def test_spawn_with_elemental_chance_zero_leaves_element_none():
    group = pygame.sprite.Group()
    Asteroid.containers = (group,)
    AsteroidField.containers = ()
    field = make_field()
    with patch("entities.asteroidfield.random.random", return_value=1.0):
        field.spawn(1, pygame.Vector2(0, 0), pygame.Vector2(0, 0))
    asteroid = next(iter(group))
    assert asteroid.element is None
    Asteroid.containers = ()

def test_spawn_normal_size_uses_standard_elemental_chance():
    group = pygame.sprite.Group()
    Asteroid.containers = (group,)
    field = make_field()
    chance_between_large_and_normal = (C.ASTEROID_LARGE_ELEMENTAL_SPAWN_CHANCE
                                       + C.ASTEROID_ELEMENTAL_SPAWN_CHANCE) / 2
    with patch("entities.asteroidfield.random.random", return_value=chance_between_large_and_normal):
        field.spawn(1, pygame.Vector2(0, 0), pygame.Vector2(0, 0))
    asteroid = next(iter(group))
    assert asteroid.element is not None
    Asteroid.containers = ()

def test_spawn_large_size_uses_lower_elemental_chance():
    group = pygame.sprite.Group()
    Asteroid.containers = (group,)
    field = make_field()
    chance_between_large_and_normal = (C.ASTEROID_LARGE_ELEMENTAL_SPAWN_CHANCE
                                       + C.ASTEROID_ELEMENTAL_SPAWN_CHANCE) / 2
    with patch("entities.asteroidfield.random.random", return_value=chance_between_large_and_normal):
        field.spawn(C.ASTEROID_LARGE_THRESHOLD, pygame.Vector2(0, 0), pygame.Vector2(0, 0))
    asteroid = next(iter(group))
    assert asteroid.element is None
    Asteroid.containers = ()

# --- size cap ---
class _MockAsteroid(pygame.sprite.Sprite):
    def __init__(self, size):
        super().__init__()
        self.size = size

def test_update_does_not_spawn_when_total_size_at_cap():
    capped_group = pygame.sprite.Group()
    capped_group.add(_MockAsteroid(C.ASTEROID_SIZE_CAP))
    field = AsteroidField(capped_group)
    spawn_group = pygame.sprite.Group()
    Asteroid.containers = (spawn_group,)
    field.spawn_timer = C.ASTEROID_SPAWN_RATE_SECONDS + 0.01
    field.update(0.0)
    assert len(spawn_group) == 0
    Asteroid.containers = ()

def test_update_spawns_when_total_size_below_cap():
    below_group = pygame.sprite.Group()
    below_group.add(_MockAsteroid(C.ASTEROID_SIZE_CAP - 1))
    field = AsteroidField(below_group)
    spawn_group = pygame.sprite.Group()
    Asteroid.containers = (spawn_group,)
    field.spawn_timer = C.ASTEROID_SPAWN_RATE_SECONDS + 0.01
    field.update(0.0)
    assert len(spawn_group) == 1
    Asteroid.containers = ()

# --- large asteroid spawning ---
def test_large_asteroid_spawned_when_random_below_large_spawn_chance():
    spawn_group = pygame.sprite.Group()
    Asteroid.containers = (spawn_group,)
    field = make_field()
    field.spawn_timer = C.ASTEROID_SPAWN_RATE_SECONDS + 0.01
    with patch("entities.asteroidfield.random.random", return_value=0.0):
        field.update(0.0)
    asteroid = next(iter(spawn_group))
    assert asteroid.size >= C.ASTEROID_LARGE_THRESHOLD
    Asteroid.containers = ()

def test_normal_asteroid_spawned_when_random_above_large_spawn_chance():
    spawn_group = pygame.sprite.Group()
    Asteroid.containers = (spawn_group,)
    field = make_field()
    field.spawn_timer = C.ASTEROID_SPAWN_RATE_SECONDS + 0.01
    with patch("entities.asteroidfield.random.random", return_value=1.0):
        field.update(0.0)
    asteroid = next(iter(spawn_group))
    assert asteroid.size <= C.ASTEROID_KINDS
    Asteroid.containers = ()
