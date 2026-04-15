from core.element import Element
from entities.projectile import _elemental_damage

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
