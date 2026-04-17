import pygame
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from systems.mapsystem import MapSystem
from core import constants as C

def make_portal(unlocked):
    return SimpleNamespace(unlocked=unlocked)

def make_space(*portal_lock_states):
    return SimpleNamespace(portals={i: make_portal(s) for i, s in enumerate(portal_lock_states)})

def make_map_stub(spaces):
    ms = object.__new__(MapSystem)
    ms.grid = {i: space for i, space in enumerate(spaces)}
    return ms

# --- count_locked_portals ---
def test_count_locked_portals_returns_zero_when_grid_empty():
    ms = make_map_stub([])
    assert ms.count_locked_portals() == 0

def test_count_locked_portals_counts_all_locked():
    ms = make_map_stub([make_space(False, False), make_space(False)])
    assert ms.count_locked_portals() == 3

def test_count_locked_portals_counts_none_when_all_unlocked():
    ms = make_map_stub([make_space(True, True), make_space(True)])
    assert ms.count_locked_portals() == 0

def test_count_locked_portals_counts_partial():
    ms = make_map_stub([make_space(False, True), make_space(False, False)])
    assert ms.count_locked_portals() == 3

def test_count_locked_portals_single_locked_portal():
    ms = make_map_stub([make_space(False)])
    assert ms.count_locked_portals() == 1

def test_count_locked_portals_single_unlocked_portal():
    ms = make_map_stub([make_space(True)])
    assert ms.count_locked_portals() == 0

# --- try_interact / _unlock_back_portal / _transit ---
def make_portal_stub(unlocked=True, near=True, cost=C.PORTAL_ESSENCE_COST):
    return SimpleNamespace(unlocked=unlocked, cost=cost,
        is_near=lambda pos: near)

def make_ms(portals=None, shop=None, current_pos=(0, 0)):
    space = SimpleNamespace(portals=portals or {}, shop=shop)
    ms = object.__new__(MapSystem)
    ms.grid = {current_pos: space}
    ms.current_pos = current_pos
    ms.cell_states = {}
    ms.wizard_element_counts = {}
    ms.game = SimpleNamespace(player=SimpleNamespace(position=pygame.Vector2(0, 0)),
        essence=SimpleNamespace(spend=MagicMock(return_value=True)),
        open_shop=MagicMock(), enter_new_airspace=MagicMock(), wizard_element_counts={})
    return ms

def test_try_interact_returns_false_when_no_portals_or_shop():
    ms = make_ms()
    assert ms.try_interact() is False

def test_try_interact_near_unlocked_portal_returns_true():
    portal = make_portal_stub(unlocked=True, near=True)
    ms = make_ms(portals={C.NORTH: portal})
    ms.grid[(0, -1)] = SimpleNamespace(portals={}, shop=None, active_state=None)
    assert ms.try_interact() is True

def test_try_interact_far_portal_returns_false():
    portal = make_portal_stub(unlocked=True, near=False)
    ms = make_ms(portals={C.NORTH: portal})
    assert ms.try_interact() is False

def test_try_interact_near_locked_portal_spends_essence():
    portal = make_portal_stub(unlocked=False, near=True)
    ms = make_ms(portals={C.NORTH: portal})
    ms.grid[(0, -1)] = SimpleNamespace(portals={}, shop=None, active_state=None)
    ms.try_interact()
    ms.game.essence.spend.assert_called_with(portal.cost)

def test_try_interact_near_locked_portal_unlocks_it_on_success():
    portal = make_portal_stub(unlocked=False, near=True)
    ms = make_ms(portals={C.NORTH: portal})
    ms.grid[(0, -1)] = SimpleNamespace(portals={}, shop=None, active_state=None)
    ms.game.essence.spend = MagicMock(return_value=True)
    ms.try_interact()
    assert portal.unlocked is True

def test_try_interact_locked_portal_not_unlocked_when_cannot_afford():
    portal = make_portal_stub(unlocked=False, near=True)
    ms = make_ms(portals={C.NORTH: portal})
    ms.game.essence.spend = MagicMock(return_value=False)
    result = ms.try_interact()
    assert portal.unlocked is False
    assert result is True

def test_try_interact_near_shop_calls_open_shop():
    shop = SimpleNamespace(is_near=lambda pos: True)
    ms = make_ms(shop=shop)
    ms.try_interact()
    ms.game.open_shop.assert_called_with(shop)

def test_try_interact_near_shop_returns_true():
    shop = SimpleNamespace(is_near=lambda pos: True)
    ms = make_ms(shop=shop)
    assert ms.try_interact() is True

# --- _unlock_back_portal ---
def test_unlock_back_portal_unlocks_adjacent_back_portal():
    back_portal = SimpleNamespace(unlocked=False)
    neighbor = SimpleNamespace(portals={C.SOUTH: back_portal})
    ms = make_ms(portals={C.NORTH: make_portal_stub()})
    ms.grid[(0, -1)] = neighbor
    ms._unlock_back_portal(C.NORTH)
    assert back_portal.unlocked is True

def test_unlock_back_portal_no_error_when_adj_not_in_grid():
    ms = make_ms()
    ms._unlock_back_portal(C.NORTH)

def test_unlock_back_portal_no_error_when_back_portal_missing():
    neighbor = SimpleNamespace(portals={})
    ms = make_ms()
    ms.grid[(0, -1)] = neighbor
    ms._unlock_back_portal(C.NORTH)

# --- _transit ---
def test_transit_updates_current_pos():
    target = SimpleNamespace(portals={}, shop=None, active_state=None)
    ms = make_ms(portals={C.EAST: make_portal_stub()})
    ms.grid[(1, 0)] = target
    ms._transit(C.EAST)
    assert ms.current_pos == (1, 0)

def test_transit_calls_enter_new_airspace():
    target = SimpleNamespace(portals={}, shop=None, active_state=None)
    ms = make_ms(portals={C.EAST: make_portal_stub()})
    ms.grid[(1, 0)] = target
    ms._transit(C.EAST)
    ms.game.enter_new_airspace.assert_called_once()

def test_transit_creates_new_airspace_when_not_in_grid():
    ms = make_ms(portals={C.NORTH: make_portal_stub()})
    with patch("systems.mapsystem.AirSpace") as mock_cls:
        mock_space = SimpleNamespace(portals={}, shop=None, active_state=None)
        mock_cls.return_value = mock_space
        ms._transit(C.NORTH)
    assert (0, -1) in ms.grid

def test_transit_reuses_existing_space_without_creating_new():
    target = SimpleNamespace(portals={}, shop=None, active_state=None)
    ms = make_ms(portals={C.EAST: make_portal_stub()})
    ms.grid[(1, 0)] = target
    with patch("systems.mapsystem.AirSpace") as mock_cls:
        ms._transit(C.EAST)
    mock_cls.assert_not_called()
