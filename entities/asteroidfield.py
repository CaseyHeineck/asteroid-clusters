import pygame
import random
from core import constants as C
from core.element import ALL_ELEMENTS
from entities.asteroid import Asteroid

class AsteroidField(pygame.sprite.Sprite):
    edges = [
        [
            pygame.Vector2(1, 0),
            lambda y: pygame.Vector2(-C.ASTEROID_MAX_RADIUS, y * C.SCREEN_HEIGHT),
        ],
        [
            pygame.Vector2(-1, 0),
            lambda y: pygame.Vector2(
                C.SCREEN_WIDTH + C.ASTEROID_MAX_RADIUS, y * C.SCREEN_HEIGHT
            ),
        ],
        [
            pygame.Vector2(0, 1),
            lambda x: pygame.Vector2(x * C.SCREEN_WIDTH, -C.ASTEROID_MAX_RADIUS),
        ],
        [
            pygame.Vector2(0, -1),
            lambda x: pygame.Vector2(
                x * C.SCREEN_WIDTH, C.SCREEN_HEIGHT + C.ASTEROID_MAX_RADIUS
            ),
        ],
    ]

    def __init__(self):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.spawn_timer = 0.0

    def spawn(self, radius, position, velocity):
        asteroid = Asteroid(position.x, position.y, radius)
        asteroid.velocity = velocity
        if random.random() < C.ASTEROID_ELEMENTAL_SPAWN_CHANCE:
            asteroid.element = random.choice(ALL_ELEMENTS)

    def update(self, dt):
        self.spawn_timer += dt
        if self.spawn_timer > C.ASTEROID_SPAWN_RATE_SECONDS:
            self.spawn_timer = 0
            edge = random.choice(self.edges)
            speed = random.uniform(C.ASTEROID_MIN_SPEED**0.5, C.ASTEROID_MAX_SPEED**0.5) ** 2
            velocity = edge[0] * speed
            velocity = velocity.rotate(random.randint(-30, 30))
            position = edge[1](random.uniform(0, 1))
            kind = random.randint(1, C.ASTEROID_KINDS)
            self.spawn(kind, position, velocity)