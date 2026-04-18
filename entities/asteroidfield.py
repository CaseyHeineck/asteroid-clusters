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

    def __init__(self, asteroids_group):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.spawn_timer = 0.0
        self.asteroids_group = asteroids_group

    def spawn(self, size, position, velocity):
        asteroid = Asteroid(position.x, position.y, size)
        asteroid.velocity = velocity
        elemental_chance = (C.ASTEROID_LARGE_ELEMENTAL_SPAWN_CHANCE
                            if size >= C.ASTEROID_LARGE_THRESHOLD
                            else C.ASTEROID_ELEMENTAL_SPAWN_CHANCE)
        if random.random() < elemental_chance:
            asteroid.element = random.choice(ALL_ELEMENTS)

    def update(self, dt):
        self.spawn_timer += dt
        if self.spawn_timer > C.ASTEROID_SPAWN_RATE_SECONDS:
            self.spawn_timer = 0
            current_size = sum(a.size for a in self.asteroids_group)
            if current_size >= C.ASTEROID_SIZE_CAP:
                return
            edge = random.choice(self.edges)
            speed = random.uniform(C.ASTEROID_MIN_SPEED**0.5, C.ASTEROID_MAX_SPEED**0.5) ** 2
            velocity = edge[0] * speed
            velocity = velocity.rotate(random.randint(-30, 30))
            position = edge[1](random.uniform(0, 1))
            if random.random() < C.ASTEROID_LARGE_SPAWN_CHANCE:
                size = random.randint(C.ASTEROID_LARGE_THRESHOLD, C.ASTEROID_LARGE_SPAWN_MAX)
            else:
                size = random.randint(1, C.ASTEROID_KINDS)
            self.spawn(size, position, velocity)
