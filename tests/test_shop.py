import pygame
from unittest.mock import patch
from ui.shop import Shop
from core import constants as C
from core.element import ALL_ELEMENTS

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

# --- _generate_wizards ---
def make_shop_stub():
    return object.__new__(Shop)

def test_generate_wizards_zero_count_returns_empty():
    shop = make_shop_stub()
    with patch("ui.shop.random.choices", side_effect=[[0]]):
        result = shop._generate_wizards({})
    assert result == []

def test_generate_wizards_produces_no_duplicates():
    shop = make_shop_stub()
    for _ in range(30):
        result = shop._generate_wizards({})
        assert len(set(result)) == len(result)

def test_generate_wizards_count_never_exceeds_total_elements():
    shop = make_shop_stub()
    for _ in range(20):
        result = shop._generate_wizards({})
        assert len(result) <= len(ALL_ELEMENTS)

def test_generate_wizards_all_returned_elements_are_valid():
    shop = make_shop_stub()
    result = shop._generate_wizards({})
    for elem in result:
        assert elem in ALL_ELEMENTS

def test_shop_init_increments_wizard_element_counts_for_each_wizard():
    with patch("ui.shop.random.uniform", return_value=400.0):
        with patch("ui.shop.random.choices") as mock_choices:
            mock_choices.side_effect = [[2], [ALL_ELEMENTS[0]], [ALL_ELEMENTS[1]]]
            counts = {}
            shop = Shop(wizard_element_counts=counts)
    assert counts.get(ALL_ELEMENTS[0], 0) == 1
    assert counts.get(ALL_ELEMENTS[1], 0) == 1

def test_shop_init_with_no_wizard_counts_does_not_raise():
    with patch("ui.shop.random.uniform", return_value=400.0):
        with patch("ui.shop.random.choices", side_effect=[[1], [ALL_ELEMENTS[0]]]):
            Shop(wizard_element_counts=None)
