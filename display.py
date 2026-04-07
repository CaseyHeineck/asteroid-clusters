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
        self.level = 1
        self.xp_current = 0
        self.xp_needed = int(C.EXP_LEVEL_BASE)
        self.level_up_timer = 0.0
        self.level_up_duration = 2.5
        self.essence = 0
        self.update_image()

    def update_image(self):
        self.image = self.font.render(
            f"Lives: {self.player_lives}  Score: {int(self.score)}", True, self.color)
        self.rect = self.image.get_rect(topleft=(self.x, self.y))

    def update_score(self, points):
        self.score += points
        if self.score <= 0:
            self.score = 0
        self.update_image()

    def update_player_lives(self, player_lives):
        self.player_lives = player_lives
        self.update_image()

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

    def draw(self, screen):
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
