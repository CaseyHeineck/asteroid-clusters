import pygame
from core import constants as C
from entities.drone import ExplosiveDrone, KineticDrone, LaserDrone, PlasmaDrone, SentinelDrone
from ui.menus import _drone_keywords, _drone_upgrades, get_source_color

class FakePlayer:
    def __init__(self):
        self.position = pygame.Vector2(0, 0)

def make_drone(cls):
    cls.containers = []
    return cls(FakePlayer(), [])

# --- _drone_keywords ---
def test_drone_keywords_sentinel_with_no_extras_returns_empty():
    drone = make_drone(SentinelDrone)
    assert _drone_keywords(drone) == ""

def test_drone_keywords_kinetic_with_no_extras_returns_impact():
    drone = make_drone(KineticDrone)
    assert _drone_keywords(drone) == "  [IMPACT]"

def test_drone_keywords_plasma_with_no_extras_returns_burn():
    drone = make_drone(PlasmaDrone)
    assert _drone_keywords(drone) == "  [BURN]"

def test_drone_keywords_explosive_with_no_extras_returns_explosion():
    drone = make_drone(ExplosiveDrone)
    assert _drone_keywords(drone) == "  [EXPLOSION]"

def test_drone_keywords_laser_with_no_extras_returns_overkill():
    drone = make_drone(LaserDrone)
    assert _drone_keywords(drone) == "  [OVERKILL]"

def test_drone_keywords_kinetic_with_extra_appends_after_base():
    drone = make_drone(KineticDrone)
    drone.extra_abilities = {"burn"}
    assert _drone_keywords(drone) == "  [IMPACT, BURN]"

def test_drone_keywords_extra_matching_base_not_duplicated():
    drone = make_drone(KineticDrone)
    drone.extra_abilities = {"impact"}
    assert _drone_keywords(drone) == "  [IMPACT]"

def test_drone_keywords_sentinel_with_extra_shows_only_extra():
    drone = make_drone(SentinelDrone)
    drone.extra_abilities = {"burn"}
    assert _drone_keywords(drone) == "  [BURN]"

def test_drone_keywords_multiple_extras_are_sorted_after_base():
    drone = make_drone(KineticDrone)
    drone.extra_abilities = {"overkill", "burn"}
    result = _drone_keywords(drone)
    assert result == "  [IMPACT, BURN, OVERKILL]"

def test_drone_keywords_result_uses_uppercase():
    drone = make_drone(PlasmaDrone)
    assert _drone_keywords(drone) == _drone_keywords(drone).upper().rstrip()

# --- _drone_upgrades ---
def test_drone_upgrades_sentinel_returns_shield_options():
    drone = make_drone(SentinelDrone)
    types = [t for t, _ in _drone_upgrades(drone)]
    assert types == ["shield_health", "repair_rate"]

def test_drone_upgrades_kinetic_returns_all_four():
    drone = make_drone(KineticDrone)
    types = [t for t, _ in _drone_upgrades(drone)]
    assert types == ["damage", "fire_rate", "kinetic_mass", "projectile_speed"]

def test_drone_upgrades_explosive_without_impact_returns_two():
    drone = make_drone(ExplosiveDrone)
    types = [t for t, _ in _drone_upgrades(drone)]
    assert types == ["damage", "fire_rate"]

def test_drone_upgrades_plasma_returns_four():
    drone = make_drone(PlasmaDrone)
    types = [t for t, _ in _drone_upgrades(drone)]
    assert types == ["damage", "fire_rate", "burn_tick_rate", "burn_spread"]

def test_drone_upgrades_explosive_with_impact_returns_all_four():
    drone = make_drone(ExplosiveDrone)
    drone.extra_abilities = {"impact"}
    types = [t for t, _ in _drone_upgrades(drone)]
    assert types == ["damage", "fire_rate", "kinetic_mass", "projectile_speed"]

def test_drone_upgrades_plasma_with_impact_returns_six():
    drone = make_drone(PlasmaDrone)
    drone.extra_abilities = {"impact"}
    types = [t for t, _ in _drone_upgrades(drone)]
    assert types == ["damage", "fire_rate", "burn_tick_rate", "burn_spread",
                     "kinetic_mass", "projectile_speed"]

def test_drone_upgrades_laser_with_impact_includes_kinetic_mass_but_not_speed():
    drone = make_drone(LaserDrone)
    drone.extra_abilities = {"impact"}
    types = [t for t, _ in _drone_upgrades(drone)]
    assert types == ["damage", "fire_rate", "kinetic_mass"]

# --- get_source_color ---
def test_get_source_color_player_returns_red():
    assert get_source_color(C.PLAYER) == C.RED

def test_get_source_color_kinetic_drone_returns_silver():
    assert get_source_color(C.KINETIC_DRONE) == C.SILVER

def test_get_source_color_plasma_drone_returns_magenta():
    assert get_source_color(C.PLASMA_DRONE) == C.MAGENTA

def test_get_source_color_laser_drone_returns_laser_red():
    assert get_source_color(C.LASER_DRONE) == C.LASER_RED

def test_get_source_color_explosive_drone_returns_orange():
    assert get_source_color(C.EXPLOSIVE_DRONE) == C.ORANGE

def test_get_source_color_sentinel_drone_returns_gold():
    assert get_source_color(C.SENTINEL_DRONE) == C.GOLD

def test_get_source_color_unknown_source_returns_cyan():
    assert get_source_color("unknown_source") == C.CYAN
