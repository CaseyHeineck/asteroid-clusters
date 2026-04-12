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
            elif self.game.current_state == C.SHOP:
                if self.game.shop_mode == "hub":
                    self.game.on_shop_leave()
                else:
                    self.game.on_mancer_back()

        if event.key == pygame.K_e:
            if self.game.current_state == C.GAME_RUNNING and self.game.map_system:
                self.game.map_system.try_interact()