from systems.gameplayeffect import GameplayEffect

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