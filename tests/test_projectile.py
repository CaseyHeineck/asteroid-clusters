import pygame
from core import constants as C
from core.element import Element
from entities.projectile import Kinetic, Plasma, Projectile, Rocket, _elemental_damage
from systems.gameplayeffect import OverkillSTE, PlasmaBurnSTE
from ui.visualeffect import RocketHitExplosionVE

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

# --- Kinetic.on_hit / Plasma.on_hit / Rocket.on_hit ---
class FakeHitAsteroid:
    def __init__(self, x=10, y=0, health=100, full_health=100):
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, 0)
        self.health = health
        self.full_health = full_health
        self.element = None
        self.radius = 20
        self.applied_effects = []
        self._alive = True

    def damaged(self, amount):
        self.health -= amount
        if self.health <= 0:
            self._alive = False
            return 50
        return 0

    def add_gameplay_effect(self, effect):
        self.applied_effects.append(effect)

    def alive(self):
        return self._alive

def make_kinetic():
    Kinetic.containers = ()
    k = Kinetic(0, 0)
    k.velocity = pygame.Vector2(200, 0)
    k.stat_source = "test"
    k.combat_stats = FakeCombatStats()
    k.extra_abilities = set()
    k.asteroids = None
    k.element = None
    group = pygame.sprite.Group()
    group.add(k)
    return k, group

def make_plasma():
    Plasma.containers = ()
    p = Plasma(0, 0)
    p.velocity = pygame.Vector2(200, 0)
    p.stat_source = "test"
    p.combat_stats = FakeCombatStats()
    p.extra_abilities = set()
    p.asteroids = None
    p.element = None
    group = pygame.sprite.Group()
    group.add(p)
    return p, group

def make_rocket(asteroids=None):
    Rocket.containers = ()
    RocketHitExplosionVE.containers = ()
    r = Rocket(0, 0, asteroids or [])
    r.velocity = pygame.Vector2(200, 0)
    r.stat_source = "test"
    r.combat_stats = FakeCombatStats()
    r.extra_abilities = set()
    r.element = None
    group = pygame.sprite.Group()
    group.add(r)
    return r, group

def test_kinetic_on_hit_damages_asteroid():
    k, _ = make_kinetic()
    asteroid = FakeHitAsteroid(x=10, y=0, health=100)
    k.on_hit(asteroid)
    assert asteroid.health < 100

def test_kinetic_on_hit_adds_velocity_to_asteroid():
    k, _ = make_kinetic()
    asteroid = FakeHitAsteroid(x=10, y=0)
    k.on_hit(asteroid)
    assert asteroid.velocity.length() > 0

def test_kinetic_on_hit_kills_projectile():
    k, _ = make_kinetic()
    asteroid = FakeHitAsteroid(x=10, y=0)
    k.on_hit(asteroid)
    assert not k.alive()

def test_kinetic_on_hit_caps_asteroid_velocity_at_max_speed():
    k, _ = make_kinetic()
    k.velocity = pygame.Vector2(C.ASTEROID_MAX_SPEED * 1000, 0)
    asteroid = FakeHitAsteroid(x=10, y=0)
    asteroid.velocity = pygame.Vector2(0, 0)
    k.on_hit(asteroid)
    assert asteroid.velocity.length() <= C.ASTEROID_MAX_SPEED + 0.01

def test_plasma_on_hit_damages_asteroid():
    p, _ = make_plasma()
    asteroid = FakeHitAsteroid(x=10, y=0, health=100)
    p.on_hit(asteroid)
    assert asteroid.health < 100

def test_plasma_on_hit_applies_burn_to_asteroid():
    p, _ = make_plasma()
    asteroid = FakeHitAsteroid(x=10, y=0)
    p.on_hit(asteroid)
    assert any(isinstance(e, PlasmaBurnSTE) for e in asteroid.applied_effects)

def test_plasma_on_hit_applies_burn_even_when_asteroid_killed():
    p, _ = make_plasma()
    asteroid = FakeHitAsteroid(x=10, y=0, health=1)
    p.on_hit(asteroid)
    assert any(isinstance(e, PlasmaBurnSTE) for e in asteroid.applied_effects)

def test_plasma_on_hit_kills_projectile():
    p, _ = make_plasma()
    asteroid = FakeHitAsteroid(x=10, y=0)
    p.on_hit(asteroid)
    assert not p.alive()

def test_rocket_on_hit_damages_direct_target():
    r, _ = make_rocket()
    asteroid = FakeHitAsteroid(x=10, y=0, health=100)
    r.on_hit(asteroid)
    assert asteroid.health < 100

def test_rocket_on_hit_applies_aoe_to_nearby_asteroids():
    nearby = FakeHitAsteroid(x=15, y=0, health=100)
    r, _ = make_rocket(asteroids=[nearby])
    main = FakeHitAsteroid(x=10, y=0, health=100)
    r.on_hit(main)
    assert nearby.health < 100

def test_rocket_on_hit_ignores_direct_target_in_aoe():
    r, _ = make_rocket()
    asteroid = FakeHitAsteroid(x=10, y=0, health=200)
    r.asteroids = [asteroid]
    r.on_hit(asteroid)
    assert asteroid.health == 200 - C.ROCKET_PROJECTILE_DAMAGE

def test_rocket_on_hit_kills_projectile():
    r, _ = make_rocket()
    asteroid = FakeHitAsteroid(x=10, y=0)
    r.on_hit(asteroid)
    assert not r.alive()
