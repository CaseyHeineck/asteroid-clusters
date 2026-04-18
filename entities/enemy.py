import pygame
from core import constants as C
from core.circleshape import CircleShape
from core.element import draw_elemental_glow, get_damage_multiplier
from entities.weaponsplatform import PlasmaPlatform

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
        self.line_width = 0
        self.target = None
        self.speed = C.ENEMY_SPEED
        self.airspace = None

    def damaged(self, amount, attacker_element=None):
        mult = get_damage_multiplier(attacker_element, self.element)
        self.health -= max(1, int(amount * mult))
        if self.health <= 0:
            self.kill()
            return self.score_value, self.xp_value
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

    def move_toward_player(self, dt):
        direction = self.player.position - self.position
        if direction.length_squared() > 0:
            self.velocity = direction.normalize() * self.speed
            self.rotation = pygame.Vector2(0, -1).angle_to(direction)

    def draw_body(self, screen):
        if self.element is not None:
            draw_elemental_glow(screen, self.position, self.radius, self.element)
        pygame.draw.circle(screen, self.body_color, self.position, self.radius, self.line_width)

    def draw(self, screen):
        if not self._in_current_airspace():
            return
        self.draw_body(screen)
        if self.platform is not None:
            self.platform.draw(screen, self)

    def update(self, dt):
        if self._in_current_airspace():
            self.move_toward_player(dt)
        self.physics_move(dt)
        if self.platform is not None:
            self.platform.tick(dt)
        self.acquire_target()
        self.aim_at_target()
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
