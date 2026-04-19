import pygame
import pytest
from core import constants as C
from core.element import Element
from entities.enemy import Enemy, PlasmaEnemy
from entities.projectile import Plasma
from types import SimpleNamespace
from ui.visualeffect import EnemyKillExplosionVE
from unittest.mock import MagicMock, patch

class FakePlayer:
    def __init__(self, x=0, y=0):
        self.position = pygame.Vector2(x, y)
        self.radius = C.PLAYER_RADIUS
        self.weight = C.PLAYER_WEIGHT
        self.velocity = pygame.Vector2(0, 0)
        self.bounciness = C.PLAYER_BOUNCINESS
        self.can_be_damaged = True
        self.game_over = False
        self.collision_calls = []
        self.collision_damage = C.PLAYER_COLLISION_DAMAGE

    def collides_with(self, other):
        return self.position.distance_to(other.position) <= self.radius + other.radius

    def damaged(self):
        return C.LIFE_LOSS_SCORE, 2

    def sync_local_speeds_from_velocity(self):
        pass

class FakeProjectile:
    def __init__(self, damage=10, element=None, collide=True, stat_source=C.PLAYER):
        self.damage = damage
        self.element = element
        self._collide = collide
        self._killed = False
        self.stat_source = stat_source

    def collides_with(self, other):
        return self._collide

    def kill(self):
        self._killed = True

class FakeHUD:
    def __init__(self):
        self.score_updates = []
        self.lives_updates = []

    def update_score(self, delta):
        self.score_updates.append(delta)

    def update_player_lives(self, lives):
        self.lives_updates.append(lives)

class FakeExperience:
    def __init__(self):
        self.xp_added = []

    def add_xp(self, amount):
        self.xp_added.append(amount)

def make_enemy(px=0, py=0, ex=500, ey=500):
    player = FakePlayer(px, py)
    enemy = Enemy(ex, ey, player)
    return enemy, player

def make_cs_game(enemies=None, projectiles=None, player=None, current_space=None):
    hud = FakeHUD()
    experience = FakeExperience()
    player = player or FakePlayer(x=9999, y=9999)
    from systems.collisionsystem import CollisionSystem
    game = SimpleNamespace(
        enemies=enemies or [],
        projectiles=projectiles or [],
        player=player,
        HUD=hud,
        experience=experience,
        on_game_over=MagicMock(),
        asteroids=[],
        shields=[],
        essence_orbs=[],
        elemental_essence_orbs=[],
        wrap_object=lambda obj: None,
        combat_stats=SimpleNamespace(record_damage_event=lambda **kw: None),
        current_space=current_space,
    )
    return game, CollisionSystem(game)

# --- Enemy construction ---
def test_enemy_initial_health_equals_max_health():
    enemy, _ = make_enemy()
    assert enemy.health == C.ENEMY_MAX_HEALTH

def test_enemy_body_color_is_neutral_steel_gray():
    enemy, _ = make_enemy()
    assert enemy.body_color == C.ENEMY_BODY_COLOR

def test_enemy_hull_width_uses_constant():
    enemy, _ = make_enemy()
    assert enemy.hull_width == C.ENEMY_HULL_WIDTH

def test_enemy_hull_length_uses_constant():
    enemy, _ = make_enemy()
    assert enemy.hull_length == C.ENEMY_HULL_LENGTH

def test_enemy_initial_element_is_none():
    enemy, _ = make_enemy()
    assert enemy.element is None

def test_enemy_stat_source_is_enemy_constant():
    enemy, _ = make_enemy()
    assert enemy.stat_source == C.ENEMY

# --- Enemy.damaged ---
def test_damaged_reduces_health():
    enemy, _ = make_enemy()
    enemy.damaged(5)
    assert enemy.health == C.ENEMY_MAX_HEALTH - 5

def test_damaged_returns_zero_score_when_alive():
    enemy, _ = make_enemy()
    score, xp = enemy.damaged(1)
    assert score == 0
    assert xp == 0

def test_damaged_kills_enemy_when_health_depleted():
    EnemyKillExplosionVE.containers = ()
    enemy, _ = make_enemy()
    enemy.damaged(C.ENEMY_MAX_HEALTH)
    assert not enemy.alive()

def test_damaged_returns_score_and_xp_on_death():
    EnemyKillExplosionVE.containers = ()
    enemy, _ = make_enemy()
    score, xp = enemy.damaged(C.ENEMY_MAX_HEALTH)
    assert score == C.ENEMY_SCORE_VALUE
    assert xp == C.ENEMY_XP_VALUE

def test_damaged_applies_elemental_multiplier_strong():
    enemy, _ = make_enemy()
    enemy.element = Element.CRYO
    enemy.damaged(10, attacker_element=Element.SOLAR)
    assert enemy.health == C.ENEMY_MAX_HEALTH - 20

def test_damaged_applies_elemental_multiplier_weak():
    enemy, _ = make_enemy()
    enemy.element = Element.CRYO
    enemy.damaged(10, attacker_element=Element.FLUX)
    assert enemy.health == C.ENEMY_MAX_HEALTH - 5

def test_damaged_minimum_one_damage():
    enemy, _ = make_enemy()
    enemy.element = Element.CRYO
    enemy.damaged(1, attacker_element=Element.FLUX)
    assert enemy.health == C.ENEMY_MAX_HEALTH - 1

def test_damaged_logs_enemy_hit_when_alive():
    enemy, _ = make_enemy()
    with patch("entities.enemy.log_event") as mock_log:
        enemy.damaged(1)
        mock_log.assert_called_once_with("enemy_hit")

def test_damaged_logs_enemy_destroyed_on_kill():
    EnemyKillExplosionVE.containers = ()
    enemy, _ = make_enemy()
    with patch("entities.enemy.log_event") as mock_log:
        enemy.damaged(C.ENEMY_MAX_HEALTH)
        mock_log.assert_called_once_with("enemy_destroyed")

def test_damaged_spawns_explosion_on_kill():
    EnemyKillExplosionVE.containers = ()
    enemy, _ = make_enemy()
    with patch("entities.enemy.EnemyKillExplosionVE") as mock_ve:
        enemy.damaged(C.ENEMY_MAX_HEALTH)
        mock_ve.assert_called_once()

# --- Enemy.rect_corners ---
def test_rect_corners_returns_four_points():
    enemy, _ = make_enemy()
    corners = enemy.rect_corners()
    assert len(corners) == 4

def test_rect_corners_nose_is_forward_of_center():
    enemy, _ = make_enemy(ex=500, ey=500)
    enemy.rotation = 0
    corners = enemy.rect_corners()
    nose_y = min(c.y for c in corners)
    assert nose_y < enemy.position.y

def test_rect_corners_span_hull_width():
    enemy, _ = make_enemy()
    enemy.rotation = 0
    corners = enemy.rect_corners()
    x_values = [c.x for c in corners]
    assert max(x_values) - min(x_values) == pytest.approx(C.ENEMY_HULL_WIDTH, abs=0.1)

def test_rect_corners_span_hull_length():
    enemy, _ = make_enemy()
    enemy.rotation = 0
    corners = enemy.rect_corners()
    y_values = [c.y for c in corners]
    assert max(y_values) - min(y_values) == pytest.approx(C.ENEMY_HULL_LENGTH, abs=0.1)

# --- Enemy.move_toward_player ---
def test_move_toward_player_sets_velocity_toward_player():
    enemy, player = make_enemy(px=0, py=0, ex=100, ey=0)
    enemy.move_toward_player(0.1)
    assert enemy.velocity.x < 0

def test_move_toward_player_sets_velocity_magnitude_to_enemy_speed():
    enemy, player = make_enemy(px=0, py=0, ex=100, ey=0)
    enemy.move_toward_player(0.1)
    assert enemy.velocity.length() == pytest.approx(C.ENEMY_SPEED, abs=0.1)

def test_move_toward_player_no_crash_when_at_same_position():
    enemy, player = make_enemy(px=0, py=0, ex=0, ey=0)
    enemy.move_toward_player(0.1)

# --- Enemy._calculate_avoidance ---
class FakeAsteroidForAvoidance:
    def __init__(self, x, y, vx=0, vy=0, radius=15):
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(vx, vy)
        self.radius = radius

def test_avoidance_zero_when_no_asteroids():
    enemy, _ = make_enemy(ex=0, ey=0)
    result = enemy._calculate_avoidance([])
    assert result.length() == pytest.approx(0, abs=0.001)

def test_avoidance_zero_when_asteroid_out_of_range():
    enemy, _ = make_enemy(ex=0, ey=0)
    far = FakeAsteroidForAvoidance(x=9999, y=9999, vx=1, vy=0)
    result = enemy._calculate_avoidance([far])
    assert result.length() == pytest.approx(0, abs=0.001)

def test_avoidance_zero_when_asteroid_moving_away():
    enemy, _ = make_enemy(ex=100, ey=0)
    asteroid = FakeAsteroidForAvoidance(x=0, y=0, vx=-100, vy=0)
    result = enemy._calculate_avoidance([asteroid])
    assert result.length() == pytest.approx(0, abs=0.001)

def test_avoidance_nonzero_when_asteroid_approaching():
    enemy, _ = make_enemy(ex=100, ey=0)
    asteroid = FakeAsteroidForAvoidance(x=0, y=0, vx=100, vy=0)
    result = enemy._calculate_avoidance([asteroid])
    assert result.length() > 0

def test_avoidance_points_away_from_incoming_asteroid():
    enemy, _ = make_enemy(ex=100, ey=0)
    asteroid = FakeAsteroidForAvoidance(x=0, y=0, vx=100, vy=0)
    result = enemy._calculate_avoidance([asteroid])
    assert result.x > 0

def test_move_toward_player_blends_avoidance_when_asteroid_incoming():
    enemy, player = make_enemy(px=0, py=0, ex=100, ey=0)
    incoming = FakeAsteroidForAvoidance(x=200, y=0, vx=-100, vy=0)
    enemy.asteroids = [incoming]
    enemy.move_toward_player(0.1)
    assert enemy.velocity.length() == pytest.approx(C.ENEMY_SPEED, abs=0.1)

# --- Enemy.impact_timer ---
def test_enemy_impact_timer_defaults_to_zero():
    enemy, _ = make_enemy()
    assert enemy.impact_timer == 0

def test_enemy_impact_timer_prevents_velocity_override():
    enemy, player = make_enemy(px=0, py=0, ex=100, ey=0)
    enemy.impact_timer = 0.5
    enemy.velocity = pygame.Vector2(0, 0)
    enemy.move_toward_player(0.1)
    assert enemy.velocity.length() == pytest.approx(0, abs=0.001)

def test_enemy_impact_timer_decrements_in_update():
    enemy, _ = make_enemy(ex=500, ey=500)
    enemy.impact_timer = 1.0
    enemy.update(0.1)
    assert enemy.impact_timer == pytest.approx(0.9, abs=0.001)

def test_enemy_impact_timer_does_not_go_below_zero():
    enemy, _ = make_enemy(ex=500, ey=500)
    enemy.impact_timer = 0.05
    enemy.update(0.5)
    assert enemy.impact_timer == pytest.approx(0, abs=0.001)

# --- handle_enemy_collisions: projectile hits ---
def test_projectile_hit_enemy_takes_damage():
    Enemy.containers = ()
    player = FakePlayer(x=9999, y=9999)
    enemy = Enemy(0, 0, player)
    projectile = FakeProjectile(damage=5)
    game, cs = make_cs_game(enemies=[enemy], projectiles=[projectile])
    cs.handle_enemy_collisions()
    assert enemy.health == C.ENEMY_MAX_HEALTH - 5

def test_projectile_hit_kills_projectile():
    Enemy.containers = ()
    player = FakePlayer(x=9999, y=9999)
    enemy = Enemy(0, 0, player)
    projectile = FakeProjectile(damage=5)
    game, cs = make_cs_game(enemies=[enemy], projectiles=[projectile])
    cs.handle_enemy_collisions()
    assert projectile._killed

def test_projectile_kill_enemy_reports_score_to_hud():
    Enemy.containers = ()
    EnemyKillExplosionVE.containers = ()
    player = FakePlayer(x=9999, y=9999)
    enemy = Enemy(0, 0, player)
    projectile = FakeProjectile(damage=C.ENEMY_MAX_HEALTH)
    game, cs = make_cs_game(enemies=[enemy], projectiles=[projectile])
    cs.handle_enemy_collisions()
    assert C.ENEMY_SCORE_VALUE in game.HUD.score_updates

def test_projectile_kill_enemy_awards_xp():
    Enemy.containers = ()
    EnemyKillExplosionVE.containers = ()
    player = FakePlayer(x=9999, y=9999)
    enemy = Enemy(0, 0, player)
    projectile = FakeProjectile(damage=C.ENEMY_MAX_HEALTH)
    game, cs = make_cs_game(enemies=[enemy], projectiles=[projectile])
    cs.handle_enemy_collisions()
    assert C.ENEMY_XP_VALUE in game.experience.xp_added

def test_non_colliding_projectile_does_not_damage_enemy():
    Enemy.containers = ()
    player = FakePlayer(x=9999, y=9999)
    enemy = Enemy(0, 0, player)
    projectile = FakeProjectile(damage=5, collide=False)
    game, cs = make_cs_game(enemies=[enemy], projectiles=[projectile])
    cs.handle_enemy_collisions()
    assert enemy.health == C.ENEMY_MAX_HEALTH

# --- handle_enemy_collisions: player body hit ---
def test_enemy_contact_damages_player():
    Enemy.containers = ()
    player = FakePlayer(x=0, y=0)
    enemy = Enemy(0, 0, player)
    damaged_calls = []
    player.damaged = lambda: (damaged_calls.append(1) or (C.LIFE_LOSS_SCORE, 2))
    game, cs = make_cs_game(enemies=[enemy], player=player)
    cs.handle_enemy_collisions()
    assert len(damaged_calls) == 1

def test_enemy_contact_updates_hud_lives():
    Enemy.containers = ()
    player = FakePlayer(x=0, y=0)
    enemy = Enemy(0, 0, player)
    game, cs = make_cs_game(enemies=[enemy], player=player)
    cs.handle_enemy_collisions()
    assert len(game.HUD.lives_updates) == 1

def test_enemy_contact_skipped_when_player_cannot_be_damaged():
    Enemy.containers = ()
    player = FakePlayer(x=0, y=0)
    player.can_be_damaged = False
    enemy = Enemy(0, 0, player)
    damaged_calls = []
    player.damaged = lambda: (damaged_calls.append(1) or (C.LIFE_LOSS_SCORE, 2))
    game, cs = make_cs_game(enemies=[enemy], player=player)
    cs.handle_enemy_collisions()
    assert damaged_calls == []

def test_game_over_triggered_when_player_dies_from_enemy():
    Enemy.containers = ()
    player = FakePlayer(x=0, y=0)
    player.game_over = True
    enemy = Enemy(0, 0, player)
    game, cs = make_cs_game(enemies=[enemy], player=player)
    cs.handle_enemy_collisions()
    game.on_game_over.assert_called_once()

# --- handle_enemy_collisions: player damages enemy on contact ---
def test_player_contact_damages_enemy():
    Enemy.containers = ()
    player = FakePlayer(x=0, y=0)
    enemy = Enemy(0, 0, player)
    game, cs = make_cs_game(enemies=[enemy], player=player)
    cs.handle_enemy_collisions()
    assert enemy.health < C.ENEMY_MAX_HEALTH

def test_player_contact_sets_enemy_impact_timer():
    Enemy.containers = ()
    player = FakePlayer(x=0, y=0)
    enemy = Enemy(0, 0, player)
    game, cs = make_cs_game(enemies=[enemy], player=player)
    cs.handle_enemy_collisions()
    assert enemy.impact_timer > 0

def test_player_contact_does_not_damage_player_when_enemy_dies():
    Enemy.containers = ()
    EnemyKillExplosionVE.containers = ()
    player = FakePlayer(x=0, y=0)
    player.collision_damage = C.ENEMY_MAX_HEALTH + 100
    enemy = Enemy(0, 0, player)
    damaged_calls = []
    player.damaged = lambda: (damaged_calls.append(1) or (C.LIFE_LOSS_SCORE, 2))
    game, cs = make_cs_game(enemies=[enemy], player=player)
    cs.handle_enemy_collisions()
    assert damaged_calls == []

# --- enemy wrapping ---
def test_same_airspace_enemies_not_wrapped_by_collision_system():
    Enemy.containers = ()
    player = FakePlayer(x=9999, y=9999)
    enemy = Enemy(0, 0, player)
    wrapped = []
    game, cs = make_cs_game(enemies=[enemy])
    game.wrap_object = lambda obj: wrapped.append(obj)
    cs.handle_enemy_collisions()
    assert enemy not in wrapped

# --- stat_source team filtering ---
def test_enemy_projectile_does_not_damage_enemy():
    Enemy.containers = ()
    player = FakePlayer(x=9999, y=9999)
    enemy = Enemy(0, 0, player)
    projectile = FakeProjectile(damage=C.ENEMY_MAX_HEALTH, stat_source=C.ENEMY)
    game, cs = make_cs_game(enemies=[enemy], projectiles=[projectile])
    cs.handle_enemy_collisions()
    assert enemy.health == C.ENEMY_MAX_HEALTH

def test_enemy_projectile_damages_player_on_collision():
    Enemy.containers = ()
    player = FakePlayer(x=0, y=0)
    projectile = FakeProjectile(damage=5, collide=True, stat_source=C.ENEMY)
    damaged_calls = []
    player.damaged = lambda: (damaged_calls.append(1) or (C.LIFE_LOSS_SCORE, 2))
    game, cs = make_cs_game(enemies=[], projectiles=[projectile], player=player)
    cs.handle_enemy_collisions()
    assert len(damaged_calls) == 1

def test_enemy_projectile_is_killed_after_hitting_player():
    Enemy.containers = ()
    player = FakePlayer(x=0, y=0)
    projectile = FakeProjectile(damage=5, collide=True, stat_source=C.ENEMY)
    game, cs = make_cs_game(enemies=[], projectiles=[projectile], player=player)
    cs.handle_enemy_collisions()
    assert projectile._killed

def test_friendly_projectile_does_not_damage_player():
    Enemy.containers = ()
    player = FakePlayer(x=0, y=0)
    projectile = FakeProjectile(damage=5, collide=True, stat_source=C.PLAYER)
    damaged_calls = []
    player.damaged = lambda: (damaged_calls.append(1) or (C.LIFE_LOSS_SCORE, 2))
    game, cs = make_cs_game(enemies=[], projectiles=[projectile], player=player)
    cs.handle_enemy_collisions()
    assert damaged_calls == []

# --- PlasmaEnemy ---
class FakeGame:
    def __init__(self):
        self.asteroids = []
        self.combat_stats = SimpleNamespace(record_damage_event=lambda **kw: None)

def test_plasma_enemy_has_platform():
    Plasma.containers = ()
    player = FakePlayer()
    enemy = PlasmaEnemy(0, 0, player, FakeGame())
    assert enemy.platform is not None

def test_plasma_enemy_health_uses_plasma_enemy_constant():
    Plasma.containers = ()
    player = FakePlayer()
    enemy = PlasmaEnemy(0, 0, player, FakeGame())
    assert enemy.health == C.PLASMA_ENEMY_MAX_HEALTH

def test_plasma_enemy_speed_uses_plasma_enemy_constant():
    Plasma.containers = ()
    player = FakePlayer()
    enemy = PlasmaEnemy(0, 0, player, FakeGame())
    assert enemy.speed == C.PLASMA_ENEMY_SPEED

def test_plasma_enemy_projectile_color_is_danger_red():
    Plasma.containers = ()
    player = FakePlayer()
    enemy = PlasmaEnemy(0, 0, player, FakeGame())
    assert enemy.platform.projectile_color == C.PLASMA_ENEMY_PROJECTILE_COLOR

def test_plasma_enemy_xp_uses_plasma_enemy_constant():
    Plasma.containers = ()
    player = FakePlayer()
    enemy = PlasmaEnemy(0, 0, player, FakeGame())
    assert enemy.xp_value == C.PLASMA_ENEMY_XP_VALUE

def test_plasma_enemy_fires_with_enemy_stat_source():
    Plasma.containers = ()
    player = FakePlayer(x=0, y=0)
    game = FakeGame()
    enemy = PlasmaEnemy(500, 500, player, game)
    enemy.platform.weapons_free_timer = 0
    enemy.target = player
    enemy.rotation = 180
    enemy.shoot()

def test_plasma_enemy_update_decrements_platform_timer():
    Plasma.containers = ()
    player = FakePlayer()
    enemy = PlasmaEnemy(500, 500, player, FakeGame())
    enemy.platform.weapons_free_timer = 5.0
    enemy.update(1.0)
    assert enemy.platform.weapons_free_timer < 5.0

# --- Enemy._in_current_airspace ---
def test_enemy_default_airspace_is_none():
    enemy, _ = make_enemy()
    assert enemy.airspace is None

def test_in_current_airspace_true_when_airspace_is_none():
    enemy, _ = make_enemy()
    assert enemy._in_current_airspace() is True

def test_in_current_airspace_true_when_game_is_none():
    enemy, _ = make_enemy()
    enemy.airspace = object()
    assert enemy._in_current_airspace() is True

def test_in_current_airspace_true_when_current_space_is_none():
    enemy, _ = make_enemy()
    space = object()
    enemy.airspace = space
    enemy.game = SimpleNamespace(current_space=None)
    assert enemy._in_current_airspace() is True

def test_in_current_airspace_true_when_airspaces_match():
    enemy, _ = make_enemy()
    space = object()
    enemy.airspace = space
    enemy.game = SimpleNamespace(current_space=space)
    assert enemy._in_current_airspace() is True

def test_in_current_airspace_false_when_airspaces_differ():
    enemy, _ = make_enemy()
    enemy.airspace = object()
    enemy.game = SimpleNamespace(current_space=object())
    assert enemy._in_current_airspace() is False

# --- Enemy behavior in different airspace ---
def test_enemy_shoot_returns_zero_in_different_airspace():
    Plasma.containers = ()
    player = FakePlayer(x=0, y=0)
    game = FakeGame()
    enemy = PlasmaEnemy(500, 500, player, game)
    space_a = object()
    space_b = object()
    enemy.airspace = space_a
    enemy.game = SimpleNamespace(current_space=space_b, asteroids=game.asteroids,
        combat_stats=game.combat_stats)
    enemy.platform.weapons_free_timer = 0
    enemy.target = player
    assert enemy.shoot() == 0

def test_enemy_draw_body_skipped_in_different_airspace():
    enemy, _ = make_enemy()
    space_a = object()
    space_b = object()
    enemy.airspace = space_a
    enemy.game = SimpleNamespace(current_space=space_b)
    draw_calls = []
    enemy.draw_body = lambda screen: draw_calls.append(screen)
    enemy.draw(None)
    assert draw_calls == []

def test_enemy_draw_body_called_in_same_airspace():
    enemy, _ = make_enemy()
    space = object()
    enemy.airspace = space
    enemy.game = SimpleNamespace(current_space=space)
    draw_calls = []
    enemy.draw_body = lambda screen: draw_calls.append(screen)
    enemy.draw(None)
    assert len(draw_calls) == 1

def test_enemy_update_preserves_velocity_in_different_airspace():
    enemy, _ = make_enemy()
    space_a = object()
    space_b = object()
    enemy.airspace = space_a
    enemy.game = SimpleNamespace(current_space=space_b)
    enemy.velocity = pygame.Vector2(42, 0)
    enemy.update(0.0)
    assert enemy.velocity.x == pytest.approx(42, abs=0.01)

# --- handle_enemy_collisions: airspace ---
def test_enemy_in_different_airspace_not_wrapped():
    Enemy.containers = ()
    space_a = object()
    space_b = object()
    player = FakePlayer(x=9999, y=9999)
    enemy = Enemy(0, 0, player)
    enemy.airspace = space_a
    wrapped = []
    game, cs = make_cs_game(enemies=[enemy], current_space=space_b)
    game.wrap_object = lambda obj: wrapped.append(obj)
    cs.handle_enemy_collisions()
    assert enemy not in wrapped

def test_enemy_in_same_airspace_not_wrapped():
    Enemy.containers = ()
    space = object()
    player = FakePlayer(x=9999, y=9999)
    enemy = Enemy(0, 0, player)
    enemy.airspace = space
    wrapped = []
    game, cs = make_cs_game(enemies=[enemy], current_space=space)
    game.wrap_object = lambda obj: wrapped.append(obj)
    cs.handle_enemy_collisions()
    assert enemy not in wrapped

def test_enemy_in_different_airspace_not_damaged_by_projectile():
    Enemy.containers = ()
    space_a = object()
    space_b = object()
    player = FakePlayer(x=9999, y=9999)
    enemy = Enemy(0, 0, player)
    enemy.airspace = space_a
    projectile = FakeProjectile(damage=C.ENEMY_MAX_HEALTH)
    game, cs = make_cs_game(enemies=[enemy], projectiles=[projectile], current_space=space_b)
    cs.handle_enemy_collisions()
    assert enemy.health == C.ENEMY_MAX_HEALTH

def test_enemy_in_different_airspace_not_checked_against_player():
    Enemy.containers = ()
    space_a = object()
    space_b = object()
    player = FakePlayer(x=0, y=0)
    enemy = Enemy(0, 0, player)
    enemy.airspace = space_a
    damaged_calls = []
    player.damaged = lambda: (damaged_calls.append(1) or (C.LIFE_LOSS_SCORE, 2))
    game, cs = make_cs_game(enemies=[enemy], player=player, current_space=space_b)
    cs.handle_enemy_collisions()
    assert damaged_calls == []

def test_enemy_offscreen_in_different_airspace_switches_to_current():
    Enemy.containers = ()
    space_a = object()
    space_b = object()
    player = FakePlayer(x=9999, y=9999)
    enemy = Enemy(-100, 300, player)
    enemy.airspace = space_a
    game, cs = make_cs_game(enemies=[enemy], current_space=space_b)
    cs.handle_enemy_collisions()
    assert enemy.airspace is space_b

def test_enemy_offscreen_east_placed_at_west_edge_of_new_airspace():
    Enemy.containers = ()
    space_a = object()
    space_b = object()
    player = FakePlayer(x=9999, y=9999)
    enemy = Enemy(C.SCREEN_WIDTH + 50, 300, player)
    enemy.airspace = space_a
    game, cs = make_cs_game(enemies=[enemy], current_space=space_b)
    cs.handle_enemy_collisions()
    assert enemy.position.x == pytest.approx(50, abs=0.1)

def test_enemy_offscreen_north_placed_at_south_edge_of_new_airspace():
    Enemy.containers = ()
    space_a = object()
    space_b = object()
    player = FakePlayer(x=9999, y=9999)
    enemy = Enemy(400, -60, player)
    enemy.airspace = space_a
    game, cs = make_cs_game(enemies=[enemy], current_space=space_b)
    cs.handle_enemy_collisions()
    assert enemy.position.y == pytest.approx(C.SCREEN_HEIGHT - 60, abs=0.1)

def test_enemy_onscreen_in_different_airspace_does_not_switch():
    Enemy.containers = ()
    space_a = object()
    space_b = object()
    player = FakePlayer(x=9999, y=9999)
    enemy = Enemy(400, 300, player)
    enemy.airspace = space_a
    game, cs = make_cs_game(enemies=[enemy], current_space=space_b)
    cs.handle_enemy_collisions()
    assert enemy.airspace is space_a
