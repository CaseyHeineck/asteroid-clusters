import pygame
import pytest
from core.circleshape import CircleShape
from systems.gameplayeffect import GameplayEffect, PlasmaBurnSTE, SingleTargetEffect

class EffectTypeA(SingleTargetEffect): pass
class EffectTypeB(SingleTargetEffect): pass

class StackableEffect(SingleTargetEffect):
    stackable = True

# --- collides_with ---
def test_overlapping_circles_collide():
    a = CircleShape(0, 0, 10)
    b = CircleShape(5, 0, 10)
    assert a.collides_with(b)

def test_separated_circles_do_not_collide():
    a = CircleShape(0, 0, 10)
    b = CircleShape(25, 0, 10)
    assert not a.collides_with(b)

def test_circles_touching_exactly_collide():
    a = CircleShape(0, 0, 10)
    b = CircleShape(20, 0, 10)
    assert a.collides_with(b)

# --- get_collision_normal ---
def test_collision_normal_points_from_self_toward_other():
    a = CircleShape(0, 0, 10)
    b = CircleShape(10, 0, 10)
    normal = a.get_collision_normal(b)
    assert normal.x > 0
    assert abs(normal.y) < 0.001

def test_collision_normal_is_unit_length():
    a = CircleShape(0, 0, 10)
    b = CircleShape(3, 4, 10)
    normal = a.get_collision_normal(b)
    assert abs(normal.length() - 1.0) < 0.001

def test_collision_normal_coincident_positions_returns_fallback():
    a = CircleShape(0, 0, 10)
    b = CircleShape(0, 0, 10)
    normal = a.get_collision_normal(b)
    assert normal == pygame.Vector2(1, 0)

# --- apply_drag ---
def test_apply_drag_reduces_speed():
    shape = CircleShape(0, 0, 10, drag=10)
    shape.velocity = pygame.Vector2(100, 0)
    shape.apply_drag(1.0)
    assert shape.velocity.length() < 100

def test_apply_drag_stops_when_drag_exceeds_speed():
    shape = CircleShape(0, 0, 10, drag=200)
    shape.velocity = pygame.Vector2(10, 0)
    shape.apply_drag(1.0)
    assert shape.velocity.length() == 0

def test_apply_drag_no_op_when_zero_drag():
    shape = CircleShape(0, 0, 10, drag=0)
    shape.velocity = pygame.Vector2(50, 0)
    shape.apply_drag(1.0)
    assert shape.velocity.length() == 50

def test_apply_drag_no_op_when_velocity_is_zero():
    shape = CircleShape(0, 0, 10, drag=50)
    shape.velocity = pygame.Vector2(0, 0)
    shape.apply_drag(1.0)
    assert shape.velocity.length() == 0

# --- apply_rotation ---
def test_apply_rotation_increments_rotation():
    shape = CircleShape(0, 0, 10, angular_velocity=90)
    shape.apply_rotation(1.0)
    assert shape.rotation == pytest.approx(90, abs=0.01)

def test_apply_rotation_no_op_when_zero_angular_velocity():
    shape = CircleShape(0, 0, 10, angular_velocity=0)
    shape.apply_rotation(1.0)
    assert shape.rotation == 0

def test_apply_rotation_wraps_at_360():
    shape = CircleShape(0, 0, 10, angular_velocity=270, rotation=180)
    shape.apply_rotation(1.0)
    assert shape.rotation == pytest.approx(90, abs=0.01)

# --- physics_move ---
def test_physics_move_updates_position_by_velocity_times_dt():
    shape = CircleShape(0, 0, 10, drag=0)
    shape.velocity = pygame.Vector2(100, 0)
    shape.physics_move(1.0)
    assert shape.position.x == pytest.approx(100, abs=0.01)

# --- pulse_outline / update_outline_pulse / get_outline_color ---
def test_pulse_outline_sets_color_and_timer():
    shape = CircleShape(0, 0, 10)
    shape.pulse_outline((255, 0, 0), 0.5)
    assert shape.outline_pulse_color == (255, 0, 0)
    assert shape.outline_pulse_timer == 0.5

def test_update_outline_pulse_decrements_timer():
    shape = CircleShape(0, 0, 10)
    shape.pulse_outline((255, 0, 0), 1.0)
    shape.update_outline_pulse(0.5)
    assert shape.outline_pulse_timer == pytest.approx(0.5, abs=0.001)

def test_update_outline_pulse_clears_color_when_timer_reaches_zero():
    shape = CircleShape(0, 0, 10)
    shape.pulse_outline((255, 0, 0), 0.1)
    shape.update_outline_pulse(1.0)
    assert shape.outline_pulse_color is None

def test_get_outline_color_returns_pulse_color_when_active():
    shape = CircleShape(0, 0, 10)
    shape.pulse_outline((255, 0, 0), 1.0)
    assert shape.get_outline_color((255, 255, 255)) == (255, 0, 0)

def test_get_outline_color_returns_default_when_no_pulse():
    shape = CircleShape(0, 0, 10)
    assert shape.get_outline_color((255, 255, 255)) == (255, 255, 255)

# --- separate_from ---
def test_separate_from_pushes_overlapping_shapes_apart():
    a = CircleShape(0, 0, 10)
    b = CircleShape(5, 0, 10)
    a.separate_from(b)
    assert a.position.distance_to(b.position) >= 20

def test_separate_from_no_op_when_not_overlapping():
    a = CircleShape(0, 0, 10)
    b = CircleShape(25, 0, 10)
    a.separate_from(b)
    assert a.position.x == pytest.approx(0, abs=0.001)
    assert b.position.x == pytest.approx(25, abs=0.001)

# --- resolve_impact ---
def test_resolve_impact_transfers_velocity_in_elastic_equal_mass_collision():
    a = CircleShape(0, 0, 10, bounciness=1.0)
    b = CircleShape(25, 0, 10, bounciness=1.0)
    a.velocity = pygame.Vector2(100, 0)
    b.velocity = pygame.Vector2(0, 0)
    a.resolve_impact(b)
    assert a.velocity.x == pytest.approx(0, abs=0.001)
    assert b.velocity.x == pytest.approx(100, abs=0.001)

def test_resolve_impact_no_op_when_objects_moving_apart():
    a = CircleShape(0, 0, 10, bounciness=1.0)
    b = CircleShape(25, 0, 10, bounciness=1.0)
    a.velocity = pygame.Vector2(-100, 0)
    b.velocity = pygame.Vector2(0, 0)
    a.resolve_impact(b)
    assert a.velocity.x == pytest.approx(-100, abs=0.001)

# --- add_gameplay_effect ---
def test_add_gameplay_effect_appends_new_effect():
    shape = CircleShape(0, 0, 10)
    effect = SingleTargetEffect(duration=1.0)
    shape.add_gameplay_effect(effect)
    assert effect in shape.gameplay_effects

def test_add_gameplay_effect_merges_same_type_instead_of_appending():
    shape = CircleShape(0, 0, 10)
    e1 = SingleTargetEffect(duration=1.0)
    e2 = SingleTargetEffect(duration=5.0)
    shape.add_gameplay_effect(e1)
    shape.add_gameplay_effect(e2)
    assert len(shape.gameplay_effects) == 1
    assert e1.duration == 5.0

def test_add_gameplay_effect_appends_different_types_separately():
    shape = CircleShape(0, 0, 10)
    e1 = EffectTypeA(duration=1.0)
    e2 = EffectTypeB(duration=1.0)
    shape.add_gameplay_effect(e1)
    shape.add_gameplay_effect(e2)
    assert len(shape.gameplay_effects) == 2

def test_burn_stack_limit_defaults_to_none():
    shape = CircleShape(0, 0, 10)
    assert shape.burn_stack_limit is None

def test_add_gameplay_effect_stacks_stackable_effects_independently():
    shape = CircleShape(0, 0, 10)
    e1 = StackableEffect(duration=3.0)
    e2 = StackableEffect(duration=3.0)
    shape.add_gameplay_effect(e1)
    shape.add_gameplay_effect(e2)
    assert len(shape.gameplay_effects) == 2

def test_add_gameplay_effect_respects_stack_limit_by_merging_oldest():
    shape = CircleShape(0, 0, 10)
    shape.burn_stack_limit = 2
    e1 = StackableEffect(duration=1.0)
    e2 = StackableEffect(duration=1.0)
    e3 = StackableEffect(duration=9.0)
    shape.add_gameplay_effect(e1)
    shape.add_gameplay_effect(e2)
    shape.add_gameplay_effect(e3)
    assert len(shape.gameplay_effects) == 2
    assert e1.duration == 9.0

def test_plasma_burn_stacks_without_limit_by_default():
    shape = CircleShape(0, 0, 10)
    for _ in range(5):
        shape.add_gameplay_effect(PlasmaBurnSTE())
    assert len(shape.gameplay_effects) == 5

# --- update_gameplay_effects ---
def test_update_gameplay_effects_removes_expired_effect():
    shape = CircleShape(0, 0, 10)
    effect = GameplayEffect(duration=0.5)
    shape.gameplay_effects.append(effect)
    shape.update_gameplay_effects(1.0)
    assert effect not in shape.gameplay_effects

def test_update_gameplay_effects_keeps_active_effect():
    shape = CircleShape(0, 0, 10)
    effect = GameplayEffect(duration=5.0)
    shape.gameplay_effects.append(effect)
    shape.update_gameplay_effects(1.0)
    assert effect in shape.gameplay_effects

# --- get_forward_vector ---
def test_get_forward_vector_at_zero_rotation_points_up():
    shape = CircleShape(0, 0, 10)
    fwd = shape.get_forward_vector()
    assert fwd.x == pytest.approx(0, abs=0.001)
    assert fwd.y == pytest.approx(-1, abs=0.001)

def test_get_forward_vector_at_90_rotation_points_right():
    shape = CircleShape(0, 0, 10, rotation=90)
    fwd = shape.get_forward_vector()
    assert fwd.x == pytest.approx(1, abs=0.001)
    assert fwd.y == pytest.approx(0, abs=0.001)

def test_get_forward_vector_is_unit_length():
    shape = CircleShape(0, 0, 10, rotation=45)
    assert shape.get_forward_vector().length() == pytest.approx(1.0, abs=0.001)
