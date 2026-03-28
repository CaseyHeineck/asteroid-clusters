import pygame
import constants as C

class Display:
    def __init__(self, x, y, font_size=50, color=C.CYAN):
        self.score = 0
        self.font = pygame.font.Font(None, font_size)
        self.color = color
        self.x, self.y = x, y
        self.player_lives = 3
        self.update_image()

    def update_image(self):
        self.image = self.font.render(f"Lives: {self.player_lives}  Score: {int(self.score)}", True, self.color)
        self.rect = self.image.get_rect(topleft=(self.x, self.y))

    def update_score(self, points):
        self.score += points
        if self.score <= 0:
            self.score = 0
        self.update_image()

    def update_player_lives(self, player_lives):
        self.player_lives = player_lives
        self.update_image()

    def update(self, dt):
        pass        

    def draw(self, screen):
        screen.blit(self.image, self.rect)