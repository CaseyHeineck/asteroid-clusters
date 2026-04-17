import pygame
import pytest
from core import constants as C
from entities.portal import Portal

# --- position (edge placement from __init__) ---
def test_north_portal_positioned_at_top_center():
    portal = Portal(C.NORTH)
    assert portal.position.y == pytest.approx(0, abs=0.001)
    assert portal.position.x == pytest.approx(C.SCREEN_WIDTH / 2, abs=0.001)

def test_south_portal_positioned_at_bottom_center():
    portal = Portal(C.SOUTH)
    assert portal.position.y == pytest.approx(C.SCREEN_HEIGHT, abs=0.001)

def test_east_portal_positioned_at_right_center():
    portal = Portal(C.EAST)
    assert portal.position.x == pytest.approx(C.SCREEN_WIDTH, abs=0.001)

def test_west_portal_positioned_at_left_center():
    portal = Portal(C.WEST)
    assert portal.position.x == pytest.approx(0, abs=0.001)

# --- arrival_position ---
def test_north_arrival_position_is_inset_from_top():
    portal = Portal(C.NORTH)
    arrival = portal.arrival_position()
    assert arrival.y == pytest.approx(C.PORTAL_ARRIVAL_OFFSET, abs=0.001)

def test_south_arrival_position_is_inset_from_bottom():
    portal = Portal(C.SOUTH)
    arrival = portal.arrival_position()
    assert arrival.y == pytest.approx(C.SCREEN_HEIGHT - C.PORTAL_ARRIVAL_OFFSET, abs=0.001)

def test_east_arrival_position_is_inset_from_right():
    portal = Portal(C.EAST)
    arrival = portal.arrival_position()
    assert arrival.x == pytest.approx(C.SCREEN_WIDTH - C.PORTAL_ARRIVAL_OFFSET, abs=0.001)

def test_west_arrival_position_is_inset_from_left():
    portal = Portal(C.WEST)
    arrival = portal.arrival_position()
    assert arrival.x == pytest.approx(C.PORTAL_ARRIVAL_OFFSET, abs=0.001)

# --- is_near ---
def test_player_within_interaction_radius_is_near():
    portal = Portal(C.NORTH)
    nearby = pygame.Vector2(portal.position.x, portal.position.y + C.PORTAL_INTERACTION_RADIUS - 1)
    assert portal.is_near(nearby)

def test_player_outside_interaction_radius_is_not_near():
    portal = Portal(C.NORTH)
    far = pygame.Vector2(portal.position.x, portal.position.y + C.PORTAL_INTERACTION_RADIUS + 1)
    assert not portal.is_near(far)

def test_player_exactly_at_interaction_radius_is_near():
    portal = Portal(C.NORTH)
    edge = pygame.Vector2(portal.position.x, portal.position.y + C.PORTAL_INTERACTION_RADIUS)
    assert portal.is_near(edge)

# --- update ---
def test_update_advances_pulse_timer():
    portal = Portal(C.NORTH)
    portal.pulse_timer = 0.0
    portal.update(0.1)
    assert portal.pulse_timer == pytest.approx(0.1, abs=0.001)

def test_update_pulse_timer_wraps_at_1():
    portal = Portal(C.NORTH)
    portal.pulse_timer = 0.95
    portal.update(0.1)
    assert portal.pulse_timer == pytest.approx(0.05, abs=0.001)

# --- unlocked state ---
def test_portal_locked_by_default():
    portal = Portal(C.NORTH)
    assert not portal.unlocked

def test_portal_can_be_created_unlocked():
    portal = Portal(C.NORTH, unlocked=True)
    assert portal.unlocked
