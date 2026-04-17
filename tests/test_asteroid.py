import pygame
import pytest
import unittest.mock as mock
from core import constants as C
from core.element import Element
from entities.asteroid import Asteroid
from entities.elementalessenceorb import ElementalEssenceOrb
from entities.essenceorb import EssenceOrb
from entities.experiorb import ExpOrb
from ui.visualeffect import AsteroidKillExplosionVE, OverkillExplosionVE

# --- split_factor ---
def test_split_factor_at_45_degrees():
    a = Asteroid(0, 0, 1)
    assert a.split_factor(45) == pytest.approx(0.5, abs=0.001)

def test_split_factor_at_90_clamps_to_minimum():
    a = Asteroid(0, 0, 1)
    assert a.split_factor(90) == pytest.approx(C.ASTEROID_SPLIT_FACTOR_MIN, abs=0.001)

def test_split_factor_at_135_degrees():
    a = Asteroid(0, 0, 1)
    assert a.split_factor(135) == pytest.approx(0.5, abs=0.001)

def test_split_factor_at_180_returns_one():
    a = Asteroid(0, 0, 1)
    assert a.split_factor(180) == pytest.approx(1.0, abs=0.001)

def test_split_factor_at_225_degrees():
    a = Asteroid(0, 0, 1)
    assert a.split_factor(225) == pytest.approx(0.5, abs=0.001)

def test_split_factor_at_270_clamps_to_minimum():
    a = Asteroid(0, 0, 1)
    assert a.split_factor(270) == pytest.approx(C.ASTEROID_SPLIT_FACTOR_MIN, abs=0.001)

def test_split_factor_at_315_degrees():
    a = Asteroid(0, 0, 1)
    assert a.split_factor(315) == pytest.approx(0.5, abs=0.001)

def test_split_factor_at_360_returns_one():
    a = Asteroid(0, 0, 1)
    assert a.split_factor(360) == pytest.approx(1.0, abs=0.001)

def test_split_factor_never_below_minimum():
    a = Asteroid(0, 0, 1)
    for angle in range(1, 361):
        assert a.split_factor(angle) >= C.ASTEROID_SPLIT_FACTOR_MIN

def test_split_factor_raises_on_zero_angle():
    a = Asteroid(0, 0, 1)
    with pytest.raises(ValueError):
        a.split_factor(0)

# --- damaged (non-lethal path only) ---
def test_damaged_reduces_health():
    a = Asteroid(0, 0, 2)
    a.damaged(5)
    assert a.health == a.full_health - 5

def test_damaged_returns_zero_when_not_lethal():
    a = Asteroid(0, 0, 2)
    result = a.damaged(1)
    assert result == 0

def test_damaged_health_decreases_by_exact_amount():
    a = Asteroid(0, 0, 3)
    a.damaged(10)
    assert a.health == 20
    a.damaged(7)
    assert a.health == 13

# --- spawn_children ---
def test_spawn_children_returns_false_for_size_one():
    a = Asteroid(0, 0, 1)
    assert a.spawn_children() is False

def test_spawn_children_returns_true_for_size_two():
    a = Asteroid(0, 0, 2)
    assert a.spawn_children() is True

def test_spawn_children_returns_false_when_child_size_reduced_to_zero():
    a = Asteroid(0, 0, 2)
    a.child_size_reduction = 1
    assert a.spawn_children() is False

def test_spawn_children_returns_false_when_child_count_reduced_to_zero():
    a = Asteroid(0, 0, 2)
    a.child_count_reduction = 1
    assert a.spawn_children() is False

def test_spawn_children_returns_true_when_reductions_leave_valid_children():
    a = Asteroid(0, 0, 3)
    a.child_size_reduction = 1
    a.child_count_reduction = 1
    assert a.spawn_children() is True

def capture_children(parent):
    created = []
    class _Capturing(Asteroid):
        def __init__(self, x, y, size):
            super().__init__(x, y, size)
            created.append(self)
    with mock.patch("entities.asteroid.Asteroid", _Capturing):
        parent.spawn_children()
    return created

def test_spawn_children_element_is_not_propagated_without_parent_element():
    Asteroid.containers = ()
    a = Asteroid(0, 0, 3)
    a.element = None
    a.velocity = C.ASTEROID_MIN_SPEED * pygame.Vector2(1, 0)
    children = capture_children(a)
    assert all(c.element is None for c in children)

def test_spawn_children_at_least_one_child_inherits_parent_element():
    Asteroid.containers = ()
    a = Asteroid(0, 0, 3)
    a.element = Element.SOLAR
    a.velocity = C.ASTEROID_MIN_SPEED * pygame.Vector2(1, 0)
    children = capture_children(a)
    assert any(c.element == Element.SOLAR for c in children)

def test_spawn_children_creates_correct_child_count():
    Asteroid.containers = ()
    a = Asteroid(0, 0, 3)
    a.velocity = C.ASTEROID_MIN_SPEED * pygame.Vector2(1, 0)
    children = capture_children(a)
    assert len(children) == 2

def test_spawn_children_creates_one_child_for_size_two():
    Asteroid.containers = ()
    a = Asteroid(0, 0, 2)
    a.velocity = C.ASTEROID_MIN_SPEED * pygame.Vector2(1, 0)
    children = capture_children(a)
    assert len(children) == 1

# --- get_zigzag_points ---
def test_get_zigzag_points_zero_length_direction_returns_start_and_end():
    a = Asteroid(0, 0, 1)
    start = pygame.Vector2(5, 5)
    end = pygame.Vector2(5, 5)
    points = a.get_zigzag_points(start, end, segments=4, jag_amount=5)
    assert points == [start, end]

def test_get_zigzag_points_returns_segments_plus_one_points():
    a = Asteroid(0, 0, 1)
    start = pygame.Vector2(0, 0)
    end = pygame.Vector2(100, 0)
    points = a.get_zigzag_points(start, end, segments=4, jag_amount=5)
    assert len(points) == 5

def test_get_zigzag_points_starts_at_start_and_ends_at_end():
    a = Asteroid(0, 0, 1)
    start = pygame.Vector2(10, 20)
    end = pygame.Vector2(80, 40)
    points = a.get_zigzag_points(start, end, segments=4, jag_amount=5)
    assert points[0] == start
    assert points[-1] == end

def test_get_zigzag_points_with_one_segment_returns_only_endpoints():
    a = Asteroid(0, 0, 1)
    start = pygame.Vector2(0, 0)
    end = pygame.Vector2(50, 0)
    points = a.get_zigzag_points(start, end, segments=1, jag_amount=5)
    assert len(points) == 2
    assert points[0] == start
    assert points[-1] == end

def make_kill_ready_asteroid(size):
    AsteroidKillExplosionVE.containers = ()
    OverkillExplosionVE.containers = ()
    ExpOrb.containers = ()
    EssenceOrb.containers = ()
    ElementalEssenceOrb.containers = ()
    Asteroid.containers = ()
    return Asteroid(0, 0, size)

# --- damaged (lethal path) ---
def test_damaged_kills_asteroid_when_health_depleted():
    a = make_kill_ready_asteroid(2)
    a.damaged(a.health)
    assert not a.alive()

def test_damaged_returns_score_on_lethal_hit():
    a = make_kill_ready_asteroid(2)
    score = a.damaged(a.health)
    assert score > 0

def test_damaged_lethal_hit_returns_base_score_times_size():
    a = make_kill_ready_asteroid(3)
    score = a.damaged(a.health)
    assert score == C.BASE_SCORE * 3

# --- kill ---
def test_kill_returns_base_score_times_size():
    a = make_kill_ready_asteroid(3)
    score = a.kill()
    assert score == C.BASE_SCORE * 3

def test_kill_size_one_does_not_call_spawn_children():
    a = make_kill_ready_asteroid(1)
    with mock.patch.object(a, "spawn_children") as mocked:
        a.kill()
    mocked.assert_not_called()

def test_kill_size_greater_than_one_calls_spawn_children():
    a = make_kill_ready_asteroid(2)
    with mock.patch.object(a, "spawn_children", return_value=True) as mocked:
        a.kill()
    mocked.assert_called_once()

def test_kill_with_overkill_triggered_returns_correct_score():
    a = make_kill_ready_asteroid(2)
    a.overkill_triggered = True
    score = a.kill()
    assert score == C.BASE_SCORE * 2
