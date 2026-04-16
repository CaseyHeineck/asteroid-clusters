import pygame
from ui.shop import Shop
from core import constants as C

def make_shop():
    shop = object.__new__(Shop)
    shop.position = pygame.Vector2(200, 200)
    shop.pulse_timer = 0.0
    return shop

# --- is_near ---
def test_is_near_when_within_interaction_radius():
    shop = make_shop()
    nearby = pygame.Vector2(shop.position.x, shop.position.y + C.SHOP_INTERACTION_RADIUS - 1)
    assert shop.is_near(nearby)

def test_is_near_when_outside_interaction_radius():
    shop = make_shop()
    far = pygame.Vector2(shop.position.x, shop.position.y + C.SHOP_INTERACTION_RADIUS + 1)
    assert not shop.is_near(far)

def test_is_near_exactly_at_radius_edge():
    shop = make_shop()
    edge = pygame.Vector2(shop.position.x, shop.position.y + C.SHOP_INTERACTION_RADIUS)
    assert shop.is_near(edge)

# --- update ---
def test_update_advances_pulse_timer():
    shop = make_shop()
    shop.update(0.1)
    assert shop.pulse_timer > 0.0

def test_update_pulse_timer_wraps_at_1():
    shop = make_shop()
    shop.pulse_timer = 0.99
    shop.update(0.1)
    assert shop.pulse_timer < 0.5
