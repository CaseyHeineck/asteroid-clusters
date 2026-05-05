from core import constants as C
from systems.gameplayeffect import GameplayEffect, BurnSTE, SingleTargetEffect

class FakeCombatStats:
    def __init__(self):
        self.events = []
    def record_damage_event(self, source, health_before, attempted_damage):
        self.events.append(attempted_damage)

class FakeBurnTarget:
    def __init__(self, health=100):
        self.health = health
        self.pulsed = False
    def alive(self):
        return True
    def damaged(self, amount):
        self.health -= amount
        return 0 if self.health > 0 else 1
    def pulse_outline(self, color, duration):
        self.pulsed = True

# --- GameplayEffect update ---
def test_duration_decreases_on_update():
    effect = GameplayEffect(duration=2.0)
    effect.update(1.0)
    assert effect.duration == 1.0

def test_duration_timer_is_zero_if_would_be_negative():
    effect = GameplayEffect(duration=1.0)
    effect.update(3.0)
    assert effect.duration == 0.0
    assert effect.expired == True

def test_effect_ends_if_timer_is_zero():
    effect = GameplayEffect(duration=1.0)
    effect.update(1.0)
    assert effect.expired == True

# --- BurnSTE.update ---
def test_plasma_burn_does_not_tick_before_timer_expires():
    effect = BurnSTE(damage_per_tick=10, tick_rate=1.0, duration=5.0)
    target = FakeBurnTarget(health=100)
    effect.apply_to(target)
    effect.update(0.5)
    assert target.health == 100

def test_plasma_burn_ticks_when_timer_expires():
    effect = BurnSTE(damage_per_tick=10, tick_rate=1.0, duration=5.0)
    target = FakeBurnTarget(health=100)
    effect.apply_to(target)
    effect.update(1.0)
    assert target.health == 90

def test_plasma_burn_calls_pulse_outline_on_tick():
    effect = BurnSTE(damage_per_tick=5, tick_rate=1.0, duration=5.0)
    target = FakeBurnTarget(health=100)
    effect.apply_to(target)
    effect.update(1.0)
    assert target.pulsed

def test_plasma_burn_tick_resets_timer():
    effect = BurnSTE(damage_per_tick=5, tick_rate=1.0, duration=5.0)
    target = FakeBurnTarget(health=100)
    effect.apply_to(target)
    effect.update(1.0)
    assert effect.tick_timer > 0

def test_plasma_burn_expires_on_lethal_tick():
    effect = BurnSTE(damage_per_tick=50, tick_rate=1.0, duration=5.0)
    target = FakeBurnTarget(health=50)
    effect.apply_to(target)
    effect.update(1.0)
    assert effect.expired

def test_plasma_burn_returns_score_on_lethal_tick():
    effect = BurnSTE(damage_per_tick=50, tick_rate=1.0, duration=5.0)
    target = FakeBurnTarget(health=50)
    effect.apply_to(target)
    score = effect.update(1.0)
    assert score > 0

# --- GameplayEffect with zero duration (permanent) ---
def test_permanent_effect_zero_duration_never_expires():
    effect = GameplayEffect(duration=0)
    effect.update(100.0)
    assert not effect.expired

def test_permanent_effect_zero_duration_does_not_decrement():
    effect = GameplayEffect(duration=0)
    effect.update(1.0)
    assert effect.duration == 0

# --- BurnSTE multiple ticks in one update ---
def test_plasma_burn_applies_multiple_ticks_when_dt_exceeds_tick_rate():
    effect = BurnSTE(damage_per_tick=5, tick_rate=1.0, duration=10.0)
    target = FakeBurnTarget(health=100)
    effect.apply_to(target)
    effect.update(3.5)
    assert target.health == 85

# --- BurnSTE skips tick when target is dead ---
def test_plasma_burn_does_not_tick_when_target_is_dead():
    effect = BurnSTE(damage_per_tick=10, tick_rate=1.0, duration=5.0)
    target = FakeBurnTarget(health=100)
    target.alive = lambda: False
    effect.apply_to(target)
    effect.update(2.0)
    assert target.health == 100

# --- BurnSTE records to combat_stats ---
def test_plasma_burn_records_damage_event_to_combat_stats():
    stats = FakeCombatStats()
    effect = BurnSTE(damage_per_tick=10, tick_rate=1.0, duration=5.0)
    effect.combat_stats = stats
    target = FakeBurnTarget(health=100)
    effect.apply_to(target)
    effect.update(1.0)
    assert len(stats.events) == 1
    assert stats.events[0] == 10

# --- BurnSTE class variable defaults ---
def test_plasma_burn_tick_rate_override_defaults_to_none():
    BurnSTE.tick_rate_override = None
    assert BurnSTE.tick_rate_override is None

def test_plasma_burn_spread_chance_override_defaults_to_none():
    assert BurnSTE.spread_chance_override is None

def test_plasma_burn_default_tick_rate_equals_constant():
    BurnSTE.tick_rate_override = None
    effect = BurnSTE()
    assert effect.tick_rate == C.PLASMA_BURN_TICK_RATE

def test_plasma_burn_default_spread_chance_equals_constant():
    effect = BurnSTE()
    assert effect.spread_chance == C.PLASMA_BURN_SPREAD_CHANCE

def test_plasma_burn_tick_rate_override_applied_on_construction():
    BurnSTE.tick_rate_override = 0.5
    effect = BurnSTE()
    BurnSTE.tick_rate_override = None
    assert effect.tick_rate == 0.5

def test_plasma_burn_spread_chance_override_applied_on_construction():
    BurnSTE.spread_chance_override = 0.5
    effect = BurnSTE()
    BurnSTE.spread_chance_override = None
    assert effect.spread_chance == 0.5

def test_plasma_burn_explicit_tick_rate_ignores_override():
    BurnSTE.tick_rate_override = 0.25
    effect = BurnSTE(tick_rate=2.0)
    BurnSTE.tick_rate_override = None
    assert effect.tick_rate == 2.0

# --- BurnSTE merge with spread_chance ---
def test_plasma_burn_merge_takes_max_spread_chance():
    e1 = BurnSTE(spread_chance=0.2, tick_rate=1.0, duration=5.0)
    e2 = BurnSTE(spread_chance=0.5, tick_rate=1.0, duration=5.0)
    e1.merge(e2)
    assert e1.spread_chance == 0.5

def test_plasma_burn_merge_keeps_own_spread_chance_when_higher():
    e1 = BurnSTE(spread_chance=0.8, tick_rate=1.0, duration=5.0)
    e2 = BurnSTE(spread_chance=0.3, tick_rate=1.0, duration=5.0)
    e1.merge(e2)
    assert e1.spread_chance == 0.8

# --- BurnSTE handles tuple return from damaged (enemy-style) ---
class FakeTupleTarget:
    def __init__(self, health=100):
        self.health = health
        self.pulsed = False
    def alive(self):
        return self.health > 0
    def damaged(self, amount):
        self.health -= amount
        return (10, 5) if self.health <= 0 else (0, 0)
    def pulse_outline(self, color, duration):
        self.pulsed = True

def test_plasma_burn_handles_tuple_damaged_return_without_crash():
    effect = BurnSTE(damage_per_tick=50, tick_rate=1.0, duration=5.0)
    target = FakeTupleTarget(health=50)
    effect.apply_to(target)
    score = effect.update(1.0)
    assert score == 10

def test_plasma_burn_expires_on_lethal_tick_with_tuple_target():
    effect = BurnSTE(damage_per_tick=50, tick_rate=1.0, duration=5.0)
    target = FakeTupleTarget(health=50)
    effect.apply_to(target)
    effect.update(1.0)
    assert effect.expired

# --- Stackable flag ---
def test_single_target_effect_is_not_stackable():
    assert SingleTargetEffect.stackable is False

def test_plasma_burn_is_stackable():
    assert BurnSTE.stackable is True