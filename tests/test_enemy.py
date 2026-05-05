import pygame
import pytest
from core import constants as C
from core.element import Element
from entities.enemy import Enemy, ExplosiveEnemy, KineticEnemy, LaserEnemy, PlasmaEnemy
from entities.projectile import Kinetic, Plasma
from types import SimpleNamespace
from ui.visualeffect import EnemyKillExplosionVE, LaserBeamVE
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
        self.uses_health = False

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
    assert xp == C.ENEMY_XP_VALUE + C.ENEMY_NON_ELEMENTAL_BONUS_XP

def test_damaged_elemental_enemy_returns_base_xp_without_bonus():
    from entities.elementalessenceorb import ElementalEssenceOrb
    from core.element import Element
    EnemyKillExplosionVE.containers = ()
    ElementalEssenceOrb.containers = ()
    enemy, _ = make_enemy()
    enemy.element = Element.SOLAR
    score, xp = enemy.damaged(C.ENEMY_MAX_HEALTH)
    assert score == C.ENEMY_SCORE_VALUE
    assert xp == C.ENEMY_XP_VALUE

def test_damaged_elemental_enemy_drops_elemental_essence():
    from entities.elementalessenceorb import ElementalEssenceOrb
    from core.element import Element
    from unittest.mock import patch as mpatch
    EnemyKillExplosionVE.containers = ()
    enemy, _ = make_enemy()
    enemy.element = Element.SOLAR
    with mpatch("entities.enemy.ElementalEssenceOrb") as MockOrb:
        MockOrb.containers = True
        enemy.damaged(C.ENEMY_MAX_HEALTH)
    MockOrb.assert_called_once()
    assert MockOrb.call_args[0][2] == C.ENEMY_ELEMENTAL_ESSENCE_DROP
    assert MockOrb.call_args[0][3] == Element.SOLAR

def test_damaged_non_elemental_enemy_does_not_drop_elemental_essence():
    from unittest.mock import patch as mpatch
    EnemyKillExplosionVE.containers = ()
    enemy, _ = make_enemy()
    with mpatch("entities.enemy.ElementalEssenceOrb") as MockOrb:
        MockOrb.containers = True
        enemy.damaged(C.ENEMY_MAX_HEALTH)
    MockOrb.assert_not_called()

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

def test_damaged_applies_mark_multiplier():
    enemy, _ = make_enemy()
    enemy.mark_multiplier = 2.0
    enemy.damaged(5)
    assert enemy.health == C.ENEMY_MAX_HEALTH - 10

def test_damaged_consumes_mark_multiplier_after_hit():
    enemy, _ = make_enemy()
    enemy.mark_multiplier = 2.0
    enemy.damaged(5)
    assert enemy.mark_multiplier == 1.0

def test_damaged_applies_corrode_multiplier():
    enemy, _ = make_enemy()
    enemy.corrode_multiplier = 1.5
    enemy.damaged(10)
    assert enemy.health == C.ENEMY_MAX_HEALTH - 15

def test_damaged_corrode_multiplier_persists_after_hit():
    enemy, _ = make_enemy()
    enemy.corrode_multiplier = 1.5
    enemy.damaged(5)
    assert enemy.corrode_multiplier == 1.5

def test_damaged_applies_both_multipliers():
    enemy, _ = make_enemy()
    enemy.mark_multiplier = 2.0
    enemy.corrode_multiplier = 1.5
    enemy.damaged(4)
    assert enemy.health == C.ENEMY_MAX_HEALTH - 12

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
    assert C.ENEMY_XP_VALUE + C.ENEMY_NON_ELEMENTAL_BONUS_XP in game.experience.xp_added

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

# --- enemy update calls gameplay effect and outline pulse ---
def test_enemy_update_calls_update_gameplay_effects():
    enemy, _ = make_enemy(ex=500, ey=500)
    called = []
    enemy.update_gameplay_effects = lambda dt: called.append(dt) or 0
    enemy.update(0.1)
    assert called == [0.1]

def test_enemy_update_calls_update_outline_pulse():
    enemy, _ = make_enemy(ex=500, ey=500)
    called = []
    enemy.update_outline_pulse = lambda dt: called.append(dt)
    enemy.update(0.1)
    assert called == [0.1]

# --- plasma projectile applies burn to enemy on collision ---
def test_plasma_hit_applies_burn_to_enemy():
    Enemy.containers = ()
    Plasma.containers = ()
    player = FakePlayer(x=9999, y=9999)
    enemy = Enemy(0, 0, player)
    projectile = Plasma(0, 0)
    projectile.stat_source = C.PLAYER
    from unittest.mock import MagicMock
    projectile.combat_stats = MagicMock()
    game, cs = make_cs_game(enemies=[enemy], projectiles=[projectile])
    cs.handle_enemy_collisions()
    from systems.gameplayeffect import BurnSTE
    assert any(isinstance(e, BurnSTE) for e in enemy.gameplay_effects)

def test_non_plasma_hit_does_not_apply_burn_to_enemy():
    Enemy.containers = ()
    player = FakePlayer(x=9999, y=9999)
    enemy = Enemy(0, 0, player)
    projectile = FakeProjectile(damage=5)
    game, cs = make_cs_game(enemies=[enemy], projectiles=[projectile])
    cs.handle_enemy_collisions()
    from systems.gameplayeffect import BurnSTE
    assert not any(isinstance(e, BurnSTE) for e in enemy.gameplay_effects)

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
def test_enemy_projectile_damages_other_enemy_friendly_fire():
    Enemy.containers = ()
    player = FakePlayer(x=9999, y=9999)
    enemy = Enemy(0, 0, player)
    projectile = FakeProjectile(damage=5, stat_source=C.ENEMY)
    game, cs = make_cs_game(enemies=[enemy], projectiles=[projectile])
    cs.handle_enemy_collisions()
    assert enemy.health < C.ENEMY_MAX_HEALTH

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

# --- Enemy burn body flash visual ---
def test_enemy_draw_body_uses_pulse_color_as_fill_when_burning():
    enemy, _ = make_enemy()
    enemy.pulse_outline(C.PLASMA_PROJECTILE_COLOR, 0.5)
    drawn_colors = []
    with patch("entities.enemy.pygame.draw.polygon",
               side_effect=lambda s, color, pts, *a: drawn_colors.append(color)):
        enemy.draw_body(None)
    assert C.PLASMA_PROJECTILE_COLOR in drawn_colors

def test_enemy_draw_body_uses_body_color_as_fill_when_not_burning():
    enemy, _ = make_enemy()
    drawn_colors = []
    with patch("entities.enemy.pygame.draw.polygon",
               side_effect=lambda s, color, pts, *a: drawn_colors.append(color)):
        enemy.draw_body(None)
    assert enemy.body_color in drawn_colors
    assert C.PLASMA_PROJECTILE_COLOR not in drawn_colors

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

def test_plasma_enemy_draw_wings_uses_pulse_color_when_burning():
    Plasma.containers = ()
    player = FakePlayer()
    enemy = PlasmaEnemy(0, 0, player, FakeGame())
    enemy.pulse_outline(C.PLASMA_PROJECTILE_COLOR, 0.5)
    drawn_colors = []
    with patch("entities.enemy.pygame.draw.polygon",
               side_effect=lambda s, color, pts, *a: drawn_colors.append(color)):
        enemy._draw_wings(None)
    assert drawn_colors.count(C.PLASMA_PROJECTILE_COLOR) == 2

def test_plasma_enemy_draw_wings_uses_body_color_when_not_burning():
    Plasma.containers = ()
    player = FakePlayer()
    enemy = PlasmaEnemy(0, 0, player, FakeGame())
    drawn_colors = []
    with patch("entities.enemy.pygame.draw.polygon",
               side_effect=lambda s, color, pts, *a: drawn_colors.append(color)):
        enemy._draw_wings(None)
    assert C.PLASMA_PROJECTILE_COLOR not in drawn_colors

def test_plasma_enemy_draw_wings_calls_elemental_glow_per_wing_when_elemental():
    from core.element import Element
    Plasma.containers = ()
    player = FakePlayer()
    enemy = PlasmaEnemy(0, 0, player, FakeGame())
    enemy.element = Element.SOLAR
    glow_calls = []
    with patch("entities.enemy.draw_elemental_glow_poly",
               side_effect=lambda s, corners, el: glow_calls.append(el)), \
         patch("entities.enemy.pygame.draw.polygon"):
        enemy._draw_wings(None)
    assert glow_calls.count(Element.SOLAR) == 2

def test_plasma_enemy_draw_wings_no_elemental_glow_when_not_elemental():
    Plasma.containers = ()
    player = FakePlayer()
    enemy = PlasmaEnemy(0, 0, player, FakeGame())
    glow_calls = []
    with patch("entities.enemy.draw_elemental_glow_poly",
               side_effect=lambda s, corners, el: glow_calls.append(el)), \
         patch("entities.enemy.pygame.draw.polygon"):
        enemy._draw_wings(None)
    assert glow_calls == []

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


class FakeAsteroid:
    def __init__(self, x, y, radius=30, health=50):
        self.position = pygame.Vector2(x, y)
        self.radius = radius
        self.velocity = pygame.Vector2(0, 0)
        self.health = health

    def damaged(self, amount):
        self.health -= amount
        return 10 if self.health <= 0 else 0


def make_kinetic_enemy(px=0, py=0, ex=500, ey=500):
    Kinetic.containers = ()
    player = FakePlayer(px, py)
    game = SimpleNamespace(
        asteroids=[],
        combat_stats=SimpleNamespace(record_damage_event=lambda **kw: None),
    )
    KineticEnemy.containers = ()
    enemy = KineticEnemy(ex, ey, player, game)
    return enemy, player, game


# --- KineticEnemy construction ---
def test_kinetic_enemy_health_uses_constant():
    enemy, _, _ = make_kinetic_enemy()
    assert enemy.health == C.KINETIC_ENEMY_MAX_HEALTH

def test_kinetic_enemy_max_health_uses_constant():
    enemy, _, _ = make_kinetic_enemy()
    assert enemy.max_health == C.KINETIC_ENEMY_MAX_HEALTH

def test_kinetic_enemy_body_color_uses_constant():
    enemy, _, _ = make_kinetic_enemy()
    assert enemy.body_color == C.KINETIC_ENEMY_BODY_COLOR

def test_kinetic_enemy_hull_width_uses_constant():
    enemy, _, _ = make_kinetic_enemy()
    assert enemy.hull_width == C.KINETIC_ENEMY_HULL_WIDTH

def test_kinetic_enemy_hull_length_uses_constant():
    enemy, _, _ = make_kinetic_enemy()
    assert enemy.hull_length == C.KINETIC_ENEMY_HULL_LENGTH

def test_kinetic_enemy_hull_is_wider_than_long():
    assert C.KINETIC_ENEMY_HULL_WIDTH > C.KINETIC_ENEMY_HULL_LENGTH

def test_kinetic_enemy_speed_uses_constant():
    enemy, _, _ = make_kinetic_enemy()
    assert enemy.speed == C.KINETIC_ENEMY_SPEED

def test_kinetic_enemy_xp_uses_constant():
    enemy, _, _ = make_kinetic_enemy()
    assert enemy.xp_value == C.KINETIC_ENEMY_XP_VALUE

def test_kinetic_enemy_has_platform():
    enemy, _, _ = make_kinetic_enemy()
    assert enemy.platform is not None

def test_kinetic_enemy_platform_range_uses_constant():
    enemy, _, _ = make_kinetic_enemy()
    assert enemy.platform.range == C.KINETIC_ENEMY_WEAPONS_RANGE

def test_kinetic_enemy_platform_timer_max_uses_constant():
    enemy, _, _ = make_kinetic_enemy()
    assert enemy.platform.weapons_free_timer_max == C.KINETIC_ENEMY_WEAPONS_FREE_TIMER

def test_kinetic_enemy_platform_projectile_speed_uses_constant():
    enemy, _, _ = make_kinetic_enemy()
    assert enemy.platform.projectile_speed == C.KINETIC_ENEMY_PROJECTILE_SPEED

def test_kinetic_enemy_platform_projectile_color_is_danger_red():
    enemy, _, _ = make_kinetic_enemy()
    assert enemy.platform.projectile_color == C.KINETIC_ENEMY_PROJECTILE_COLOR

# --- KineticEnemy._find_largest_asteroid ---
def test_find_largest_returns_none_when_no_asteroids():
    enemy, _, _ = make_kinetic_enemy()
    assert enemy._find_largest_asteroid() is None

def test_find_largest_returns_only_asteroid():
    enemy, _, game = make_kinetic_enemy()
    a = FakeAsteroid(100, 100, radius=30)
    game.asteroids = [a]
    enemy.asteroids = game.asteroids
    assert enemy._find_largest_asteroid() is a

def test_find_largest_returns_asteroid_with_greatest_radius():
    enemy, _, game = make_kinetic_enemy()
    small = FakeAsteroid(100, 100, radius=15)
    big = FakeAsteroid(200, 200, radius=60)
    medium = FakeAsteroid(300, 300, radius=30)
    game.asteroids = [small, big, medium]
    enemy.asteroids = game.asteroids
    assert enemy._find_largest_asteroid() is big

# --- KineticEnemy._find_nearest_asteroid ---
def test_find_nearest_returns_none_when_no_asteroids():
    enemy, _, _ = make_kinetic_enemy()
    assert enemy._find_nearest_asteroid() is None

def test_find_nearest_returns_closest_asteroid():
    enemy, _, game = make_kinetic_enemy(ex=0, ey=0)
    near = FakeAsteroid(50, 0, radius=15)
    far = FakeAsteroid(500, 0, radius=15)
    game.asteroids = [near, far]
    enemy.asteroids = game.asteroids
    assert enemy._find_nearest_asteroid() is near

def test_find_nearest_excludes_specified_asteroid():
    enemy, _, game = make_kinetic_enemy(ex=0, ey=0)
    near = FakeAsteroid(50, 0, radius=15)
    far = FakeAsteroid(500, 0, radius=15)
    game.asteroids = [near, far]
    enemy.asteroids = game.asteroids
    assert enemy._find_nearest_asteroid(exclude=near) is far

def test_find_nearest_returns_none_when_only_excluded():
    enemy, _, game = make_kinetic_enemy(ex=0, ey=0)
    only = FakeAsteroid(50, 0, radius=15)
    game.asteroids = [only]
    enemy.asteroids = game.asteroids
    assert enemy._find_nearest_asteroid(exclude=only) is None

# --- KineticEnemy._calculate_proximity_avoidance ---
def test_proximity_avoidance_zero_when_no_objects():
    enemy, _, _ = make_kinetic_enemy(ex=0, ey=0)
    result = enemy._calculate_proximity_avoidance([])
    assert result.length() == pytest.approx(0, abs=0.001)

def test_proximity_avoidance_zero_when_object_out_of_range():
    enemy, _, _ = make_kinetic_enemy(ex=0, ey=0)
    far = FakeAsteroid(9999, 0, radius=15)
    result = enemy._calculate_proximity_avoidance([far])
    assert result.length() == pytest.approx(0, abs=0.001)

def test_proximity_avoidance_nonzero_when_object_in_range():
    enemy, _, _ = make_kinetic_enemy(ex=100, ey=0)
    near = FakeAsteroid(0, 0, radius=15)
    result = enemy._calculate_proximity_avoidance([near])
    assert result.length() > 0

def test_proximity_avoidance_points_away_from_nearby_object():
    enemy, _, _ = make_kinetic_enemy(ex=100, ey=0)
    near = FakeAsteroid(0, 0, radius=15)
    result = enemy._calculate_proximity_avoidance([near])
    assert result.x > 0

# --- KineticEnemy.acquire_target ---
def test_acquire_target_sets_player_when_player_within_threat_radius():
    enemy, player, game = make_kinetic_enemy(px=500, py=500, ex=500, ey=500)
    enemy.acquire_target()
    assert enemy.target is player

def test_acquire_target_sets_largest_when_in_weapon_range():
    enemy, player, game = make_kinetic_enemy(px=9999, py=9999, ex=0, ey=0)
    a = FakeAsteroid(10, 0, radius=60)
    game.asteroids = [a]
    enemy.asteroids = game.asteroids
    enemy.acquire_target()
    assert enemy.target is a

def test_acquire_target_sets_nearest_when_largest_out_of_range():
    enemy, player, game = make_kinetic_enemy(px=9999, py=9999, ex=0, ey=0)
    large = FakeAsteroid(9000, 0, radius=60)
    near = FakeAsteroid(50, 0, radius=15)
    game.asteroids = [large, near]
    enemy.asteroids = game.asteroids
    enemy.acquire_target()
    assert enemy.target is near

def test_acquire_target_falls_back_to_largest_when_no_other_asteroid():
    enemy, player, game = make_kinetic_enemy(px=9999, py=9999, ex=0, ey=0)
    large = FakeAsteroid(9000, 0, radius=60)
    game.asteroids = [large]
    enemy.asteroids = game.asteroids
    enemy.acquire_target()
    assert enemy.target is large

def test_acquire_target_sets_none_when_no_asteroids_and_player_far():
    enemy, player, game = make_kinetic_enemy(px=9999, py=9999, ex=0, ey=0)
    game.asteroids = []
    enemy.asteroids = game.asteroids
    enemy.acquire_target()
    assert enemy.target is None

# --- KineticEnemy.move_toward_asteroid ---
def test_move_toward_asteroid_sets_velocity_toward_largest():
    enemy, player, game = make_kinetic_enemy(px=9999, py=9999, ex=0, ey=0)
    a = FakeAsteroid(200, 0, radius=30)
    game.asteroids = [a]
    enemy.asteroids = game.asteroids
    enemy.move_toward_asteroid(0.1)
    assert enemy.velocity.x > 0

def test_move_toward_asteroid_speed_equals_enemy_speed():
    enemy, player, game = make_kinetic_enemy(px=9999, py=9999, ex=0, ey=0)
    a = FakeAsteroid(200, 0, radius=30)
    game.asteroids = [a]
    enemy.asteroids = game.asteroids
    enemy.move_toward_asteroid(0.1)
    assert enemy.velocity.length() == pytest.approx(C.KINETIC_ENEMY_SPEED, abs=0.1)

def test_move_toward_asteroid_moves_toward_player_when_in_threat_radius():
    enemy, player, game = make_kinetic_enemy(px=500, py=500, ex=500, ey=600)
    a = FakeAsteroid(0, 0, radius=30)
    game.asteroids = [a]
    enemy.asteroids = game.asteroids
    enemy.move_toward_asteroid(0.1)
    assert enemy.velocity.y < 0

def test_move_toward_asteroid_respects_impact_timer():
    enemy, player, game = make_kinetic_enemy(px=9999, py=9999, ex=0, ey=0)
    a = FakeAsteroid(200, 0, radius=30)
    game.asteroids = [a]
    enemy.asteroids = game.asteroids
    enemy.impact_timer = 0.5
    enemy.velocity = pygame.Vector2(0, 0)
    enemy.move_toward_asteroid(0.1)
    assert enemy.velocity.length() == pytest.approx(0, abs=0.001)

def test_move_toward_asteroid_no_crash_when_no_asteroids():
    enemy, player, game = make_kinetic_enemy(px=9999, py=9999, ex=0, ey=0)
    game.asteroids = []
    enemy.asteroids = game.asteroids
    enemy.move_toward_asteroid(0.1)

# --- KineticEnemy.update ---
def test_kinetic_enemy_update_ticks_platform():
    enemy, _, _ = make_kinetic_enemy(ex=500, ey=500)
    enemy.platform.weapons_free_timer = 5.0
    enemy.update(1.0)
    assert enemy.platform.weapons_free_timer < 5.0

def test_kinetic_enemy_update_calls_update_gameplay_effects():
    enemy, _, _ = make_kinetic_enemy(ex=500, ey=500)
    called = []
    enemy.update_gameplay_effects = lambda dt: called.append(dt) or 0
    enemy.update(0.1)
    assert called == [0.1]

def test_kinetic_enemy_update_calls_update_outline_pulse():
    enemy, _, _ = make_kinetic_enemy(ex=500, ey=500)
    called = []
    enemy.update_outline_pulse = lambda dt: called.append(dt)
    enemy.update(0.1)
    assert called == [0.1]

def test_kinetic_enemy_moves_toward_player_when_in_different_airspace():
    enemy, player, game = make_kinetic_enemy(px=0, py=0, ex=300, ey=0)
    space_a = object()
    space_b = object()
    enemy.airspace = space_a
    enemy.game = SimpleNamespace(current_space=space_b, asteroids=game.asteroids,
        combat_stats=game.combat_stats)
    enemy.update(0.1)
    assert enemy.velocity.x < 0

def test_kinetic_enemy_does_not_move_toward_asteroid_when_in_different_airspace():
    # player is left, asteroid is right — enemy should move left (toward player)
    enemy, player, game = make_kinetic_enemy(px=-300, py=0, ex=0, ey=0)
    a = FakeAsteroid(300, 0, radius=60)
    game.asteroids = [a]
    enemy.asteroids = game.asteroids
    space_a = object()
    space_b = object()
    enemy.airspace = space_a
    enemy.game = SimpleNamespace(current_space=space_b, asteroids=game.asteroids,
        combat_stats=game.combat_stats)
    enemy.update(0.1)
    assert enemy.velocity.x < 0

# --- KineticEnemy._draw_fins ---
def test_kinetic_enemy_draw_fins_draws_two_polygons():
    enemy, _, _ = make_kinetic_enemy()
    draw_calls = []
    with patch("entities.enemy.pygame.draw.polygon",
               side_effect=lambda s, color, pts, *a: draw_calls.append(pts)):
        enemy._draw_fins(None)
    assert len(draw_calls) == 2

def test_kinetic_enemy_draw_fins_uses_body_color_when_not_burning():
    enemy, _, _ = make_kinetic_enemy()
    drawn_colors = []
    with patch("entities.enemy.pygame.draw.polygon",
               side_effect=lambda s, color, pts, *a: drawn_colors.append(color)):
        enemy._draw_fins(None)
    assert all(c == C.KINETIC_ENEMY_BODY_COLOR for c in drawn_colors)

def test_kinetic_enemy_draw_fins_calls_elemental_glow_per_fin_when_elemental():
    enemy, _, _ = make_kinetic_enemy()
    enemy.element = Element.SOLAR
    glow_calls = []
    with patch("entities.enemy.draw_elemental_glow_poly",
               side_effect=lambda s, corners, el: glow_calls.append(el)), \
         patch("entities.enemy.pygame.draw.polygon"):
        enemy._draw_fins(None)
    assert glow_calls.count(Element.SOLAR) == 2

def test_kinetic_enemy_draw_fins_no_elemental_glow_when_not_elemental():
    enemy, _, _ = make_kinetic_enemy()
    glow_calls = []
    with patch("entities.enemy.draw_elemental_glow_poly",
               side_effect=lambda s, corners, el: glow_calls.append(el)), \
         patch("entities.enemy.pygame.draw.polygon"):
        enemy._draw_fins(None)
    assert glow_calls == []


def make_laser_enemy(px=0, py=0, ex=500, ey=500):
    player = FakePlayer(px, py)
    game = SimpleNamespace(
        asteroids=[],
        enemies=[],
        combat_stats=SimpleNamespace(record_damage_event=lambda **kw: None),
        HUD=FakeHUD(),
        experience=FakeExperience(),
        on_game_over=MagicMock(),
    )
    LaserEnemy.containers = ()
    enemy = LaserEnemy(ex, ey, player, game)
    return enemy, player, game


def make_explosive_enemy(px=0, py=0, ex=500, ey=500):
    player = FakePlayer(px, py)
    game = SimpleNamespace(
        asteroids=[],
        combat_stats=SimpleNamespace(record_damage_event=lambda **kw: None),
    )
    ExplosiveEnemy.containers = ()
    enemy = ExplosiveEnemy(ex, ey, player, game)
    return enemy, player, game


# --- LaserEnemy construction ---
def test_laser_enemy_health_uses_constant():
    enemy, _, _ = make_laser_enemy()
    assert enemy.health == C.LASER_ENEMY_MAX_HEALTH

def test_laser_enemy_max_health_uses_constant():
    enemy, _, _ = make_laser_enemy()
    assert enemy.max_health == C.LASER_ENEMY_MAX_HEALTH

def test_laser_enemy_speed_uses_constant():
    enemy, _, _ = make_laser_enemy()
    assert enemy.speed == C.LASER_ENEMY_SPEED

def test_laser_enemy_body_color_uses_constant():
    enemy, _, _ = make_laser_enemy()
    assert enemy.body_color == C.LASER_ENEMY_BODY_COLOR

def test_laser_enemy_xp_uses_constant():
    enemy, _, _ = make_laser_enemy()
    assert enemy.xp_value == C.LASER_ENEMY_XP_VALUE

def test_laser_enemy_score_uses_constant():
    enemy, _, _ = make_laser_enemy()
    assert enemy.score_value == C.LASER_ENEMY_SCORE_VALUE

def test_laser_enemy_hull_length_uses_constant():
    enemy, _, _ = make_laser_enemy()
    assert enemy.hull_length == C.LASER_ENEMY_HULL_LENGTH

def test_laser_enemy_hull_width_uses_constant():
    enemy, _, _ = make_laser_enemy()
    assert enemy.hull_width == C.LASER_ENEMY_HULL_WIDTH

def test_laser_enemy_has_platform():
    enemy, _, _ = make_laser_enemy()
    assert enemy.platform is not None

def test_laser_enemy_locked_target_pos_starts_none():
    enemy, _, _ = make_laser_enemy()
    assert enemy.locked_target_pos is None


# --- LaserEnemy._mirror_position ---
def test_mirror_position_is_opposite_player_through_screen_center():
    enemy, player, _ = make_laser_enemy(px=200, py=100, ex=500, ey=360)
    mirror = enemy._mirror_position()
    expected_x = C.SCREEN_WIDTH - 200
    expected_y = C.SCREEN_HEIGHT - 100
    assert mirror.x == pytest.approx(expected_x, abs=0.1)
    assert mirror.y == pytest.approx(expected_y, abs=0.1)

def test_mirror_position_is_center_when_player_is_at_center():
    cx, cy = C.SCREEN_WIDTH / 2, C.SCREEN_HEIGHT / 2
    enemy, player, _ = make_laser_enemy(px=int(cx), py=int(cy), ex=500, ey=360)
    mirror = enemy._mirror_position()
    assert mirror.x == pytest.approx(cx, abs=0.1)
    assert mirror.y == pytest.approx(cy, abs=0.1)


# --- LaserEnemy.move_toward_player (mirror behavior) ---
def test_laser_enemy_moves_toward_mirror_when_player_nearby():
    # Player at left edge, enemy at center — mirror is at right edge
    cx, cy = C.SCREEN_WIDTH / 2, C.SCREEN_HEIGHT / 2
    px, py = 100, int(cy)
    ex, ey = int(cx), int(cy)
    enemy, player, _ = make_laser_enemy(px=px, py=py, ex=ex, ey=ey)
    enemy.move_toward_player(0.1)
    assert enemy.velocity.x > 0

def test_laser_enemy_moves_toward_player_when_far_away():
    # Enemy far from player (> fallback dist) — should follow player
    enemy, player, _ = make_laser_enemy(px=0, py=0, ex=0, ey=int(C.LASER_ENEMY_FOLLOW_FALLBACK_DIST + 100))
    enemy.move_toward_player(0.1)
    assert enemy.velocity.y < 0

def test_laser_enemy_move_speed_equals_laser_enemy_speed():
    enemy, player, _ = make_laser_enemy(px=0, py=0, ex=500, ey=500)
    enemy.move_toward_player(0.1)
    assert enemy.velocity.length() == pytest.approx(C.LASER_ENEMY_SPEED, abs=0.1)

def test_laser_enemy_impact_timer_prevents_move():
    enemy, player, _ = make_laser_enemy(px=0, py=0, ex=500, ey=500)
    enemy.impact_timer = 0.5
    enemy.velocity = pygame.Vector2(0, 0)
    enemy.move_toward_player(0.1)
    assert enemy.velocity.length() == pytest.approx(0, abs=0.001)


# --- LaserEnemy crosshair lock ---
def test_laser_enemy_locks_target_when_timer_enters_warn_window():
    enemy, player, _ = make_laser_enemy(px=100, py=200, ex=500, ey=500)
    enemy.platform.weapons_free_timer = C.LASER_ENEMY_CROSSHAIR_WARN_TIME - 0.01
    enemy.update(0.0)
    assert enemy.locked_target_pos is not None

def test_laser_enemy_locks_to_player_position():
    enemy, player, _ = make_laser_enemy(px=100, py=200, ex=500, ey=500)
    enemy.platform.weapons_free_timer = C.LASER_ENEMY_CROSSHAIR_WARN_TIME - 0.01
    enemy.update(0.0)
    assert enemy.locked_target_pos.x == pytest.approx(100, abs=0.1)
    assert enemy.locked_target_pos.y == pytest.approx(200, abs=0.1)

def test_laser_enemy_does_not_relatch_when_already_locked():
    enemy, player, _ = make_laser_enemy(px=100, py=200, ex=500, ey=500)
    enemy.platform.weapons_free_timer = C.LASER_ENEMY_CROSSHAIR_WARN_TIME - 0.01
    enemy.update(0.0)
    player.position = pygame.Vector2(999, 999)
    enemy.update(0.0)
    assert enemy.locked_target_pos.x == pytest.approx(100, abs=0.1)

def test_laser_enemy_clears_lock_when_timer_above_warn():
    enemy, player, _ = make_laser_enemy(px=100, py=200, ex=500, ey=500)
    enemy.locked_target_pos = pygame.Vector2(100, 200)
    enemy.platform.weapons_free_timer = C.LASER_ENEMY_CROSSHAIR_WARN_TIME + 0.1
    enemy.update(0.0)
    assert enemy.locked_target_pos is None

def test_laser_enemy_faces_locked_target_pos_when_locked():
    # enemy at center-right, player directly to the right — lock snaps to that direction
    enemy, player, _ = make_laser_enemy(px=700, py=500, ex=500, ey=500)
    enemy.platform.weapons_free_timer = C.LASER_ENEMY_CROSSHAIR_WARN_TIME - 0.01
    enemy.update(0.0)
    locked_direction = enemy.locked_target_pos - enemy.position
    expected_rotation = pygame.Vector2(0, -1).angle_to(locked_direction)
    assert enemy.rotation == pytest.approx(expected_rotation, abs=0.1)

def test_laser_enemy_faces_locked_pos_not_current_player_after_player_moves():
    enemy, player, _ = make_laser_enemy(px=700, py=500, ex=500, ey=500)
    enemy.platform.weapons_free_timer = C.LASER_ENEMY_CROSSHAIR_WARN_TIME - 0.01
    enemy.update(0.0)  # locks to player at (700, 500)
    player.position = pygame.Vector2(500, 700)  # player moves somewhere else
    enemy.update(0.0)
    locked_direction = enemy.locked_target_pos - enemy.position
    expected_rotation = pygame.Vector2(0, -1).angle_to(locked_direction)
    assert enemy.rotation == pytest.approx(expected_rotation, abs=0.1)


# --- LaserEnemy.shoot ---
def test_laser_enemy_shoot_returns_zero_without_lock():
    enemy, _, _ = make_laser_enemy()
    enemy.platform.weapons_free_timer = 0
    assert enemy.shoot() == 0

def test_laser_enemy_shoot_clears_lock_after_firing():
    LaserBeamVE.containers = ()
    enemy, player, game = make_laser_enemy(px=0, py=0, ex=500, ey=500)
    enemy.platform.weapons_free_timer = 0
    enemy.locked_target_pos = pygame.Vector2(0, 0)
    enemy.shoot()
    assert enemy.locked_target_pos is None

def test_laser_enemy_shoot_not_fired_when_not_in_airspace():
    enemy, player, game = make_laser_enemy(px=0, py=0, ex=500, ey=500)
    space_a = object()
    space_b = object()
    enemy.airspace = space_a
    enemy.game = SimpleNamespace(current_space=space_b, asteroids=game.asteroids,
        combat_stats=game.combat_stats)
    enemy.platform.weapons_free_timer = 0
    enemy.locked_target_pos = pygame.Vector2(0, 0)
    assert enemy.shoot() == 0


# --- LaserEnemy._fire_laser_at ---
def test_laser_fire_direction_toward_locked_not_ship_facing():
    LaserBeamVE.containers = ()
    enemy, player, game = make_laser_enemy(ex=0, ey=500)
    enemy.rotation = 90  # ship faces right
    player.position = pygame.Vector2(9999, 9999)
    target_pos = pygame.Vector2(0, 0)  # directly above enemy
    asteroid = FakeAsteroid(0, 250, radius=20)  # on the vertical ray, not on the rightward ray
    game.asteroids = [asteroid]
    enemy.asteroids = game.asteroids
    enemy._fire_laser_at(target_pos)
    assert asteroid.health < 50

def test_laser_fire_hits_player_when_on_ray():
    LaserBeamVE.containers = ()
    enemy, player, game = make_laser_enemy(ex=0, ey=500)
    player.position = pygame.Vector2(0, 200)
    target_pos = pygame.Vector2(0, 50)
    damaged_calls = []
    player.damaged = lambda: (damaged_calls.append(1) or (C.LIFE_LOSS_SCORE, 2))
    enemy._fire_laser_at(target_pos)
    assert len(damaged_calls) == 1

def test_laser_fire_does_not_damage_player_when_invincible():
    LaserBeamVE.containers = ()
    enemy, player, game = make_laser_enemy(ex=0, ey=500)
    player.position = pygame.Vector2(0, 200)
    player.can_be_damaged = False
    target_pos = pygame.Vector2(0, 50)
    damaged_calls = []
    player.damaged = lambda: (damaged_calls.append(1) or (C.LIFE_LOSS_SCORE, 2))
    enemy._fire_laser_at(target_pos)
    assert damaged_calls == []

def test_laser_fire_routes_player_lives_to_hud():
    LaserBeamVE.containers = ()
    enemy, player, game = make_laser_enemy(ex=0, ey=500)
    player.position = pygame.Vector2(0, 200)
    target_pos = pygame.Vector2(0, 50)
    enemy._fire_laser_at(target_pos)
    assert len(game.HUD.lives_updates) == 1

def test_laser_fire_hits_enemy_when_on_ray():
    LaserBeamVE.containers = ()
    Enemy.containers = ()
    EnemyKillExplosionVE.containers = ()
    enemy, player, game = make_laser_enemy(ex=0, ey=500)
    player.position = pygame.Vector2(9999, 9999)
    enemy_group = pygame.sprite.Group()
    other_enemy = Enemy(0, 200, player)
    enemy_group.add(other_enemy)
    game.enemies = [enemy, other_enemy]
    target_pos = pygame.Vector2(0, 50)
    enemy._fire_laser_at(target_pos)
    assert other_enemy.health < C.ENEMY_MAX_HEALTH

def test_laser_fire_does_not_damage_self():
    LaserBeamVE.containers = ()
    enemy, player, game = make_laser_enemy(ex=0, ey=500)
    player.position = pygame.Vector2(9999, 9999)
    game.enemies = [enemy]
    target_pos = pygame.Vector2(0, 0)
    health_before = enemy.health
    enemy._fire_laser_at(target_pos)
    assert enemy.health == health_before

def test_laser_fire_extends_past_locked_position():
    LaserBeamVE.containers = ()
    enemy, player, game = make_laser_enemy(ex=0, ey=500)
    player.position = pygame.Vector2(0, 0)  # 500 units above enemy
    target_pos = pygame.Vector2(0, 300)  # locked 200 units away
    damaged_calls = []
    player.damaged = lambda: (damaged_calls.append(1) or (C.LIFE_LOSS_SCORE, 2))
    enemy._fire_laser_at(target_pos)
    assert len(damaged_calls) == 1

def test_laser_fire_hits_closest_of_asteroid_and_player():
    LaserBeamVE.containers = ()
    enemy, player, game = make_laser_enemy(ex=0, ey=500)
    player.position = pygame.Vector2(0, 100)  # 400 units above
    asteroid = FakeAsteroid(0, 400, radius=20)  # 100 units above (closer)
    game.asteroids = [asteroid]
    enemy.asteroids = game.asteroids
    target_pos = pygame.Vector2(0, 0)
    damaged_calls = []
    player.damaged = lambda: (damaged_calls.append(1) or (C.LIFE_LOSS_SCORE, 2))
    enemy._fire_laser_at(target_pos)
    assert asteroid.health < 50
    assert damaged_calls == []

def test_laser_fire_routes_enemy_kill_score_to_hud():
    LaserBeamVE.containers = ()
    Enemy.containers = ()
    EnemyKillExplosionVE.containers = ()
    enemy, player, game = make_laser_enemy(ex=0, ey=500)
    player.position = pygame.Vector2(9999, 9999)
    enemy_group = pygame.sprite.Group()
    other_enemy = Enemy(0, 200, player)
    enemy_group.add(other_enemy)
    other_enemy.health = 1
    game.enemies = [other_enemy]
    target_pos = pygame.Vector2(0, 50)
    enemy._fire_laser_at(target_pos)
    assert C.ENEMY_SCORE_VALUE in game.HUD.score_updates

def test_laser_fire_routes_enemy_kill_xp_to_experience():
    LaserBeamVE.containers = ()
    Enemy.containers = ()
    EnemyKillExplosionVE.containers = ()
    enemy, player, game = make_laser_enemy(ex=0, ey=500)
    player.position = pygame.Vector2(9999, 9999)
    enemy_group = pygame.sprite.Group()
    other_enemy = Enemy(0, 200, player)
    enemy_group.add(other_enemy)
    other_enemy.health = 1
    game.enemies = [other_enemy]
    target_pos = pygame.Vector2(0, 50)
    enemy._fire_laser_at(target_pos)
    assert len(game.experience.xp_added) > 0


# --- LaserEnemy.draw_body ---
def test_laser_enemy_draw_body_draws_two_triangles():
    enemy, _, _ = make_laser_enemy()
    poly_calls = []
    with patch("entities.enemy.pygame.draw.polygon",
               side_effect=lambda s, color, pts, *a: poly_calls.append(pts)):
        enemy.draw_body(None)
    assert len(poly_calls) == 2
    assert all(len(pts) == 3 for pts in poly_calls)

def test_laser_enemy_draw_body_nose_is_forward_of_base():
    enemy, _, _ = make_laser_enemy(ex=500, ey=500)
    enemy.rotation = 0
    poly_calls = []
    with patch("entities.enemy.pygame.draw.polygon",
               side_effect=lambda s, color, pts, *a: poly_calls.append(pts)):
        enemy.draw_body(None)
    pts = poly_calls[0]
    nose_y = min(p.y for p in pts)
    base_y = max(p.y for p in pts)
    assert nose_y < enemy.position.y
    assert base_y > enemy.position.y

def test_laser_enemy_draw_body_uses_elemental_glow_when_elemental():
    enemy, _, _ = make_laser_enemy()
    enemy.element = Element.SOLAR
    glow_calls = []
    with patch("entities.enemy.draw_elemental_glow_poly",
               side_effect=lambda s, corners, el: glow_calls.append(el)), \
         patch("entities.enemy.pygame.draw.polygon"):
        enemy.draw_body(None)
    assert glow_calls == [Element.SOLAR]


# --- LaserEnemy ray/edge helpers ---
def test_ray_hits_asteroid_when_ray_passes_through():
    enemy, _, _ = make_laser_enemy()
    start = pygame.Vector2(0, 0)
    direction = pygame.Vector2(1, 0)

    class FakeAst:
        position = pygame.Vector2(100, 0)
        radius = 15

    hit, dist = enemy._ray_hits_asteroid(start, direction, FakeAst())
    assert hit is True
    assert dist == pytest.approx(100, abs=0.1)

def test_ray_misses_asteroid_when_perpendicular_distance_too_large():
    enemy, _, _ = make_laser_enemy()
    start = pygame.Vector2(0, 0)
    direction = pygame.Vector2(1, 0)

    class FakeAst:
        position = pygame.Vector2(100, 20)
        radius = 15

    hit, _ = enemy._ray_hits_asteroid(start, direction, FakeAst())
    assert hit is False

def test_ray_misses_asteroid_behind_start():
    enemy, _, _ = make_laser_enemy()
    start = pygame.Vector2(200, 0)
    direction = pygame.Vector2(1, 0)

    class FakeAst:
        position = pygame.Vector2(100, 0)
        radius = 15

    hit, _ = enemy._ray_hits_asteroid(start, direction, FakeAst())
    assert hit is False

def test_screen_edge_endpoint_right():
    enemy, _, _ = make_laser_enemy()
    start = pygame.Vector2(C.SCREEN_WIDTH / 2, C.SCREEN_HEIGHT / 2)
    direction = pygame.Vector2(1, 0)
    end = enemy._screen_edge_endpoint(start, direction)
    assert end.x == pytest.approx(C.SCREEN_WIDTH, abs=0.1)

def test_screen_edge_endpoint_up():
    enemy, _, _ = make_laser_enemy()
    start = pygame.Vector2(C.SCREEN_WIDTH / 2, C.SCREEN_HEIGHT / 2)
    direction = pygame.Vector2(0, -1)
    end = enemy._screen_edge_endpoint(start, direction)
    assert end.y == pytest.approx(0, abs=0.1)


# --- ExplosiveEnemy construction ---
def test_explosive_enemy_health_uses_constant():
    enemy, _, _ = make_explosive_enemy()
    assert enemy.health == C.EXPLOSIVE_ENEMY_MAX_HEALTH

def test_explosive_enemy_max_health_uses_constant():
    enemy, _, _ = make_explosive_enemy()
    assert enemy.max_health == C.EXPLOSIVE_ENEMY_MAX_HEALTH

def test_explosive_enemy_speed_uses_constant():
    enemy, _, _ = make_explosive_enemy()
    assert enemy.speed == C.EXPLOSIVE_ENEMY_SPEED

def test_explosive_enemy_body_color_uses_constant():
    enemy, _, _ = make_explosive_enemy()
    assert enemy.body_color == C.EXPLOSIVE_ENEMY_BODY_COLOR

def test_explosive_enemy_xp_uses_constant():
    enemy, _, _ = make_explosive_enemy()
    assert enemy.xp_value == C.EXPLOSIVE_ENEMY_XP_VALUE

def test_explosive_enemy_score_uses_constant():
    enemy, _, _ = make_explosive_enemy()
    assert enemy.score_value == C.EXPLOSIVE_ENEMY_SCORE_VALUE

def test_explosive_enemy_hull_is_square():
    enemy, _, _ = make_explosive_enemy()
    assert enemy.hull_width == C.EXPLOSIVE_ENEMY_HULL_SIZE
    assert enemy.hull_length == C.EXPLOSIVE_ENEMY_HULL_SIZE

def test_explosive_enemy_has_platform():
    enemy, _, _ = make_explosive_enemy()
    assert enemy.platform is not None

def test_explosive_enemy_platform_range_uses_constant():
    enemy, _, _ = make_explosive_enemy()
    assert enemy.platform.range == C.EXPLOSIVE_ENEMY_WEAPONS_RANGE

def test_explosive_enemy_platform_timer_max_uses_constant():
    enemy, _, _ = make_explosive_enemy()
    assert enemy.platform.weapons_free_timer_max == C.EXPLOSIVE_ENEMY_WEAPONS_FREE_TIMER

def test_explosive_enemy_platform_projectile_speed_uses_constant():
    enemy, _, _ = make_explosive_enemy()
    assert enemy.platform.projectile_speed == C.EXPLOSIVE_ENEMY_PROJECTILE_SPEED


# --- ExplosiveEnemy._find_best_explosion_pos ---
def test_find_best_explosion_pos_returns_player_when_alone():
    enemy, player, game = make_explosive_enemy(px=100, py=200, ex=500, ey=500)
    pos = enemy._find_best_explosion_pos()
    assert pos.x == pytest.approx(100, abs=0.1)
    assert pos.y == pytest.approx(200, abs=0.1)

def test_find_best_explosion_pos_returns_cluster_over_isolated_player():
    enemy, player, game = make_explosive_enemy(px=9999, py=9999, ex=500, ey=500)
    a1 = FakeAsteroid(10, 10, radius=15)
    a2 = FakeAsteroid(20, 10, radius=15)
    a3 = FakeAsteroid(15, 20, radius=15)
    game.asteroids = [a1, a2, a3]
    enemy.asteroids = game.asteroids
    pos = enemy._find_best_explosion_pos()
    assert pos.distance_to(pygame.Vector2(9999, 9999)) > pos.distance_to(pygame.Vector2(15, 13))

def test_find_best_explosion_pos_returns_player_when_no_asteroids():
    enemy, player, game = make_explosive_enemy(px=300, py=400, ex=500, ey=500)
    pos = enemy._find_best_explosion_pos()
    assert pos.x == pytest.approx(300, abs=0.1)
    assert pos.y == pytest.approx(400, abs=0.1)


# --- ExplosiveEnemy.move_toward_player ---
def test_explosive_enemy_moves_toward_cluster():
    enemy, player, game = make_explosive_enemy(px=9999, py=9999, ex=500, ey=500)
    a1 = FakeAsteroid(100, 500, radius=15)
    a2 = FakeAsteroid(110, 500, radius=15)
    game.asteroids = [a1, a2]
    enemy.asteroids = game.asteroids
    enemy.move_toward_player(0.1)
    assert enemy.velocity.x < 0

def test_explosive_enemy_move_speed_equals_explosive_enemy_speed():
    enemy, player, game = make_explosive_enemy(px=0, py=0, ex=500, ey=500)
    enemy.move_toward_player(0.1)
    assert enemy.velocity.length() == pytest.approx(C.EXPLOSIVE_ENEMY_SPEED, abs=0.1)

def test_explosive_enemy_impact_timer_prevents_move():
    enemy, player, game = make_explosive_enemy(px=0, py=0, ex=500, ey=500)
    enemy.impact_timer = 0.5
    enemy.velocity = pygame.Vector2(0, 0)
    enemy.move_toward_player(0.1)
    assert enemy.velocity.length() == pytest.approx(0, abs=0.001)


# --- ExplosiveEnemy.draw_body ---
def test_explosive_enemy_draw_body_draws_four_corners():
    enemy, _, _ = make_explosive_enemy()
    poly_calls = []
    with patch("entities.enemy.pygame.draw.polygon",
               side_effect=lambda s, color, pts, *a: poly_calls.append(pts)):
        enemy.draw_body(None)
    assert len(poly_calls) == 1
    assert len(poly_calls[0]) == 4

def test_explosive_enemy_update_ticks_platform():
    enemy, _, _ = make_explosive_enemy(ex=500, ey=500)
    enemy.platform.weapons_free_timer = 5.0
    enemy.update(1.0)
    assert enemy.platform.weapons_free_timer < 5.0
