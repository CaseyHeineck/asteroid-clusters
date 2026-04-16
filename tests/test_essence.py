from systems.essence import EssenceSystem

class FakeHUD:
    def update_essence(self, amount): pass
    def update_elemental_essence(self, amount): pass

class FakeGame:
    HUD = FakeHUD()

# --- can_afford ---
def test_can_afford_when_sufficient():
    ess = EssenceSystem(None)
    ess.amount = 50
    assert ess.can_afford(50)

def test_can_afford_more_than_held_is_false():
    ess = EssenceSystem(None)
    ess.amount = 10
    assert not ess.can_afford(50)

def test_can_afford_zero_always_true():
    ess = EssenceSystem(None)
    assert ess.can_afford(0)

# --- can_afford_elemental ---
def test_can_afford_elemental_when_sufficient():
    ess = EssenceSystem(None)
    ess.elemental_amount = 30
    assert ess.can_afford_elemental(30)

def test_can_afford_elemental_more_than_held_is_false():
    ess = EssenceSystem(None)
    ess.elemental_amount = 5
    assert not ess.can_afford_elemental(30)

# --- spend (failure path — no game needed) ---
def test_spend_returns_false_when_insufficient():
    ess = EssenceSystem(None)
    ess.amount = 10
    assert not ess.spend(50)

def test_spend_does_not_change_amount_when_insufficient():
    ess = EssenceSystem(None)
    ess.amount = 10
    ess.spend(50)
    assert ess.amount == 10

def test_spend_elemental_returns_false_when_insufficient():
    ess = EssenceSystem(None)
    ess.elemental_amount = 5
    assert not ess.spend_elemental(30)

def test_spend_elemental_does_not_change_amount_when_insufficient():
    ess = EssenceSystem(None)
    ess.elemental_amount = 5
    ess.spend_elemental(30)
    assert ess.elemental_amount == 5

# --- add / spend (success paths — need FakeGame for HUD calls) ---
def test_add_increases_amount():
    ess = EssenceSystem(FakeGame())
    ess.add(25)
    assert ess.amount == 25

def test_add_accumulates():
    ess = EssenceSystem(FakeGame())
    ess.add(25)
    ess.add(10)
    assert ess.amount == 35

def test_spend_returns_true_when_sufficient():
    ess = EssenceSystem(FakeGame())
    ess.amount = 50
    assert ess.spend(25)

def test_spend_decrements_amount():
    ess = EssenceSystem(FakeGame())
    ess.amount = 50
    ess.spend(25)
    assert ess.amount == 25

def test_add_elemental_increases_elemental_amount():
    ess = EssenceSystem(FakeGame())
    ess.add_elemental(10)
    assert ess.elemental_amount == 10

def test_spend_elemental_returns_true_when_sufficient():
    ess = EssenceSystem(FakeGame())
    ess.elemental_amount = 30
    assert ess.spend_elemental(20)

def test_spend_elemental_decrements_elemental_amount():
    ess = EssenceSystem(FakeGame())
    ess.elemental_amount = 30
    ess.spend_elemental(20)
    assert ess.elemental_amount == 10
