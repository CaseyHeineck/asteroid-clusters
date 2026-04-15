from core.element import get_damage_multiplier, get_element_name, Element

# --- Returns the correct element ---
def test_cryo_element_returns_cryo_name():
    result = get_element_name(Element.CRYO)
    assert result == "Cryo"
    
def test_flux_element_returns_flux_name():
    result = get_element_name(Element.FLUX)
    assert result == "Flux"

def test_ion_element_returns_ion_name():
    result = get_element_name(Element.ION)
    assert result == "Ion"

def test_solar_element_returns_solar_name():
    result = get_element_name(Element.SOLAR)
    assert result == "Solar"

def test_void_element_returns_void_name():
    result = get_element_name(Element.VOID)
    assert result == "Void"

# --- None / missing element cases ---
def test_none_attacker_returns_neutral():
    result = get_damage_multiplier(None, Element.SOLAR)
    assert result == 1.0

def test_none_target_returns_neutral():
    result = get_damage_multiplier(Element.SOLAR, None)
    assert result == 1.0

def test_both_none_returns_neutral():
    result = get_damage_multiplier(None, None)
    assert result == 1.0


# --- Strong matchups (attacker deals 2x damage) ---
def test_solar_is_strong_against_cryo():
    result = get_damage_multiplier(Element.SOLAR, Element.CRYO)
    assert result == 2.0

def test_solar_is_strong_against_void():
    result = get_damage_multiplier(Element.SOLAR, Element.VOID)
    assert result == 2.0


# --- Weak matchups (attacker deals .5x damage) ---
def test_solar_is_weak_against_flux():
    result = get_damage_multiplier(Element.SOLAR, Element.FLUX)
    assert result == 0.5

def test_solar_is_weak_against_ion():
    result = get_damage_multiplier(Element.SOLAR, Element.ION)
    assert result == 0.5


# --- Neutral matchup (same element vs same element attacker deals 1x damage) ---
def test_solar_vs_solar_is_neutral():
    result = get_damage_multiplier(Element.SOLAR, Element.SOLAR)
    assert result == 1.0
