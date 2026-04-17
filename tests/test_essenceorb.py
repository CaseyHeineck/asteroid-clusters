import pygame
import pytest
from core import constants as C
from entities.essenceorb import EssenceOrb

def make_orb(value=1):
    EssenceOrb.containers = []
    return EssenceOrb(0, 0, value)

# --- __init__ ---
def test_init_stores_value():
    orb = make_orb(value=5)
    assert orb.value == 5

def test_init_sets_lifetime_to_constant():
    orb = make_orb()
    assert orb.lifetime == C.ESSENCE_ORB_LIFETIME

def test_init_sets_pulse_timer_to_zero():
    orb = make_orb()
    assert orb.pulse_timer == 0.0

def test_init_sets_correct_radius():
    orb = make_orb()
    assert orb.radius == C.ESSENCE_ORB_RADIUS

# --- update ---
def test_update_decrements_lifetime():
    orb = make_orb()
    orb.lifetime = 5.0
    orb.update(1.0)
    assert orb.lifetime == pytest.approx(4.0, abs=0.001)

def test_update_advances_pulse_timer_by_dt_scaled():
    orb = make_orb()
    orb.pulse_timer = 0.0
    orb.update(0.1)
    assert orb.pulse_timer == pytest.approx(0.13, abs=0.001)

def test_update_pulse_timer_wraps_below_one():
    orb = make_orb()
    orb.pulse_timer = 0.95
    orb.update(0.1)
    assert orb.pulse_timer < 1.0

def test_update_pulse_timer_wraps_when_above_one():
    orb = make_orb()
    orb.pulse_timer = 0.95
    orb.update(0.5)
    assert orb.pulse_timer < 1.0

def test_update_returns_zero():
    orb = make_orb()
    assert orb.update(0.1) == 0

def test_update_removes_orb_from_group_when_lifetime_expires():
    group = pygame.sprite.Group()
    EssenceOrb.containers = [group]
    orb = EssenceOrb(0, 0, 1)
    EssenceOrb.containers = []
    orb.lifetime = 0.05
    orb.update(0.1)
    assert not orb.alive()

def test_update_does_not_kill_orb_before_lifetime_expires():
    group = pygame.sprite.Group()
    EssenceOrb.containers = [group]
    orb = EssenceOrb(0, 0, 1)
    EssenceOrb.containers = []
    orb.lifetime = 1.0
    orb.update(0.1)
    assert orb.alive()
