import math
import pygame
import constants as C
from circleshape import CircleShape
from projectile import Kinetic, LaserBeam, Plasma, Rocket
from shield import Shield
from visualeffect import MuzzleFlareVE

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
        self.range = float("inf")
        self.weapons_free_timer = 0
        self.weapons_free_timer_max = C.DRONE_WEAPONS_FREE_TIMER
        self.body_color = C.WHITE
        self.body_line_width = C.DRONE_LINE_WIDTH
        self.stat_source = None

    def acquire_target(self):
        closest_so_far = float("inf")
        self.target = None
        for asteroid in self.asteroids:
            player_distance = self.player.position.distance_to(asteroid.position)
            drone_distance = self.position.distance_to(asteroid.position)
            if drone_distance <= self.range and player_distance < closest_so_far:
                closest_so_far = player_distance
                self.target = asteroid

    def aim_at_target(self):
        if self.target is None:
            return
        direction = self.target.position - self.position
        if direction.length_squared() > 0:
            self.rotation = pygame.Vector2(0, -1).angle_to(direction)

    def get_projectile_spawn_position(self):
        forward = self.get_forward_vector()
        return self.position + forward * self.radius

    def weapons_free(self):
        raise NotImplementedError("Drone subclass not instantiated")

    def shoot(self):
        if self.weapons_free_timer > 0 or self.target is None:
            return 0
        score = self.weapons_free()
        self.weapons_free_timer = self.weapons_free_timer_max
        return score or 0

    def draw_body(self, screen):
        pygame.draw.circle(screen, self.body_color, self.position, self.radius, self.body_line_width)

    def draw_weapons_platform(self, screen):
        raise NotImplementedError("Drone subclass not instantiated")

    def draw(self, screen):
        self.draw_body(screen)
        self.draw_weapons_platform(screen)

    def update(self, dt):
        self.orbit_player(dt)
        self.weapons_free_timer = max(0, self.weapons_free_timer - dt)
        self.acquire_target()
        self.aim_at_target()
        return self.shoot()

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
        self.range = C.EXPLOSIVE_DRONE_WEAPONS_RANGE
        self.weapons_free_timer_max = C.EXPLOSIVE_DRONE_WEAPONS_FREE_TIMER
        self.projectile_speed = C.EXPLOSIVE_DRONE_PROJECTILE_SPEED
        self.launch_animation_timer = 0
        self.launch_animation_duration = C.EXPLOSIVE_DRONE_DOOR_ANIMATION_TIME
        self.stat_source = C.EXPLOSIVE_DRONE
        self.damage_multiplier = 1.0

    def get_projectile_spawn_position(self):
        forward = self.get_forward_vector()
        return self.position + forward * (self.radius + 4)

    def weapons_free(self):
        spawn_position = self.get_projectile_spawn_position()
        forward = self.get_forward_vector()
        projectile = Rocket(spawn_position.x, spawn_position.y, self.asteroids)
        projectile.damage = int(C.ROCKET_PROJECTILE_DAMAGE * self.damage_multiplier)
        projectile.velocity = forward * self.projectile_speed
        projectile.stat_source = self.stat_source
        projectile.combat_stats = self.player.game.combat_stats
        self.launch_animation_timer = self.launch_animation_duration
        return 0

    def update(self, dt):
        super().update(dt)
        self.launch_animation_timer = max(0, self.launch_animation_timer - dt)

    def draw_weapons_platform(self, screen):
        open_ratio = 0.0
        if self.launch_animation_duration > 0:
            open_ratio = self.launch_animation_timer / self.launch_animation_duration
        surf_size = int(self.radius * 6)
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        c = surf_size // 2
        door_half_w = int(self.radius * 0.65)
        door_h = int(self.radius * 0.62)
        slide = int(door_half_w * open_ratio)
        if open_ratio > 0.05:
            silo_r = max(2, int(self.radius * 0.32))
            alpha = min(255, int(255 * open_ratio))
            pygame.draw.circle(surf, (20, 20, 20, alpha), (c, c), silo_r)
        left_rect = pygame.Rect(c - door_half_w - slide, c - door_h // 2, door_half_w, door_h)
        right_rect = pygame.Rect(c + slide, c - door_h // 2, door_half_w, door_h)
        pygame.draw.rect(surf, C.GRAY, left_rect)
        pygame.draw.rect(surf, C.GRAY, right_rect)
        pygame.draw.rect(surf, C.SILVER, left_rect, 1)
        pygame.draw.rect(surf, C.SILVER, right_rect, 1)
        if open_ratio < 0.15:
            fade = int(160 * (1 - open_ratio / 0.15))
            pygame.draw.line(surf, (20, 20, 20, fade),
                (c, c - door_h // 2), (c, c + door_h // 2), 1)
        rotated = pygame.transform.rotate(surf, -self.rotation)
        screen.blit(rotated, rotated.get_rect(center=(int(self.position.x), int(self.position.y))))

class KineticDrone(Drone):
    def __init__(self, player, asteroids):
        super().__init__(player, asteroids)
        self.body_color = C.KINETIC_DRONE_BODY_COLOR
        self.body_line_width = 0
        self.range = C.KINETIC_DRONE_WEAPONS_RANGE
        self.weapons_free_timer_max = C.KINETIC_DRONE_WEAPONS_FREE_TIMER
        self.projectile_speed = C.KINETIC_DRONE_PROJECTILE_SPEED
        self.weapons_platform_color = C.KINETIC_DRONE_WEAPONS_PLATFORM_COLOR
        self.weapons_platform_length = C.KINETIC_DRONE_WEAPONS_PLATFORM_LENGTH
        self.stat_source = C.KINETIC_DRONE
        self.damage_multiplier = 1.0

    def get_projectile_spawn_position(self):
        forward = self.get_forward_vector()
        muzzle_dist = int(self.radius * 0.1) + max(6, int(self.radius * 0.9))
        return self.position + forward * muzzle_dist

    def weapons_free(self):
        spawn_position = self.get_projectile_spawn_position()
        forward = self.get_forward_vector()
        projectile = Kinetic(spawn_position.x, spawn_position.y)
        projectile.damage = int(C.KINETIC_PROJECTILE_DAMAGE * self.damage_multiplier)
        projectile.velocity = forward * self.projectile_speed
        projectile.stat_source = self.stat_source
        projectile.combat_stats = self.player.game.combat_stats
        if MuzzleFlareVE.containers:
            MuzzleFlareVE(spawn_position.x, spawn_position.y, size=5)
        return 0

    def draw_weapons_platform(self, screen):
        surf_size = int(self.radius * 6)
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        c = surf_size // 2
        muzzle_half = max(2, int(self.radius * 0.22))
        base_half   = max(4, int(self.radius * 0.55))
        height      = max(6, int(self.radius * 0.9))
        top_y  = c - int(self.radius * 0.1) - height
        base_y = c - int(self.radius * 0.1)
        trap_pts = [(c - muzzle_half, top_y), (c + muzzle_half, top_y),
            (c + base_half,   base_y), (c - base_half,   base_y)]
        pygame.draw.polygon(surf, C.GRAY, trap_pts)
        pygame.draw.polygon(surf, C.SILVER, trap_pts, 1)
        rotated = pygame.transform.rotate(surf, -self.rotation)
        screen.blit(rotated, rotated.get_rect(center=(int(self.position.x), int(self.position.y))))

class LaserDrone(Drone):
    def __init__(self, player, asteroids):
        super().__init__(player, asteroids)
        self.body_color = C.LASER_DRONE_BODY_COLOR
        self.body_line_width = 4
        self.range = C.LASER_DRONE_WEAPONS_RANGE
        self.weapons_free_timer_max = C.LASER_DRONE_WEAPONS_FREE_TIMER
        self.damage = C.LASER_DRONE_DAMAGE
        self.weapons_platform_length = C.LASER_DRONE_WEAPONS_PLATFORM_LENGTH
        self.weapons_platform_width = C.LASER_DRONE_WEAPONS_PLATFORM_WIDTH
        self.weapons_platform_offset = C.LASER_DRONE_WEAPONS_PLATFORM_OFFSET
        self.stat_source = C.LASER_DRONE

    def acquire_target(self):
        self.target = None
        valid_targets = []
        for asteroid in self.asteroids:
            drone_distance = self.position.distance_to(asteroid.position)
            if drone_distance <= self.range:
                valid_targets.append(asteroid)
        if not valid_targets:
            return
        highest_health = max(asteroid.health for asteroid in valid_targets)
        healthiest_targets = [asteroid for asteroid in valid_targets
            if asteroid.health == highest_health]
        self.target = min(healthiest_targets,
            key=lambda asteroid: self.player.position.distance_to(asteroid.position))

    def get_projectile_spawn_position(self):
        forward = self.get_forward_vector()
        return self.position + forward * (self.radius + self.weapons_platform_offset)

    def weapons_free(self):
        if self.target is None:
            return 0
        spawn_position = self.get_projectile_spawn_position()
        projectile = LaserBeam(spawn_position.x, spawn_position.y, self.target,
            self.damage, stat_source=self.stat_source, combat_stats=self.player.game.combat_stats)
        return projectile.score

    def lerp_color(self, start_color, end_color, t):
        t = max(0, min(1, t))
        return tuple(int(start + (end - start) * t)
            for start, end in zip(start_color, end_color))

    def get_charge_ratio(self):
        if self.weapons_free_timer_max <= 0:
            return 1
        return 1 - (self.weapons_free_timer / self.weapons_free_timer_max)

    def get_platform_color(self):
        charge_colors = [C.INDIGO, C.PURPLE, C.MAGENTA,
            C.DEEP_PINK, C.RED, C.LASER_RED]
        ratio = self.get_charge_ratio()
        if ratio >= 1:
            return charge_colors[-1]
        scaled = ratio * (len(charge_colors) - 1)
        index = int(scaled)
        local_t = scaled - index
        start_color = charge_colors[index]
        end_color = charge_colors[min(index + 1, len(charge_colors) - 1)]
        return self.lerp_color(start_color, end_color, local_t)

    def draw_weapons_platform(self, screen):
        platform_color = self.get_platform_color()
        surface_size = (self.radius + self.weapons_platform_offset + self.weapons_platform_length) * 2
        platform_surface = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        center_x = surface_size // 2
        center_y = surface_size // 2
        emitter_center_y = center_y - (self.radius + self.weapons_platform_offset)
        points = [(center_x, emitter_center_y - self.weapons_platform_length),
            (center_x - self.weapons_platform_width // 2, emitter_center_y),
            (center_x + self.weapons_platform_width // 2, emitter_center_y)]
        pygame.draw.polygon(platform_surface, platform_color, points)
        rotated_platform = pygame.transform.rotate(platform_surface, -self.rotation)
        rotated_rect = rotated_platform.get_rect(center=(self.position.x, self.position.y))
        screen.blit(rotated_platform, rotated_rect)

class PlasmaDrone(Drone):
    def __init__(self, player, asteroids):
        super().__init__(player, asteroids)
        self.body_color = C.PLASMA_DRONE_BODY_COLOR
        self.range = C.PLASMA_DRONE_WEAPONS_RANGE
        self.weapons_free_timer_max = C.PLASMA_DRONE_WEAPONS_FREE_TIMER
        self.projectile_speed = C.PLASMA_DRONE_PROJECTILE_SPEED
        self.weapons_platform_color = C.PLASMA_DRONE_WEAPONS_PLATFORM_COLOR
        self.weapons_platform_length = self.radius + C.PLASMA_DRONE_WEAPONS_PLATFORM_LENGTH_OFFSET
        self.weapons_platform_width = C.PLASMA_DRONE_WEAPONS_PLATFORM_WIDTH
        self.stat_source = C.PLASMA_DRONE
        self.damage_multiplier = 1.0

    def get_projectile_spawn_position(self):
        forward = self.get_forward_vector()
        return self.position + forward * self.weapons_platform_length

    def weapons_free(self):
        spawn_position = self.get_projectile_spawn_position()
        forward = self.get_forward_vector()
        projectile = Plasma(spawn_position.x, spawn_position.y)
        projectile.damage = int(C.PLASMA_PROJECTILE_DAMAGE * self.damage_multiplier)
        projectile.velocity = forward * self.projectile_speed
        projectile.stat_source = self.stat_source
        projectile.combat_stats = self.player.game.combat_stats
        return 0

    def draw_weapons_platform(self, screen):
        surf_size = int(self.weapons_platform_length * 3)
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        c = surf_size // 2
        bw = self.weapons_platform_width
        bh = self.weapons_platform_length
        barrel_rect = pygame.Rect(c - bw // 2, c - bh, bw, bh)
        pygame.draw.rect(surf, C.SILVER, barrel_rect)
        pygame.draw.rect(surf, C.GRAY, barrel_rect, 1)
        muzzle_w = bw + 4
        muzzle_h = max(4, bw // 2 + 1)
        muzzle_rect = pygame.Rect(c - muzzle_w // 2, c - bh - muzzle_h + 2, muzzle_w, muzzle_h)
        pygame.draw.rect(surf, C.LIGHT_GRAY, muzzle_rect)
        pygame.draw.rect(surf, C.GRAY, muzzle_rect, 1)
        rotated = pygame.transform.rotate(surf, -self.rotation)
        screen.blit(rotated, rotated.get_rect(center=(int(self.position.x), int(self.position.y))))

class SentinelDrone(Drone):
    def __init__(self, player, asteroids):
        super().__init__(player, asteroids)
        self.body_color = C.SENTINEL_DRONE_BODY_COLOR
        self.body_line_width = 0
        self.radius = int(C.DRONE_RADIUS * 0.65)  # smaller body than combat drones
        self.weapons_platform_color = C.SENTINEL_DRONE_WEAPONS_PLATFORM_COLOR
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

    def draw_weapons_platform(self, screen):
        direction = self.player.position - self.position
        if direction.length_squared() == 0:
            return
        angle = pygame.Vector2(0, -1).angle_to(direction)
        r = self.radius
        n = 14
        fang_len   = int(r * 1.5)
        base_sep   = int(r * 0.72)
        tip_inward = int(r * 0.55)
        base_w     = max(2, int(r * 0.22))   
        tip_w      = max(1, int(r * 0.07))   
        surf_size = int(r * 8)
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        c = surf_size // 2
        root_y = c - r
        for side in (-1, 1):
            root_cx = c + side * base_sep
            tip_cx  = c + side * (base_sep - tip_inward)
            tip_y   = root_y - fang_len
            outer_pts = []
            inner_pts = []
            for i in range(n + 1):
                t = i / n
                y = root_y - int(t * fang_len)
                spine_x = root_cx + (tip_cx - root_cx) * (t ** 0.7)
                hw = base_w + (tip_w - base_w) * t
                bow = side * hw * (1.0 + 0.9 * math.sin(t * math.pi))
                outer_pts.append((spine_x + bow, y))
                inner_pts.append((spine_x - bow * 0.35, y))
            fang_poly = outer_pts + list(reversed(inner_pts))
            pygame.draw.polygon(surf, self.weapons_platform_color, fang_poly)
            pygame.draw.polygon(surf, C.LIGHT_GRAY, fang_poly, 1)
        rotated = pygame.transform.rotate(surf, -angle)
        screen.blit(rotated, rotated.get_rect(center=(int(self.position.x), int(self.position.y))))