import pygame
import sys
import constants as C

class EventHandler:
    def __init__(self, game):
        self.game = game

    def handle(self, events):
        for event in events:
            if event.type == pygame.QUIT:
                self.game.exit()

            if event.type == pygame.KEYDOWN:
                self.handle_keydown(event)

    def handle_keydown(self, event):
        if event.key == pygame.K_ESCAPE:
            if self.game.current_state == C.GAME_RUNNING:
                self.game.current_state = C.PAUSED
            elif self.game.current_state == C.PAUSED:
                self.game.current_state = C.GAME_RUNNING