import pygame
import pytest
from core import constants as C
from ui.visualeffect import (BaseExplosion, LaserBeamVE, MuzzleFlareVE,
    RocketExhaustVE, ShipExhaustVE, VisualEffect)

# --- VisualEffect.update ---
def test_visual_effect_timer_decrements_with_dt():
    group = pygame.sprite.Group()
    VisualEffect.containers = (group,)
    ve = VisualEffect(0, 0, duration=1.0)
    ve.update(0.4)
    assert ve.timer == pytest.approx(0.6, abs=0.001)
    VisualEffect.containers = ()

def test_visual_effect_timer_clamps_at_zero():
    group = pygame.sprite.Group()
    VisualEffect.containers = (group,)
    ve = VisualEffect(0, 0, duration=0.5)
    ve.update(10.0)
    assert ve.timer == 0
    VisualEffect.containers = ()

def test_visual_effect_kills_self_when_timer_reaches_zero():
    group = pygame.sprite.Group()
    VisualEffect.containers = (group,)
    ve = VisualEffect(0, 0, duration=0.5)
    ve.update(0.5)
    assert not ve.alive()
    VisualEffect.containers = ()

def test_visual_effect_still_alive_before_timer_expires():
    group = pygame.sprite.Group()
    VisualEffect.containers = (group,)
    ve = VisualEffect(0, 0, duration=1.0)
    ve.update(0.5)
    assert ve.alive()
    VisualEffect.containers = ()

def test_visual_effect_zero_duration_does_not_kill_on_update():
    group = pygame.sprite.Group()
    VisualEffect.containers = (group,)
    ve = VisualEffect(0, 0, duration=0)
    ve.update(1.0)
    assert ve.alive()
    VisualEffect.containers = ()

def test_visual_effect_stores_position():
    group = pygame.sprite.Group()
    VisualEffect.containers = (group,)
    ve = VisualEffect(50, 75, duration=1.0)
    assert ve.position.x == pytest.approx(50)
    assert ve.position.y == pytest.approx(75)
    VisualEffect.containers = ()

# --- BaseExplosion.get_alpha ---
def test_get_alpha_returns_zero_when_layer_duration_is_zero():
    group = pygame.sprite.Group()
    BaseExplosion.containers = (group,)
    explosion = BaseExplosion(0, 0, radius=10, base_duration=1.0)
    assert explosion.get_alpha(0, 255) == 0
    BaseExplosion.containers = ()

def test_get_alpha_returns_max_alpha_at_full_timer():
    group = pygame.sprite.Group()
    BaseExplosion.containers = (group,)
    explosion = BaseExplosion(0, 0, radius=10, base_duration=1.0)
    alpha = explosion.get_alpha(1.0, 200)
    assert alpha == 200
    BaseExplosion.containers = ()

def test_get_alpha_returns_half_alpha_at_halfway():
    group = pygame.sprite.Group()
    BaseExplosion.containers = (group,)
    explosion = BaseExplosion(0, 0, radius=10, base_duration=1.0)
    explosion.timer = 0.5
    alpha = explosion.get_alpha(1.0, 200)
    assert alpha == 100
    BaseExplosion.containers = ()

def test_get_alpha_returns_zero_when_layer_fully_expired():
    group = pygame.sprite.Group()
    BaseExplosion.containers = (group,)
    explosion = BaseExplosion(0, 0, radius=10, base_duration=2.0, overlay_duration=1.0)
    explosion.timer = 0.5
    alpha = explosion.get_alpha(1.0, 255)
    assert alpha == 0
    BaseExplosion.containers = ()

def test_get_alpha_negative_max_alpha_returns_zero():
    group = pygame.sprite.Group()
    BaseExplosion.containers = (group,)
    explosion = BaseExplosion(0, 0, radius=10, base_duration=1.0)
    alpha = explosion.get_alpha(1.0, 0)
    assert alpha == 0
    BaseExplosion.containers = ()

# --- BaseExplosion duration ---
def test_base_explosion_duration_is_max_of_base_and_overlay():
    group = pygame.sprite.Group()
    BaseExplosion.containers = (group,)
    explosion = BaseExplosion(0, 0, radius=10, base_duration=0.3, overlay_duration=0.8)
    assert explosion.duration == pytest.approx(0.8, abs=0.001)
    BaseExplosion.containers = ()

def test_base_explosion_duration_with_no_overlay_is_base_duration():
    group = pygame.sprite.Group()
    BaseExplosion.containers = (group,)
    explosion = BaseExplosion(0, 0, radius=10, base_duration=0.5)
    assert explosion.duration == pytest.approx(0.5, abs=0.001)
    BaseExplosion.containers = ()

# --- LaserBeamVE ---
def test_laser_beam_ve_stores_start_position():
    group = pygame.sprite.Group()
    LaserBeamVE.containers = (group,)
    start = pygame.Vector2(10, 20)
    end = pygame.Vector2(100, 200)
    beam = LaserBeamVE(start, end)
    assert beam.start_pos == start
    LaserBeamVE.containers = ()

def test_laser_beam_ve_stores_end_position():
    group = pygame.sprite.Group()
    LaserBeamVE.containers = (group,)
    start = pygame.Vector2(10, 20)
    end = pygame.Vector2(100, 200)
    beam = LaserBeamVE(start, end)
    assert beam.end_pos == end
    LaserBeamVE.containers = ()

def test_laser_beam_ve_position_is_midpoint_of_start_and_end():
    group = pygame.sprite.Group()
    LaserBeamVE.containers = (group,)
    start = pygame.Vector2(0, 0)
    end = pygame.Vector2(100, 100)
    beam = LaserBeamVE(start, end)
    assert beam.position.x == pytest.approx(50)
    assert beam.position.y == pytest.approx(50)
    LaserBeamVE.containers = ()

def test_laser_beam_ve_uses_constant_color_by_default():
    group = pygame.sprite.Group()
    LaserBeamVE.containers = (group,)
    beam = LaserBeamVE(pygame.Vector2(0, 0), pygame.Vector2(10, 10))
    assert beam.color == C.LASER_BEAM_COLOR
    LaserBeamVE.containers = ()

def test_laser_beam_ve_uses_constant_duration_by_default():
    group = pygame.sprite.Group()
    LaserBeamVE.containers = (group,)
    beam = LaserBeamVE(pygame.Vector2(0, 0), pygame.Vector2(10, 10))
    assert beam.duration == pytest.approx(C.LASER_BEAM_DURATION, abs=0.001)
    LaserBeamVE.containers = ()

# --- MuzzleFlareVE ---
def test_muzzle_flare_has_correct_duration():
    group = pygame.sprite.Group()
    MuzzleFlareVE.containers = (group,)
    flare = MuzzleFlareVE(0, 0)
    assert flare.duration == pytest.approx(0.08, abs=0.001)
    MuzzleFlareVE.containers = ()

def test_muzzle_flare_stores_default_size():
    group = pygame.sprite.Group()
    MuzzleFlareVE.containers = (group,)
    flare = MuzzleFlareVE(0, 0)
    assert flare.size == 7
    MuzzleFlareVE.containers = ()

def test_muzzle_flare_stores_custom_size():
    group = pygame.sprite.Group()
    MuzzleFlareVE.containers = (group,)
    flare = MuzzleFlareVE(0, 0, size=12)
    assert flare.size == 12
    MuzzleFlareVE.containers = ()

# --- RocketExhaustVE ---
def test_rocket_exhaust_has_correct_duration():
    group = pygame.sprite.Group()
    RocketExhaustVE.containers = (group,)
    exhaust = RocketExhaustVE(0, 0)
    assert exhaust.duration == pytest.approx(0.12, abs=0.001)
    RocketExhaustVE.containers = ()

def test_rocket_exhaust_stores_default_size():
    group = pygame.sprite.Group()
    RocketExhaustVE.containers = (group,)
    exhaust = RocketExhaustVE(0, 0)
    assert exhaust.size == 5
    RocketExhaustVE.containers = ()

# --- ShipExhaustVE ---
def test_ship_exhaust_normalizes_direction():
    group = pygame.sprite.Group()
    ShipExhaustVE.containers = (group,)
    ve = ShipExhaustVE(0, 0, pygame.Vector2(3, 4))
    assert ve.direction.length() == pytest.approx(1.0, abs=0.001)
    ShipExhaustVE.containers = ()

def test_ship_exhaust_stores_length():
    group = pygame.sprite.Group()
    ShipExhaustVE.containers = (group,)
    ve = ShipExhaustVE(0, 0, pygame.Vector2(1, 0), length=40)
    assert ve.length == 40
    ShipExhaustVE.containers = ()

def test_ship_exhaust_stores_width():
    group = pygame.sprite.Group()
    ShipExhaustVE.containers = (group,)
    ve = ShipExhaustVE(0, 0, pygame.Vector2(1, 0), width=10)
    assert ve.width == 10
    ShipExhaustVE.containers = ()
