from ui.endgamereport import CombatStats

# --- add_damage ---
def test_add_damage_records_amount():
    stats = CombatStats()
    stats.add_damage("player", 50)
    assert stats.damage_dealt["player"] == 50

def test_add_damage_accumulates():
    stats = CombatStats()
    stats.add_damage("player", 30)
    stats.add_damage("player", 20)
    assert stats.damage_dealt["player"] == 50

def test_add_damage_ignores_zero():
    stats = CombatStats()
    stats.add_damage("player", 0)
    assert "player" not in stats.damage_dealt

def test_add_damage_ignores_negative():
    stats = CombatStats()
    stats.add_damage("player", -10)
    assert "player" not in stats.damage_dealt

# --- add_kill ---
def test_add_kill_records_first_kill():
    stats = CombatStats()
    stats.add_kill("kinetic_drone")
    assert stats.kills["kinetic_drone"] == 1

def test_add_kill_accumulates():
    stats = CombatStats()
    stats.add_kill("kinetic_drone")
    stats.add_kill("kinetic_drone")
    assert stats.kills["kinetic_drone"] == 2

# --- add_overkill ---
def test_add_overkill_records_first_overkill():
    stats = CombatStats()
    stats.add_overkill("laser_drone")
    assert stats.overkills["laser_drone"] == 1

def test_add_overkill_accumulates():
    stats = CombatStats()
    stats.add_overkill("laser_drone")
    stats.add_overkill("laser_drone")
    assert stats.overkills["laser_drone"] == 2

# --- add_absorbed ---
def test_add_absorbed_records_amount():
    stats = CombatStats()
    stats.add_absorbed("player_shield", 8)
    assert stats.damage_absorbed["player_shield"] == 8

def test_add_absorbed_ignores_zero():
    stats = CombatStats()
    stats.add_absorbed("player_shield", 0)
    assert "player_shield" not in stats.damage_absorbed

# --- add_repaired ---
def test_add_repaired_records_amount():
    stats = CombatStats()
    stats.add_repaired("sentinel_drone", 2)
    assert stats.shield_repaired["sentinel_drone"] == 2

# --- record_damage_event ---
def test_record_damage_event_tracks_actual_damage():
    stats = CombatStats()
    stats.record_damage_event(source="player", health_before=10, attempted_damage=4)
    assert stats.damage_dealt["player"] == 4

def test_record_damage_event_caps_at_health_before():
    # Can't deal more damage than the target had health
    stats = CombatStats()
    stats.record_damage_event(source="player", health_before=5, attempted_damage=100)
    assert stats.damage_dealt["player"] == 5

def test_record_damage_event_records_kill_when_lethal():
    stats = CombatStats()
    stats.record_damage_event(source="player", health_before=10, attempted_damage=10)
    assert stats.kills.get("player", 0) == 1

def test_record_damage_event_no_kill_when_not_lethal():
    stats = CombatStats()
    stats.record_damage_event(source="player", health_before=10, attempted_damage=5)
    assert "player" not in stats.kills

def test_record_damage_event_records_overkill_flag():
    stats = CombatStats()
    stats.record_damage_event(source="laser_drone", health_before=10, attempted_damage=10,
        overkill=True)
    assert stats.overkills.get("laser_drone", 0) == 1

def test_record_damage_event_kill_not_overkill_when_flag_false():
    stats = CombatStats()
    stats.record_damage_event(source="player", health_before=10, attempted_damage=10,
        overkill=False)
    assert stats.kills.get("player", 0) == 1
    assert "player" not in stats.overkills

def test_record_damage_event_ignores_zero_health_before():
    stats = CombatStats()
    stats.record_damage_event(source="player", health_before=0, attempted_damage=10)
    assert "player" not in stats.damage_dealt

def test_record_damage_event_ignores_zero_attempted_damage():
    stats = CombatStats()
    stats.record_damage_event(source="player", health_before=10, attempted_damage=0)
    assert "player" not in stats.damage_dealt

def test_record_damage_event_tracks_multiple_sources_separately():
    stats = CombatStats()
    stats.record_damage_event(source="player", health_before=10, attempted_damage=5)
    stats.record_damage_event(source="kinetic_drone", health_before=10, attempted_damage=3)
    assert stats.damage_dealt["player"] == 5
    assert stats.damage_dealt["kinetic_drone"] == 3
