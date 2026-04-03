import pygame
import constants as C

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

# class PlasmaBurnVE(VisualEffect):
#     def __init__(self, x, y, radius=C.PLASMA_BURN_MARK_RADIUS, color=C.PLASMA_BURN_MARK_COLOR,
#             triangle_count=C.PLASMA_BURN_MARK_TRIANGLE_COUNT, triangle_length=C.PLASMA_BURN_MARK_TRIANGLE_LENGTH,
#             triangle_width=C.PLASMA_BURN_MARK_TRIANGLE_WIDTH, duration=C.PLASMA_BURN_MARK_DURATION,
#             max_alpha=C.PLASMA_BURN_MARK_MAX_ALPHA):
#         super().__init__(x, y, duration)
#         self.radius = radius
#         self.color = color
#         self.triangle_count = triangle_count
#         self.triangle_length = triangle_length
#         self.triangle_width = triangle_width
#         self.max_alpha = max_alpha

#     def draw(self, screen):
#         if self.duration <= 0:
#             return
#         alpha_ratio = max(0, self.timer / self.duration)
#         alpha = int(self.max_alpha * alpha_ratio)
#         overlay = pygame.Surface((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.SRCALPHA)
#         for i in range(self.triangle_count):
#             angle = (360 / self.triangle_count) * i
#             forward = pygame.Vector2(0, -1).rotate(angle)
#             right = forward.rotate(90)
#             tip = self.position + forward * (self.radius + self.triangle_length)
#             base_center = self.position + forward * self.radius
#             left = base_center - right * (self.triangle_width / 2)
#             right_point = base_center + right * (self.triangle_width / 2)
#             pygame.draw.polygon(overlay, (*self.color, alpha), [tip, left, right_point])
#         screen.blit(overlay, (0, 0))