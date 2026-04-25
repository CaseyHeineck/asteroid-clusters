import pygame
import random
from core import constants as C
from core.element import ALL_ELEMENTS
from entities.enemy import KineticEnemy, PlasmaEnemy

class EnemySpawner(pygame.sprite.Sprite):
    def __init__(self, game):
        pygame.sprite.Sprite.__init__(self, self.containers)
        self.game = game
        self.spawn_timer = 0.0

    def _offscreen_position(self):
        edge = random.randint(0, 3)
        if edge == 0:
            return -C.ENEMY_SPAWN_MARGIN, random.uniform(0, C.SCREEN_HEIGHT)
        elif edge == 1:
            return C.SCREEN_WIDTH + C.ENEMY_SPAWN_MARGIN, random.uniform(0, C.SCREEN_HEIGHT)
        elif edge == 2:
            return random.uniform(0, C.SCREEN_WIDTH), -C.ENEMY_SPAWN_MARGIN
        else:
            return random.uniform(0, C.SCREEN_WIDTH), C.SCREEN_HEIGHT + C.ENEMY_SPAWN_MARGIN

    def _pick_enemy_class(self):
        return random.choice([KineticEnemy, PlasmaEnemy])

    def spawn(self):
        x, y = self._offscreen_position()
        cls = self._pick_enemy_class()
        enemy = cls(x, y, self.game.player, self.game)
        enemy.airspace = getattr(self.game, 'current_space', None)
        if random.random() < C.ENEMY_ELEMENTAL_SPAWN_CHANCE:
            enemy.element = random.choice(ALL_ELEMENTS)

    def update(self, dt):
        self.spawn_timer += dt
        if self.spawn_timer >= C.ENEMY_SPAWN_INTERVAL:
            self.spawn_timer = 0.0
            self.spawn()
