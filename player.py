import pygame
import constants as C
from circleshape import CircleShape
from logger import log_event

class Player(CircleShape):
    def __init__(self, x, y):
        super().__init__(x, y, C.PLAYER_RADIUS)
        self.rotation = 0
        self.shot_cooldown = 0
        self.lives = 3
        self.life = True
        self.respawn_timer = 0
        self.blink_timer = 0
        self.vulnerable = True
        self.speed = 0
        self.game_over = False
        self.drones = []
        self.shield = False
        
    def draw(self, screen):
        if self.vulnerable:
            pygame.draw.polygon(screen, C.RED, self.triangle(), C.LINE_WIDTH)
        else:            
            pygame.draw.polygon(screen, C.WHITE, self.triangle(), C.LINE_WIDTH)

    def rotate(self, dt):
        self.rotation += C.PLAYER_TURN_SPEED * dt
    
    def accelerate(self, dt):
        self.speed += C.PLAYER_ACCELERATION_RATE * dt

    def decelerate(self, dt):
        if self.speed < 0:
            self.speed += C.PLAYER_DECELERATION_RATE * dt
        elif self.speed > 0:
            self.speed -= C.PLAYER_DECELERATION_RATE * dt
        elif self.speed == 0:
            return

    def brake(self, dt):
        if self.speed < 0:
            self.speed += C.PLAYER_BRAKE_SPEED * dt
        elif self.speed > 0:
            self.speed -= C.PLAYER_BRAKE_SPEED * dt
        elif self.speed == 0:
            return

    def move(self, dt):
        unit_vector = pygame.Vector2(0, 1)
        rotated_vector = unit_vector.rotate(self.rotation)
        rotated_with_speed_vector = rotated_vector * self.speed * dt
        self.position += rotated_with_speed_vector

    def strafe(self, dt):
        unit_vector = pygame.Vector2(0, 1)
        rotated_vector = unit_vector.rotate((self.rotation + 90))
        rotated_with_speed_vector = rotated_vector * C.PLAYER_STRAFE_SPEED * dt
        self.position += rotated_with_speed_vector

    def respawn(self, HUD):
        log_event("player_hit")
        HUD.update_score(C.LIFE_LOSS_SCORE * self.lives)
        self.lives -= 1
        HUD.update_player_lives(self.lives)
        self.life = False
        self.vulnerable = False
        if self.lives > 0:
            log_event("player_respawned")
            self.position.x = C.SCREEN_WIDTH / 2
            self.position.y = C.SCREEN_HEIGHT / 2
        else:
            log_event("game_over")
            HUD.update_score(C.GAME_OVER_SCORE)
            self.game_over = True
    
    def update(self, dt):
        keys = pygame.key.get_pressed()

        if keys[pygame.K_SPACE]:
            self.brake(dt)        
        
        if keys[pygame.K_RSHIFT] or keys[pygame.K_LSHIFT]:
            if keys[pygame.K_RCTRL] or keys[pygame.K_LCTRL]:
                if keys[pygame.K_w]:
                    self.accelerate(dt * 2)
                if keys[pygame.K_s]:
                    self.accelerate(-dt * 2)
                if keys[pygame.K_a]:
                    self.strafe(-dt * 2)
                if keys[pygame.K_d]:
                    self.strafe(dt * 2)
            else:
                if keys[pygame.K_w]:
                    self.accelerate(dt * 2)
                if keys[pygame.K_s]:
                    self.accelerate(-dt * 2)
                if keys[pygame.K_a]:
                    self.rotate(-dt)
                if keys[pygame.K_d]:
                    self.rotate(dt)                    
        elif keys[pygame.K_RCTRL] or keys[pygame.K_LCTRL]:
            if keys[pygame.K_a]:
                self.strafe(-dt)
            if keys[pygame.K_d]:
                self.strafe(dt)
            if keys[pygame.K_w]:
                self.accelerate(dt)
            if keys[pygame.K_s]:
                self.accelerate(-dt)                                                           
        else:
            if keys[pygame.K_a]:
                self.rotate(-dt)
            if keys[pygame.K_d]:
                self.rotate(dt)
            if keys[pygame.K_w]:
                self.accelerate(dt)
            if keys[pygame.K_s]:
                self.accelerate(-dt)
        
        if self.life is not True:
            if self.blink_timer < C.PLAYER_BLINK_TIMER:
                self.blink_timer += dt
            else:
                if self.vulnerable:
                    self.vulnerable = False
                    self.blink_timer = 0
                else:
                    self.vulnerable = True
                    self.blink_timer = 0     
            if self.respawn_timer < C.PLAYER_RESPAWN_COOLDOWN_SECONDS:
                self.respawn_timer += dt
            else:
                self.life = True
                self.respawn_timer = 0 
        else:
            self.vulnerable = True
        self.move(dt)
        self.decelerate(dt)     

    def triangle(self):    
        forward = pygame.Vector2(0, 1).rotate(self.rotation)
        right = pygame.Vector2(0, 1).rotate(self.rotation + 90) * self.radius / 1.5
        a = self.position + forward * self.radius
        b = self.position - forward * self.radius - right
        c = self.position - forward * self.radius + right
        return [a, b, c]

    def add_drone(self, drone_class, asteroids, HUD):
        new_drone = drone_class(self, asteroids, HUD)
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
                (triangle_points[2], triangle_points[0]),]
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