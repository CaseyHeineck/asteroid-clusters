import math
import pygame
import constants as C

class Display:
    def __init__(self, x, y, font_size=50, color=C.CYAN):
        self.score = 0
        self.font = pygame.font.Font(None, font_size)
        self.small_font = pygame.font.Font(None, 36)
        self.color = color
        self.x, self.y = x, y
        self.player_lives = 3
        self.max_lives = 3
        self.life_regen = False
        self.life_regen_timer = 0.0
        self.level = 1
        self.xp_current = 0
        self.xp_needed = int(C.EXP_LEVEL_BASE)
        self.level_up_timer = 0.0
        self.level_up_duration = 2.5
        self.essence = 0
        self.update_image()

    def update_image(self):
        self.image = self.font.render(f"Score: {int(self.score)}", True, self.color)
        self.rect = self.image.get_rect(topleft=(68, 18))

    def update_score(self, points):
        self.score += points
        if self.score <= 0:
            self.score = 0
        self.update_image()

    def update_player_lives(self, player_lives):
        self.player_lives = player_lives

    def update_life_regen_state(self, life_regen, timer, max_lives):
        self.life_regen = life_regen
        self.life_regen_timer = timer
        self.max_lives = max_lives

    def update_essence(self, amount):
        self.essence = amount

    def update_level(self, level, xp_current, xp_needed):
        if level > self.level:
            self.level_up_timer = self.level_up_duration
        self.level = level
        self.xp_current = xp_current
        self.xp_needed = max(1, xp_needed)

    def update(self, dt):
        if self.level_up_timer > 0:
            self.level_up_timer = max(0.0, self.level_up_timer - dt)

    def _heart_points(self, cx, cy, size, n=60):
        scale = size / 17.0
        points = []
        for i in range(n):
            t = 2 * math.pi * i / n
            x = 16 * (math.sin(t) ** 3)
            y = -(13 * math.cos(t) - 5 * math.cos(2 * t)
                - 2 * math.cos(3 * t) - math.cos(4 * t))
            points.append((cx + x * scale, cy + y * scale))
        return points

    def draw_heart(self, screen):
        size = 22
        cx = 34
        cy = 40
        pts = self._heart_points(cx, cy, size)
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        heart_h = max_y - min_y
        regen_filling = self.life_regen and self.player_lives < self.max_lives
        if regen_filling:
            ratio = min(1.0, self.life_regen_timer / C.PLAYER_LIFE_REGEN_INTERVAL)
            if ratio > 0:
                fill_top = max_y - heart_h * ratio
                clip = pygame.Rect(
                    int(min_x) - 1, int(fill_top),
                    int(max_x - min_x) + 2, int(max_y - fill_top) + 2)
                old_clip = screen.get_clip()
                screen.set_clip(clip)
                pygame.draw.polygon(screen, C.HEART_RUBY, pts)
                screen.set_clip(old_clip)
        else:
            pygame.draw.polygon(screen, C.HEART_RUBY, pts)
        pygame.draw.polygon(screen, C.WHITE, pts, 2)
        lives_surf = self.small_font.render(str(self.player_lives), True, C.WHITE)
        lives_rect = lives_surf.get_rect(center=(int(cx), int(cy + size * 0.18)))
        screen.blit(lives_surf, lives_rect)

    def draw(self, screen):
        self.draw_heart(screen)
        screen.blit(self.image, self.rect)
        level_text = self.small_font.render(f"LVL {self.level}", True, C.NEON_GREEN)
        screen.blit(level_text, (C.SCREEN_WIDTH - level_text.get_width() - 12, 12))
        bar_height = 8
        bar_y = C.SCREEN_HEIGHT - bar_height
        ratio = min(1.0, self.xp_current / self.xp_needed)
        fill_width = int(C.SCREEN_WIDTH * ratio)
        pygame.draw.rect(screen, C.DARK_GRAY, (0, bar_y, C.SCREEN_WIDTH, bar_height))
        if fill_width > 0:
            pygame.draw.rect(screen, C.NEON_GREEN, (0, bar_y, fill_width, bar_height))
        pygame.draw.rect(screen, C.LIGHT_GRAY, (0, bar_y, C.SCREEN_WIDTH, bar_height), 1)
        essence_text = self.small_font.render(f"◆ {self.essence}", True, C.BRIGHT_PURPLE)
        screen.blit(essence_text, (C.SCREEN_WIDTH - essence_text.get_width() - 12, 42))
        if self.level_up_timer > 0:
            fade = min(1.0, self.level_up_timer / 0.4)
            alpha = int(255 * fade)
            levelup_font = pygame.font.Font(None, 72)
            levelup_surf = levelup_font.render(f"LEVEL {self.level}!", True, C.NEON_GREEN)
            levelup_surf.set_alpha(alpha)
            cx = (C.SCREEN_WIDTH - levelup_surf.get_width()) // 2
            cy = C.SCREEN_HEIGHT // 3
            screen.blit(levelup_surf, (cx, cy))
