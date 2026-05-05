import pygame
from core import constants as C
from core.circleshape import CircleShape

class Decoy(CircleShape):
    def __init__(self, x, y):
        super().__init__(x, y, C.DECOY_RADIUS)

    def update(self, dt):
        pass

    def collides_with(self, other):
        return False

    def draw(self, screen):
        pygame.draw.circle(screen, C.DECOY_COLOR, self.position, self.radius, 2)
