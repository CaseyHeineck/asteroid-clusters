from systems.gameplayeffect import SingleTargetEffect, PlasmaBurnSTE, OverkillSTE

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
    burn = PlasmaBurnSTE()
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

# --- PlasmaBurnSTE.merge ---
def test_merge_keeps_higher_damage_per_tick():
    low = PlasmaBurnSTE(damage_per_tick=1.0)
    high = PlasmaBurnSTE(damage_per_tick=5.0)
    high.merge(low)
    assert high.damage_per_tick == 5.0

def test_merge_adopts_higher_damage_per_tick_from_other():
    low = PlasmaBurnSTE(damage_per_tick=1.0)
    high = PlasmaBurnSTE(damage_per_tick=5.0)
    low.merge(high)
    assert low.damage_per_tick == 5.0

def test_merge_keeps_lower_tick_rate():
    low = PlasmaBurnSTE(tick_rate=1.0)
    high = PlasmaBurnSTE(tick_rate=5.0)
    low.merge(high)
    assert low.tick_rate == 1.0

def test_merge_adopts_lower_tick_rate_from_other():
    low = PlasmaBurnSTE(tick_rate=1.0)
    high = PlasmaBurnSTE(tick_rate=5.0)
    high.merge(low)
    assert high.tick_rate == 1.0

def test_merge_keeps_lower_tick_timer():
    low = PlasmaBurnSTE()
    high = PlasmaBurnSTE()
    low.tick_timer = 1.0
    high.tick_timer = 5.0
    low.merge(high)
    assert low.tick_timer == 1.0

def test_merge_adopts_lower_tick_timer_from_other():
    low = PlasmaBurnSTE()
    high = PlasmaBurnSTE()
    low.tick_timer = 1.0
    high.tick_timer = 5.0
    high.merge(low)
    assert high.tick_timer == 1.0

# --- OverkillSTE ---
class FakeAsteroid:
    def __init__(self):
        self.child_size_reduction = 0
        self.child_count_reduction = 0
        self.overkill_triggered = False

def test_overkill_sets_overkill_triggered_on_target():
    target = FakeAsteroid()
    OverkillSTE().apply_to(target)
    assert target.overkill_triggered

def test_overkill_sets_child_size_reduction():
    target = FakeAsteroid()
    OverkillSTE(child_size_reduction=1).apply_to(target)
    assert target.child_size_reduction == 1

def test_overkill_sets_child_count_reduction():
    target = FakeAsteroid()
    OverkillSTE(child_count_reduction=1).apply_to(target)
    assert target.child_count_reduction == 1

def test_overkill_does_not_lower_existing_higher_size_reduction():
    target = FakeAsteroid()
    target.child_size_reduction = 5
    OverkillSTE(child_size_reduction=1).apply_to(target)
    assert target.child_size_reduction == 5

def test_overkill_does_not_lower_existing_higher_count_reduction():
    target = FakeAsteroid()
    target.child_count_reduction = 3
    OverkillSTE(child_count_reduction=1).apply_to(target)
    assert target.child_count_reduction == 3

def test_overkill_expires_immediately_after_apply():
    target = FakeAsteroid()
    effect = OverkillSTE()
    effect.apply_to(target)
    assert effect.expired
