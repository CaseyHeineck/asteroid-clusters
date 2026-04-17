import pytest
from ui.display import Display

def make_display():
    return Display(0, 0)

# --- update_score ---
def test_update_score_adds_to_score():
    d = make_display()
    d.update_score(100)
    assert d.score == 100

def test_update_score_accumulates_across_calls():
    d = make_display()
    d.update_score(50)
    d.update_score(30)
    assert d.score == 80

def test_update_score_clamps_at_zero_when_negative():
    d = make_display()
    d.update_score(-500)
    assert d.score == 0

def test_update_score_reduces_when_partial_negative_delta():
    d = make_display()
    d.update_score(100)
    d.update_score(-30)
    assert d.score == 70

def test_update_score_does_not_go_below_zero_after_reduction():
    d = make_display()
    d.update_score(20)
    d.update_score(-100)
    assert d.score == 0

# --- update_player_lives ---
def test_update_player_lives_stores_value():
    d = make_display()
    d.update_player_lives(2)
    assert d.player_lives == 2

def test_update_player_lives_stores_zero():
    d = make_display()
    d.update_player_lives(0)
    assert d.player_lives == 0

# --- update_level ---
def test_update_level_stores_level():
    d = make_display()
    d.update_level(5, 200, 300)
    assert d.level == 5

def test_update_level_stores_xp_current():
    d = make_display()
    d.update_level(3, 150, 400)
    assert d.xp_current == 150

def test_update_level_stores_xp_needed():
    d = make_display()
    d.update_level(3, 0, 400)
    assert d.xp_needed == 400

def test_update_level_clamps_xp_needed_to_1_when_zero():
    d = make_display()
    d.update_level(3, 0, 0)
    assert d.xp_needed == 1

def test_update_level_sets_level_up_timer_on_increase():
    d = make_display()
    d.update_level(2, 0, 100)
    assert d.level_up_timer > 0

def test_update_level_timer_equals_duration_on_increase():
    d = make_display()
    d.update_level(2, 0, 100)
    assert d.level_up_timer == d.level_up_duration

def test_update_level_does_not_set_timer_on_same_level():
    d = make_display()
    d.update_level(1, 0, 100)
    assert d.level_up_timer == 0.0

def test_update_level_does_not_set_timer_on_lower_level():
    d = make_display()
    d.update_level(5, 0, 100)
    d.level_up_timer = 0.0
    d.update_level(3, 0, 100)
    assert d.level_up_timer == 0.0

# --- update_essence ---
def test_update_essence_stores_value():
    d = make_display()
    d.update_essence(42)
    assert d.essence == 42

def test_update_essence_overwrites_previous_value():
    d = make_display()
    d.update_essence(10)
    d.update_essence(99)
    assert d.essence == 99

# --- update_elemental_essence ---
def test_update_elemental_essence_stores_value():
    d = make_display()
    d.update_elemental_essence(7)
    assert d.elemental_essence == 7

# --- show_banish_notify ---
def test_show_banish_notify_stores_text():
    d = make_display()
    d.show_banish_notify("IMPACT")
    assert d.banish_notify_text == "IMPACT"

def test_show_banish_notify_sets_timer_to_duration():
    d = make_display()
    d.show_banish_notify("BURN")
    assert d.banish_notify_timer == d.banish_notify_duration

# --- update (timers) ---
def test_update_decrements_level_up_timer():
    d = make_display()
    d.level_up_timer = 1.0
    d.update(0.4)
    assert d.level_up_timer == pytest.approx(0.6, abs=0.001)

def test_update_clamps_level_up_timer_at_zero():
    d = make_display()
    d.level_up_timer = 0.2
    d.update(1.0)
    assert d.level_up_timer == 0.0

def test_update_does_not_decrement_level_up_timer_when_zero():
    d = make_display()
    d.level_up_timer = 0.0
    d.update(0.5)
    assert d.level_up_timer == 0.0

def test_update_decrements_banish_notify_timer():
    d = make_display()
    d.banish_notify_timer = 1.0
    d.update(0.3)
    assert d.banish_notify_timer == pytest.approx(0.7, abs=0.001)

def test_update_clamps_banish_notify_timer_at_zero():
    d = make_display()
    d.banish_notify_timer = 0.1
    d.update(5.0)
    assert d.banish_notify_timer == 0.0

def test_update_does_not_decrement_banish_notify_timer_when_zero():
    d = make_display()
    d.banish_notify_timer = 0.0
    d.update(0.5)
    assert d.banish_notify_timer == 0.0

# --- update_life_regen_state ---
def test_update_life_regen_state_stores_regen_flag_true():
    d = make_display()
    d.update_life_regen_state(True, 5.0, 3)
    assert d.life_regen is True

def test_update_life_regen_state_stores_regen_flag_false():
    d = make_display()
    d.update_life_regen_state(False, 0.0, 3)
    assert d.life_regen is False

def test_update_life_regen_state_stores_timer():
    d = make_display()
    d.update_life_regen_state(True, 5.0, 3)
    assert d.life_regen_timer == 5.0

def test_update_life_regen_state_stores_max_lives():
    d = make_display()
    d.update_life_regen_state(False, 0.0, 5)
    assert d.max_lives == 5

# --- _heart_points ---
def test_heart_points_returns_default_n_points():
    d = make_display()
    pts = d._heart_points(0, 0, 20)
    assert len(pts) == 60

def test_heart_points_returns_custom_n_points():
    d = make_display()
    pts = d._heart_points(0, 0, 20, n=30)
    assert len(pts) == 30

def test_heart_points_each_point_is_a_tuple_of_two():
    d = make_display()
    pts = d._heart_points(0, 0, 20)
    for pt in pts:
        assert len(pt) == 2
