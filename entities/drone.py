import pygame
from core import constants as C
from core.circleshape import CircleShape
from core.element import draw_elemental_glow
from entities.shield import Shield
from entities.weaponsplatform import ExplosivePlatform, KineticPlatform, LaserPlatform, PlasmaPlatform, SentinelPlatform

class Drone(CircleShape):
    def __init__(self, player, asteroids):
        super().__init__(player.position.x, player.position.y, C.DRONE_RADIUS,
            weight=C.DRONE_WEIGHT, bounciness=C.DRONE_BOUNCINESS,
            drag=C.DRONE_DRAG, rotation=0, angular_velocity=0)
        self.asteroids = asteroids
        self.player = player
        self.orbit_angle = C.DRONE_ORBIT_ANGLE_OFFSET
        self.orbit_radius = C.DRONE_ORBIT_RADIUS
        self.orbit_speed = C.DRONE_ORBIT_SPEED
        self.target = None
        self.element = None
        self.extra_abilities = set()
        self.body_color = C.WHITE
        self.body_line_width = C.DRONE_LINE_WIDTH
        self.stat_source = None
        self.platform = None

    def _same_airspace(self, enemy):
        airspace = getattr(enemy, 'airspace', None)
        if airspace is None:
            return True
        current = getattr(self.game, 'current_space', None)
        return current is None or airspace == current

    def acquire_target(self):
        if self.platform is None:
            return
        target_range = self.platform.range
        closest_so_far = float("inf")
        self.target = None
        for enemy in getattr(self.game, 'enemies', []):
            if not self._same_airspace(enemy):
                continue
            drone_distance = self.position.distance_to(enemy.position)
            player_distance = self.player.position.distance_to(enemy.position)
            if drone_distance <= target_range and player_distance < closest_so_far:
                closest_so_far = player_distance
                self.target = enemy
        if self.target is not None:
            return
        closest_so_far = float("inf")
        for asteroid in self.asteroids:
            player_distance = self.player.position.distance_to(asteroid.position)
            drone_distance = self.position.distance_to(asteroid.position)
            if drone_distance <= target_range and player_distance < closest_so_far:
                closest_so_far = player_distance
                self.target = asteroid

    def aim_at_target(self):
        if self.target is None:
            return
        direction = self.target.position - self.position
        if direction.length_squared() > 0:
            self.rotation = pygame.Vector2(0, -1).angle_to(direction)

    def shoot(self):
        if self.platform is None or not self.platform.can_fire() or self.target is None:
            return 0
        return self.platform.fire(self) or 0

    def draw_body(self, screen):
        if self.element is not None:
            draw_elemental_glow(screen, self.position, self.radius, self.element)
        pygame.draw.circle(screen, self.body_color, self.position, self.radius, self.body_line_width)

    def draw(self, screen):
        self.draw_body(screen)
        if self.platform is not None:
            self.platform.draw(screen, self)

    def update(self, dt):
        self.orbit_player(dt)
        if self.platform is not None:
            self.platform.tick(dt)
        self.acquire_target()
        self.aim_at_target()
        return self.shoot()

    @property
    def game(self):
        return getattr(self.player, 'game', None)

    def orbit_player(self, dt):
        self.orbit_angle += self.orbit_speed * dt
        offset = pygame.Vector2(self.orbit_radius, 0).rotate(self.orbit_angle)
        self.position = self.player.position + offset

    def collides_with(self, other):
        return False


class ExplosiveDrone(Drone):
    def __init__(self, player, asteroids):
        super().__init__(player, asteroids)
        self.body_color = C.EXPLOSIVE_DRONE_BODY_COLOR
        self.body_line_width = 0
        self.platform = ExplosivePlatform()
        self.stat_source = C.EXPLOSIVE_DRONE


class KineticDrone(Drone):
    def __init__(self, player, asteroids):
        super().__init__(player, asteroids)
        self.body_color = C.KINETIC_DRONE_BODY_COLOR
        self.body_line_width = 0
        self.platform = KineticPlatform()
        self.stat_source = C.KINETIC_DRONE


class LaserDrone(Drone):
    def __init__(self, player, asteroids):
        super().__init__(player, asteroids)
        self.body_color = C.LASER_DRONE_BODY_COLOR
        self.body_line_width = 4
        self.platform = LaserPlatform()
        self.stat_source = C.LASER_DRONE

    def acquire_target(self):
        self.target = None
        valid_enemies = [
            e for e in getattr(self.game, 'enemies', [])
            if self._same_airspace(e)
            and self.position.distance_to(e.position) <= self.platform.range
        ]
        if valid_enemies:
            highest_health = max(e.health for e in valid_enemies)
            healthiest = [e for e in valid_enemies if e.health == highest_health]
            self.target = min(healthiest,
                key=lambda e: self.player.position.distance_to(e.position))
            return
        valid_targets = [
            a for a in self.asteroids
            if self.position.distance_to(a.position) <= self.platform.range
        ]
        if not valid_targets:
            return
        highest_health = max(a.health for a in valid_targets)
        healthiest = [a for a in valid_targets if a.health == highest_health]
        self.target = min(healthiest,
            key=lambda a: self.player.position.distance_to(a.position))


class PlasmaDrone(Drone):
    def __init__(self, player, asteroids):
        super().__init__(player, asteroids)
        self.body_color = C.PLASMA_DRONE_BODY_COLOR
        self.platform = PlasmaPlatform()
        self.stat_source = C.PLASMA_DRONE


class SentinelDrone(Drone):
    def __init__(self, player, asteroids):
        super().__init__(player, asteroids)
        self.body_color = C.SENTINEL_DRONE_BODY_COLOR
        self.body_line_width = 0
        self.radius = int(C.DRONE_RADIUS * 0.65)
        self.platform = SentinelPlatform()
        self.player_shield = None
        self.shield_create_timer = 0
        self.shield_max_health = C.SHIELD_MAX_HEALTH
        self.shield_repair_timer_base = C.SENTINEL_DRONE_SHIELD_REPAIR_TIMER
        self.shield_repair_timer = self.shield_repair_timer_base
        self.stat_source = C.SENTINEL_DRONE

    def update(self, dt):
        self.shield_sentinel(dt)
        self.orbit_player(dt)
        return 0

    def shield_sentinel(self, dt):
        self.shield_create_timer = max(0, self.shield_create_timer - dt)
        self.shield_repair_timer = max(0, self.shield_repair_timer - dt)
        if not self.player_shield:
            self.player.shield = False
            if self.shield_create_timer == 0:
                self.player_shield = Shield(owner=self.player, source=self,
                    max_health=self.shield_max_health)
                self.player.shield = True
                self.shield_create_timer = C.SENTINEL_DRONE_SHIELD_CREATE_TIMER
        else:
            self.player.shield = True
            if self.player_shield and not self.player_shield.alive():
                self.player_shield = None
                self.player.shield = False
        if self.player_shield:
            if self.player_shield.health < self.player_shield.max_health:
                if self.shield_repair_timer == 0:
                    before = self.player_shield.health
                    self.player_shield.health = min(self.player_shield.max_health,
                        self.player_shield.health + 1)
                    repaired = self.player_shield.health - before
                    if repaired > 0:
                        self.player.game.combat_stats.add_repaired(
                            self.stat_source, repaired)
                    self.shield_repair_timer = self.shield_repair_timer_base
