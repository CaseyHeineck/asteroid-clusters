import pygame
from core import constants as C

class VisualEffect(pygame.sprite.Sprite):
    def __init__(self, x, y, duration=0):
        super().__init__(self.containers)
        self.position = pygame.Vector2(x, y)
        self.duration = duration
        self.timer = duration

    def update(self, dt):
        if self.duration > 0:
            self.timer = max(0, self.timer - dt)
            if self.timer == 0:
                self.kill()

    def draw(self, screen):
        raise NotImplementedError("Effect subclasses must implement draw()")
    
class BaseExplosion(VisualEffect):
    def __init__(self, x, y, radius, base_color=C.BASE_EXPLOSION_COLOR,
            base_duration=C.BASE_EXPLOSION_DURATION, base_max_alpha=C.BASE_EXPLOSION_MAX_ALPHA,
            overlay_color=None, overlay_duration=None, overlay_max_alpha=0, line_width=0):
        duration = max(base_duration, overlay_duration or 0)
        super().__init__(x, y, duration)
        self.radius = radius
        self.base_color = base_color
        self.base_duration = base_duration
        self.base_max_alpha = base_max_alpha
        self.overlay_color = overlay_color
        self.overlay_duration = overlay_duration or 0
        self.overlay_max_alpha = overlay_max_alpha
        self.line_width = line_width

    def get_alpha(self, layer_duration, max_alpha):
        if layer_duration <= 0:
            return 0
        elapsed = self.duration - self.timer
        remaining = max(0, layer_duration - elapsed)
        ratio = remaining / layer_duration
        return int(max_alpha * ratio)

    def draw_circle(self, surface, color, alpha):
        if alpha <= 0:
            return
        surface_size = self.radius * 2
        circle_surface = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        pygame.draw.circle(circle_surface, (*color, alpha),
            (self.radius, self.radius), self.radius, self.line_width)
        surface.blit(circle_surface, (0, 0))

    def draw(self, screen):
        surface_size = self.radius * 2
        effect_surface = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        base_alpha = self.get_alpha(self.base_duration, self.base_max_alpha)
        self.draw_circle(effect_surface, self.base_color, base_alpha)
        if self.overlay_color:
            overlay_alpha = self.get_alpha(self.overlay_duration, self.overlay_max_alpha)
            self.draw_circle(effect_surface, self.overlay_color, overlay_alpha)
        rect = effect_surface.get_rect(center=(self.position.x, self.position.y))
        screen.blit(effect_surface, rect)
class AsteroidKillExplosionVE(BaseExplosion):
    def __init__(self, x, y, radius):
        super().__init__(x, y, radius,
            overlay_color=C.ASTEROID_KILL_EXPLOSION_COLOR,
            overlay_duration=C.ASTEROID_KILL_EXPLOSION_DURATION,
            overlay_max_alpha=C.ASTEROID_KILL_EXPLOSION_MAX_ALPHA)
class OverkillExplosionVE(BaseExplosion):
    def __init__(self, x, y, radius):
        super().__init__(x, y, radius,
            overlay_color=C.OVERKILL_EXPLOSION_COLOR,
            overlay_duration=C.OVERKILL_EXPLOSION_DURATION,
            overlay_max_alpha=C.OVERKILL_EXPLOSION_MAX_ALPHA)
class RocketHitExplosionVE(BaseExplosion):
    def __init__(self, x, y, radius):
        super().__init__(x, y, radius,
            overlay_color=C.ROCKET_HIT_EXPLOSION_COLOR,
            overlay_duration=C.ROCKET_HIT_EXPLOSION_DURATION,
            overlay_max_alpha=C.ROCKET_HIT_EXPLOSION_MAX_ALPHA)
class EnemyKillExplosionVE(BaseExplosion):
    def __init__(self, x, y, radius):
        super().__init__(x, y, radius,
            overlay_color=C.ENEMY_KILL_EXPLOSION_COLOR,
            overlay_duration=C.ENEMY_KILL_EXPLOSION_DURATION,
            overlay_max_alpha=C.ENEMY_KILL_EXPLOSION_MAX_ALPHA)

class MuzzleFlareVE(VisualEffect):
    def __init__(self, x, y, size=7):
        super().__init__(x, y, duration=0.08)
        self.size = size

    def draw(self, screen):
        ratio = self.timer / self.duration if self.duration > 0 else 0
        expand = 1 - ratio
        surf_size = int((self.size + 18) * 2)
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        c = surf_size // 2
        outer_r = max(1, int(self.size + 10 * expand))
        pygame.draw.circle(surf, (*C.DARK_ORANGE, int(180 * ratio)), (c, c), outer_r,
            max(1, int(3 * ratio)))
        mid_r = max(1, int(self.size * (0.7 + 0.5 * ratio)))
        pygame.draw.circle(surf, (*C.ORANGE, int(220 * ratio)), (c, c), mid_r)
        core_r = max(1, int(self.size * 0.45 * ratio))
        pygame.draw.circle(surf, (*C.WHITE, int(255 * ratio)), (c, c), core_r)
        screen.blit(surf, surf.get_rect(center=(int(self.position.x), int(self.position.y))))

class RocketExhaustVE(VisualEffect):
    def __init__(self, x, y, size=5):
        super().__init__(x, y, duration=0.12)
        self.size = size

    def draw(self, screen):
        ratio = self.timer / self.duration if self.duration > 0 else 0
        surf_size = int((self.size + 14) * 2)
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        c = surf_size // 2
        layers = [
            (self.size * 1.6, C.DARK_ORANGE, 110),
            (self.size * 1.0, C.ORANGE,      170),
            (self.size * 0.5, C.YELLOW,       200),
        ]
        for r_scale, color, max_alpha in layers:
            r = max(1, int(r_scale * ratio))
            alpha = int(max_alpha * ratio)
            if alpha > 0:
                pygame.draw.circle(surf, (*color, alpha), (c, c), r)
        screen.blit(surf, surf.get_rect(center=(int(self.position.x), int(self.position.y))))

class ShipExhaustVE(VisualEffect):
    def __init__(self, x, y, direction, length=28, width=7):
        super().__init__(x, y, duration=0.001)
        self.direction = pygame.Vector2(direction).normalize()
        self.length = length
        self.width = width

    def draw(self, screen):
        ratio = self.timer / self.duration if self.duration > 0 else 0
        if ratio <= 0:
            return
        end = self.position + self.direction * self.length
        pad = self.width + 2
        min_x = int(min(self.position.x, end.x)) - pad
        min_y = int(min(self.position.y, end.y)) - pad
        max_x = int(max(self.position.x, end.x)) + pad
        max_y = int(max(self.position.y, end.y)) + pad
        surf = pygame.Surface((max(1, max_x - min_x), max(1, max_y - min_y)), pygame.SRCALPHA)
        origin = pygame.Vector2(self.position.x - min_x, self.position.y - min_y)
        steps = 9
        for i in range(steps):
            t = i / (steps - 1)
            p = origin + self.direction * (self.length * t)
            r = max(1, int(self.width * (1.0 - t * 0.88)))
            if   t < 0.15: color, max_a = C.WHITE,       240
            elif t < 0.40: color, max_a = C.YELLOW,      215
            elif t < 0.70: color, max_a = C.ORANGE,      170
            else:          color, max_a = C.DARK_ORANGE,  80
            alpha = int(max_a * ratio)
            if alpha > 0:
                pygame.draw.circle(surf, (*color, alpha), (int(p.x), int(p.y)), r)
        screen.blit(surf, (min_x, min_y))


class LaserBeamVE(VisualEffect):
    def __init__(self, start_pos, end_pos, color=C.LASER_BEAM_COLOR, width=C.LASER_BEAM_WIDTH,
            duration=C.LASER_BEAM_DURATION, max_alpha=255):
        midpoint = (pygame.Vector2(start_pos) + pygame.Vector2(end_pos)) / 2
        super().__init__(midpoint.x, midpoint.y, duration)
        self.start_pos = pygame.Vector2(start_pos)
        self.end_pos = pygame.Vector2(end_pos)
        self.color = color
        self.width = width
        self.max_alpha = max_alpha

    def draw(self, screen):
        if self.duration <= 0:
            return
        alpha_ratio = max(0, self.timer / self.duration)
        alpha = int(self.max_alpha * alpha_ratio)
        overlay = pygame.Surface((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.line(overlay, (*self.color, alpha), self.start_pos, self.end_pos, self.width)
        screen.blit(overlay, (0, 0))

