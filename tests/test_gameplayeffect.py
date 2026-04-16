from systems.gameplayeffect import GameplayEffect, PlasmaBurnSTE
from core import constants as C

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