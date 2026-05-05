import pygame
import pytest
from core import constants as C
from game import Game
from types import SimpleNamespace
from core.element import Element
from entities.drone import ExplosiveDrone, KineticDrone, SlayerDrone, DebuffDrone, SentinelDrone
from entities.weaponsplatform import ExplosivePlatform, KineticPlatform, LaserPlatform, BurnPlatform, SentinelPlatform
from unittest.mock import MagicMock, patch

def make_game_stub():
    g = Game.__new__(Game)
    g.current_state = C.MAIN_MENU
    g.player = MagicMock()
    g.player.drones = []
    g.HUD = MagicMock()
    g.experience = MagicMock()
    g.essence = MagicMock()
    g.upgrade_counts = {}
    g.shop_mode = "hub"
    g.map_system = None
    g._current_shop = MagicMock()
    g.pending_drone_class = None
    g.pending_variant_action = None
    g.variant_select_menu = None
    return g

class FakePlayer:
    def __init__(self):
        self.position = pygame.Vector2(0, 0)

# --- wrap_object ---
def test_wrap_object_past_right_edge_wraps_left():
    g = make_game_stub()
    obj = SimpleNamespace(position=pygame.Vector2(C.SCREEN_WIDTH + 1, 100))
    g.wrap_object(obj)
    assert obj.position.x == pytest.approx(1.0)

def test_wrap_object_past_left_edge_wraps_right():
    g = make_game_stub()
    obj = SimpleNamespace(position=pygame.Vector2(-1, 100))
    g.wrap_object(obj)
    assert obj.position.x == pytest.approx(C.SCREEN_WIDTH - 1)

def test_wrap_object_past_bottom_edge_wraps_top():
    g = make_game_stub()
    obj = SimpleNamespace(position=pygame.Vector2(100, C.SCREEN_HEIGHT + 1))
    g.wrap_object(obj)
    assert obj.position.y == pytest.approx(1.0)

def test_wrap_object_past_top_edge_wraps_bottom():
    g = make_game_stub()
    obj = SimpleNamespace(position=pygame.Vector2(100, -1))
    g.wrap_object(obj)
    assert obj.position.y == pytest.approx(C.SCREEN_HEIGHT - 1)

def test_wrap_object_within_bounds_is_unchanged():
    g = make_game_stub()
    obj = SimpleNamespace(position=pygame.Vector2(100, 200))
    g.wrap_object(obj)
    assert obj.position.x == pytest.approx(100.0)
    assert obj.position.y == pytest.approx(200.0)

# --- state transitions ---
def test_on_resume_sets_state_to_game_running():
    g = make_game_stub()
    g.current_state = C.PAUSED
    g.on_resume()
    assert g.current_state == C.GAME_RUNNING

def test_on_main_menu_sets_state_to_main_menu():
    g = make_game_stub()
    g.current_state = C.GAME_RUNNING
    g.on_main_menu()
    assert g.current_state == C.MAIN_MENU

def test_on_shop_leave_sets_state_to_game_running():
    g = make_game_stub()
    g.current_state = C.SHOP
    g.on_shop_leave()
    assert g.current_state == C.GAME_RUNNING

def test_on_enter_technomancer_sets_shop_mode():
    g = make_game_stub()
    g.on_enter_technomancer()
    assert g.shop_mode == "technomancer"

def test_on_enter_elementalmancer_sets_shop_mode_to_element():
    g = make_game_stub()
    g.on_enter_elementalmancer(Element.CRYO)
    assert g.shop_mode == Element.CRYO

def test_on_mancer_back_resets_shop_mode_to_hub():
    g = make_game_stub()
    g.shop_mode = "technomancer"
    g._rebuild_hub_menu = MagicMock()
    g.on_mancer_back()
    assert g.shop_mode == "hub"

# --- enter_drone_choice ---
def test_enter_drone_choice_with_empty_pending_sets_game_running():
    g = make_game_stub()
    g.experience.pending_drones = []
    g.current_state = C.DRONE_CHOICE
    g.enter_drone_choice()
    assert g.current_state == C.GAME_RUNNING

# --- _apply_banish_ability ---
def test_banish_sentinel_enables_player_life_regen():
    g = make_game_stub()
    g.player.life_regen = False
    g._apply_banish_ability(SentinelPlatform)
    assert g.player.life_regen is True

def test_banish_sentinel_notifies_hud():
    g = make_game_stub()
    g.player.life_regen = False
    g._apply_banish_ability(SentinelPlatform)
    g.HUD.show_banish_notify.assert_called_once()

def test_banish_kinetic_adds_impact_ability_to_drone():
    g = make_game_stub()
    fake_drone = MagicMock()
    fake_drone.extra_abilities = set()
    fake_drone.platform.upgrade_paths = []
    g.player.drones = [fake_drone]
    g._apply_banish_ability(KineticPlatform)
    assert "impact" in fake_drone.extra_abilities

def test_banish_plasma_adds_burn_ability_to_drone():
    g = make_game_stub()
    fake_drone = MagicMock()
    fake_drone.extra_abilities = set()
    fake_drone.platform.upgrade_paths = []
    g.player.drones = [fake_drone]
    g._apply_banish_ability(BurnPlatform)
    assert "burn" in fake_drone.extra_abilities

def test_banish_explosive_adds_explosion_ability_to_drone():
    g = make_game_stub()
    fake_drone = MagicMock()
    fake_drone.extra_abilities = set()
    fake_drone.platform.upgrade_paths = []
    g.player.drones = [fake_drone]
    g._apply_banish_ability(ExplosivePlatform)
    assert "explosion" in fake_drone.extra_abilities

def test_banish_laser_adds_overkill_ability_to_drone():
    g = make_game_stub()
    fake_drone = MagicMock()
    fake_drone.extra_abilities = set()
    fake_drone.platform.upgrade_paths = []
    g.player.drones = [fake_drone]
    g._apply_banish_ability(LaserPlatform)
    assert "overkill" in fake_drone.extra_abilities

def test_banish_ability_is_no_op_when_player_has_no_drones():
    g = make_game_stub()
    g.player.drones = []
    g._apply_banish_ability(KineticPlatform)
    g.HUD.show_banish_notify.assert_not_called()

# --- apply_upgrade ---
def test_apply_upgrade_does_nothing_when_essence_insufficient():
    g = make_game_stub()
    g.essence.spend.return_value = False
    g.apply_upgrade(KineticDrone, "damage")
    assert g.upgrade_counts == {}

def test_apply_upgrade_increments_upgrade_count():
    g = make_game_stub()
    g.essence.spend.return_value = True
    drone = KineticDrone(FakePlayer(), [])
    g.player.drones = [drone]
    g.apply_upgrade(KineticDrone, "damage")
    assert g.upgrade_counts.get(("KineticDrone", "damage"), 0) == 1

def test_apply_upgrade_price_escalates_with_count():
    g = make_game_stub()
    g.essence.spend.return_value = True
    g.upgrade_counts[("KineticDrone", "damage")] = 3
    drone = KineticDrone(FakePlayer(), [])
    g.player.drones = [drone]
    g.apply_upgrade(KineticDrone, "damage")
    expected_price = C.SHOP_UPGRADE_BASE_PRICE + 3 * C.SHOP_UPGRADE_PRICE_STEP
    g.essence.spend.assert_called_with(expected_price)

def test_apply_upgrade_damage_increases_kinetic_damage_multiplier():
    g = make_game_stub()
    g.essence.spend.return_value = True
    drone = KineticDrone(FakePlayer(), [])
    original = drone.platform.damage_multiplier
    g.player.drones = [drone]
    g.apply_upgrade(KineticDrone, "damage")
    assert drone.platform.damage_multiplier > original

def test_apply_upgrade_fire_rate_reduces_timer_max():
    g = make_game_stub()
    g.essence.spend.return_value = True
    drone = KineticDrone(FakePlayer(), [])
    original = drone.platform.weapons_free_timer_max
    g.player.drones = [drone]
    g.apply_upgrade(KineticDrone, "fire_rate")
    assert drone.platform.weapons_free_timer_max < original

def test_apply_upgrade_only_affects_matching_drone_class():
    g = make_game_stub()
    g.essence.spend.return_value = True
    kinetic = KineticDrone(FakePlayer(), [])
    plasma = DebuffDrone(FakePlayer(), [])
    original_plasma_mult = plasma.platform.damage_multiplier
    g.player.drones = [kinetic, plasma]
    g.apply_upgrade(KineticDrone, "damage")
    assert plasma.platform.damage_multiplier == original_plasma_mult

def test_apply_upgrade_damage_increases_laser_drone_damage_directly():
    g = make_game_stub()
    g.essence.spend.return_value = True
    drone = SlayerDrone(FakePlayer(), [])
    original = drone.platform.damage
    g.player.drones = [drone]
    g.apply_upgrade(SlayerDrone, "damage")
    assert drone.platform.damage > original

def test_apply_upgrade_shield_health_increases_sentinel_shield_max_health():
    g = make_game_stub()
    g.essence.spend.return_value = True
    drone = SentinelDrone(FakePlayer(), [])
    drone.player_shield = None
    original = drone.shield_max_health
    g.player.drones = [drone]
    g.apply_upgrade(SentinelDrone, "shield_health")
    assert drone.shield_max_health == original + C.SHOP_SHIELD_HEALTH_INCREASE

def test_apply_upgrade_shield_health_updates_live_shield_max_health():
    g = make_game_stub()
    g.essence.spend.return_value = True
    drone = SentinelDrone(FakePlayer(), [])
    fake_shield = SimpleNamespace(max_health=drone.shield_max_health)
    drone.player_shield = fake_shield
    original = fake_shield.max_health
    g.player.drones = [drone]
    g.apply_upgrade(SentinelDrone, "shield_health")
    assert fake_shield.max_health == original + C.SHOP_SHIELD_HEALTH_INCREASE

def test_apply_upgrade_repair_rate_reduces_sentinel_repair_timer():
    g = make_game_stub()
    g.essence.spend.return_value = True
    drone = SentinelDrone(FakePlayer(), [])
    original = drone.shield_repair_timer_base
    g.player.drones = [drone]
    g.apply_upgrade(SentinelDrone, "repair_rate")
    assert drone.shield_repair_timer_base < original

def test_apply_upgrade_kinetic_mass_via_explosive_drone_updates_weight_override():
    from entities.projectile import Kinetic
    Kinetic.weight_override = None
    g = make_game_stub()
    g.essence.spend.return_value = True
    drone = ExplosiveDrone(FakePlayer(), [])
    g.player.drones = [drone]
    g.apply_upgrade(ExplosiveDrone, "kinetic_mass")
    assert Kinetic.weight_override == pytest.approx(
        C.KINETIC_PROJECTILE_WEIGHT_BASE * C.SHOP_KINETIC_MASS_INCREASE, abs=0.001)
    Kinetic.weight_override = None

def test_apply_upgrade_projectile_speed_via_explosive_drone_increases_speed():
    g = make_game_stub()
    g.essence.spend.return_value = True
    drone = ExplosiveDrone(FakePlayer(), [])
    original = drone.platform.projectile_speed
    g.player.drones = [drone]
    g.apply_upgrade(ExplosiveDrone, "projectile_speed")
    assert drone.platform.projectile_speed > original

def test_apply_upgrade_projectile_speed_via_laser_drone_does_nothing():
    g = make_game_stub()
    g.essence.spend.return_value = True
    drone = SlayerDrone(FakePlayer(), [])
    g.player.drones = [drone]
    g.apply_upgrade(SlayerDrone, "projectile_speed")

def test_apply_upgrade_burn_tick_rate_uses_start_decrease_on_first_purchase():
    from systems.gameplayeffect import BurnSTE
    BurnSTE.tick_rate_override = None
    g = make_game_stub()
    g.essence.spend.return_value = True
    g.player.drones = []
    g.apply_upgrade(DebuffDrone, "burn_tick_rate")
    expected = C.PLASMA_BURN_TICK_RATE - C.SHOP_BURN_TICK_RATE_DECREASE_START
    assert BurnSTE.tick_rate_override == pytest.approx(expected, abs=0.001)
    BurnSTE.tick_rate_override = None

def test_apply_upgrade_burn_tick_rate_tapers_on_repeated_purchase():
    from systems.gameplayeffect import BurnSTE
    BurnSTE.tick_rate_override = None
    g = make_game_stub()
    g.essence.spend.return_value = True
    g.player.drones = []
    g.apply_upgrade(DebuffDrone, "burn_tick_rate")
    g.apply_upgrade(DebuffDrone, "burn_tick_rate")
    first_decrease = C.SHOP_BURN_TICK_RATE_DECREASE_START
    second_decrease = C.SHOP_BURN_TICK_RATE_DECREASE_START - C.SHOP_BURN_TICK_RATE_DECREASE_TAPER
    expected = C.PLASMA_BURN_TICK_RATE - first_decrease - second_decrease
    assert BurnSTE.tick_rate_override == pytest.approx(expected, abs=0.001)
    BurnSTE.tick_rate_override = None

def test_apply_upgrade_burn_spread_increases_spread_chance_override():
    from systems.gameplayeffect import BurnSTE
    BurnSTE.spread_chance_override = None
    g = make_game_stub()
    g.essence.spend.return_value = True
    g.player.drones = []
    g.apply_upgrade(DebuffDrone, "burn_spread")
    assert BurnSTE.spread_chance_override == pytest.approx(
        C.PLASMA_BURN_SPREAD_CHANCE + C.SHOP_BURN_SPREAD_INCREASE, abs=0.001)
    BurnSTE.spread_chance_override = None

def test_apply_upgrade_burn_spread_caps_at_one():
    from systems.gameplayeffect import BurnSTE
    BurnSTE.spread_chance_override = 0.95
    g = make_game_stub()
    g.essence.spend.return_value = True
    g.player.drones = []
    g.apply_upgrade(DebuffDrone, "burn_spread")
    assert BurnSTE.spread_chance_override == pytest.approx(1.0, abs=0.001)
    BurnSTE.spread_chance_override = None

# --- on_shop_infuse ---
def test_on_shop_infuse_uses_infuse_cost_when_drone_has_no_element():
    g = make_game_stub()
    g.essence.spend_elemental.return_value = False
    g.elem_mancer_menus = {}
    drone = KineticDrone(FakePlayer(), [])
    drone.element = None
    g.on_shop_infuse(drone, Element.SOLAR)
    g.essence.spend_elemental.assert_called_with(C.WIZARD_INFUSE_COST)

def test_on_shop_infuse_uses_overwrite_cost_when_drone_already_infused():
    g = make_game_stub()
    g.essence.spend_elemental.return_value = False
    g.elem_mancer_menus = {}
    drone = KineticDrone(FakePlayer(), [])
    drone.element = Element.CRYO
    g.on_shop_infuse(drone, Element.SOLAR)
    g.essence.spend_elemental.assert_called_with(C.WIZARD_OVERWRITE_COST)

def test_on_shop_infuse_does_not_change_element_when_spend_fails():
    g = make_game_stub()
    g.essence.spend_elemental.return_value = False
    g.elem_mancer_menus = {}
    drone = KineticDrone(FakePlayer(), [])
    drone.element = None
    g.on_shop_infuse(drone, Element.SOLAR)
    assert drone.element is None

def test_on_shop_infuse_sets_drone_element_on_success():
    g = make_game_stub()
    g.essence.spend_elemental.return_value = True
    g.elem_mancer_menus = {}
    drone = KineticDrone(FakePlayer(), [])
    drone.element = None
    with patch("game.create_elementalmancer_menu", return_value=MagicMock()):
        g.on_shop_infuse(drone, Element.SOLAR)
    assert drone.element == Element.SOLAR

# --- on_game_over ---
def test_on_game_over_sets_state_to_game_over():
    g = make_game_stub()
    g.combat_stats = MagicMock()
    with patch("game.create_game_over_menu", return_value=MagicMock()):
        g.on_game_over()
    assert g.current_state == C.GAME_OVER

def test_on_game_over_rebuilds_game_over_menu():
    g = make_game_stub()
    g.combat_stats = MagicMock()
    with patch("game.create_game_over_menu", return_value=MagicMock()) as mock_create:
        g.on_game_over()
    mock_create.assert_called_once()

# --- on_variant_selected (add action) ---
def test_on_add_drone_removes_drone_class_from_pending():
    g = make_game_stub()
    g.asteroids = []
    g.experience.pending_drones = [KineticDrone]
    g.experience.added_drones = []
    g.pending_drone_class = KineticDrone
    g.pending_variant_action = "add"
    g.on_variant_selected(KineticPlatform)
    assert KineticDrone not in g.experience.pending_drones

def test_on_add_drone_appends_drone_class_to_added():
    g = make_game_stub()
    g.asteroids = []
    g.experience.pending_drones = [KineticDrone]
    g.experience.added_drones = []
    g.pending_drone_class = KineticDrone
    g.pending_variant_action = "add"
    g.on_variant_selected(KineticPlatform)
    assert KineticDrone in g.experience.added_drones

def test_on_add_drone_calls_player_add_drone_with_correct_args():
    g = make_game_stub()
    g.asteroids = []
    g.experience.pending_drones = [KineticDrone]
    g.experience.added_drones = []
    g.pending_drone_class = KineticDrone
    g.pending_variant_action = "add"
    g.on_variant_selected(KineticPlatform)
    g.player.add_drone.assert_called_with(KineticDrone, [], platform_class=KineticPlatform)

# --- on_variant_selected (banish action) ---
def test_on_banish_drone_removes_drone_class_from_pending():
    g = make_game_stub()
    g.experience.pending_drones = [KineticDrone]
    g.experience.banished_drones = []
    g._apply_banish_ability = MagicMock()
    g.pending_drone_class = KineticDrone
    g.pending_variant_action = "banish"
    g.on_variant_selected(KineticPlatform)
    assert KineticDrone not in g.experience.pending_drones

def test_on_banish_drone_appends_drone_class_to_banished():
    g = make_game_stub()
    g.experience.pending_drones = [KineticDrone]
    g.experience.banished_drones = []
    g._apply_banish_ability = MagicMock()
    g.pending_drone_class = KineticDrone
    g.pending_variant_action = "banish"
    g.on_variant_selected(KineticPlatform)
    assert KineticDrone in g.experience.banished_drones

def test_on_banish_drone_calls_apply_banish_ability():
    g = make_game_stub()
    g.experience.pending_drones = [KineticDrone]
    g.experience.banished_drones = []
    g._apply_banish_ability = MagicMock()
    g.pending_drone_class = KineticDrone
    g.pending_variant_action = "banish"
    g.on_variant_selected(KineticPlatform)
    g._apply_banish_ability.assert_called_with(KineticPlatform)
