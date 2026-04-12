import math
import pygame
import random
import constants as C
from circleshape import CircleShape
from experiorb import ExpOrb
from essenceorb import EssenceOrb
from elementalessenceorb import ElementalEssenceOrb
from visualeffect import AsteroidKillExplosionVE, OverkillExplosionVE
from logger import log_event
from element import ELEMENT_COLORS

class Asteroid(CircleShape):
    def __init__(self, x, y, size):
        super().__init__(x, y, size * C.ASTEROID_MIN_RADIUS,
            weight=size * C.ASTEROID_WEIGHT, bounciness=C.ASTEROID_BOUNCINESS,
            drag=C.ASTEROID_DRAG, rotation=random.uniform(0, 360),
            angular_velocity=random.uniform(-C.ASTEROID_MAX_ANGULAR_VELOCITY,
                C.ASTEROID_MAX_ANGULAR_VELOCITY))
        self.size = size
        self.damage = self.size
        self.full_health = self.size * 10
        self.health = self.full_health
        self.element = None
        self.child_count_reduction = 0
        self.child_size_reduction = 0
        self.overkill_triggered = False
        self.line_width = int(C.LINE_WIDTH + (self.size * 2))
        self.outline_color = self.get_outline_color(C.WHITE)
        self.outline_points = self.generate_outline_points()
        self.surface_details = self.generate_surface_details()
        self.crack_data = self.generate_crack_data()

    def generate_outline_points(self):
        points = []
        point_count = max(8, self.size * 5)
        for i in range(point_count):
            angle = (360 / point_count) * i
            variation = random.uniform(-self.radius * 0.2, self.radius * 0.2)
            radius = self.radius + variation
            point = pygame.Vector2(radius, 0).rotate(angle)
            points.append(point)
        return points

    def generate_surface_details(self):
        details = []
        detail_count = max(2, self.size + random.choice([1, 2]))
        min_detail_radius = max(3, int(self.radius * 0.08))
        max_attempts = detail_count * 20
        while len(details) < detail_count and max_attempts > 0:
            max_attempts -= 1
            max_detail_radius = max(min_detail_radius + 3, int(self.radius * 0.28))
            detail_radius = random.randint(min_detail_radius, max_detail_radius)
            max_distance = self.radius - detail_radius - self.line_width - 2
            if max_distance <= 0:
                continue
            angle = random.uniform(0, 360)
            distance = random.uniform(max_distance * 0.15, max_distance * 0.9)
            offset = pygame.Vector2(distance, 0).rotate(angle)
            overlaps = False
            for existing_offset, existing_radius in details:
                if offset.distance_to(existing_offset) < (detail_radius + existing_radius + 6):
                    overlaps = True
                    break
            if not overlaps:
                details.append((offset, detail_radius))
        return details

    def generate_crack_data(self):
        cracks = []
        primary_crack_count = max(2, self.size)
        attempts = 0
        max_attempts = primary_crack_count * 12
        min_start_spacing = self.radius * 0.45
        while len(cracks) < primary_crack_count and attempts < max_attempts:
            attempts += 1
            angle = random.uniform(0, 360)
            start_distance = random.uniform(self.radius * 0.45, self.radius * 0.92)
            start_offset = pygame.Vector2(start_distance, 0).rotate(angle)
            overlaps = False
            for crack in cracks:
                existing_start = crack["main"][0]
                if start_offset.distance_to(existing_start) < min_start_spacing:
                    overlaps = True
                    break
            if overlaps:
                continue
            crack_length = random.uniform(self.radius * 0.45, self.radius * 0.95)
            end_angle = angle + random.uniform(-45, 45)
            end_offset = start_offset + pygame.Vector2(-crack_length, 0).rotate(end_angle)
            main_points = self.get_zigzag_points(start_offset, end_offset,
                segments=max(4, int(crack_length / 10)), jag_amount=8)
            branches = []
            branch_count = random.randint(0, 2)
            for _ in range(branch_count):
                branch_t = random.uniform(0.25, 0.8)
                branch_start = start_offset.lerp(end_offset, branch_t)
                branch_length = crack_length * random.uniform(0.25, 0.55)
                branch_angle = end_angle + random.uniform(-80, 80)
                branch_end = branch_start + pygame.Vector2(-branch_length, 0).rotate(branch_angle)
                branch_points = self.get_zigzag_points(branch_start, branch_end,
                    segments=max(3, int(branch_length / 10)), jag_amount=5)
                branches.append(branch_points)
            cracks.append({
                "main": main_points,
                "branches": branches,
            })
        return cracks

    def draw(self, screen):
        if self.element is not None:
            t = pygame.time.get_ticks() / 1000.0
            pulse = 0.3 + ((math.sin(t * 0.9) + 1) / 2) * 0.7
            primary = ELEMENT_COLORS[self.element]["primary"]
            base_color = tuple(int(C.WHITE[i] + (primary[i] - C.WHITE[i]) * pulse) for i in range(3))
        else:
            base_color = C.WHITE
        outline_color = self.get_outline_color(base_color)
        surface_size = int((self.radius * 2) + (self.line_width * 4))
        asteroid_surface = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        center = surface_size // 2
        rotated_points = [pygame.Vector2(center, center) + point.rotate(self.rotation)
            for point in self.outline_points]
        int_points = [(int(p.x), int(p.y)) for p in rotated_points]
        pygame.draw.polygon(asteroid_surface, outline_color, int_points, self.line_width)
        for offset, detail_radius in self.surface_details:
            rotated_offset = offset.rotate(self.rotation)
            detail_position = pygame.Vector2(center, center) + rotated_offset
            pygame.draw.circle(asteroid_surface, outline_color,
                (int(detail_position.x), int(detail_position.y)), detail_radius, C.LINE_WIDTH)
        if self.health < self.full_health:
            self.draw_cracks(asteroid_surface, center, outline_color)
        rect = asteroid_surface.get_rect(center=(self.position.x, self.position.y))
        screen.blit(asteroid_surface, rect)

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
        points = self.get_zigzag_points(start_pos, end_pos,
            segments=segments, jag_amount=jag_amount)
        pygame.draw.lines(screen, color, False, points, width)

    def draw_cracks(self, surface, center, color):
        damage_ratio = 1 - (self.health / self.full_health)
        center_vector = pygame.Vector2(center, center)
        visible_crack_count = max(1, int(len(self.crack_data) * damage_ratio))
        for i in range(visible_crack_count):
            crack = self.crack_data[i]
            main_points = crack["main"]
            branches = crack["branches"]
            rotated_main = [center_vector + point.rotate(self.rotation)
                for point in main_points]
            pygame.draw.lines(surface, color, False,
                [(int(p.x), int(p.y)) for p in rotated_main],
                C.LINE_WIDTH + 2)
            if damage_ratio > 0.2 and branches:
                branch_ratio = (damage_ratio - 0.2) / 0.8
                visible_branch_count = max(0, int(len(branches) * branch_ratio))
                for branch_points in branches[:visible_branch_count]:
                    rotated_branch = [center_vector + point.rotate(self.rotation)
                        for point in branch_points]
                    pygame.draw.lines(surface, color, False,
                        [(int(p.x), int(p.y)) for p in rotated_branch],
                        C.LINE_WIDTH + 1)

    def update(self, dt):
        self.update_outline_pulse(dt)
        self.physics_move(dt)
        return self.update_gameplay_effects(dt)

    def damaged(self, damage):
        log_event("asteroid_damaged")
        self.health -= damage
        if self.health <= 0:
            return self.kill()
        return 0

    def kill(self):
        score_value = C.BASE_SCORE * self.size
        explosion_radius = max(12, int(self.radius * 1.1))
        AsteroidKillExplosionVE(self.position.x, self.position.y, explosion_radius)
        if self.overkill_triggered:
            OverkillExplosionVE(self.position.x, self.position.y, explosion_radius)
        if ExpOrb.containers and random.random() < C.EXP_ORB_DROP_CHANCE:
            angle = random.uniform(0, 360)
            dist = random.uniform(0, self.radius)
            offset = pygame.Vector2(dist, 0).rotate(angle)
            ExpOrb(self.position.x + offset.x, self.position.y + offset.y,
                int(self.size ** C.EXP_ORB_SIZE_EXPONENT * C.EXP_ORB_VALUE_BASE))
        if EssenceOrb.containers and random.random() < C.ESSENCE_ORB_DROP_CHANCE:
            angle = random.uniform(0, 360)
            dist = random.uniform(0, self.radius)
            offset = pygame.Vector2(dist, 0).rotate(angle)
            EssenceOrb(self.position.x + offset.x, self.position.y + offset.y,
                int(self.size ** C.ESSENCE_ORB_SIZE_EXPONENT * C.ESSENCE_ORB_VALUE_BASE))
        if self.element is not None and ElementalEssenceOrb.containers:
            angle = random.uniform(0, 360)
            dist = random.uniform(0, self.radius)
            offset = pygame.Vector2(dist, 0).rotate(angle)
            drop_amount = max(1, self.size * C.ELEMENTAL_ESSENCE_DROP_BASE)
            ElementalEssenceOrb(self.position.x + offset.x, self.position.y + offset.y,
                drop_amount, self.element)
        did_split = False
        if self.size > 1:
            did_split = self.spawn_children()
        if did_split:
            log_event("asteroid_split")
        else:
            log_event("asteroid_destroyed")
        super().kill()
        return score_value

    def spawn_children(self):
        child_size = self.size - 1 - self.child_size_reduction
        child_count = self.size - 1 - self.child_count_reduction
        if child_size < 1 or child_count < 1:
            return False
        child_radius = child_size * C.ASTEROID_MIN_RADIUS
        children = []
        for i in range(child_count):
            range_size = 360 / child_count
            new_angle = random.uniform(1 + (range_size * i), range_size * (i + 1))
            velocity = self.velocity.rotate(new_angle)
            if velocity.length_squared() == 0:
                direction = pygame.Vector2(1, 0)
            else:
                direction = velocity.normalize()
            min_spawn_distance = self.radius - 10
            max_spawn_distance = self.radius + child_radius + 10
            spawn_distance = random.uniform(min_spawn_distance, max_spawn_distance)
            spawn_position = self.position + direction * spawn_distance
            asteroid = Asteroid(spawn_position.x, spawn_position.y, child_size)
            asteroid.velocity = velocity * self.split_factor(new_angle) * C.ASTEROID_SPLIT_ACCELERATION
            children.append(asteroid)
        if self.element is not None and children:
            elemental_mask = [random.random() < C.ASTEROID_CHILD_ELEMENTAL_CHANCE
                              for _ in children]
            if not any(elemental_mask):
                elemental_mask[random.randrange(len(children))] = True
            for child, is_elemental in zip(children, elemental_mask):
                if is_elemental:
                    child.element = self.element
        return True

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
        if factor < C.ASTEROID_SPLIT_FACTOR_MIN:
            return C.ASTEROID_SPLIT_FACTOR_MIN
        else:
            return factor