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

class ExplosionVE(VisualEffect):
    def __init__(self, x, y, radius=C.EXPLOSION_RADIUS, color=C.EXPLOSION_COLOR,
            duration=C.EXPLOSION_DURATION, max_alpha=C.EXPLOSION_MAX_ALPHA, line_width=0):
        super().__init__(x, y, duration)
        self.radius = radius
        self.color = color
        self.max_alpha = max_alpha
        self.line_width = line_width

    def draw(self, screen):
        if self.duration <= 0:
            return
        alpha_ratio = max(0, self.timer / self.duration)
        alpha = int(self.max_alpha * alpha_ratio)
        surface_size = self.radius * 2
        effect_surface = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        pygame.draw.circle(effect_surface, (*self.color, alpha), (self.radius, self.radius),
                    self.radius, self.line_width)
        rect = effect_surface.get_rect(center=(self.position.x, self.position.y))
        screen.blit(effect_surface, rect)

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