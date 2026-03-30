import pygame
import random
import constants as C
from circleshape import CircleShape
from visualeffect import Explosion
from logger import log_event

class Asteroid(CircleShape):
    def __init__(self, x, y, size):
        super().__init__(x, y, size * C.ASTEROID_MIN_RADIUS)
        self.size = size
        self.damage = self.size
        self.full_health = self.size * 10
        self.health = self.full_health
        self.line_width = int(C.LINE_WIDTH + (self.size * 2))
        self.surface_details = self.generate_surface_details()
        self.crack_data = self.generate_crack_data()

    def generate_surface_details(self):
        details = []
        detail_count = self.size + 1
        min_detail_radius = 6
        attempts = 0
        max_attempts = 50
        while len(details) < detail_count and attempts < max_attempts:
            attempts += 1
            detail_radius = random.randint(min_detail_radius,
                max(min_detail_radius, int(self.radius * 0.18)))
            max_distance = self.radius - detail_radius - self.line_width - 2
            if max_distance <= 0:
                continue
            angle = random.uniform(0, 360)
            distance = random.uniform(max_distance * 0.2, max_distance * 0.85)
            offset = pygame.Vector2(distance, 0).rotate(angle)
            overlaps = False
            for existing_offset, existing_radius in details:
                if offset.distance_to(existing_offset) < (detail_radius + existing_radius + 2):
                    overlaps = True
                    break
            if not overlaps:
                details.append((offset, detail_radius))
        return details
    
    def generate_crack_data(self):
        cracks = []
        crack_count = max(3, self.size * 3)
        attempts = 0
        max_attempts = 100

        while len(cracks) < crack_count and attempts < max_attempts:
            attempts += 1
            angle = random.uniform(0, 360)
            start_distance = random.uniform(self.radius * 0.35, self.radius * 0.95)
            start_offset = pygame.Vector2(start_distance, 0).rotate(angle)
            overlaps = False
            min_start_spacing = self.radius * 0.35
            for existing_start, _, _ in cracks:
                if start_offset.distance_to(existing_start) < min_start_spacing:
                    overlaps = True
                    break
            if overlaps:
                continue
            if random.random() < 0.25:
                crack_length = random.uniform(self.radius * 0.65, self.radius * 1.1)
            else:
                crack_length = random.uniform(self.radius * 0.3, self.radius * 0.7)
            end_angle = angle + random.uniform(-50, 50)
            end_offset = start_offset + pygame.Vector2(-crack_length, 0).rotate(end_angle)
            branch_data = None
            if random.choice([True, False]):
                branch_length = crack_length * random.uniform(0.3, 0.6)
                branch_angle = end_angle + random.uniform(-70, 70)
                branch_start = start_offset.lerp(end_offset, random.uniform(0.25, 0.75))
                branch_end = branch_start + pygame.Vector2(-branch_length, 0).rotate(branch_angle)
                branch_data = (branch_start, branch_end)
            cracks.append((start_offset, end_offset, branch_data))
        return cracks

    def draw(self, screen):
        pygame.draw.circle(screen, C.WHITE, self.position, self.radius, self.line_width)
        for offset, detail_radius in self.surface_details:
            detail_position = self.position + offset
            pygame.draw.circle(screen, C.WHITE, detail_position, detail_radius, C.LINE_WIDTH)
        if self.health < self.full_health:
            self.draw_cracks(screen)

    def get_zigzag_points(self, start_pos, end_pos, segments=4, jag_amount=5):
        points = [start_pos]
        direction = end_pos - start_pos
        if direction.length_squared() == 0:
            return [start_pos, end_pos]
        normal = pygame.Vector2(-direction.y, direction.x)
        if normal.length_squared() > 0:
            normal = normal.normalize()
        for i in range(1, segments):
            t = i / segments
            base_point = start_pos.lerp(end_pos, t)
            offset_strength = random.uniform(jag_amount * 0.4, jag_amount)
            if i % 2 == 0:
                offset_strength *= -1
            offset_point = base_point + normal * offset_strength
            points.append(offset_point)
        points.append(end_pos)
        return points
    
    def draw_zigzag_line(self, screen, color, start_pos, end_pos, width, jag_amount=5):
        distance = start_pos.distance_to(end_pos)
        segments = max(3, min(6, int(distance / 8)))
        points = self.get_zigzag_points(start_pos, end_pos, segments=segments,
                            jag_amount=jag_amount)
        pygame.draw.lines(screen, color, False, points, width)

    def draw_cracks(self, screen):
        damage_ratio = 1 - (self.health / self.full_health)
        visible_cracks = max(1, int(len(self.crack_data) * damage_ratio))
        for i in range(visible_cracks):
            start_offset, end_offset, branch_data = self.crack_data[i]
            start_pos = self.position + start_offset
            end_pos = self.position + end_offset
            self.draw_zigzag_line(screen, C.WHITE, start_pos, end_pos, C.LINE_WIDTH + 2, jag_amount=8)
            if branch_data:
                branch_start, branch_end = branch_data
                branch_start_pos = self.position + branch_start
                branch_end_pos = self.position + branch_end
                self.draw_zigzag_line(screen, C.WHITE, branch_start_pos, branch_end_pos, C.LINE_WIDTH + 1, jag_amount=5)

    def update(self, dt):
        self.position += self.velocity * dt

    def damaged(self, damage):
        self.health -= damage
        if self.health <= 0:
            return self.kill()
        return 0
    
    def kill(self):
        score_value = C.BASE_SCORE * self.size
        Explosion(self.position.x, self.position.y, radius=max(12, int(self.radius * 1.1)),
            color=C.ORANGE, duration=0.12 + (self.radius / 200), max_alpha=150)
        if self.size > 1:
            self.spawn_children()
            log_event("asteroid_split")
        else:
            log_event("asteroid_destroyed")
        super().kill()
        return score_value
        
    def spawn_children(self):
        child_size = self.size - 1
        child_radius = child_size * C.ASTEROID_MIN_RADIUS
        for i in range(self.size):
            range_size = 360 / self.size
            new_angle = random.uniform(1 + (range_size * i), range_size * (i + 1))
            velocity = self.velocity.rotate(new_angle)
            if velocity.length_squared() == 0:
                direction = pygame.Vector2(1, 0)
            else:
                direction = velocity.normalize()
            min_spawn_distance = max(0, self.radius - 10)
            max_spawn_distance = self.radius + child_radius + 10
            spawn_distance = random.uniform(min_spawn_distance, max_spawn_distance)
            spawn_position = self.position + direction * spawn_distance
            asteroid = Asteroid(spawn_position.x, spawn_position.y, child_size)
            asteroid.velocity = velocity * self.split_factor(new_angle) * C.ASTEROID_SPLIT_ACCELERATION
    
    def split_factor(self, angle):
        factor = 0
        if angle > 270 and angle <= 360:
            angle = angle - 270
            factor = angle / 90   
        elif angle > 180 and angle <= 270:
            angle = angle - 180
            factor = 1 - (angle / 90)
        elif angle > 90 and angle <= 180:
            angle = angle - 90
            factor = angle / 90
        elif angle > 0 and angle <= 90:
            factor = 1 - (angle / 90)
        else:
            raise ValueError
        if factor < C.MIN_ASTEROID_SPLIT_FACTOR:
            return C.MIN_ASTEROID_SPLIT_FACTOR
        else:
            return factor