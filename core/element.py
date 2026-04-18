import math
import pygame
from core import constants as C
from enum import Enum

class Element(Enum):
    SOLAR = "solar"
    CRYO  = "cryo"
    FLUX  = "flux"
    ION   = "ion"
    VOID  = "void"

ALL_ELEMENTS = list(Element)

STRONG_AGAINST = {
    Element.SOLAR: {Element.CRYO,  Element.VOID},
    Element.CRYO:  {Element.FLUX,  Element.ION},
    Element.FLUX:  {Element.VOID,  Element.SOLAR},
    Element.ION:   {Element.SOLAR, Element.FLUX},
    Element.VOID:  {Element.ION,   Element.CRYO},
}

WEAK_AGAINST = {
    Element.SOLAR: {Element.FLUX,  Element.ION},
    Element.CRYO:  {Element.VOID,  Element.SOLAR},
    Element.FLUX:  {Element.ION,   Element.CRYO},
    Element.ION:   {Element.CRYO,  Element.VOID},
    Element.VOID:  {Element.SOLAR, Element.FLUX},
}

ELEMENT_COLORS = {
    Element.SOLAR: {
        "primary":   C.SOLAR_PRIMARY,
        "secondary": C.SOLAR_SECONDARY,
        "glow":      C.SOLAR_GLOW,
        "name":      "Solar",
    },
    Element.CRYO: {
        "primary":   C.CRYO_PRIMARY,
        "secondary": C.CRYO_SECONDARY,
        "glow":      C.CRYO_GLOW,
        "name":      "Cryo",
    },
    Element.FLUX: {
        "primary":   C.FLUX_PRIMARY,
        "secondary": C.FLUX_SECONDARY,
        "glow":      C.FLUX_GLOW,
        "name":      "Flux",
    },
    Element.ION: {
        "primary":   C.ION_PRIMARY,
        "secondary": C.ION_SECONDARY,
        "glow":      C.ION_GLOW,
        "name":      "Ion",
    },
    Element.VOID: {
        "primary":   C.VOID_PRIMARY,
        "secondary": C.VOID_SECONDARY,
        "glow":      C.VOID_GLOW,
        "name":      "Void",
    },
}

def get_damage_multiplier(attacker_element, target_element):
    """Return 2.0 if attacker is strong against target, 0.5 if weak, else 1.0."""
    if attacker_element is None or target_element is None:
        return 1.0
    if target_element in STRONG_AGAINST[attacker_element]:
        return 2.0
    if target_element in WEAK_AGAINST[attacker_element]:
        return 0.5
    return 1.0

def get_element_primary_color(element):
    return ELEMENT_COLORS[element]["primary"]

def get_element_glow_color(element):
    return ELEMENT_COLORS[element]["glow"]

def get_element_name(element):
    return ELEMENT_COLORS[element]["name"]

def draw_elemental_glow(screen, position, radius, element):
    t = pygame.time.get_ticks() / 1000.0
    pulse = (math.sin(t * 2.2) + 1) / 2
    colors = ELEMENT_COLORS[element]
    glow_rgb = colors["glow"]
    primary_rgb = colors["primary"]
    glow_radius = int(radius * (1.38 + 0.14 * pulse))
    surf_size = glow_radius * 2 + 10
    surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
    c = surf_size // 2
    glow_alpha = int(55 + 38 * pulse)
    pygame.draw.circle(surf, (*glow_rgb, glow_alpha), (c, c), glow_radius)
    ring_alpha = int(195 + 50 * pulse)
    ring_width = max(2, int(radius * 0.15))
    inner_ring_r = max(ring_width + 1, int(radius * 1.12))
    pygame.draw.circle(surf, (*primary_rgb, ring_alpha), (c, c), inner_ring_r, ring_width)
    screen.blit(surf, surf.get_rect(center=(int(position.x), int(position.y))))

def draw_elemental_glow_poly(screen, corners, element):
    t = pygame.time.get_ticks() / 1000.0
    pulse = (math.sin(t * 2.2) + 1) / 2
    colors = ELEMENT_COLORS[element]
    glow_rgb = colors["glow"]
    primary_rgb = colors["primary"]
    pad = 18
    min_x = min(c.x for c in corners)
    max_x = max(c.x for c in corners)
    min_y = min(c.y for c in corners)
    max_y = max(c.y for c in corners)
    ox = int(min_x) - pad
    oy = int(min_y) - pad
    w = int(max_x - min_x) + pad * 2
    h = int(max_y - min_y) + pad * 2
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    local = [(c.x - ox, c.y - oy) for c in corners]
    glow_alpha = int(55 + 38 * pulse)
    pygame.draw.polygon(surf, (*glow_rgb, glow_alpha), local)
    ring_alpha = int(195 + 50 * pulse)
    pygame.draw.polygon(surf, (*primary_rgb, ring_alpha), local, 3)
    screen.blit(surf, (ox, oy))
