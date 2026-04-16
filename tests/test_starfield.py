import pygame
from ui.starfield import StarField
from core import constants as C

# --- _generate ---
def test_generate_creates_correct_star_count():
    sf = StarField(star_count=50)
    assert len(sf.stars) == 50

def test_generate_zero_stars():
    sf = StarField(star_count=0)
    assert len(sf.stars) == 0

def test_generate_star_positions_within_screen_bounds():
    sf = StarField(star_count=100)
    for (x, y, radius, brightness) in sf.stars:
        assert 0 <= x <= C.SCREEN_WIDTH
        assert 0 <= y <= C.SCREEN_HEIGHT

def test_generate_star_radius_is_1_or_2():
    sf = StarField(star_count=200)
    for (x, y, radius, brightness) in sf.stars:
        assert radius in (1, 2)

def test_generate_brightness_in_valid_range():
    sf = StarField(star_count=200)
    for (x, y, radius, brightness) in sf.stars:
        assert 60 <= brightness <= 220

# --- update ---
def test_update_shifts_offset_when_player_moves_right():
    sf = StarField(star_count=0)
    sf.update(pygame.Vector2(100, 0), 1.0)
    assert sf.offset_x != 0.0

def test_update_shifts_offset_when_player_moves_down():
    sf = StarField(star_count=0)
    sf.update(pygame.Vector2(0, 100), 1.0)
    assert sf.offset_y != 0.0

def test_update_no_movement_leaves_offset_unchanged():
    sf = StarField(star_count=0)
    sf.update(pygame.Vector2(0, 0), 1.0)
    assert sf.offset_x == 0.0
    assert sf.offset_y == 0.0

def test_update_offset_x_wraps_within_screen_width():
    sf = StarField(star_count=0)
    sf.update(pygame.Vector2(-99999, 0), 1.0)
    assert 0 <= sf.offset_x < C.SCREEN_WIDTH

def test_update_offset_y_wraps_within_screen_height():
    sf = StarField(star_count=0)
    sf.update(pygame.Vector2(0, -99999), 1.0)
    assert 0 <= sf.offset_y < C.SCREEN_HEIGHT
