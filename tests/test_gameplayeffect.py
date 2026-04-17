from core import constants as C
from systems.gameplayeffect import GameplayEffect, PlasmaBurnSTE

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

# --- PlasmaBurnSTE.update ---
def test_plasma_burn_does_not_tick_before_timer_expires():
    effect = PlasmaBurnSTE(damage_per_tick=10, tick_rate=1.0, duration=5.0)
    target = FakeBurnTarget(health=100)
    effect.apply_to(target)
    effect.update(0.5)
    assert target.health == 100

def test_plasma_burn_ticks_when_timer_expires():
    effect = PlasmaBurnSTE(damage_per_tick=10, tick_rate=1.0, duration=5.0)
    target = FakeBurnTarget(health=100)
    effect.apply_to(target)
    effect.update(1.0)
    assert target.health == 90

def test_plasma_burn_calls_pulse_outline_on_tick():
    effect = PlasmaBurnSTE(damage_per_tick=5, tick_rate=1.0, duration=5.0)
    target = FakeBurnTarget(health=100)
    effect.apply_to(target)
    effect.update(1.0)
    assert target.pulsed

def test_plasma_burn_tick_resets_timer():
    effect = PlasmaBurnSTE(damage_per_tick=5, tick_rate=1.0, duration=5.0)
    target = FakeBurnTarget(health=100)
    effect.apply_to(target)
    effect.update(1.0)
    assert effect.tick_timer > 0

def test_plasma_burn_expires_on_lethal_tick():
    effect = PlasmaBurnSTE(damage_per_tick=50, tick_rate=1.0, duration=5.0)
    target = FakeBurnTarget(health=50)
    effect.apply_to(target)
    effect.update(1.0)
    assert effect.expired

def test_plasma_burn_returns_score_on_lethal_tick():
    effect = PlasmaBurnSTE(damage_per_tick=50, tick_rate=1.0, duration=5.0)
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

# --- PlasmaBurnSTE multiple ticks in one update ---
def test_plasma_burn_applies_multiple_ticks_when_dt_exceeds_tick_rate():
    effect = PlasmaBurnSTE(damage_per_tick=5, tick_rate=1.0, duration=10.0)
    target = FakeBurnTarget(health=100)
    effect.apply_to(target)
    effect.update(3.5)
    assert target.health == 85

# --- PlasmaBurnSTE skips tick when target is dead ---
def test_plasma_burn_does_not_tick_when_target_is_dead():
    effect = PlasmaBurnSTE(damage_per_tick=10, tick_rate=1.0, duration=5.0)
    target = FakeBurnTarget(health=100)
    target.alive = lambda: False
    effect.apply_to(target)
    effect.update(2.0)
    assert target.health == 100

# --- PlasmaBurnSTE records to combat_stats ---
def test_plasma_burn_records_damage_event_to_combat_stats():
    stats = FakeCombatStats()
    effect = PlasmaBurnSTE(damage_per_tick=10, tick_rate=1.0, duration=5.0)
    effect.combat_stats = stats
    target = FakeBurnTarget(health=100)
    effect.apply_to(target)
    effect.update(1.0)
    assert len(stats.events) == 1
    assert stats.events[0] == 10