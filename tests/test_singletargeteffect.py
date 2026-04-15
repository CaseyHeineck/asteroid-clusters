from systems.gameplayeffect import SingleTargetEffect, PlasmaBurnSTE

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