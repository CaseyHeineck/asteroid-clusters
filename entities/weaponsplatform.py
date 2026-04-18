import math
import pygame
from core import constants as C
from entities.projectile import Kinetic, LaserBeam, Plasma, Rocket
from ui.visualeffect import MuzzleFlareVE

class WeaponsPlatform:
    def __init__(self):
        self.weapons_free_timer = 0.0
        self.weapons_free_timer_max = 0.0
        self.range = float("inf")
        self.damage_multiplier = 1.0

    def tick(self, dt):
        self.weapons_free_timer = max(0.0, self.weapons_free_timer - dt)

    def can_fire(self):
        return self.weapons_free_timer <= 0.0

    def fire(self, owner):
        raise NotImplementedError

    def draw(self, screen, owner):
        raise NotImplementedError


class KineticPlatform(WeaponsPlatform):
    def __init__(self):
        super().__init__()
        self.weapons_free_timer_max = C.KINETIC_DRONE_WEAPONS_FREE_TIMER
        self.range = C.KINETIC_DRONE_WEAPONS_RANGE
        self.projectile_speed = C.KINETIC_DRONE_PROJECTILE_SPEED

    def _muzzle_position(self, owner):
        forward = owner.get_forward_vector()
        muzzle_dist = int(owner.radius * 0.1) + max(6, int(owner.radius * 0.9))
        return owner.position + forward * muzzle_dist

    def fire(self, owner):
        spawn_pos = self._muzzle_position(owner)
        forward = owner.get_forward_vector()
        projectile = Kinetic(spawn_pos.x, spawn_pos.y)
        projectile.damage = int(C.KINETIC_PROJECTILE_DAMAGE * self.damage_multiplier)
        projectile.velocity = forward * self.projectile_speed
        projectile.stat_source = owner.stat_source
        projectile.combat_stats = owner.game.combat_stats
        projectile.extra_abilities = set(owner.extra_abilities)
        projectile.asteroids = owner.asteroids
        projectile.element = owner.element
        if MuzzleFlareVE.containers:
            MuzzleFlareVE(spawn_pos.x, spawn_pos.y, size=5)
        self.weapons_free_timer = self.weapons_free_timer_max
        return 0

    def draw(self, screen, owner):
        surf_size = int(owner.radius * 6)
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        c = surf_size // 2
        muzzle_half = max(2, int(owner.radius * 0.22))
        base_half   = max(4, int(owner.radius * 0.55))
        height      = max(6, int(owner.radius * 0.9))
        top_y  = c - int(owner.radius * 0.1) - height
        base_y = c - int(owner.radius * 0.1)
        trap_pts = [(c - muzzle_half, top_y), (c + muzzle_half, top_y),
            (c + base_half, base_y), (c - base_half, base_y)]
        pygame.draw.polygon(surf, C.GRAY, trap_pts)
        pygame.draw.polygon(surf, C.SILVER, trap_pts, 1)
        rotated = pygame.transform.rotate(surf, -owner.rotation)
        screen.blit(rotated, rotated.get_rect(center=(int(owner.position.x), int(owner.position.y))))


class PlasmaPlatform(WeaponsPlatform):
    def __init__(self, base_damage=C.PLASMA_PROJECTILE_DAMAGE, projectile_color=None):
        super().__init__()
        self.weapons_free_timer_max = C.PLASMA_DRONE_WEAPONS_FREE_TIMER
        self.range = C.PLASMA_DRONE_WEAPONS_RANGE
        self.projectile_speed = C.PLASMA_DRONE_PROJECTILE_SPEED
        self.base_damage = base_damage
        self.projectile_color = projectile_color

    def _muzzle_position(self, owner):
        forward = owner.get_forward_vector()
        platform_length = owner.radius + C.PLASMA_DRONE_WEAPONS_PLATFORM_LENGTH_OFFSET
        return owner.position + forward * platform_length

    def fire(self, owner):
        spawn_pos = self._muzzle_position(owner)
        forward = owner.get_forward_vector()
        projectile = Plasma(spawn_pos.x, spawn_pos.y)
        projectile.damage = int(self.base_damage * self.damage_multiplier)
        projectile.velocity = forward * self.projectile_speed
        projectile.stat_source = owner.stat_source
        projectile.combat_stats = owner.game.combat_stats
        projectile.extra_abilities = set(owner.extra_abilities)
        projectile.asteroids = owner.asteroids
        projectile.element = owner.element
        if self.projectile_color is not None:
            projectile.color = self.projectile_color
        self.weapons_free_timer = self.weapons_free_timer_max
        return 0

    def draw(self, screen, owner):
        platform_length = owner.radius + C.PLASMA_DRONE_WEAPONS_PLATFORM_LENGTH_OFFSET
        surf_size = int(platform_length * 3)
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        c = surf_size // 2
        bw = C.PLASMA_DRONE_WEAPONS_PLATFORM_WIDTH
        bh = int(platform_length)
        barrel_rect = pygame.Rect(c - bw // 2, c - bh, bw, bh)
        pygame.draw.rect(surf, C.SILVER, barrel_rect)
        pygame.draw.rect(surf, C.GRAY, barrel_rect, 1)
        muzzle_w = bw + 4
        muzzle_h = max(4, bw // 2 + 1)
        muzzle_rect = pygame.Rect(c - muzzle_w // 2, c - bh - muzzle_h + 2, muzzle_w, muzzle_h)
        pygame.draw.rect(surf, C.LIGHT_GRAY, muzzle_rect)
        pygame.draw.rect(surf, C.GRAY, muzzle_rect, 1)
        rotated = pygame.transform.rotate(surf, -owner.rotation)
        screen.blit(rotated, rotated.get_rect(center=(int(owner.position.x), int(owner.position.y))))


class LaserPlatform(WeaponsPlatform):
    def __init__(self):
        super().__init__()
        self.weapons_free_timer_max = C.LASER_DRONE_WEAPONS_FREE_TIMER
        self.range = C.LASER_DRONE_WEAPONS_RANGE
        self.damage = C.LASER_DRONE_DAMAGE

    def fire(self, owner):
        if owner.target is None:
            return 0
        forward = owner.get_forward_vector()
        spawn_pos = owner.position + forward * (owner.radius + C.LASER_DRONE_WEAPONS_PLATFORM_OFFSET)
        projectile = LaserBeam(spawn_pos.x, spawn_pos.y, owner.target,
            self.damage, stat_source=owner.stat_source,
            combat_stats=owner.game.combat_stats,
            extra_abilities=owner.extra_abilities,
            asteroids=owner.asteroids, element=owner.element)
        self.weapons_free_timer = self.weapons_free_timer_max
        return projectile.score

    def get_charge_ratio(self):
        if self.weapons_free_timer_max <= 0:
            return 1
        return 1 - (self.weapons_free_timer / self.weapons_free_timer_max)

    def get_platform_color(self):
        charge_colors = [C.INDIGO, C.PURPLE, C.MAGENTA, C.DEEP_PINK, C.RED, C.LASER_RED]
        ratio = self.get_charge_ratio()
        if ratio >= 1:
            return charge_colors[-1]
        scaled = ratio * (len(charge_colors) - 1)
        index = int(scaled)
        local_t = scaled - index
        return self.lerp_color(charge_colors[index],
            charge_colors[min(index + 1, len(charge_colors) - 1)], local_t)

    def lerp_color(self, start_color, end_color, t):
        t = max(0, min(1, t))
        return tuple(int(s + (e - s) * t) for s, e in zip(start_color, end_color))

    def draw(self, screen, owner):
        platform_color = self.get_platform_color()
        offset = C.LASER_DRONE_WEAPONS_PLATFORM_OFFSET
        length = C.LASER_DRONE_WEAPONS_PLATFORM_LENGTH
        width = C.LASER_DRONE_WEAPONS_PLATFORM_WIDTH
        surface_size = (owner.radius + offset + length) * 2
        surf = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        cx = surface_size // 2
        cy = surface_size // 2
        emitter_y = cy - (owner.radius + offset)
        points = [(cx, emitter_y - length),
            (cx - width // 2, emitter_y),
            (cx + width // 2, emitter_y)]
        pygame.draw.polygon(surf, platform_color, points)
        rotated = pygame.transform.rotate(surf, -owner.rotation)
        screen.blit(rotated, rotated.get_rect(center=(owner.position.x, owner.position.y)))


class ExplosivePlatform(WeaponsPlatform):
    def __init__(self):
        super().__init__()
        self.weapons_free_timer_max = C.EXPLOSIVE_DRONE_WEAPONS_FREE_TIMER
        self.range = C.EXPLOSIVE_DRONE_WEAPONS_RANGE
        self.projectile_speed = C.EXPLOSIVE_DRONE_PROJECTILE_SPEED
        self.launch_animation_timer = 0.0
        self.launch_animation_duration = C.EXPLOSIVE_DRONE_DOOR_ANIMATION_TIME

    def tick(self, dt):
        super().tick(dt)
        self.launch_animation_timer = max(0.0, self.launch_animation_timer - dt)

    def fire(self, owner):
        forward = owner.get_forward_vector()
        spawn_pos = owner.position + forward * (owner.radius + 4)
        projectile = Rocket(spawn_pos.x, spawn_pos.y, owner.asteroids)
        projectile.damage = int(C.ROCKET_PROJECTILE_DAMAGE * self.damage_multiplier)
        projectile.velocity = forward * self.projectile_speed
        projectile.stat_source = owner.stat_source
        projectile.combat_stats = owner.game.combat_stats
        projectile.extra_abilities = set(owner.extra_abilities)
        projectile.element = owner.element
        self.launch_animation_timer = self.launch_animation_duration
        self.weapons_free_timer = self.weapons_free_timer_max
        return 0

    def draw(self, screen, owner):
        open_ratio = 0.0
        if self.launch_animation_duration > 0:
            open_ratio = self.launch_animation_timer / self.launch_animation_duration
        surf_size = int(owner.radius * 6)
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        c = surf_size // 2
        door_half_w = int(owner.radius * 0.65)
        door_h = int(owner.radius * 0.62)
        slide = int(door_half_w * open_ratio)
        if open_ratio > 0.05:
            silo_r = max(2, int(owner.radius * 0.32))
            alpha = min(255, int(255 * open_ratio))
            pygame.draw.circle(surf, (20, 20, 20, alpha), (c, c), silo_r)
        left_rect  = pygame.Rect(c - door_half_w - slide, c - door_h // 2, door_half_w, door_h)
        right_rect = pygame.Rect(c + slide,               c - door_h // 2, door_half_w, door_h)
        pygame.draw.rect(surf, C.GRAY,   left_rect)
        pygame.draw.rect(surf, C.GRAY,   right_rect)
        pygame.draw.rect(surf, C.SILVER, left_rect,  1)
        pygame.draw.rect(surf, C.SILVER, right_rect, 1)
        if open_ratio < 0.15:
            fade = int(160 * (1 - open_ratio / 0.15))
            pygame.draw.line(surf, (20, 20, 20, fade),
                (c, c - door_h // 2), (c, c + door_h // 2), 1)
        rotated = pygame.transform.rotate(surf, -owner.rotation)
        screen.blit(rotated, rotated.get_rect(center=(int(owner.position.x), int(owner.position.y))))


class SentinelPlatform(WeaponsPlatform):
    def __init__(self):
        super().__init__()
        self.range = 0.0
        self.weapons_free_timer_max = 0.0

    def can_fire(self):
        return False

    def fire(self, owner):
        return 0

    def draw(self, screen, owner):
        direction = owner.player.position - owner.position
        if direction.length_squared() == 0:
            return
        angle = pygame.Vector2(0, -1).angle_to(direction)
        r = owner.radius
        n = 14
        fang_len   = int(r * 1.5)
        base_sep   = int(r * 0.72)
        tip_inward = int(r * 0.55)
        base_w     = max(2, int(r * 0.22))
        tip_w      = max(1, int(r * 0.07))
        surf_size  = int(r * 8)
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        c = surf_size // 2
        root_y = c - r
        for side in (-1, 1):
            root_cx = c + side * base_sep
            tip_cx  = c + side * (base_sep - tip_inward)
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
            pygame.draw.polygon(surf, C.SENTINEL_DRONE_WEAPONS_PLATFORM_COLOR, fang_poly)
            pygame.draw.polygon(surf, C.LIGHT_GRAY, fang_poly, 1)
        rotated = pygame.transform.rotate(surf, -angle)
        screen.blit(rotated, rotated.get_rect(center=(int(owner.position.x), int(owner.position.y))))
