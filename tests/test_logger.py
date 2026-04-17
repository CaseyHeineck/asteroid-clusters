import core.logger as logger_module
import json
import os
import pytest
from core.logger import log_event

@pytest.fixture(autouse=True)
def reset_logger_state():
    logger_module._event_log_initialized = False
    logger_module._frame_count = 0
    yield
    logger_module._event_log_initialized = False
    logger_module._frame_count = 0

# --- log_event ---
def test_log_event_creates_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    log_event("test_type")
    assert (tmp_path / "game_events.jsonl").exists()

def test_log_event_writes_event_type(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    log_event("asteroid_killed")
    line = (tmp_path / "game_events.jsonl").read_text().strip()
    entry = json.loads(line)
    assert entry["type"] == "asteroid_killed"

def test_log_event_includes_extra_details(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    log_event("asteroid_split", size=3, element="cryo")
    line = (tmp_path / "game_events.jsonl").read_text().strip()
    entry = json.loads(line)
    assert entry["size"] == 3
    assert entry["element"] == "cryo"

def test_log_event_includes_timestamp_field(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    log_event("test_type")
    line = (tmp_path / "game_events.jsonl").read_text().strip()
    entry = json.loads(line)
    assert "timestamp" in entry

def test_log_event_includes_frame_field(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    log_event("test_type")
    line = (tmp_path / "game_events.jsonl").read_text().strip()
    entry = json.loads(line)
    assert "frame" in entry

def test_log_event_appends_multiple_events(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    log_event("first")
    log_event("second")
    lines = (tmp_path / "game_events.jsonl").read_text().strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["type"] == "first"
    assert json.loads(lines[1])["type"] == "second"

def test_log_event_first_call_overwrites_existing_file(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "game_events.jsonl").write_text("stale data\n")
    log_event("fresh")
    lines = (tmp_path / "game_events.jsonl").read_text().strip().splitlines()
    assert len(lines) == 1
    assert json.loads(lines[0])["type"] == "fresh"
