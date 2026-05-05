import os
import random
import pygame
from core import constants as C
from core.circleshape import CircleShape
from core.logger import log_event
from ui.visualeffect import ShipExhaustVE

class Player(CircleShape):
    _sprite = None

    @classmethod
    def _load_sprite(cls):
        if cls._sprite is not None:
            return
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
            "..", "assets", "images", "Player.png")
        raw = pygame.image.load(path)
        size = C.PLAYER_RADIUS * 2
        cls._sprite = pygame.transform.scale(raw, (size, size))

    def __init__(self, x, y):
        self._load_sprite()
        super().__init__(x, y, C.PLAYER_RADIUS, weight=C.PLAYER_WEIGHT,
            bounciness=C.PLAYER_BOUNCINESS, drag=C.PLAYER_DRAG,
            rotation=0, angular_velocity=0)
        self.lives = 3
        self.max_lives = 3
        self.uses_health = False
        self.health = 0
        self.max_health = 0
        self.evasion_chance = 0.0
        self.life_regen = False
        self.life_regen_timer = 0
        self.damage_cooldown = False
        self.damage_cooldown_timer = 0
        self.blink_timer = 0
        self.can_be_damaged = True
        self.flash_visible = False
        self.game_over = False
        self.drones = []
        self.shield = False
        self.forward_speed = 0
        self.perpendicular_speed = 0
        self.strafe_speed = 0
        self.collision_damage = C.PLAYER_COLLISION_DAMAGE
        self.stat_source = C.PLAYER
        self.game = None

    def approach_zero(self, value, amount):
        if value > 0:
            return max(0, value - amount)
        if value < 0:
            return min(0, value + amount)
        return 0

    def rotate(self, dt):
        self.rotation += C.PLAYER_TURN_SPEED * dt

    def accelerate(self, dt):
        self.forward_speed += C.PLAYER_ACCELERATION_RATE * dt

    def brake(self, dt):
        self.forward_speed = self.approach_zero(self.forward_speed,
            C.PLAYER_BRAKE_SPEED * dt)
        self.perpendicular_speed = self.approach_zero(self.perpendicular_speed,
            C.PLAYER_PERPENDICULAR_BRAKE_SPEED * dt)    

    def strafe(self, direction, scale=1):
        self.strafe_speed = C.PLAYER_STRAFE_SPEED * direction 

    def update_damage_cooldown(self, dt):
        if not self.damage_cooldown:
            self.can_be_damaged = True
            self.flash_visible = False
            return
        self.can_be_damaged = False
        self.damage_cooldown_timer += dt
        self.blink_timer += dt
        if self.blink_timer >= C.PLAYER_BLINK_TIMER:
            self.flash_visible = not self.flash_visible
            self.blink_timer = 0
        if self.damage_cooldown_timer >= C.PLAYER_DAMAGE_COOLDOWN_SECONDS:
            self.damage_cooldown = False
            self.damage_cooldown_timer = 0
            self.blink_timer = 0
            self.can_be_damaged = True
            self.flash_visible = False

    def damaged(self, damage=1):
        if self.uses_health:
            self.health -= damage
            if self.health <= 0:
                self.health = 0
                log_event("game_over")
                self.game_over = True
            return 0, self.health
        if not self.can_be_damaged:
            return 0, self.lives
        if self.evasion_chance > 0 and random.random() < self.evasion_chance:
            return 0, self.lives
        log_event("player_hit")
        self.lives -= damage
        self.damage_cooldown = True
        self.damage_cooldown_timer = 0
        self.blink_timer = 0
        self.flash_visible = False
        self.can_be_damaged = False
        score_delta = C.LIFE_LOSS_SCORE * (self.lives + damage)
        if self.lives <= 0:
            self.lives = 0
            log_event("game_over")
            score_delta += C.GAME_OVER_SCORE
            self.game_over = True
        return score_delta, self.lives
    
    def sync_local_speeds_from_velocity(self):
        forward = pygame.Vector2(0, 1).rotate(self.rotation)
        right = forward.rotate(90)
        self.forward_speed = self.velocity.dot(forward)
        self.perpendicular_speed = self.velocity.dot(right)

    def apply_collision_to_asteroid(self, asteroid, impact_scale=1.0):
        self.collide_and_impact(asteroid, impact_scale=impact_scale)
        if self.velocity.length() > C.PLAYER_MAX_SPEED:
            self.velocity.scale_to_length(C.PLAYER_MAX_SPEED)
        if asteroid.velocity.length() > C.ASTEROID_MAX_SPEED:
            asteroid.velocity.scale_to_length(C.ASTEROID_MAX_SPEED)
        self.sync_local_speeds_from_velocity()

    def move(self, dt):
        forward = pygame.Vector2(0, 1).rotate(self.rotation)
        right = forward.rotate(90)
        self.apply_movement_decay(dt)
        self.apply_rotation(dt)
        self.velocity = (forward * self.forward_speed
            + right * (self.perpendicular_speed + self.strafe_speed))
        if self.velocity.length() > C.PLAYER_MAX_SPEED:
            scale = C.PLAYER_MAX_SPEED / self.velocity.length()
            self.forward_speed *= scale
            self.perpendicular_speed *= scale
            self.velocity.scale_to_length(C.PLAYER_MAX_SPEED)
        self.position += self.velocity * dt

    def apply_movement_decay(self, dt):
        self.forward_speed = self.approach_zero(self.forward_speed,
            C.PLAYER_FORWARD_DECELERATION_RATE * dt)
        self.perpendicular_speed = self.approach_zero(self.perpendicular_speed,
            C.PLAYER_PERPENDICULAR_DECELERATION_RATE * dt)

    def triangle(self):
        forward = pygame.Vector2(0, 1).rotate(self.rotation)
        right = pygame.Vector2(0, 1).rotate(self.rotation + 90) * self.radius / 1.5
        a = self.position + forward * self.radius
        b = self.position - forward * self.radius - right
        c = self.position - forward * self.radius + right
        return [a, b, c]

    def add_drone(self, drone_class, asteroids, platform_class=None):
        new_drone = drone_class(self, asteroids, platform_class=platform_class)
        self.drones.append(new_drone)
        self.rebalance_drones()
        return new_drone

    def rebalance_drones(self):
        drone_count = len(self.drones)
        if drone_count == 0:
            return
        angle_step = 360 / drone_count
        starting_angle = self.drones[0].orbit_angle
        for i, drone in enumerate(self.drones):
            drone.orbit_angle = starting_angle + (i * angle_step)

    def collides_with(self, other):
        if self.shield:
            return False
        triangle_points = self.triangle()
        circle_center = other.position
        circle_radius = other.radius
        if self.point_in_triangle(circle_center, triangle_points):
            return True
        for point in triangle_points:
            if point.distance_to(circle_center) <= circle_radius:
                return True
        edges = [(triangle_points[0], triangle_points[1]),
                (triangle_points[1], triangle_points[2]),
                (triangle_points[2], triangle_points[0])]
        for start, end in edges:
            if self.distance_point_to_segment(circle_center, start, end) <= circle_radius:
                return True
        return False

    def point_in_triangle(self, point, triangle_points):
        a, b, c = triangle_points
        def sign(p1, p2, p3):
            return ((p1.x - p3.x) * (p2.y - p3.y) - (p2.x - p3.x) * (p1.y - p3.y))
        d1 = sign(point, a, b)
        d2 = sign(point, b, c)
        d3 = sign(point, c, a)
        has_neg = (d1 < 0) or (d2 < 0) or (d3 < 0)
        has_pos = (d1 > 0) or (d2 > 0) or (d3 > 0)
        return not (has_neg and has_pos)

    def distance_point_to_segment(self, point, start, end):
        segment = end - start
        segment_length_squared = segment.length_squared()
        if segment_length_squared == 0:
            return point.distance_to(start)
        t = (point - start).dot(segment) / segment_length_squared
        t = max(0, min(1, t))
        closest_point = start + segment * t
        return point.distance_to(closest_point)
    
    def draw(self, screen):
        if self.damage_cooldown and not self.flash_visible:
            return
        rotated = pygame.transform.rotate(self._sprite, -self.rotation + 180)
        rect = rotated.get_rect(center=(int(self.position.x), int(self.position.y)))
        screen.blit(rotated, rect)

    def _spawn_exhaust_effects(self, moving_forward, moving_backward,
            moving_left, moving_right, strafing, boosting, braking):
        if not ShipExhaustVE.containers:
            return
        forward = pygame.Vector2(0, 1).rotate(self.rotation)
        right = forward.rotate(90)
        r = self.radius
        port_s = 3
        if moving_forward and not braking:
            length = 42 if boosting else 25
            width  = 11 if boosting else  7
            for side in (-1, 1):
                pos = self.position - forward * (r + 2 * port_s) + right * (port_s * side)
                ShipExhaustVE(pos.x, pos.y, -forward, length, width)
        if moving_left and not strafing:
            pos = self.position + forward * (r * 0.65) + right * (r * 0.45)
            ShipExhaustVE(pos.x, pos.y, right, 12, 4)
        if moving_right and not strafing:
            pos = self.position + forward * (r * 0.65) - right * (r * 0.45)
            ShipExhaustVE(pos.x, pos.y, -right, 12, 4)
        if strafing and moving_right:
            pos = self.position - right * (r * 0.8)
            ShipExhaustVE(pos.x, pos.y, right, 18, 5)
        if strafing and moving_left:
            pos = self.position + right * (r * 0.8)
            ShipExhaustVE(pos.x, pos.y, -right, 18, 5)

    def update(self, dt):
        keys = pygame.key.get_pressed()

        boosting = keys[pygame.K_RSHIFT] or keys[pygame.K_LSHIFT]
        strafing = keys[pygame.K_RCTRL] or keys[pygame.K_LCTRL]
        braking = keys[pygame.K_SPACE]

        moving_forward = keys[pygame.K_w] or keys[pygame.K_UP]
        moving_backward = keys[pygame.K_s] or keys[pygame.K_DOWN]
        moving_left = keys[pygame.K_a] or keys[pygame.K_LEFT]
        moving_right = keys[pygame.K_d] or keys[pygame.K_RIGHT]

        boost_scale = 2 if boosting else 1

        self.strafe_speed = 0
        if not (strafing and (moving_left or moving_right)):
            self.perpendicular_speed = 0

        if braking:
            self.brake(dt)

        if moving_forward:
            self.accelerate(dt * boost_scale)
        if moving_backward:
            self.accelerate(-dt * boost_scale)

        if strafing:
            if moving_left:
                self.strafe(-1, boost_scale)
            elif moving_right:
                self.strafe(1, boost_scale)
        else:
            if moving_left:
                self.rotate(-dt)
            if moving_right:
                self.rotate(dt)

        self.update_damage_cooldown(dt)
        self.move(dt)
        self._spawn_exhaust_effects(
            moving_forward, moving_backward,
            moving_left, moving_right,
            strafing, boosting, braking)

        if self.life_regen and self.lives < self.max_lives:
            self.life_regen_timer += dt
            if self.life_regen_timer >= C.PLAYER_LIFE_REGEN_INTERVAL:
                self.lives += 1
                self.life_regen_timer = 0
