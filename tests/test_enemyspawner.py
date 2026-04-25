import pygame
import pytest
from core import constants as C
from core.element import ALL_ELEMENTS
from entities.enemy import KineticEnemy, PlasmaEnemy
from entities.enemyspawner import EnemySpawner
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

class FakePlayer:
    def __init__(self):
        self.position = pygame.Vector2(C.SCREEN_WIDTH / 2, C.SCREEN_HEIGHT / 2)

def make_game():
    enemies = []
    player = FakePlayer()
    game = SimpleNamespace(
        player=player,
        asteroids=[],
        combat_stats=SimpleNamespace(record_damage_event=lambda **kw: None),
    )
    spawned = []
    def fake_spawn(x, y, p, g):
        e = SimpleNamespace(element=None, position=pygame.Vector2(x, y))
        spawned.append(e)
        return e
    return game, spawned, fake_spawn

# --- EnemySpawner timer ---
def test_spawner_does_not_spawn_before_interval():
    PlasmaEnemy.containers = ()
    EnemySpawner.containers = ()
    game, spawned, _ = make_game()
    spawner = EnemySpawner(game)
    with patch.object(spawner, 'spawn') as mock_spawn:
        spawner.update(C.ENEMY_SPAWN_INTERVAL - 0.1)
        mock_spawn.assert_not_called()

def test_spawner_spawns_at_interval():
    PlasmaEnemy.containers = ()
    EnemySpawner.containers = ()
    game, spawned, _ = make_game()
    spawner = EnemySpawner(game)
    with patch.object(spawner, 'spawn') as mock_spawn:
        spawner.update(C.ENEMY_SPAWN_INTERVAL)
        mock_spawn.assert_called_once()

def test_spawner_resets_timer_after_spawn():
    PlasmaEnemy.containers = ()
    EnemySpawner.containers = ()
    game, _, _ = make_game()
    spawner = EnemySpawner(game)
    with patch.object(spawner, 'spawn') as mock_spawn:
        spawner.update(C.ENEMY_SPAWN_INTERVAL)
        spawner.update(C.ENEMY_SPAWN_INTERVAL - 0.1)
        assert mock_spawn.call_count == 1

def test_spawner_spawns_again_after_second_interval():
    PlasmaEnemy.containers = ()
    EnemySpawner.containers = ()
    game, _, _ = make_game()
    spawner = EnemySpawner(game)
    with patch.object(spawner, 'spawn') as mock_spawn:
        spawner.update(C.ENEMY_SPAWN_INTERVAL)
        spawner.update(C.ENEMY_SPAWN_INTERVAL)
        assert mock_spawn.call_count == 2

# --- EnemySpawner spawn position ---
def test_spawn_position_is_outside_screen_bounds():
    PlasmaEnemy.containers = ()
    EnemySpawner.containers = ()
    game, _, _ = make_game()
    spawner = EnemySpawner(game)
    for _ in range(40):
        x, y = spawner._offscreen_position()
        on_screen = (0 <= x <= C.SCREEN_WIDTH and 0 <= y <= C.SCREEN_HEIGHT)
        assert not on_screen

def test_spawn_position_is_within_margin_of_screen():
    PlasmaEnemy.containers = ()
    EnemySpawner.containers = ()
    game, _, _ = make_game()
    spawner = EnemySpawner(game)
    for _ in range(40):
        x, y = spawner._offscreen_position()
        near = (
            -C.ENEMY_SPAWN_MARGIN <= x <= C.SCREEN_WIDTH + C.ENEMY_SPAWN_MARGIN
            and -C.ENEMY_SPAWN_MARGIN <= y <= C.SCREEN_HEIGHT + C.ENEMY_SPAWN_MARGIN
        )
        assert near

# --- EnemySpawner elemental chance ---
def test_elemental_spawn_sets_element_on_enemy():
    PlasmaEnemy.containers = ()
    EnemySpawner.containers = ()
    game, _, _ = make_game()
    spawner = EnemySpawner(game)
    enemy_obj = SimpleNamespace(element=None)
    mock_cls = MagicMock(return_value=enemy_obj)
    with patch.object(spawner, '_pick_enemy_class', return_value=mock_cls), \
         patch("entities.enemyspawner.random") as mock_rand:
        mock_rand.randint.return_value = 0
        mock_rand.uniform.return_value = 100.0
        mock_rand.random.return_value = 0.0
        mock_rand.choice.return_value = ALL_ELEMENTS[0]
        spawner.spawn()
        assert enemy_obj.element == ALL_ELEMENTS[0]

def test_non_elemental_spawn_leaves_element_none():
    PlasmaEnemy.containers = ()
    EnemySpawner.containers = ()
    game, _, _ = make_game()
    spawner = EnemySpawner(game)
    enemy_obj = SimpleNamespace(element=None)
    mock_cls = MagicMock(return_value=enemy_obj)
    with patch.object(spawner, '_pick_enemy_class', return_value=mock_cls), \
         patch("entities.enemyspawner.random") as mock_rand:
        mock_rand.randint.return_value = 0
        mock_rand.uniform.return_value = 100.0
        mock_rand.random.return_value = 1.0
        spawner.spawn()
        assert enemy_obj.element is None

def test_spawner_sets_airspace_to_current_space_on_spawn():
    PlasmaEnemy.containers = ()
    EnemySpawner.containers = ()
    game, _, _ = make_game()
    fake_space = object()
    game.current_space = fake_space
    spawner = EnemySpawner(game)
    enemy_obj = SimpleNamespace(element=None)
    mock_cls = MagicMock(return_value=enemy_obj)
    with patch.object(spawner, '_pick_enemy_class', return_value=mock_cls):
        spawner.spawn()
        assert enemy_obj.airspace is fake_space

def test_spawner_sets_airspace_none_when_game_has_no_current_space():
    PlasmaEnemy.containers = ()
    EnemySpawner.containers = ()
    game, _, _ = make_game()
    spawner = EnemySpawner(game)
    enemy_obj = SimpleNamespace(element=None)
    mock_cls = MagicMock(return_value=enemy_obj)
    with patch.object(spawner, '_pick_enemy_class', return_value=mock_cls):
        spawner.spawn()
        assert enemy_obj.airspace is None

# --- EnemySpawner._pick_enemy_class ---
def test_pick_enemy_class_returns_plasma_enemy_sometimes():
    PlasmaEnemy.containers = ()
    KineticEnemy.containers = ()
    EnemySpawner.containers = ()
    game, _, _ = make_game()
    spawner = EnemySpawner(game)
    with patch("entities.enemyspawner.random.choice", return_value=PlasmaEnemy):
        assert spawner._pick_enemy_class() is PlasmaEnemy

def test_pick_enemy_class_returns_kinetic_enemy_sometimes():
    PlasmaEnemy.containers = ()
    KineticEnemy.containers = ()
    EnemySpawner.containers = ()
    game, _, _ = make_game()
    spawner = EnemySpawner(game)
    with patch("entities.enemyspawner.random.choice", return_value=KineticEnemy):
        assert spawner._pick_enemy_class() is KineticEnemy
