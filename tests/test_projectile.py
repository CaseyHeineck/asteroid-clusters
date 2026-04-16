import pygame
from core.element import Element
from core import constants as C
from entities.projectile import Projectile, _elemental_damage
from systems.gameplayeffect import OverkillSTE, PlasmaBurnSTE


class FakeCombatStats:
    def record_damage_event(self, **kwargs): pass


class FakeAsteroid:
    def __init__(self, health=10, full_health=10):
        self.health = health
        self.full_health = full_health
        self.position = pygame.Vector2(10, 0)
        self.velocity = pygame.Vector2(0, 0)
        self.applied_effects = []
        self._alive = True

    def add_gameplay_effect(self, effect):
        self.applied_effects.append(effect)

    def alive(self):
        return self._alive


def make_projectile(extra_abilities=None, damage=20):
    Projectile.containers = ()
    p = Projectile(0, 0, damage=damage)
    p.extra_abilities = set(extra_abilities or [])
    p.position = pygame.Vector2(0, 0)
    p.velocity = pygame.Vector2(100, 0)
    p.stat_source = "test"
    p.combat_stats = FakeCombatStats()
    p.asteroids = None
    return p

# --- Defines correct elemental damage matchup ---
class FakeCryoTarget:
    element = Element.CRYO
class FakeFluxTarget:
    element = Element.FLUX
class FakeIonTarget:
    element = Element.ION
class FakeSolarTarget:
    element = Element.SOLAR
class FakeVoidTarget:
    element = Element.VOID
class FakeNeutralTarget:
    element = None

def test_cryo_projectile_good_against_flux_target():
    result = _elemental_damage(1, Element.CRYO, FakeFluxTarget())
    assert result == 2

def test_cryo_projectile_good_against_ion_target():
    result = _elemental_damage(1, Element.CRYO, FakeIonTarget())
    assert result == 2

def test_cryo_projectile_bad_against_void_target_floor():
    result = _elemental_damage(1, Element.CRYO, FakeVoidTarget())
    assert result == 1

def test_cryo_projectile_bad_against_solar_target_floor():
    result = _elemental_damage(1, Element.CRYO, FakeSolarTarget())
    assert result == 1

def test_cryo_projectile_bad_against_void_target():
    result = _elemental_damage(6, Element.CRYO, FakeVoidTarget())
    assert result == 3

def test_cryo_projectile_bad_against_solar_target():
    result = _elemental_damage(6, Element.CRYO, FakeSolarTarget())
    assert result == 3

def test_cryo_projectile_neutral_against_cryo_target():
    result = _elemental_damage(1, Element.CRYO, FakeCryoTarget())
    assert result == 1

def test_cryo_projectile_neutral_against_neutral_target():
    result = _elemental_damage(1, Element.CRYO, FakeNeutralTarget())
    assert result == 1

def test_flux_projectile_good_against_void_target():
    result = _elemental_damage(1, Element.FLUX, FakeVoidTarget())
    assert result == 2

def test_flux_projectile_good_against_solar_target():
    result = _elemental_damage(1, Element.FLUX, FakeSolarTarget())
    assert result == 2

def test_flux_projectile_bad_against_ion_target_floor():
    result = _elemental_damage(1, Element.FLUX, FakeIonTarget())
    assert result == 1

def test_flux_projectile_bad_against_cryo_target_floor():
    result = _elemental_damage(1, Element.FLUX, FakeCryoTarget())
    assert result == 1

def test_flux_projectile_bad_against_ion_target():
    result = _elemental_damage(6, Element.FLUX, FakeIonTarget())
    assert result == 3

def test_flux_projectile_bad_against_cryo_target():
    result = _elemental_damage(6, Element.FLUX, FakeCryoTarget())
    assert result == 3

def test_flux_projectile_neutral_against_flux_target():
    result = _elemental_damage(1, Element.FLUX, FakeFluxTarget())
    assert result == 1

def test_flux_projectile_neutral_against_neutral_target():
    result = _elemental_damage(1, Element.FLUX, FakeNeutralTarget())
    assert result == 1

def test_ion_projectile_good_against_solar_target():
    result = _elemental_damage(1, Element.ION, FakeSolarTarget())
    assert result == 2

def test_ion_projectile_good_against_flux_target():
    result = _elemental_damage(1, Element.ION, FakeFluxTarget())
    assert result == 2

def test_ion_projectile_bad_against_cryo_target_floor():
    result = _elemental_damage(1, Element.ION, FakeCryoTarget())
    assert result == 1

def test_ion_projectile_bad_against_void_target_floor():
    result = _elemental_damage(1, Element.ION, FakeVoidTarget())
    assert result == 1

def test_ion_projectile_bad_against_cryo_target():
    result = _elemental_damage(6, Element.ION, FakeCryoTarget())
    assert result == 3

def test_ion_projectile_bad_against_void_target():
    result = _elemental_damage(6, Element.ION, FakeVoidTarget())
    assert result == 3

def test_ion_projectile_neutral_against_ion_target():
    result = _elemental_damage(1, Element.ION, FakeIonTarget())
    assert result == 1

def test_ion_projectile_neutral_against_neutral_target():
    result = _elemental_damage(1, Element.ION, FakeNeutralTarget())
    assert result == 1

def test_solar_projectile_good_against_cryo_target():
    result = _elemental_damage(1, Element.SOLAR, FakeCryoTarget())
    assert result == 2

def test_solar_projectile_good_against_void_target():
    result = _elemental_damage(1, Element.SOLAR, FakeVoidTarget())
    assert result == 2

def test_solar_projectile_bad_against_flux_target_floor():
    result = _elemental_damage(1, Element.SOLAR, FakeFluxTarget())
    assert result == 1

def test_solar_projectile_bad_against_ion_target_floor():
    result = _elemental_damage(1, Element.SOLAR, FakeIonTarget())
    assert result == 1

def test_solar_projectile_bad_against_flux_target():
    result = _elemental_damage(6, Element.SOLAR, FakeFluxTarget())
    assert result == 3

def test_solar_projectile_neutral_against_solar_target():
    result = _elemental_damage(1, Element.SOLAR, FakeSolarTarget())
    assert result == 1

def test_solar_projectile_neutral_against_neutral_target():
    result = _elemental_damage(1, Element.SOLAR, FakeNeutralTarget())
    assert result == 1

def test_solar_projectile_bad_against_ion_target():
    result = _elemental_damage(6, Element.SOLAR, FakeIonTarget())
    assert result == 3

def test_void_projectile_good_against_cryo_target():
    result = _elemental_damage(1, Element.VOID, FakeCryoTarget())
    assert result == 2

def test_void_projectile_good_against_ion_target():
    result = _elemental_damage(1, Element.VOID, FakeIonTarget())
    assert result == 2

def test_void_projectile_bad_against_flux_target_floor():
    result = _elemental_damage(1, Element.VOID, FakeFluxTarget())
    assert result == 1

def test_void_projectile_bad_against_solar_target_floor():
    result = _elemental_damage(1, Element.VOID, FakeSolarTarget())
    assert result == 1

def test_void_projectile_bad_against_flux_target():
    result = _elemental_damage(6, Element.VOID, FakeFluxTarget())
    assert result == 3

def test_void_projectile_bad_against_solar_target():
    result = _elemental_damage(6, Element.VOID, FakeSolarTarget())
    assert result == 3

def test_void_projectile_neutral_against_void_target():
    result = _elemental_damage(1, Element.VOID, FakeVoidTarget())
    assert result == 1

def test_void_projectile_neutral_against_neutral_target():
    result = _elemental_damage(1, Element.VOID, FakeNeutralTarget())
    assert result == 1


# --- pre_hit_extras: overkill ---
def test_overkill_applies_ste_when_damage_meets_threshold():
    p = make_projectile(["overkill"], damage=20)
    asteroid = FakeAsteroid(health=5, full_health=10)
    p.pre_hit_extras(asteroid)
    assert any(isinstance(e, OverkillSTE) for e in asteroid.applied_effects)

def test_overkill_does_not_apply_when_damage_below_threshold():
    p = make_projectile(["overkill"], damage=5)
    asteroid = FakeAsteroid(health=10, full_health=10)
    p.pre_hit_extras(asteroid)
    assert not any(isinstance(e, OverkillSTE) for e in asteroid.applied_effects)

def test_overkill_does_not_apply_without_ability():
    p = make_projectile([], damage=100)
    asteroid = FakeAsteroid(health=1, full_health=1)
    p.pre_hit_extras(asteroid)
    assert not any(isinstance(e, OverkillSTE) for e in asteroid.applied_effects)

def test_overkill_skipped_when_in_skip_abilities():
    p = make_projectile(["overkill"], damage=100)
    asteroid = FakeAsteroid(health=1, full_health=1)
    p.pre_hit_extras(asteroid, skip_abilities={"overkill"})
    assert not any(isinstance(e, OverkillSTE) for e in asteroid.applied_effects)


# --- post_hit_extras: burn ---
def test_burn_applies_plasma_burn_ste_when_alive():
    p = make_projectile(["burn"])
    asteroid = FakeAsteroid()
    asteroid._alive = True
    p.post_hit_extras(asteroid)
    assert any(isinstance(e, PlasmaBurnSTE) for e in asteroid.applied_effects)

def test_burn_does_not_apply_when_asteroid_dead():
    p = make_projectile(["burn"])
    asteroid = FakeAsteroid()
    asteroid._alive = False
    p.post_hit_extras(asteroid)
    assert not any(isinstance(e, PlasmaBurnSTE) for e in asteroid.applied_effects)

def test_burn_does_not_apply_without_ability():
    p = make_projectile([])
    asteroid = FakeAsteroid()
    p.post_hit_extras(asteroid)
    assert not any(isinstance(e, PlasmaBurnSTE) for e in asteroid.applied_effects)

def test_burn_skipped_when_in_skip_abilities():
    p = make_projectile(["burn"])
    asteroid = FakeAsteroid()
    asteroid._alive = True
    p.post_hit_extras(asteroid, skip_abilities={"burn"})
    assert not any(isinstance(e, PlasmaBurnSTE) for e in asteroid.applied_effects)


# --- post_hit_extras: impact ---
def test_impact_adds_velocity_to_asteroid():
    p = make_projectile(["impact"])
    asteroid = FakeAsteroid()
    asteroid.velocity = pygame.Vector2(0, 0)
    p.post_hit_extras(asteroid)
    assert asteroid.velocity.length() > 0

def test_impact_caps_velocity_at_max_speed():
    p = make_projectile(["impact"])
    p.velocity = pygame.Vector2(C.ASTEROID_MAX_SPEED * 1000, 0)
    asteroid = FakeAsteroid()
    asteroid.velocity = pygame.Vector2(0, 0)
    p.post_hit_extras(asteroid)
    assert asteroid.velocity.length() <= C.ASTEROID_MAX_SPEED + 0.01

def test_impact_skipped_when_in_skip_abilities():
    p = make_projectile(["impact"])
    asteroid = FakeAsteroid()
    asteroid.velocity = pygame.Vector2(0, 0)
    p.post_hit_extras(asteroid, skip_abilities={"impact"})
    assert asteroid.velocity.length() == 0
