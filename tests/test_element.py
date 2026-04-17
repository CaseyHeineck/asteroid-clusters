from core.element import (
    ALL_ELEMENTS, Element, get_damage_multiplier, get_element_glow_color,
    get_element_name, get_element_primary_color,
)

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

# --- Cryo matchups ---
def test_cryo_is_strong_against_flux():
    assert get_damage_multiplier(Element.CRYO, Element.FLUX) == 2.0

def test_cryo_is_strong_against_ion():
    assert get_damage_multiplier(Element.CRYO, Element.ION) == 2.0

def test_cryo_is_weak_against_void():
    assert get_damage_multiplier(Element.CRYO, Element.VOID) == 0.5

def test_cryo_is_weak_against_solar():
    assert get_damage_multiplier(Element.CRYO, Element.SOLAR) == 0.5

def test_cryo_vs_cryo_is_neutral():
    assert get_damage_multiplier(Element.CRYO, Element.CRYO) == 1.0

# --- Flux matchups ---
def test_flux_is_strong_against_void():
    assert get_damage_multiplier(Element.FLUX, Element.VOID) == 2.0

def test_flux_is_strong_against_solar():
    assert get_damage_multiplier(Element.FLUX, Element.SOLAR) == 2.0

def test_flux_is_weak_against_ion():
    assert get_damage_multiplier(Element.FLUX, Element.ION) == 0.5

def test_flux_is_weak_against_cryo():
    assert get_damage_multiplier(Element.FLUX, Element.CRYO) == 0.5

def test_flux_vs_flux_is_neutral():
    assert get_damage_multiplier(Element.FLUX, Element.FLUX) == 1.0

# --- Ion matchups ---
def test_ion_is_strong_against_solar():
    assert get_damage_multiplier(Element.ION, Element.SOLAR) == 2.0

def test_ion_is_strong_against_flux():
    assert get_damage_multiplier(Element.ION, Element.FLUX) == 2.0

def test_ion_is_weak_against_cryo():
    assert get_damage_multiplier(Element.ION, Element.CRYO) == 0.5

def test_ion_is_weak_against_void():
    assert get_damage_multiplier(Element.ION, Element.VOID) == 0.5

def test_ion_vs_ion_is_neutral():
    assert get_damage_multiplier(Element.ION, Element.ION) == 1.0

# --- Void matchups ---
def test_void_is_strong_against_ion():
    assert get_damage_multiplier(Element.VOID, Element.ION) == 2.0

def test_void_is_strong_against_cryo():
    assert get_damage_multiplier(Element.VOID, Element.CRYO) == 2.0

def test_void_is_weak_against_solar():
    assert get_damage_multiplier(Element.VOID, Element.SOLAR) == 0.5

def test_void_is_weak_against_flux():
    assert get_damage_multiplier(Element.VOID, Element.FLUX) == 0.5

def test_void_vs_void_is_neutral():
    assert get_damage_multiplier(Element.VOID, Element.VOID) == 1.0

# --- Color helpers ---
def test_get_element_primary_color_returns_value_for_each_element():
    for element in ALL_ELEMENTS:
        color = get_element_primary_color(element)
        assert color is not None

def test_get_element_glow_color_returns_value_for_each_element():
    for element in ALL_ELEMENTS:
        color = get_element_glow_color(element)
        assert color is not None

def test_get_element_primary_color_is_rgb_tuple():
    for element in ALL_ELEMENTS:
        color = get_element_primary_color(element)
        assert len(color) == 3

def test_get_element_glow_color_is_rgb_tuple():
    for element in ALL_ELEMENTS:
        color = get_element_glow_color(element)
        assert len(color) == 3

# --- ALL_ELEMENTS ---
def test_all_elements_contains_all_five():
    assert len(ALL_ELEMENTS) == 5

def test_all_elements_contains_each_member():
    for element in Element:
        assert element in ALL_ELEMENTS
