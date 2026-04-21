import pygame
from core import constants as C
from core.circleshape import CircleShape
from core.element import draw_elemental_glow_poly, get_damage_multiplier
from core.logger import log_event
from entities.weaponsplatform import PlasmaPlatform
from ui.visualeffect import EnemyKillExplosionVE

class Enemy(CircleShape):
    def __init__(self, x, y, player, game=None):
        super().__init__(x, y, C.ENEMY_RADIUS,
            weight=C.ENEMY_WEIGHT, bounciness=C.ENEMY_BOUNCINESS,
            drag=C.ENEMY_DRAG, rotation=0, angular_velocity=0)
        self.player = player
        self.game = game
        self.health = C.ENEMY_MAX_HEALTH
        self.max_health = C.ENEMY_MAX_HEALTH
        self.element = None
        self.xp_value = C.ENEMY_XP_VALUE
        self.score_value = C.ENEMY_SCORE_VALUE
        self.damage = C.ENEMY_COLLISION_DAMAGE
        self.stat_source = C.ENEMY
        self.platform = None
        self.extra_abilities = set()
        self.asteroids = None
        self.body_color = C.ENEMY_BODY_COLOR
        self.hull_width = C.ENEMY_HULL_WIDTH
        self.hull_length = C.ENEMY_HULL_LENGTH
        self.target = None
        self.speed = C.ENEMY_SPEED
        self.airspace = None
        self.impact_timer = 0

    def damaged(self, amount, attacker_element=None):
        mult = get_damage_multiplier(attacker_element, self.element)
        self.health -= max(1, int(amount * mult))
        if self.health <= 0:
            log_event("enemy_destroyed")
            explosion_radius = max(12, int(self.radius * 1.5))
            EnemyKillExplosionVE(self.position.x, self.position.y, explosion_radius)
            self.kill()
            return self.score_value, self.xp_value
        log_event("enemy_hit")
        return 0, 0

    def acquire_target(self):
        self.target = self.player

    def aim_at_target(self):
        if self.target is None:
            return
        direction = self.target.position - self.position
        if direction.length_squared() > 0:
            self.rotation = pygame.Vector2(0, -1).angle_to(direction)

    def _in_current_airspace(self):
        if self.airspace is None or self.game is None:
            return True
        current = getattr(self.game, 'current_space', None)
        return current is None or self.airspace == current

    def shoot(self):
        if not self._in_current_airspace():
            return 0
        if self.platform is None or not self.platform.can_fire() or self.target is None:
            return 0
        return self.platform.fire(self) or 0

    def _calculate_avoidance(self, asteroids):
        avoidance = pygame.Vector2(0, 0)
        for asteroid in asteroids:
            to_enemy = self.position - asteroid.position
            if to_enemy.length_squared() == 0:
                continue
            distance = to_enemy.length()
            if distance > C.ENEMY_ASTEROID_AVOIDANCE_RADIUS:
                continue
            if asteroid.velocity.length_squared() > 0:
                approach_speed = asteroid.velocity.dot(to_enemy.normalize())
                if approach_speed <= 0:
                    continue
            strength = 1.0 - (distance / C.ENEMY_ASTEROID_AVOIDANCE_RADIUS)
            avoidance += to_enemy.normalize() * strength
        if avoidance.length_squared() > 0:
            avoidance = avoidance.normalize()
        return avoidance

    def move_toward_player(self, dt):
        if self.impact_timer > 0:
            return
        direction = self.player.position - self.position
        if direction.length_squared() == 0:
            return
        move_dir = direction.normalize()
        if self.asteroids:
            avoidance = self._calculate_avoidance(self.asteroids)
            if avoidance.length_squared() > 0:
                move_dir = (move_dir * (1.0 - C.ENEMY_ASTEROID_AVOIDANCE_WEIGHT)
                            + avoidance * C.ENEMY_ASTEROID_AVOIDANCE_WEIGHT)
                if move_dir.length_squared() > 0:
                    move_dir = move_dir.normalize()
        self.velocity = move_dir * self.speed

    def rect_corners(self):
        forward = pygame.Vector2(0, -1).rotate(self.rotation)
        right = forward.rotate(90)
        hw = self.hull_width / 2
        hl = self.hull_length / 2
        return [
            self.position + forward * hl + right * hw,
            self.position + forward * hl - right * hw,
            self.position - forward * hl - right * hw,
            self.position - forward * hl + right * hw,
        ]

    def draw_body(self, screen):
        corners = self.rect_corners()
        if self.element is not None:
            draw_elemental_glow_poly(screen, corners, self.element)
        pygame.draw.polygon(screen, self.get_outline_color(self.body_color), corners)

    def draw(self, screen):
        if not self._in_current_airspace():
            return
        self.draw_body(screen)
        if self.platform is not None:
            self.platform.draw(screen, self)

    def update(self, dt):
        if self.impact_timer > 0:
            self.impact_timer = max(0, self.impact_timer - dt)
        if self._in_current_airspace():
            self.move_toward_player(dt)
        self.physics_move(dt)
        if self.platform is not None:
            self.platform.tick(dt)
        self.acquire_target()
        self.aim_at_target()
        self.update_outline_pulse(dt)
        self.update_gameplay_effects(dt)
        return self.shoot()


class PlasmaEnemy(Enemy):
    def __init__(self, x, y, player, game):
        super().__init__(x, y, player, game)
        self.health = C.PLASMA_ENEMY_MAX_HEALTH
        self.max_health = C.PLASMA_ENEMY_MAX_HEALTH
        self.xp_value = C.PLASMA_ENEMY_XP_VALUE
        self.body_color = C.PLASMA_ENEMY_BODY_COLOR
        self.speed = C.PLASMA_ENEMY_SPEED
        self.asteroids = game.asteroids
        self.platform = PlasmaPlatform(base_damage=C.PLASMA_ENEMY_DAMAGE,
            projectile_color=C.PLASMA_ENEMY_PROJECTILE_COLOR)
        self.platform.weapons_free_timer_max = C.PLASMA_ENEMY_WEAPONS_FREE_TIMER
        self.platform.projectile_speed = C.PLASMA_ENEMY_PROJECTILE_SPEED
        self.platform.weapons_free_timer = C.PLASMA_ENEMY_WEAPONS_FREE_TIMER

    def _draw_wings(self, screen):
        forward = pygame.Vector2(0, -1).rotate(self.rotation)
        right = forward.rotate(90)
        hw = self.hull_width / 2
        hl = self.hull_length / 2
        ws = C.PLASMA_ENEMY_WING_SPAN
        wl = C.PLASMA_ENEMY_WING_LENGTH
        fill_color = self.get_outline_color(self.body_color)
        for side in (-1, 1):
            root_front = self.position - forward * (hl * 0.1) + right * (hw * side)
            root_rear = self.position - forward * hl + right * (hw * side)
            tip = self.position - forward * (wl * 0.5) + right * ((hw + ws) * side)
            wing = [root_front, root_rear, tip]
            if self.element is not None:
                draw_elemental_glow_poly(screen, wing, self.element)
            pygame.draw.polygon(screen, fill_color, wing)

    def draw_body(self, screen):
        super().draw_body(screen)
        self._draw_wings(screen)
