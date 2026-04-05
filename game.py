import os
import pygame
import sys
import constants as C
from asteroid import *
from asteroidfield import *
from combatstats import *
from display import *
from drone import *
from logger import *
from menus import *
from player import *
from projectile import *
from shield import *
from visualeffect import *

from eventhandler import EventHandler
from collisionsystem import CollisionSystem

class Game:
    def __init__(self):
        os.environ["SDL_VIDEO_FULLSCREEN_DISPLAY"] = "1"
        pygame.init()
        self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        C.SCREEN_WIDTH, C.SCREEN_HEIGHT = self.screen.get_size()

        self.clock = pygame.time.Clock()
        self.current_state = C.MAIN_MENU
        self.dt = 0

        self.updatable = None
        self.drawable = None
        self.asteroids = None
        self.asteroid_field = None
        self.drones = None
        self.shields = None
        self.visual_effects = None
        self.HUD = None
        self.projectiles = None
        self.player = None
        self.combat_stats = None

        self.event_handler = EventHandler(self)
        self.collision_system = CollisionSystem(self)

        self.main_menu = create_main_menu(self.on_new_game, self.exit)
        self.pause_menu = create_pause_menu(self.on_resume, self.on_restart, 
            self.on_main_menu, self.exit)
        self.game_over_menu = create_game_over_menu(self.on_new_game, 
            self.on_main_menu, self.exit, score=0, combat_stats=None)

    def run(self):
        while self.screen:
            self.dt = self.clock.tick(60) / 1000
            events = pygame.event.get()
            self.event_handler.handle(events)

            if self.current_state == C.MAIN_MENU:
                self.update_main_menu(events)
            elif self.current_state == C.GAME_RUNNING:
                self.update_game_running()
            elif self.current_state == C.PAUSED:
                self.update_paused(events)
            elif self.current_state == C.GAME_OVER:
                self.update_game_over(events)

            pygame.display.flip()

    def update_main_menu(self, events):
        self.screen.fill(C.BLACK)
        self.main_menu.update(events)
        self.main_menu.draw(self.screen)

    def update_game_running(self):
        log_state()

        for obj in self.updatable:
            score = obj.update(self.dt)
            if score:
                self.HUD.update_score(score)

        self.wrap_object(self.player)
        self.collision_system.handle()
        self.draw_game()

    def update_paused(self, events):
        self.draw_game()
        self.draw_overlay(120)
        self.pause_menu.update(events)
        self.pause_menu.draw(self.screen)

    def update_game_over(self, events):
        self.draw_game()
        self.draw_overlay(170)
        self.game_over_menu.update(events)
        self.game_over_menu.draw(self.screen)

    def draw_game(self):
        self.screen.fill(C.BLACK)
        if self.drawable:
            for obj in self.drawable:
                obj.draw(self.screen)
        if self.HUD:
            self.HUD.draw(self.screen)

    def draw_overlay(self, alpha=140):
        overlay = pygame.Surface((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        self.screen.blit(overlay, (0, 0))

    def wrap_object(self, obj):
        if obj.position.x < 0:
            obj.position.x += C.SCREEN_WIDTH
        elif obj.position.x > C.SCREEN_WIDTH:
            obj.position.x -= C.SCREEN_WIDTH

        if obj.position.y < 0:
            obj.position.y += C.SCREEN_HEIGHT
        elif obj.position.y > C.SCREEN_HEIGHT:
            obj.position.y -= C.SCREEN_HEIGHT

    def create_game(self):
        self.updatable = pygame.sprite.Group()
        self.drawable = pygame.sprite.Group()
        self.asteroids = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.drones = pygame.sprite.Group()
        self.shields = pygame.sprite.Group()
        self.visual_effects = pygame.sprite.Group()

        Asteroid.containers = (self.asteroids, self.updatable, self.drawable)
        AsteroidField.containers = (self.updatable,)
        Projectile.containers = (self.projectiles, self.drawable, self.updatable)
        Player.containers = (self.updatable, self.drawable)
        Drone.containers = (self.drones, self.drawable, self.updatable)
        Shield.containers = (self.shields, self.drawable, self.updatable)
        VisualEffect.containers = (self.visual_effects, self.drawable, self.updatable)

        self.asteroid_field = AsteroidField()
        self.HUD = Display(10, 10)
        self.combat_stats = CombatStats()
        self.player = Player((C.SCREEN_WIDTH / 2), (C.SCREEN_HEIGHT / 2))
        self.player.game = self

        self.player.add_drone(PlasmaDrone, self.asteroids)
        self.player.add_drone(KineticDrone, self.asteroids)
        self.player.add_drone(ExplosiveDrone, self.asteroids)
        self.player.add_drone(LaserDrone, self.asteroids)
        self.player.add_drone(SentinelDrone, self.asteroids)

    def on_new_game(self):
        self.create_game()
        self.game_over_menu = create_game_over_menu(self.on_new_game, 
            self.on_main_menu, self.exit, score=0, combat_stats=None)
        self.current_state = C.GAME_RUNNING

    def on_resume(self):
        self.current_state = C.GAME_RUNNING

    def on_restart(self):
        self.create_game()
        self.game_over_menu = create_game_over_menu(self.on_new_game, 
            self.on_main_menu, self.exit, score=0, combat_stats=None)
        self.current_state = C.GAME_RUNNING

    def on_main_menu(self):
        self.current_state = C.MAIN_MENU

    def on_game_over(self):
        score = self.HUD.score if hasattr(self.HUD, "score") else 0
        self.game_over_menu = create_game_over_menu(self.on_new_game, 
            self.on_main_menu, self.exit, score=score, combat_stats=self.combat_stats)
        self.current_state = C.GAME_OVER

    def exit(self):
        pygame.quit()
        sys.exit()