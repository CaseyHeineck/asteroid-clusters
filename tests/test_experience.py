from core import constants as C
from systems.experience import ExperienceSystem

class FakeHUD:
    def update_level(self, level, xp_current, xp_needed): pass

class FakeGame:
    HUD = FakeHUD()
    def __init__(self):
        self.entered_drone_choice = False
    def enter_drone_choice(self):
        self.entered_drone_choice = True

# --- Initial state ---
def test_starts_at_level_1():
    exp = ExperienceSystem(None)
    assert exp.level == 1

def test_starts_with_zero_total_xp():
    exp = ExperienceSystem(None)
    assert exp.total_xp == 0

def test_starts_with_no_choices_pending():
    exp = ExperienceSystem(None)
    assert exp.choices_pending == 0

# --- xp_to_reach_level ---
def test_xp_to_reach_level_1_is_zero():
    exp = ExperienceSystem(None)
    assert exp.xp_to_reach_level(1) == 0

def test_xp_to_reach_level_2_is_positive():
    exp = ExperienceSystem(None)
    assert exp.xp_to_reach_level(2) > 0

def test_xp_to_reach_level_increases_each_level():
    exp = ExperienceSystem(None)
    for level in range(2, 6):
        assert exp.xp_to_reach_level(level) > exp.xp_to_reach_level(level - 1)

def test_xp_to_reach_level_cap_equals_past_cap():
    exp = ExperienceSystem(None)
    assert exp.xp_to_reach_level(C.EXP_LEVEL_CAP + 1) == exp.xp_to_reach_level(C.EXP_LEVEL_CAP + 5)

# --- xp_this_level ---
def test_xp_this_level_starts_at_zero():
    exp = ExperienceSystem(None)
    assert exp.xp_this_level() == 0

# --- xp_needed_this_level ---
def test_xp_needed_this_level_is_positive_at_level_1():
    exp = ExperienceSystem(None)
    assert exp.xp_needed_this_level() > 0

def test_xp_needed_this_level_matches_threshold_gap():
    exp = ExperienceSystem(None)
    expected = exp.xp_to_reach_level(2) - exp.xp_to_reach_level(1)
    assert exp.xp_needed_this_level() == expected

def test_xp_needed_at_level_cap_is_zero():
    exp = ExperienceSystem(None)
    exp.level = C.EXP_LEVEL_CAP
    assert exp.xp_needed_this_level() == 0

# --- is_drone_choice_level ---
def test_level_2_is_a_drone_choice_level():
    exp = ExperienceSystem(None)
    assert exp.is_drone_choice_level(2)

def test_level_4_is_a_drone_choice_level():
    exp = ExperienceSystem(None)
    assert exp.is_drone_choice_level(C.EXP_DRONE_CHOICE_INTERVAL)

def test_level_8_is_a_drone_choice_level():
    exp = ExperienceSystem(None)
    assert exp.is_drone_choice_level(C.EXP_DRONE_CHOICE_INTERVAL * 2)

def test_level_12_is_a_drone_choice_level():
    exp = ExperienceSystem(None)
    assert exp.is_drone_choice_level(C.EXP_DRONE_CHOICE_INTERVAL * 3)

def test_level_1_is_not_a_drone_choice_level():
    exp = ExperienceSystem(None)
    assert not exp.is_drone_choice_level(1)

def test_level_3_is_not_a_drone_choice_level():
    exp = ExperienceSystem(None)
    assert not exp.is_drone_choice_level(3)

def test_just_below_interval_is_not_a_drone_choice_level():
    exp = ExperienceSystem(None)
    assert not exp.is_drone_choice_level(C.EXP_DRONE_CHOICE_INTERVAL - 1)

# --- add_xp ---
def test_add_xp_increases_total_xp():
    exp = ExperienceSystem(FakeGame())
    exp.add_xp(10)
    assert exp.total_xp == 10

def test_add_xp_at_cap_is_no_op():
    exp = ExperienceSystem(FakeGame())
    exp.level = C.EXP_LEVEL_CAP
    exp.add_xp(9999)
    assert exp.total_xp == 0

def test_add_xp_triggers_level_up():
    exp = ExperienceSystem(FakeGame())
    exp.add_xp(exp.xp_to_reach_level(2))
    assert exp.level == 2

def test_add_xp_does_not_exceed_level_cap():
    exp = ExperienceSystem(FakeGame())
    exp.add_xp(exp.xp_to_reach_level(C.EXP_LEVEL_CAP + 1))
    assert exp.level == C.EXP_LEVEL_CAP

def test_add_xp_multiple_levels_at_once():
    exp = ExperienceSystem(FakeGame())
    exp.add_xp(exp.xp_to_reach_level(5))
    assert exp.level >= 5

def test_add_xp_sets_choices_pending_on_drone_choice_level():
    exp = ExperienceSystem(FakeGame())
    exp.add_xp(exp.xp_to_reach_level(C.EXP_DRONE_EARLY_LEVEL))
    assert exp.choices_pending >= 1

def test_add_xp_no_choice_pending_when_no_pending_drones():
    exp = ExperienceSystem(FakeGame())
    exp.pending_drones = []
    exp.add_xp(exp.xp_to_reach_level(C.EXP_DRONE_EARLY_LEVEL))
    assert exp.choices_pending == 0
