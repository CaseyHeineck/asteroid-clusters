import pygame
import pytest
from core import constants as C
from core.element import Element
from entities.decoy import Decoy
from entities.drone import Drone, ExplosiveDrone, KineticDrone, SlayerDrone, DebuffDrone, SentinelDrone
from entities.projectile import FuseBomb, Grenade, HomingMissile, Kinetic, Plasma, ProximityMine, Rocket
from entities.weaponsplatform import BreachPlatform, CascadePlatform, DecoyPlatform, EvasionPlatform, FinisherPlatform, FuseBombPlatform, GrenadePlatform, HealPlatform, HomingMissilePlatform, OverchargePlatform, ProximityMinePlatform, ResourceBoostPlatform
from ui.visualeffect import LaserBeamVE, MuzzleFlareVE, RocketHitExplosionVE

class FakePlayer:
    def __init__(self):
        self.position = pygame.Vector2(0, 0)

class FakeCombatStats:
    def add_repaired(self, source, amount): pass

class FakeSentinelGame:
    combat_stats = FakeCombatStats()

class FakeSentinelPlayer:
    def __init__(self):
        self.position = pygame.Vector2(0, 0)
        self.radius = C.PLAYER_RADIUS
        self.collision_damage = C.PLAYER_COLLISION_DAMAGE
        self.game = FakeSentinelGame()
        self.shield = False
    def alive(self):
        return True

# --- Drone.collides_with ---
def test_drone_collides_with_always_returns_false():
    drone = SlayerDrone(FakePlayer(), [])
    other = SlayerDrone(FakePlayer(), [])
    assert not drone.collides_with(other)

# --- SlayerDrone.get_charge_ratio ---
def test_charge_ratio_is_1_when_fully_charged():
    drone = SlayerDrone(FakePlayer(), [])
    drone.platform.weapons_free_timer = 0
    assert drone.platform.get_charge_ratio() == pytest.approx(1.0, abs=0.001)

def test_charge_ratio_is_0_when_just_fired():
    drone = SlayerDrone(FakePlayer(), [])
    drone.platform.weapons_free_timer = drone.platform.weapons_free_timer_max
    assert drone.platform.get_charge_ratio() == pytest.approx(0.0, abs=0.001)

def test_charge_ratio_is_half_at_midpoint():
    drone = SlayerDrone(FakePlayer(), [])
    drone.platform.weapons_free_timer = drone.platform.weapons_free_timer_max / 2
    assert drone.platform.get_charge_ratio() == pytest.approx(0.5, abs=0.001)

def test_charge_ratio_is_1_when_timer_max_is_zero():
    drone = SlayerDrone(FakePlayer(), [])
    drone.platform.weapons_free_timer_max = 0
    assert drone.platform.get_charge_ratio() == 1

# --- SlayerDrone.lerp_color ---
def test_lerp_color_at_0_returns_start():
    drone = SlayerDrone(FakePlayer(), [])
    result = drone.platform.lerp_color((0, 0, 0), (255, 255, 255), 0)
    assert result == (0, 0, 0)

def test_lerp_color_at_1_returns_end():
    drone = SlayerDrone(FakePlayer(), [])
    result = drone.platform.lerp_color((0, 0, 0), (255, 255, 255), 1)
    assert result == (255, 255, 255)

def test_lerp_color_at_half_returns_midpoint():
    drone = SlayerDrone(FakePlayer(), [])
    result = drone.platform.lerp_color((0, 0, 0), (100, 100, 100), 0.5)
    assert result == (50, 50, 50)

def test_lerp_color_clamps_t_below_zero():
    drone = SlayerDrone(FakePlayer(), [])
    result = drone.platform.lerp_color((10, 10, 10), (100, 100, 100), -1)
    assert result == (10, 10, 10)

def test_lerp_color_clamps_t_above_one():
    drone = SlayerDrone(FakePlayer(), [])
    result = drone.platform.lerp_color((10, 10, 10), (100, 100, 100), 2)
    assert result == (100, 100, 100)

# --- SlayerDrone.get_platform_color ---
def test_platform_color_when_fully_charged_is_last_in_sequence():
    drone = SlayerDrone(FakePlayer(), [])
    drone.platform.weapons_free_timer = 0
    color = drone.platform.get_platform_color()
    assert color == C.LASER_RED

def test_platform_color_when_uncharged_is_first_in_sequence():
    drone = SlayerDrone(FakePlayer(), [])
    drone.platform.weapons_free_timer = drone.platform.weapons_free_timer_max
    color = drone.platform.get_platform_color()
    assert color == C.INDIGO

# --- Drone.acquire_target ---
class FakeAsteroid:
    def __init__(self, x, y, health=10):
        self.position = pygame.Vector2(x, y)
        self.health = health

class FakeEnemy:
    def __init__(self, x, y, health=10, airspace=None):
        self.position = pygame.Vector2(x, y)
        self.health = health
        self.airspace = airspace

class FakeDroneGame:
    def __init__(self, enemies=None, current_space=None):
        self.enemies = enemies or []
        self.current_space = current_space

class FakePlayerWithGame:
    def __init__(self, game=None):
        self.position = pygame.Vector2(0, 0)
        self.game = game or FakeDroneGame()

def test_acquire_target_ignores_asteroids_outside_range():
    drone = SlayerDrone(FakePlayer(), [])
    far_asteroid = FakeAsteroid(9999, 9999)
    drone.asteroids = [far_asteroid]
    drone.acquire_target()
    assert drone.target is None

def test_acquire_target_selects_healthiest_in_range():
    player = FakePlayer()
    player.position = pygame.Vector2(0, 0)
    weak = FakeAsteroid(10, 0, health=5)
    strong = FakeAsteroid(10, 0, health=20)
    drone = SlayerDrone(player, [weak, strong])
    drone.acquire_target()
    assert drone.target is strong

def test_acquire_target_none_when_no_asteroids():
    drone = SlayerDrone(FakePlayer(), [])
    drone.acquire_target()
    assert drone.target is None

# --- Drone.aim_at_target ---
def test_aim_at_target_is_no_op_when_target_is_none():
    drone = SlayerDrone(FakePlayer(), [])
    drone.rotation = 42.0
    drone.target = None
    drone.aim_at_target()
    assert drone.rotation == 42.0

def test_aim_at_target_sets_rotation_toward_target():
    drone = SlayerDrone(FakePlayer(), [])
    drone.position = pygame.Vector2(0, 0)
    drone.target = FakeAsteroid(0, -100)
    drone.aim_at_target()
    assert drone.rotation == pytest.approx(0.0, abs=0.1)

# --- Drone.orbit_player ---
def test_orbit_player_increments_orbit_angle():
    drone = SlayerDrone(FakePlayer(), [])
    initial_angle = drone.orbit_angle
    drone.orbit_player(1.0)
    assert drone.orbit_angle == pytest.approx(initial_angle + C.DRONE_ORBIT_SPEED, abs=0.001)

def test_orbit_player_positions_drone_relative_to_player():
    player = FakePlayer()
    player.position = pygame.Vector2(100, 100)
    drone = SlayerDrone(player, [])
    drone.orbit_angle = 0
    drone.orbit_player(0)
    expected = player.position + pygame.Vector2(C.DRONE_ORBIT_RADIUS, 0).rotate(0)
    assert drone.position == expected

# --- Drone.shoot ---
def test_shoot_returns_zero_when_on_cooldown():
    drone = SlayerDrone(FakePlayer(), [])
    drone.platform.weapons_free_timer = 1.0
    drone.target = FakeAsteroid(10, 0)
    assert drone.shoot() == 0

def test_shoot_does_not_reset_timer_when_on_cooldown():
    drone = SlayerDrone(FakePlayer(), [])
    drone.platform.weapons_free_timer = 1.0
    drone.target = FakeAsteroid(10, 0)
    drone.shoot()
    assert drone.platform.weapons_free_timer == 1.0

def test_shoot_returns_zero_when_no_target():
    drone = SlayerDrone(FakePlayer(), [])
    drone.platform.weapons_free_timer = 0
    drone.target = None
    assert drone.shoot() == 0

# --- SentinelPlatform.sentinel_update ---
class FakeShieldProxy:
    health = 10
    max_health = 10
    def alive(self):
        return True

def test_sentinel_shield_create_timer_decrements():
    drone = SentinelDrone(FakeSentinelPlayer(), [])
    drone.shield_create_timer = 1.0
    drone.player_shield = FakeShieldProxy()
    drone.platform.sentinel_update(drone,0.5)
    assert drone.shield_create_timer == pytest.approx(0.5, abs=0.001)

def test_sentinel_shield_repair_timer_decrements():
    drone = SentinelDrone(FakeSentinelPlayer(), [])
    drone.shield_repair_timer = 1.0
    drone.player_shield = FakeShieldProxy()
    drone.platform.sentinel_update(drone,0.4)
    assert drone.shield_repair_timer == pytest.approx(0.6, abs=0.001)

def test_sentinel_creates_shield_when_timer_is_zero_and_no_shield():
    drone = SentinelDrone(FakeSentinelPlayer(), [])
    drone.player_shield = None
    drone.shield_create_timer = 0
    drone.platform.sentinel_update(drone,0)
    assert drone.player_shield is not None

def test_sentinel_sets_player_shield_flag_when_shield_created():
    player = FakeSentinelPlayer()
    drone = SentinelDrone(player, [])
    drone.player_shield = None
    drone.shield_create_timer = 0
    drone.platform.sentinel_update(drone,0)
    assert player.shield is True

def test_sentinel_repairs_shield_health_when_timer_expired():
    player = FakeSentinelPlayer()
    drone = SentinelDrone(player, [])
    drone.shield_create_timer = 0
    drone.platform.sentinel_update(drone,0)
    shield = drone.player_shield
    pygame.sprite.Group(shield)
    shield.health = shield.max_health - 3
    drone.shield_repair_timer = 0
    drone.platform.sentinel_update(drone,0)
    assert shield.health == shield.max_health - 2

def test_sentinel_clears_player_shield_when_shield_dies_externally():
    player = FakeSentinelPlayer()
    drone = SentinelDrone(player, [])
    dead_shield = FakeShieldProxy()
    dead_shield.alive = lambda: False
    drone.player_shield = dead_shield
    drone.shield_create_timer = 1.0
    drone.platform.sentinel_update(drone,0)
    assert drone.player_shield is None
    assert player.shield is False

# --- KineticDrone.acquire_target (base: closest to player) ---
def test_kinetic_acquire_target_selects_closest_to_player_not_healthiest():
    player = FakePlayer()
    player.position = pygame.Vector2(0, 0)
    close_weak = FakeAsteroid(5, 0, health=1)
    far_strong = FakeAsteroid(200, 0, health=999)
    drone = KineticDrone(player, [close_weak, far_strong])
    drone.acquire_target()
    assert drone.target is close_weak

# --- ExplosiveDrone.platform.fire ---
def test_explosive_drone_fire_sets_launch_animation_timer():
    Rocket.containers = ()
    player = FakeSentinelPlayer()
    drone = ExplosiveDrone(player, [])
    drone.platform.launch_animation_timer = 0
    drone.platform.fire(drone)
    assert drone.platform.launch_animation_timer > 0

def test_explosive_drone_fire_returns_zero():
    Rocket.containers = ()
    player = FakeSentinelPlayer()
    drone = ExplosiveDrone(player, [])
    assert drone.platform.fire(drone) == 0

# --- KineticDrone.platform.fire ---
def test_kinetic_drone_fire_returns_zero():
    Kinetic.containers = ()
    MuzzleFlareVE.containers = ()
    player = FakeSentinelPlayer()
    drone = KineticDrone(player, [])
    assert drone.platform.fire(drone) == 0

# --- DebuffDrone.platform.fire ---
def test_plasma_drone_fire_returns_zero():
    Plasma.containers = ()
    player = FakeSentinelPlayer()
    drone = DebuffDrone(player, [])
    assert drone.platform.fire(drone) == 0

# --- Drone.shoot (timer reset after firing) ---
def test_shoot_sets_timer_to_max_after_firing():
    Rocket.containers = ()
    player = FakeSentinelPlayer()
    drone = ExplosiveDrone(player, [])
    drone.platform.weapons_free_timer = 0
    drone.target = FakeAsteroid(10, 0)
    drone.shoot()
    assert drone.platform.weapons_free_timer == drone.platform.weapons_free_timer_max

# --- Drone.update (timer decrement) ---
def test_update_decrements_weapons_free_timer():
    drone = SlayerDrone(FakePlayer(), [])
    drone.platform.weapons_free_timer = 1.0
    drone.update(0.4)
    assert drone.platform.weapons_free_timer == pytest.approx(0.6, abs=0.001)

def test_update_clamps_timer_to_zero():
    drone = SlayerDrone(FakePlayer(), [])
    drone.platform.weapons_free_timer = 0.1
    drone.update(1.0)
    assert drone.platform.weapons_free_timer == 0.0

# --- ExplosiveDrone.update (launch animation timer) ---
def test_explosive_drone_update_decrements_launch_animation_timer():
    Rocket.containers = ()
    player = FakeSentinelPlayer()
    drone = ExplosiveDrone(player, [])
    drone.platform.launch_animation_timer = 1.0
    drone.update(0.3)
    assert drone.platform.launch_animation_timer == pytest.approx(0.7, abs=0.001)

def test_explosive_drone_update_clamps_launch_timer_to_zero():
    Rocket.containers = ()
    player = FakeSentinelPlayer()
    drone = ExplosiveDrone(player, [])
    drone.platform.launch_animation_timer = 0.1
    drone.update(5.0)
    assert drone.platform.launch_animation_timer == 0.0

# --- KineticDrone.acquire_target (range filtering) ---
def test_kinetic_acquire_target_ignores_asteroids_outside_range():
    player = FakePlayer()
    player.position = pygame.Vector2(0, 0)
    drone = KineticDrone(player, [])
    drone.position = pygame.Vector2(0, 0)
    far = FakeAsteroid(C.KINETIC_DRONE_WEAPONS_RANGE + 100, 0)
    drone.asteroids = [far]
    drone.acquire_target()
    assert drone.target is None

def test_kinetic_acquire_target_picks_asteroid_within_range():
    player = FakePlayer()
    player.position = pygame.Vector2(0, 0)
    drone = KineticDrone(player, [])
    drone.position = pygame.Vector2(0, 0)
    near = FakeAsteroid(10, 0)
    drone.asteroids = [near]
    drone.acquire_target()
    assert drone.target is near

# --- SlayerDrone.acquire_target (same-health tiebreaker) ---
def test_laser_acquire_target_picks_closest_to_player_when_health_tied():
    player = FakePlayer()
    player.position = pygame.Vector2(0, 0)
    close = FakeAsteroid(10, 0, health=10)
    far = FakeAsteroid(50, 0, health=10)
    drone = SlayerDrone(player, [close, far])
    drone.acquire_target()
    assert drone.target is close

# --- SentinelPlatform.sentinel_update (additional cases) ---
def test_sentinel_does_not_create_shield_when_create_timer_active():
    drone = SentinelDrone(FakeSentinelPlayer(), [])
    drone.player_shield = None
    drone.shield_create_timer = 1.0
    drone.platform.sentinel_update(drone,0)
    assert drone.player_shield is None

def test_sentinel_does_not_repair_when_shield_at_full_health():
    player = FakeSentinelPlayer()
    drone = SentinelDrone(player, [])
    drone.shield_create_timer = 0
    drone.platform.sentinel_update(drone,0)
    shield = drone.player_shield
    pygame.sprite.Group(shield)
    assert shield.health == shield.max_health
    drone.shield_repair_timer = 0
    drone.platform.sentinel_update(drone,0)
    assert shield.health == shield.max_health

def test_sentinel_repair_timer_resets_after_repair():
    player = FakeSentinelPlayer()
    drone = SentinelDrone(player, [])
    drone.shield_create_timer = 0
    drone.platform.sentinel_update(drone,0)
    shield = drone.player_shield
    pygame.sprite.Group(shield)
    shield.health = shield.max_health - 3
    drone.shield_repair_timer = 0
    drone.platform.sentinel_update(drone,0)
    assert drone.shield_repair_timer > 0

def test_sentinel_calls_add_repaired_on_combat_stats():
    player = FakeSentinelPlayer()
    drone = SentinelDrone(player, [])
    drone.shield_create_timer = 0
    drone.platform.sentinel_update(drone,0)
    shield = drone.player_shield
    pygame.sprite.Group(shield)
    shield.health = shield.max_health - 3
    drone.shield_repair_timer = 0
    repaired_calls = []
    player.game.combat_stats.add_repaired = lambda src, amt: repaired_calls.append((src, amt))
    drone.platform.sentinel_update(drone,0)
    assert len(repaired_calls) == 1
    assert repaired_calls[0][1] == 1

# --- Drone.acquire_target: enemy targeting ---
def test_drone_targets_enemy_over_asteroid_when_both_in_range():
    space = object()
    enemy = FakeEnemy(10, 0, airspace=space)
    game = FakeDroneGame(enemies=[enemy], current_space=space)
    player = FakePlayerWithGame(game)
    asteroid = FakeAsteroid(10, 0)
    drone = KineticDrone(player, [asteroid])
    drone.position = pygame.Vector2(0, 0)
    drone.acquire_target()
    assert drone.target is enemy

def test_drone_falls_back_to_asteroid_when_no_enemy_in_range():
    space = object()
    game = FakeDroneGame(enemies=[], current_space=space)
    player = FakePlayerWithGame(game)
    asteroid = FakeAsteroid(10, 0)
    drone = KineticDrone(player, [asteroid])
    drone.position = pygame.Vector2(0, 0)
    drone.acquire_target()
    assert drone.target is asteroid

def test_drone_ignores_enemy_in_different_airspace():
    space_a = object()
    space_b = object()
    enemy = FakeEnemy(10, 0, airspace=space_a)
    game = FakeDroneGame(enemies=[enemy], current_space=space_b)
    player = FakePlayerWithGame(game)
    asteroid = FakeAsteroid(10, 0)
    drone = KineticDrone(player, [asteroid])
    drone.position = pygame.Vector2(0, 0)
    drone.acquire_target()
    assert drone.target is asteroid

def test_drone_targets_enemy_with_none_airspace_as_same_airspace():
    space = object()
    enemy = FakeEnemy(10, 0, airspace=None)
    game = FakeDroneGame(enemies=[enemy], current_space=space)
    player = FakePlayerWithGame(game)
    drone = KineticDrone(player, [])
    drone.position = pygame.Vector2(0, 0)
    drone.acquire_target()
    assert drone.target is enemy

def test_laser_drone_targets_healthiest_enemy_over_asteroid():
    space = object()
    weak_enemy = FakeEnemy(10, 0, health=5, airspace=space)
    strong_enemy = FakeEnemy(10, 0, health=50, airspace=space)
    game = FakeDroneGame(enemies=[weak_enemy, strong_enemy], current_space=space)
    player = FakePlayerWithGame(game)
    asteroid = FakeAsteroid(10, 0, health=999)
    drone = SlayerDrone(player, [asteroid])
    drone.position = pygame.Vector2(0, 0)
    drone.acquire_target()
    assert drone.target is strong_enemy

def test_laser_drone_falls_back_to_asteroid_when_no_enemy_in_range():
    space = object()
    far_enemy = FakeEnemy(9999, 0, airspace=space)
    game = FakeDroneGame(enemies=[far_enemy], current_space=space)
    player = FakePlayerWithGame(game)
    asteroid = FakeAsteroid(10, 0, health=10)
    drone = SlayerDrone(player, [asteroid])
    drone.position = pygame.Vector2(0, 0)
    drone.acquire_target()
    assert drone.target is asteroid

def test_laser_drone_ignores_enemy_in_different_airspace():
    space_a = object()
    space_b = object()
    enemy = FakeEnemy(10, 0, health=999, airspace=space_a)
    game = FakeDroneGame(enemies=[enemy], current_space=space_b)
    player = FakePlayerWithGame(game)
    asteroid = FakeAsteroid(10, 0, health=1)
    drone = SlayerDrone(player, [asteroid])
    drone.position = pygame.Vector2(0, 0)
    drone.acquire_target()
    assert drone.target is asteroid


# --- Slayer platform fire helpers ---
class FakePlatformCombatStats:
    def record_damage_event(self, **kwargs): pass

class FakePlatformGame:
    def __init__(self, enemies=None):
        self.combat_stats = FakePlatformCombatStats()
        self.enemies = enemies or []
    class experience:
        @staticmethod
        def add_xp(xp): pass

class FakePlatformTarget:
    def __init__(self, health=100, max_health=100, element=None):
        self.health = health
        self.max_health = max_health
        self.full_health = max_health
        self.position = pygame.Vector2(0, 100)
        self.element = element
        self.applied_effects = []
        self._alive = True
    def damaged(self, amount):
        self.health -= amount
        if self.health <= 0:
            self._alive = False
            return 100, 20
        return 0, 0
    def add_gameplay_effect(self, effect):
        self.applied_effects.append(effect)
    def alive(self):
        return self._alive

class FakePlatformOwner:
    def __init__(self, target=None, element=None, enemies=None):
        self.position = pygame.Vector2(0, 0)
        self.radius = 18
        self.rotation = 0
        self.target = target
        self.element = element
        self.stat_source = "test"
        self.extra_abilities = set()
        self.asteroids = []
        self.game = FakePlatformGame(enemies=enemies)
        self.player = FakePlayer()
    def get_forward_vector(self):
        return pygame.Vector2(0, -1)

def setup_laser_containers():
    from entities.projectile import LaserBeam
    LaserBeam.containers = ()
    LaserBeamVE.containers = ()
    RocketHitExplosionVE.containers = ()


# --- FinisherPlatform ---
def test_finisher_base_damage_at_full_health():
    setup_laser_containers()
    target = FakePlatformTarget(health=C.FINISHER_BASE_DAMAGE + 100, max_health=C.FINISHER_BASE_DAMAGE + 100)
    owner = FakePlatformOwner(target=target)
    p = FinisherPlatform()
    p.fire(owner)
    damage_dealt = (C.FINISHER_BASE_DAMAGE + 100) - target.health
    assert damage_dealt == C.FINISHER_BASE_DAMAGE

def test_finisher_deals_more_damage_at_50_percent_health():
    setup_laser_containers()
    max_hp = 100
    target = FakePlatformTarget(health=50, max_health=max_hp)
    owner = FakePlatformOwner(target=target)
    p = FinisherPlatform()
    p.fire(owner)
    damage_dealt = 50 - target.health
    assert damage_dealt > C.FINISHER_BASE_DAMAGE

def test_finisher_deals_more_damage_at_low_health_than_at_50_percent():
    setup_laser_containers()
    target_50 = FakePlatformTarget(health=50, max_health=100)
    target_10 = FakePlatformTarget(health=10, max_health=100)
    owner_50 = FakePlatformOwner(target=target_50)
    owner_10 = FakePlatformOwner(target=target_10)
    p = FinisherPlatform()
    p.fire(owner_50)
    p2 = FinisherPlatform()
    p2.fire(owner_10)
    damage_50 = 50 - target_50.health
    damage_10 = 10 - target_10.health
    assert damage_10 > damage_50

def test_finisher_apply_upgrade_increases_bonus_multiplier():
    p = FinisherPlatform()
    before = p.bonus_multiplier
    p.apply_upgrade("finisher_amp", 0)
    assert p.bonus_multiplier > before

def test_finisher_returns_zero_when_target_is_none():
    p = FinisherPlatform()
    owner = FakePlatformOwner(target=None)
    assert p.fire(owner) == 0


# --- BreachPlatform ---
def test_breach_damage_against_resistant_target_equals_base_damage():
    setup_laser_containers()
    target = FakePlatformTarget(health=500, max_health=500, element=Element.SOLAR)
    owner = FakePlatformOwner(target=target, element=Element.CRYO)
    p = BreachPlatform()
    p.fire(owner)
    damage_dealt = 500 - target.health
    assert damage_dealt == C.BREACH_BASE_DAMAGE

def test_breach_damage_preserves_elemental_bonus():
    setup_laser_containers()
    target = FakePlatformTarget(health=500, max_health=500, element=Element.FLUX)
    owner = FakePlatformOwner(target=target, element=Element.CRYO)
    p = BreachPlatform()
    p.fire(owner)
    damage_dealt = 500 - target.health
    assert damage_dealt > C.BREACH_BASE_DAMAGE

def test_breach_returns_zero_when_target_is_none():
    p = BreachPlatform()
    owner = FakePlatformOwner(target=None)
    assert p.fire(owner) == 0


# --- CascadePlatform ---
def test_cascade_fires_aoe_when_target_dies_with_overkill():
    setup_laser_containers()
    nearby = FakePlatformTarget(health=500, max_health=500)
    nearby.position = pygame.Vector2(0, 50)
    target = FakePlatformTarget(health=10, max_health=100)
    owner = FakePlatformOwner(target=target, enemies=[nearby])
    p = CascadePlatform()
    p.cascade_radius = 1000
    p.fire(owner)
    assert nearby.health < 500

def test_cascade_no_aoe_when_target_survives():
    setup_laser_containers()
    nearby = FakePlatformTarget(health=500, max_health=500)
    nearby.position = pygame.Vector2(0, 50)
    target = FakePlatformTarget(health=500, max_health=500)
    owner = FakePlatformOwner(target=target, enemies=[nearby])
    p = CascadePlatform()
    p.fire(owner)
    assert nearby.health == 500

def test_cascade_apply_upgrade_increases_radius():
    p = CascadePlatform()
    before = p.cascade_radius
    p.apply_upgrade("cascade_radius", 0)
    assert p.cascade_radius > before

def test_cascade_returns_zero_when_target_is_none():
    p = CascadePlatform()
    owner = FakePlatformOwner(target=None)
    assert p.fire(owner) == 0


# --- OverchargePlatform ---
def test_overcharge_has_higher_damage_than_laser():
    assert C.OVERCHARGE_DAMAGE > C.LASER_BEAM_DAMAGE

def test_overcharge_has_longer_timer_than_laser():
    assert C.OVERCHARGE_WEAPONS_FREE_TIMER > C.LASER_BEAM_WEAPONS_FREE_TIMER

def test_overcharge_returns_zero_when_target_is_none():
    p = OverchargePlatform()
    owner = FakePlatformOwner(target=None)
    assert p.fire(owner) == 0

def test_overcharge_apply_upgrade_increases_damage():
    p = OverchargePlatform()
    before = p.damage
    p.apply_upgrade("damage", 0)
    assert p.damage > before


def setup_explosive_containers():
    FuseBomb.containers = ()
    Grenade.containers = ()
    HomingMissile.containers = ()
    ProximityMine.containers = ()
    RocketHitExplosionVE.containers = ()


# --- ProximityMinePlatform ---
def test_proximity_mine_fire_spawns_at_player_position():
    setup_explosive_containers()
    spawned = []
    _orig_init = ProximityMine.__init__
    class TrackedMine(ProximityMine):
        def __init__(self, x, y, *args, **kwargs):
            spawned.append((x, y))
            super().__init__(x, y, *args, **kwargs)
    import entities.weaponsplatform as wp
    orig = wp.ProximityMine
    wp.ProximityMine = TrackedMine
    try:
        owner = FakePlatformOwner()
        owner.player.position = pygame.Vector2(200, 300)
        p = ProximityMinePlatform()
        p.fire(owner)
        assert spawned and spawned[0] == (200, 300)
    finally:
        wp.ProximityMine = orig

def test_proximity_mine_default_range_from_constants():
    p = ProximityMinePlatform()
    assert p.range == C.EXPLOSIVE_DRONE_WEAPONS_RANGE

def test_proximity_mine_default_trigger_radius_from_constants():
    p = ProximityMinePlatform()
    assert p.trigger_radius == C.PROXIMITY_MINE_TRIGGER_RADIUS

def test_proximity_mine_default_explosion_radius_from_constants():
    p = ProximityMinePlatform()
    assert p.explosion_radius == C.PROXIMITY_MINE_EXPLOSION_RADIUS

def test_proximity_mine_upgrade_increases_explosion_radius():
    p = ProximityMinePlatform()
    before = p.explosion_radius
    p.apply_upgrade("mine_radius", 0)
    assert p.explosion_radius > before

def test_proximity_mine_upgrade_increases_trigger_radius():
    p = ProximityMinePlatform()
    before = p.trigger_radius
    p.apply_upgrade("mine_radius", 0)
    assert p.trigger_radius > before


# --- GrenadePlatform ---
def test_grenade_fire_returns_zero_when_no_target():
    setup_explosive_containers()
    p = GrenadePlatform()
    owner = FakePlatformOwner(target=None)
    assert p.fire(owner) == 0

def test_grenade_fire_sets_timer_on_projectile():
    setup_explosive_containers()
    fired = []
    class TrackedGrenade(Grenade):
        def __init__(self, x, y, *args, **kwargs):
            super().__init__(x, y, *args, **kwargs)
            fired.append(self)
    import entities.weaponsplatform as wp
    orig = wp.Grenade
    wp.Grenade = TrackedGrenade
    try:
        target = FakePlatformTarget()
        owner = FakePlatformOwner(target=target)
        p = GrenadePlatform()
        p.fuse_timer_max = 2.5
        p.fire(owner)
        assert fired and fired[0].fuse_timer == pytest.approx(2.5)
    finally:
        wp.Grenade = orig

def test_grenade_fire_sets_explosion_radius_on_projectile():
    setup_explosive_containers()
    fired = []
    class TrackedGrenade(Grenade):
        def __init__(self, x, y, *args, **kwargs):
            super().__init__(x, y, *args, **kwargs)
            fired.append(self)
    import entities.weaponsplatform as wp
    orig = wp.Grenade
    wp.Grenade = TrackedGrenade
    try:
        target = FakePlatformTarget()
        owner = FakePlatformOwner(target=target)
        p = GrenadePlatform()
        p.fire(owner)
        assert fired and fired[0].explosion_radius == p.explosion_radius
    finally:
        wp.Grenade = orig

def test_grenade_default_fuse_timer_from_constants():
    p = GrenadePlatform()
    assert p.fuse_timer_max == C.GRENADE_FUSE_TIMER

def test_grenade_upgrade_increases_explosion_radius():
    p = GrenadePlatform()
    before = p.explosion_radius
    p.apply_upgrade("grenade_radius", 0)
    assert p.explosion_radius > before

def test_grenade_fuse_upgrade_decreases_timer():
    p = GrenadePlatform()
    before = p.fuse_timer_max
    p.apply_upgrade("grenade_fuse", 0)
    assert p.fuse_timer_max < before

def test_grenade_fuse_upgrade_does_not_go_below_minimum():
    p = GrenadePlatform()
    p.fuse_timer_max = 0.3
    p.apply_upgrade("grenade_fuse", 0)
    assert p.fuse_timer_max == pytest.approx(0.5)


# --- HomingMissilePlatform ---
def test_homing_missile_fire_sets_turn_rate_on_projectile():
    setup_explosive_containers()
    fired = []
    class TrackedMissile(HomingMissile):
        def __init__(self, x, y, *args, **kwargs):
            super().__init__(x, y, *args, **kwargs)
            fired.append(self)
    import entities.weaponsplatform as wp
    orig = wp.HomingMissile
    wp.HomingMissile = TrackedMissile
    try:
        target = FakePlatformTarget()
        owner = FakePlatformOwner(target=target)
        p = HomingMissilePlatform()
        p.turn_rate = 200
        p.fire(owner)
        assert fired and fired[0].turn_rate == pytest.approx(200)
    finally:
        wp.HomingMissile = orig

def test_homing_missile_fire_sets_homing_target():
    setup_explosive_containers()
    fired = []
    class TrackedMissile(HomingMissile):
        def __init__(self, x, y, *args, **kwargs):
            super().__init__(x, y, *args, **kwargs)
            fired.append(self)
    import entities.weaponsplatform as wp
    orig = wp.HomingMissile
    wp.HomingMissile = TrackedMissile
    try:
        target = FakePlatformTarget()
        owner = FakePlatformOwner(target=target)
        p = HomingMissilePlatform()
        p.fire(owner)
        assert fired and fired[0].homing_target is target
    finally:
        wp.HomingMissile = orig

def test_homing_missile_default_turn_rate_from_constants():
    p = HomingMissilePlatform()
    assert p.turn_rate == C.HOMING_MISSILE_TURN_RATE

def test_homing_missile_upgrade_increases_turn_rate():
    p = HomingMissilePlatform()
    before = p.turn_rate
    p.apply_upgrade("homing_turn_rate", 0)
    assert p.turn_rate > before

def test_homing_missile_returns_zero_when_target_is_none():
    setup_explosive_containers()
    p = HomingMissilePlatform()
    owner = FakePlatformOwner(target=None)
    assert p.fire(owner) == 0


# --- FuseBombPlatform ---
def test_fuse_bomb_fire_spawns_at_player_position():
    setup_explosive_containers()
    spawned = []
    class TrackedBomb(FuseBomb):
        def __init__(self, x, y, *args, **kwargs):
            spawned.append((x, y))
            super().__init__(x, y, *args, **kwargs)
    import entities.weaponsplatform as wp
    orig = wp.FuseBomb
    wp.FuseBomb = TrackedBomb
    try:
        owner = FakePlatformOwner()
        owner.player.position = pygame.Vector2(150, 250)
        p = FuseBombPlatform()
        p.fire(owner)
        assert spawned and spawned[0] == (150, 250)
    finally:
        wp.FuseBomb = orig

def test_fuse_bomb_default_fuse_timer_from_constants():
    p = FuseBombPlatform()
    assert p.fuse_timer_max == C.FUSE_BOMB_FUSE_TIMER

def test_fuse_bomb_default_explosion_radius_from_constants():
    p = FuseBombPlatform()
    assert p.explosion_radius == C.FUSE_BOMB_EXPLOSION_RADIUS

def test_fuse_bomb_upgrade_increases_explosion_radius():
    p = FuseBombPlatform()
    before = p.explosion_radius
    p.apply_upgrade("fuse_radius", 0)
    assert p.explosion_radius > before

def test_fuse_bomb_timer_upgrade_decreases_fuse():
    p = FuseBombPlatform()
    before = p.fuse_timer_max
    p.apply_upgrade("fuse_timer", 0)
    assert p.fuse_timer_max < before

def test_fuse_bomb_timer_upgrade_does_not_go_below_minimum():
    p = FuseBombPlatform()
    p.fuse_timer_max = 0.8
    p.apply_upgrade("fuse_timer", 0)
    assert p.fuse_timer_max == pytest.approx(1.0)

def test_fuse_bomb_has_longer_timer_than_rocket():
    assert C.FUSE_BOMB_WEAPONS_FREE_TIMER > C.EXPLOSIVE_DRONE_WEAPONS_FREE_TIMER

def test_fuse_bomb_has_larger_blast_than_rocket():
    assert C.FUSE_BOMB_EXPLOSION_RADIUS > C.ROCKET_HIT_RADIUS


# --- ProximityMine projectile ---
def test_proximity_mine_collides_with_target_inside_trigger_radius():
    mine = ProximityMine(0, 0, [])
    class FakeTarget:
        radius = 10
        position = pygame.Vector2(10, 0)
    mine.trigger_radius = 100
    assert mine.collides_with(FakeTarget())

def test_proximity_mine_does_not_collide_with_target_outside_trigger_radius():
    mine = ProximityMine(0, 0, [])
    class FakeTarget:
        radius = 5
        position = pygame.Vector2(500, 0)
    mine.trigger_radius = 55
    assert not mine.collides_with(FakeTarget())

def test_proximity_mine_handles_own_kill():
    assert ProximityMine.handles_own_kill is True

def test_proximity_mine_does_not_move_on_update():
    mine = ProximityMine(100, 200, [])
    mine.velocity = pygame.Vector2(100, 100)
    mine.update(1.0)
    assert mine.position == pygame.Vector2(100, 200)

def test_proximity_mine_does_not_detonate_twice():
    setup_explosive_containers()
    mine = ProximityMine(0, 0, [])
    mine.stat_source = "test"
    mine.combat_stats = None
    mine._detonate()
    mine._detonated = True
    score, xp = mine._detonate()
    assert score == 0 and xp == 0


# --- Grenade projectile ---
def test_grenade_handles_own_kill():
    assert Grenade.handles_own_kill is True

def test_grenade_detonates_on_timer_expiry():
    setup_explosive_containers()
    target = FakePlatformTarget(health=500)
    target.position = pygame.Vector2(0, 0)
    grenade = Grenade(0, 0, [target])
    grenade.stat_source = "test"
    grenade.combat_stats = None
    grenade.fuse_timer = 0.1
    grenade.explosion_radius = 1000
    grenade.explosion_damage = 10
    grenade.update(0.2)
    assert target.health < 500

def test_grenade_does_not_detonate_before_timer():
    setup_explosive_containers()
    target = FakePlatformTarget(health=500)
    target.position = pygame.Vector2(0, 0)
    grenade = Grenade(0, 0, [target])
    grenade.stat_source = "test"
    grenade.combat_stats = None
    grenade.fuse_timer = 5.0
    grenade.explosion_radius = 1000
    grenade.explosion_damage = 10
    grenade.update(0.1)
    assert target.health == 500

def test_grenade_does_not_detonate_twice():
    setup_explosive_containers()
    grenade = Grenade(0, 0, [])
    grenade.stat_source = "test"
    grenade.combat_stats = None
    grenade._detonate(pygame.Vector2(0, 0))
    grenade._detonated = True
    score, xp = grenade._detonate(pygame.Vector2(0, 0))
    assert score == 0 and xp == 0


# --- HomingMissile projectile ---
def test_homing_missile_handles_own_kill():
    assert HomingMissile.handles_own_kill is True

def test_homing_missile_turns_toward_target_on_update():
    from ui.visualeffect import RocketExhaustVE
    RocketExhaustVE.containers = ()
    missile = HomingMissile(0, 0, [])
    missile.stat_source = "test"
    target = FakePlatformTarget()
    target.position = pygame.Vector2(100, 0)
    missile.homing_target = target
    missile.velocity = pygame.Vector2(0, -100)
    missile.turn_rate = 360
    missile.update(1.0)
    assert missile.velocity.x > 0

def test_homing_missile_flies_straight_when_target_dead():
    from ui.visualeffect import RocketExhaustVE
    RocketExhaustVE.containers = ()
    missile = HomingMissile(0, 0, [])
    missile.stat_source = "test"
    target = FakePlatformTarget()
    target._alive = False
    target.health = 0
    target.position = pygame.Vector2(100, 0)
    missile.homing_target = target
    missile.velocity = pygame.Vector2(0, -100)
    missile.turn_rate = 360
    missile.update(0.01)
    assert missile.velocity.x == pytest.approx(0.0, abs=0.01)


# --- FuseBomb projectile ---
def test_fuse_bomb_handles_own_kill():
    assert FuseBomb.handles_own_kill is True

def test_fuse_bomb_collides_with_returns_false():
    bomb = FuseBomb(0, 0, [])
    class FakeTarget:
        radius = 10
        position = pygame.Vector2(0, 0)
    assert not bomb.collides_with(FakeTarget())

def test_fuse_bomb_detonates_on_timer_expiry():
    setup_explosive_containers()
    target = FakePlatformTarget(health=500)
    target.position = pygame.Vector2(0, 0)
    bomb = FuseBomb(0, 0, [target])
    bomb.stat_source = "test"
    bomb.combat_stats = None
    bomb.fuse_timer = 0.1
    bomb.explosion_radius = 1000
    bomb.explosion_damage = 10
    bomb.update(0.2)
    assert target.health < 500

def test_fuse_bomb_does_not_detonate_before_timer():
    setup_explosive_containers()
    target = FakePlatformTarget(health=500)
    target.position = pygame.Vector2(0, 0)
    bomb = FuseBomb(0, 0, [target])
    bomb.stat_source = "test"
    bomb.combat_stats = None
    bomb.fuse_timer = 5.0
    bomb.explosion_radius = 1000
    bomb.explosion_damage = 10
    bomb.update(0.1)
    assert target.health == 500

def test_fuse_bomb_does_not_detonate_twice():
    setup_explosive_containers()
    bomb = FuseBomb(0, 0, [])
    bomb.stat_source = "test"
    bomb.combat_stats = None
    bomb._detonate()
    bomb._detonated = True
    score, xp = bomb._detonate()
    assert score == 0 and xp == 0

# --- HealPlatform.sentinel_update ---
class FakeHUD:
    def __init__(self):
        self.activated = False
        self.max_health_val = 0
        self.health_val = 0
    def activate_health_mode(self, max_health):
        self.activated = True
        self.max_health_val = max_health
        self.health_val = max_health
    def update_player_health(self, health):
        self.health_val = health
    def update_health_max(self, max_health):
        self.max_health_val = max_health

class FakeEssence:
    def __init__(self):
        self.amount = 0
    def add(self, n):
        self.amount += n

class FakeHealGame:
    def __init__(self):
        self.HUD = FakeHUD()

class FakeHealPlayer:
    def __init__(self):
        self.position = pygame.Vector2(0, 0)
        self.lives = 3
        self.max_lives = 3
        self.uses_health = False
        self.health = 0
        self.max_health = 0
        self.game = FakeHealGame()

def test_heal_platform_activates_health_mode_on_first_update():
    player = FakeHealPlayer()
    drone = SentinelDrone(player, [], platform_class=HealPlatform)
    drone.platform.sentinel_update(drone, 0.1)
    assert player.uses_health is True

def test_heal_platform_sets_max_health_from_lives():
    player = FakeHealPlayer()
    drone = SentinelDrone(player, [], platform_class=HealPlatform)
    drone.platform.sentinel_update(drone, 0.1)
    assert player.max_health == player.max_lives * 10

def test_heal_platform_starts_at_full_health():
    player = FakeHealPlayer()
    drone = SentinelDrone(player, [], platform_class=HealPlatform)
    drone.platform.sentinel_update(drone, 0.1)
    assert player.health == player.max_health

def test_heal_platform_activates_hud_health_mode():
    player = FakeHealPlayer()
    drone = SentinelDrone(player, [], platform_class=HealPlatform)
    drone.platform.sentinel_update(drone, 0.1)
    assert player.game.HUD.activated is True

def test_heal_platform_heals_one_hp_after_interval():
    player = FakeHealPlayer()
    drone = SentinelDrone(player, [], platform_class=HealPlatform)
    drone.platform.sentinel_update(drone, 0.1)
    player.health = player.max_health - 5
    drone.platform.heal_timer = drone.platform.heal_interval - 0.01
    drone.platform.sentinel_update(drone, 0.1)
    assert player.health == player.max_health - 4

def test_heal_platform_does_not_overheal():
    player = FakeHealPlayer()
    drone = SentinelDrone(player, [], platform_class=HealPlatform)
    drone.platform.sentinel_update(drone, 0.1)
    drone.platform.heal_timer = drone.platform.heal_interval - 0.01
    drone.platform.sentinel_update(drone, 0.1)
    assert player.health == player.max_health

def test_heal_platform_resets_timer_after_heal():
    player = FakeHealPlayer()
    drone = SentinelDrone(player, [], platform_class=HealPlatform)
    drone.platform.sentinel_update(drone, 0.1)
    player.health = player.max_health - 1
    drone.platform.heal_timer = drone.platform.heal_interval
    drone.platform.sentinel_update(drone, 0.0)
    assert drone.platform.heal_timer == pytest.approx(0.0, abs=0.001)

def test_heal_platform_only_activates_once():
    player = FakeHealPlayer()
    drone = SentinelDrone(player, [], platform_class=HealPlatform)
    drone.platform.sentinel_update(drone, 0.1)
    first_max = player.max_health
    drone.platform.sentinel_update(drone, 0.1)
    assert player.max_health == first_max

# --- EvasionPlatform.sentinel_update ---
class FakeEvasionPlayer:
    def __init__(self):
        self.position = pygame.Vector2(0, 0)
        self.evasion_chance = 0.0

def test_evasion_platform_sets_evasion_chance():
    player = FakeEvasionPlayer()
    drone = SentinelDrone(player, [], platform_class=EvasionPlatform)
    drone.platform.sentinel_update(drone, 0.1)
    assert player.evasion_chance == pytest.approx(C.EVASION_CHANCE, abs=0.001)

def test_evasion_platform_updates_evasion_each_tick():
    player = FakeEvasionPlayer()
    drone = SentinelDrone(player, [], platform_class=EvasionPlatform)
    drone.platform.evasion_chance = 0.35
    drone.platform.sentinel_update(drone, 0.1)
    assert player.evasion_chance == pytest.approx(0.35, abs=0.001)

# --- ResourceBoostPlatform.sentinel_update ---
class FakeResourceGame:
    def __init__(self):
        self.essence = FakeEssence()

class FakeResourcePlayer:
    def __init__(self):
        self.position = pygame.Vector2(0, 0)
        self.game = FakeResourceGame()

def test_resource_boost_generates_essence_after_interval():
    player = FakeResourcePlayer()
    drone = SentinelDrone(player, [], platform_class=ResourceBoostPlatform)
    drone.platform.generation_timer = drone.platform.generation_interval - 0.01
    drone.platform.sentinel_update(drone, 0.1)
    assert player.game.essence.amount == C.RESOURCE_BOOST_AMOUNT

def test_resource_boost_resets_timer_after_generation():
    player = FakeResourcePlayer()
    drone = SentinelDrone(player, [], platform_class=ResourceBoostPlatform)
    drone.platform.generation_timer = drone.platform.generation_interval
    drone.platform.sentinel_update(drone, 0.0)
    assert drone.platform.generation_timer == pytest.approx(0.0, abs=0.001)

def test_resource_boost_does_not_generate_before_interval():
    player = FakeResourcePlayer()
    drone = SentinelDrone(player, [], platform_class=ResourceBoostPlatform)
    drone.platform.sentinel_update(drone, 0.1)
    assert player.game.essence.amount == 0

# --- DecoyPlatform.sentinel_update ---
class FakeDecoyGame:
    def __init__(self):
        self.decoy = None

class FakeDecoyPlayer:
    def __init__(self):
        self.position = pygame.Vector2(0, 0)
        self.game = FakeDecoyGame()

def setup_decoy_containers():
    Decoy.containers = ()

def test_decoy_platform_deploys_decoy_immediately():
    setup_decoy_containers()
    player = FakeDecoyPlayer()
    drone = SentinelDrone(player, [], platform_class=DecoyPlatform)
    drone.platform.sentinel_update(drone, 0.1)
    assert player.game.decoy is not None

def test_decoy_platform_sets_deployed_flag():
    setup_decoy_containers()
    player = FakeDecoyPlayer()
    drone = SentinelDrone(player, [], platform_class=DecoyPlatform)
    drone.platform.sentinel_update(drone, 0.1)
    assert drone.platform._deployed is True

def test_decoy_platform_expires_after_duration():
    setup_decoy_containers()
    player = FakeDecoyPlayer()
    drone = SentinelDrone(player, [], platform_class=DecoyPlatform)
    drone.platform.sentinel_update(drone, 0.1)
    drone.platform._active_timer = drone.platform.decoy_duration
    drone.platform.sentinel_update(drone, 0.0)
    assert player.game.decoy is None

def test_decoy_platform_starts_cooldown_after_expiry():
    setup_decoy_containers()
    player = FakeDecoyPlayer()
    drone = SentinelDrone(player, [], platform_class=DecoyPlatform)
    drone.platform.sentinel_update(drone, 0.1)
    drone.platform._active_timer = drone.platform.decoy_duration
    drone.platform.sentinel_update(drone, 0.0)
    assert drone.platform._cooldown_timer == pytest.approx(drone.platform.decoy_cooldown, abs=0.001)

def test_decoy_platform_does_not_redeploy_during_cooldown():
    setup_decoy_containers()
    player = FakeDecoyPlayer()
    drone = SentinelDrone(player, [], platform_class=DecoyPlatform)
    drone.platform.sentinel_update(drone, 0.1)
    drone.platform._active_timer = drone.platform.decoy_duration
    drone.platform.sentinel_update(drone, 0.0)
    assert player.game.decoy is None
    drone.platform.sentinel_update(drone, 0.1)
    assert player.game.decoy is None

def test_decoy_platform_redeploys_after_cooldown_expires():
    setup_decoy_containers()
    player = FakeDecoyPlayer()
    drone = SentinelDrone(player, [], platform_class=DecoyPlatform)
    drone.platform.sentinel_update(drone, 0.1)
    drone.platform._active_timer = drone.platform.decoy_duration
    drone.platform.sentinel_update(drone, 0.0)
    drone.platform._cooldown_timer = 0.0
    drone.platform.sentinel_update(drone, 0.0)
    assert player.game.decoy is not None
