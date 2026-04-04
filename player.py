import pygame
import constants as C
from circleshape import CircleShape
from logger import log_event

class Player(CircleShape):
    def __init__(self, x, y):
        super().__init__(x, y, C.PLAYER_RADIUS, weight=C.PLAYER_WEIGHT,
            bounciness=C.PLAYER_BOUNCINESS, drag=C.PLAYER_DRAG,
            rotation=0, angular_velocity=0)
        self.lives = 3
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
        if not self.can_be_damaged:
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
        normal = self.get_collision_normal(asteroid)
        distance = self.position.distance_to(asteroid.position)
        overlap = (self.radius + asteroid.radius) - distance
        player_weight = max(self.weight, 0.0001)
        asteroid_weight = max(asteroid.weight, 0.0001)
        total_weight = player_weight + asteroid_weight
        if overlap > 0:
            player_shift = overlap * (asteroid_weight / total_weight)
            asteroid_shift = overlap * (player_weight / total_weight)
            self.position -= normal * player_shift
            asteroid.position += normal * asteroid_shift
        player_velocity = self.velocity.copy()
        asteroid_velocity = asteroid.velocity.copy()
        player_normal_speed = player_velocity.dot(normal)
        asteroid_normal_speed = asteroid_velocity.dot(normal)
        relative_normal_speed = player_normal_speed - asteroid_normal_speed
        if relative_normal_speed <= 0:
            return
        impact_push = relative_normal_speed * impact_scale
        asteroid_push = impact_push * C.PLAYER_COLLISION_ASTEROID_TRANSFER
        player_slow = impact_push * C.PLAYER_COLLISION_PLAYER_DAMPING
        asteroid.velocity += normal * asteroid_push
        player_velocity -= normal * player_slow
        if player_velocity.length() > C.PLAYER_MAX_SPEED:
            player_velocity.scale_to_length(C.PLAYER_MAX_SPEED)
        self.velocity = player_velocity
        self.sync_local_speeds_from_velocity()

    def move(self, dt):
        forward = pygame.Vector2(0, 1).rotate(self.rotation)
        right = forward.rotate(90)
        self.apply_movement_decay(dt)
        self.apply_rotation(dt)
        self.velocity = (forward * self.forward_speed
            + right * (self.perpendicular_speed + self.strafe_speed))
        if self.velocity.length() > C.PLAYER_MAX_SPEED:
            self.velocity.scale_to_length(C.PLAYER_MAX_SPEED)
            self.sync_local_speeds_from_velocity()
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

    def add_drone(self, drone_class, asteroids):
        new_drone = drone_class(self, asteroids)
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
        if self.damage_cooldown:
            color = C.RED if self.flash_visible else C.WHITE
        else:
            color = C.RED
        pygame.draw.polygon(screen, color, self.triangle(), C.LINE_WIDTH)

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
