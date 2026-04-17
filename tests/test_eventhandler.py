import pygame
from types import SimpleNamespace
from systems.eventhandler import EventHandler
from core import constants as C

def make_event(key):
    return SimpleNamespace(key=key)

class FakeMapSystem:
    def __init__(self):
        self.interact_called = False

    def try_interact(self):
        self.interact_called = True

class FakeGame:
    def __init__(self, state=C.GAME_RUNNING, shop_mode="hub"):
        self.current_state = state
        self.shop_mode = shop_mode
        self.map_system = None
        self._shop_leave_called = False
        self._mancer_back_called = False

    def on_shop_leave(self):
        self._shop_leave_called = True

    def on_mancer_back(self):
        self._mancer_back_called = True

    def exit(self):
        pass

# --- ESC in GAME_RUNNING ---
def test_esc_in_game_running_transitions_to_paused():
    game = FakeGame(C.GAME_RUNNING)
    EventHandler(game).handle_keydown(make_event(pygame.K_ESCAPE))
    assert game.current_state == C.PAUSED

# --- ESC in PAUSED ---
def test_esc_in_paused_transitions_to_game_running():
    game = FakeGame(C.PAUSED)
    EventHandler(game).handle_keydown(make_event(pygame.K_ESCAPE))
    assert game.current_state == C.GAME_RUNNING

# --- ESC in SHOP ---
def test_esc_in_shop_hub_mode_calls_on_shop_leave():
    game = FakeGame(C.SHOP, shop_mode="hub")
    EventHandler(game).handle_keydown(make_event(pygame.K_ESCAPE))
    assert game._shop_leave_called

def test_esc_in_shop_technomancer_mode_calls_on_mancer_back():
    game = FakeGame(C.SHOP, shop_mode="technomancer")
    EventHandler(game).handle_keydown(make_event(pygame.K_ESCAPE))
    assert game._mancer_back_called

def test_esc_in_shop_non_hub_does_not_call_shop_leave():
    game = FakeGame(C.SHOP, shop_mode="technomancer")
    EventHandler(game).handle_keydown(make_event(pygame.K_ESCAPE))
    assert not game._shop_leave_called

# --- ESC in other states ---
def test_esc_in_main_menu_has_no_effect():
    game = FakeGame(C.MAIN_MENU)
    EventHandler(game).handle_keydown(make_event(pygame.K_ESCAPE))
    assert game.current_state == C.MAIN_MENU

# --- E key in GAME_RUNNING ---
def test_e_in_game_running_calls_try_interact():
    game = FakeGame(C.GAME_RUNNING)
    game.map_system = FakeMapSystem()
    EventHandler(game).handle_keydown(make_event(pygame.K_e))
    assert game.map_system.interact_called

def test_e_in_game_running_with_no_map_system_is_no_op():
    game = FakeGame(C.GAME_RUNNING)
    game.map_system = None
    EventHandler(game).handle_keydown(make_event(pygame.K_e))

def test_e_in_paused_does_not_call_try_interact():
    game = FakeGame(C.PAUSED)
    game.map_system = FakeMapSystem()
    EventHandler(game).handle_keydown(make_event(pygame.K_e))
    assert not game.map_system.interact_called
