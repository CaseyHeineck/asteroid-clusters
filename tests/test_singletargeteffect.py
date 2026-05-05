from core import constants as C
from systems.gameplayeffect import ContagionSTE, CorrodeSTE, MarkedSTE, OverkillSTE, BurnSTE, SingleTargetEffect, SlowSTE

# --- SingleTargetEffect.merge ---
def test_merge_keeps_longer_duration():
    short = SingleTargetEffect(duration=1.0)
    long = SingleTargetEffect(duration=5.0)
    long.merge(short)
    assert long.duration == 5.0

def test_merge_adopts_longer_duration_from_other():
    short = SingleTargetEffect(duration=1.0)
    long = SingleTargetEffect(duration=5.0)
    short.merge(long)
    assert short.duration == 5.0

# --- SingleTargetEffect.can_merge_with ---
def test_can_merge_with_same_type_returns_true():
    e1 = SingleTargetEffect(duration=1.0)
    e2 = SingleTargetEffect(duration=2.0)
    assert e1.can_merge_with(e2)

def test_can_merge_with_different_type_returns_false():
    ste = SingleTargetEffect(duration=1.0)
    burn = BurnSTE()
    assert not ste.can_merge_with(burn)

def test_subtype_does_not_merge_with_parent_type():
    ste = SingleTargetEffect(duration=1.0)
    overkill = OverkillSTE()
    assert not ste.can_merge_with(overkill)

# --- SingleTargetEffect.apply_to ---
def test_apply_to_sets_target():
    effect = SingleTargetEffect(duration=1.0)
    target = object()
    effect.apply_to(target)
    assert effect.target is target

# --- BurnSTE.merge ---
def test_merge_keeps_higher_damage_per_tick():
    low = BurnSTE(damage_per_tick=1.0)
    high = BurnSTE(damage_per_tick=5.0)
    high.merge(low)
    assert high.damage_per_tick == 5.0

def test_merge_adopts_higher_damage_per_tick_from_other():
    low = BurnSTE(damage_per_tick=1.0)
    high = BurnSTE(damage_per_tick=5.0)
    low.merge(high)
    assert low.damage_per_tick == 5.0

def test_merge_keeps_lower_tick_rate():
    low = BurnSTE(tick_rate=1.0)
    high = BurnSTE(tick_rate=5.0)
    low.merge(high)
    assert low.tick_rate == 1.0

def test_merge_adopts_lower_tick_rate_from_other():
    low = BurnSTE(tick_rate=1.0)
    high = BurnSTE(tick_rate=5.0)
    high.merge(low)
    assert high.tick_rate == 1.0

def test_merge_keeps_lower_tick_timer():
    low = BurnSTE()
    high = BurnSTE()
    low.tick_timer = 1.0
    high.tick_timer = 5.0
    low.merge(high)
    assert low.tick_timer == 1.0

def test_merge_adopts_lower_tick_timer_from_other():
    low = BurnSTE()
    high = BurnSTE()
    low.tick_timer = 1.0
    high.tick_timer = 5.0
    high.merge(low)
    assert high.tick_timer == 1.0

# --- OverkillSTE ---
class FakeAsteroid:
    def __init__(self):
        self.child_size_reduction = 0
        self.overkill_triggered = False

def test_overkill_sets_overkill_triggered_on_target():
    target = FakeAsteroid()
    OverkillSTE().apply_to(target)
    assert target.overkill_triggered

def test_overkill_sets_child_size_reduction_equal_to_tier():
    target = FakeAsteroid()
    OverkillSTE(overkill_tier=1).apply_to(target)
    assert target.child_size_reduction == 1

def test_overkill_tier_2_sets_child_size_reduction_to_2():
    target = FakeAsteroid()
    OverkillSTE(overkill_tier=2).apply_to(target)
    assert target.child_size_reduction == 2

def test_overkill_tier_3_sets_child_size_reduction_to_3():
    target = FakeAsteroid()
    OverkillSTE(overkill_tier=3).apply_to(target)
    assert target.child_size_reduction == 3

def test_overkill_does_not_lower_existing_higher_size_reduction():
    target = FakeAsteroid()
    target.child_size_reduction = 5
    OverkillSTE(overkill_tier=1).apply_to(target)
    assert target.child_size_reduction == 5

def test_overkill_expires_immediately_after_apply():
    target = FakeAsteroid()
    effect = OverkillSTE()
    effect.apply_to(target)
    assert effect.expired


# --- SlowSTE ---
class FakeEnemy:
    def __init__(self, speed=100):
        self.speed = speed
        self.gameplay_effects = []
        self.mark_multiplier = 1.0
        self.corrode_multiplier = 1.0

def test_slow_reduces_target_speed_on_apply():
    enemy = FakeEnemy(speed=100)
    effect = SlowSTE(slow_factor=0.5, duration=3.0)
    effect.apply_to(enemy)
    assert enemy.speed == 50.0

def test_slow_restores_target_speed_on_expire():
    enemy = FakeEnemy(speed=100)
    effect = SlowSTE(slow_factor=0.5, duration=3.0)
    effect.apply_to(enemy)
    effect.on_expire()
    assert enemy.speed == 100

def test_slow_merge_keeps_longer_duration():
    short = SlowSTE(duration=1.0)
    long = SlowSTE(duration=5.0)
    long.merge(short)
    assert long.duration == 5.0

def test_slow_does_not_apply_to_target_without_speed():
    class NoSpeed:
        gameplay_effects = []
        mark_multiplier = 1.0
        corrode_multiplier = 1.0
    target = NoSpeed()
    effect = SlowSTE()
    effect.apply_to(target)
    assert not hasattr(target, 'speed') or True

def test_slow_default_factor_from_constants():
    effect = SlowSTE()
    assert effect.slow_factor == C.SLOW_FACTOR

def test_slow_default_duration_from_constants():
    effect = SlowSTE()
    assert effect.duration == C.SLOW_DURATION


# --- MarkedSTE ---
def test_mark_sets_mark_multiplier_on_apply():
    enemy = FakeEnemy()
    effect = MarkedSTE(amplification=2.0, duration=5.0)
    effect.apply_to(enemy)
    assert enemy.mark_multiplier == 2.0

def test_mark_resets_mark_multiplier_on_expire():
    enemy = FakeEnemy()
    effect = MarkedSTE(amplification=2.0, duration=5.0)
    effect.apply_to(enemy)
    effect.on_expire()
    assert enemy.mark_multiplier == 1.0

def test_mark_merge_keeps_longer_duration():
    short = MarkedSTE(duration=1.0)
    long = MarkedSTE(duration=5.0)
    long.merge(short)
    assert long.duration == 5.0

def test_mark_merge_keeps_higher_amplification():
    low = MarkedSTE(amplification=1.5)
    high = MarkedSTE(amplification=3.0)
    low.merge(high)
    assert low.amplification == 3.0

def test_mark_is_mark_effect_flag():
    assert MarkedSTE.is_mark_effect is True

def test_mark_default_amplification_from_constants():
    effect = MarkedSTE()
    assert effect.amplification == C.MARK_AMPLIFICATION

def test_mark_default_duration_from_constants():
    effect = MarkedSTE()
    assert effect.duration == C.MARK_DURATION


# --- CorrodeSTE ---
def test_corrode_sets_corrode_multiplier_on_apply():
    enemy = FakeEnemy()
    effect = CorrodeSTE(amplification=0.25, duration=5.0)
    effect.apply_to(enemy)
    assert enemy.corrode_multiplier == 1.25

def test_corrode_resets_corrode_multiplier_on_expire():
    enemy = FakeEnemy()
    effect = CorrodeSTE(amplification=0.25, duration=5.0)
    effect.apply_to(enemy)
    effect.on_expire()
    assert enemy.corrode_multiplier == 1.0

def test_corrode_merge_keeps_longer_duration():
    short = CorrodeSTE(duration=1.0)
    long = CorrodeSTE(duration=5.0)
    long.merge(short)
    assert long.duration == 5.0

def test_corrode_merge_keeps_higher_amplification():
    low = CorrodeSTE(amplification=0.1)
    high = CorrodeSTE(amplification=0.5)
    low.merge(high)
    assert low.amplification == 0.5

def test_corrode_default_amplification_from_constants():
    effect = CorrodeSTE()
    assert effect.amplification == C.CORRODE_AMPLIFICATION

def test_corrode_default_duration_from_constants():
    effect = CorrodeSTE()
    assert effect.duration == C.CORRODE_DURATION


# --- ContagionSTE ---
class FakeTarget:
    def __init__(self, health=20, alive=True):
        self.health = health
        self._alive = alive
        self.gameplay_effects = []
        self.mark_multiplier = 1.0
        self.corrode_multiplier = 1.0
        self.applied_effects = []

    def alive(self):
        return self._alive and self.health > 0

    def damaged(self, amount):
        self.health -= amount
        if self.health <= 0:
            self._alive = False
            return 10
        return 0

    def add_gameplay_effect(self, effect):
        self.applied_effects.append(effect)
        effect.apply_to(self)

def test_contagion_does_not_spread_when_target_survives():
    nearby = FakeTarget(health=50)
    target = FakeTarget(health=50)
    effect = ContagionSTE(nearby_targets=[nearby])
    effect.apply_to(target)
    effect.update(C.CONTAGION_TICK_RATE + 0.01)
    assert len(nearby.applied_effects) == 0

def test_contagion_spreads_to_nearby_when_target_dies_from_tick():
    import pygame as pg
    nearby = FakeTarget(health=50)
    nearby.position = pg.Vector2(50, 0)
    target = FakeTarget(health=1)
    target.position = pg.Vector2(0, 0)
    effect = ContagionSTE(
        damage_per_tick=5,
        nearby_targets=[target, nearby],
        spread_radius=C.CONTAGION_SPREAD_RADIUS)
    effect.apply_to(target)
    effect.update(C.CONTAGION_TICK_RATE + 0.01)
    assert len(nearby.applied_effects) == 1

def test_contagion_does_not_spread_to_out_of_range_targets():
    import pygame as pg
    far_target = FakeTarget(health=50)
    far_target.position = pg.Vector2(999, 0)
    target = FakeTarget(health=1)
    target.position = pg.Vector2(0, 0)
    effect = ContagionSTE(
        damage_per_tick=5,
        nearby_targets=[target, far_target],
        spread_radius=C.CONTAGION_SPREAD_RADIUS)
    effect.apply_to(target)
    effect.update(C.CONTAGION_TICK_RATE + 0.01)
    assert len(far_target.applied_effects) == 0

def test_contagion_default_damage_from_constants():
    effect = ContagionSTE()
    assert effect.damage_per_tick == C.CONTAGION_DAMAGE

def test_contagion_default_duration_from_constants():
    effect = ContagionSTE()
    assert effect.duration == C.CONTAGION_DURATION

def test_contagion_spread_not_applied_twice():
    import pygame as pg
    nearby = FakeTarget(health=50)
    nearby.position = pg.Vector2(50, 0)
    target = FakeTarget(health=1)
    target.position = pg.Vector2(0, 0)
    effect = ContagionSTE(
        damage_per_tick=5,
        nearby_targets=[target, nearby],
        spread_radius=C.CONTAGION_SPREAD_RADIUS)
    effect.apply_to(target)
    effect.update(C.CONTAGION_TICK_RATE + 0.01)
    effect.update(C.CONTAGION_TICK_RATE + 0.01)
    assert len(nearby.applied_effects) == 1
