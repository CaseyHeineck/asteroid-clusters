import os
import pygame
import sys
import constants as C
from asteroid import *
from asteroidfield import *
from collisionsystem import CollisionSystem
from endgamereport import *
from eventhandler import EventHandler
from display import *
from drone import *
from logger import *
from menus import *
from player import *
from projectile import *
from shield import *
from starfield import StarField
from visualeffect import *
from experiorb import ExpOrb
from essenceorb import EssenceOrb
from experience import ExperienceSystem
from essence import EssenceSystem
from mapsystem import MapSystem
from minimap import MiniMap

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
        self.exp_orbs = None
        self.asteroid_field = None
        self.drones = None
        self.shields = None
        self.visual_effects = None
        self.HUD = None
        self.projectiles = None
        self.player = None
        self.combat_stats = None
        self.experience = None
        self.essence = None
        self.map_system = None
        self.mini_map = MiniMap()
        self.shop_menu = None
        self.upgrade_counts = {}
        self.drone_select_menu = None
        self.drone_choice_menu = None

        self.starfield = StarField()
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
            elif self.current_state == C.DRONE_SELECT:
                self.update_drone_select(events)
            elif self.current_state == C.GAME_RUNNING:
                self.update_game_running()
            elif self.current_state == C.DRONE_CHOICE:
                self.update_drone_choice(events)
            elif self.current_state == C.SHOP:
                self.update_shop(events)
            elif self.current_state == C.PAUSED:
                self.update_paused(events)
            elif self.current_state == C.GAME_OVER:
                self.update_game_over(events)

            pygame.display.flip()

    def update_main_menu(self, events):
        self.screen.fill(C.BLACK)
        self.main_menu.update(events)
        self.main_menu.draw(self.screen)

    def update_drone_select(self, events):
        self.screen.fill(C.BLACK)
        self.drone_select_menu.update(events)
        self.drone_select_menu.draw(self.screen)

    def update_drone_choice(self, events):
        self.draw_game()
        self.draw_overlay(140)
        self.drone_choice_menu.update(events)
        self.drone_choice_menu.draw(self.screen)

    def enter_drone_choice(self):
        pending = self.experience.pending_drones
        if not pending:
            self.current_state = C.GAME_RUNNING
            return
        self.drone_choice_menu = create_drone_choice_menu(
            pending, self.experience.level,
            self.on_add_drone, self.on_banish_drone)
        self.current_state = C.DRONE_CHOICE

    def on_start_drone_selected(self, drone_class):
        self.experience.add_starting_drone(drone_class)
        self.current_state = C.GAME_RUNNING

    def on_add_drone(self, drone_class):
        self.experience.pending_drones.remove(drone_class)
        self.experience.added_drones.append(drone_class)
        self.player.add_drone(drone_class, self.asteroids)
        self.experience.resolve_choice()

    def on_banish_drone(self, drone_class):
        self.experience.pending_drones.remove(drone_class)
        self.experience.banished_drones.append(drone_class)
        self.experience.resolve_choice()

    def update_game_running(self):
        log_state()

        for obj in self.updatable:
            score = obj.update(self.dt)
            if score:
                self.HUD.update_score(score)

        self.HUD.update(self.dt)
        self.wrap_object(self.player)
        self.collision_system.handle()
        self.starfield.update(self.player.velocity, self.dt)
        self.map_system.update(self.dt)
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
        self.starfield.draw(self.screen)
        if self.drawable:
            for obj in self.drawable:
                obj.draw(self.screen)
        if self.map_system:
            self.map_system.draw(self.screen)
            self.mini_map.draw(self.screen, self.map_system)
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
        self.exp_orbs = pygame.sprite.Group()
        self.essence_orbs = pygame.sprite.Group()
        self.projectiles = pygame.sprite.Group()
        self.drones = pygame.sprite.Group()
        self.shields = pygame.sprite.Group()
        self.visual_effects = pygame.sprite.Group()

        Asteroid.containers = (self.asteroids, self.updatable, self.drawable)
        AsteroidField.containers = (self.updatable,)
        ExpOrb.containers = (self.exp_orbs, self.drawable, self.updatable)
        EssenceOrb.containers = (self.essence_orbs, self.drawable, self.updatable)
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
        self.experience = ExperienceSystem(self)
        self.essence = EssenceSystem(self)
        self.upgrade_counts = {}
        self.map_system = MapSystem(self)

    def on_new_game(self):
        self.create_game()
        self.game_over_menu = create_game_over_menu(self.on_new_game,
            self.on_main_menu, self.exit, score=0, combat_stats=None)
        self.drone_select_menu = create_drone_select_menu(self.on_start_drone_selected)
        self.current_state = C.DRONE_SELECT

    def on_resume(self):
        self.current_state = C.GAME_RUNNING

    def on_restart(self):
        self.create_game()
        self.game_over_menu = create_game_over_menu(self.on_new_game,
            self.on_main_menu, self.exit, score=0, combat_stats=None)
        self.drone_select_menu = create_drone_select_menu(self.on_start_drone_selected)
        self.current_state = C.DRONE_SELECT

    def on_main_menu(self):
        self.current_state = C.MAIN_MENU

    def enter_new_airspace(self, arrival_pos, prev_space, new_space):
        self._save_airspace_state(prev_space)
        for sprite in list(self.projectiles.sprites()):
            pygame.sprite.Sprite.kill(sprite)
        for sprite in list(self.visual_effects.sprites()):
            pygame.sprite.Sprite.kill(sprite)
        if new_space.active_state is not None:
            self._restore_airspace_state(new_space)
        else:
            self.asteroid_field = AsteroidField()
        self.player.position = pygame.Vector2(arrival_pos)
        self.player.velocity *= 0.75
        self.player.forward_speed *= 0.75
        self.player.perpendicular_speed *= 0.75

    def _save_airspace_state(self, space):
        space.active_state = {
            "asteroids":     list(self.asteroids.sprites()),
            "exp_orbs":      list(self.exp_orbs.sprites()),
            "essence_orbs":  list(self.essence_orbs.sprites()),
            "asteroid_field": self.asteroid_field,
        }
        for sprite in space.active_state["asteroids"]:
            sprite.remove(self.asteroids, self.updatable, self.drawable)
        for sprite in space.active_state["exp_orbs"]:
            sprite.remove(self.exp_orbs, self.updatable, self.drawable)
        for sprite in space.active_state["essence_orbs"]:
            sprite.remove(self.essence_orbs, self.updatable, self.drawable)
        self.asteroid_field.remove(self.updatable)

    def _restore_airspace_state(self, space):
        state = space.active_state
        for sprite in state["asteroids"]:
            sprite.add(self.asteroids, self.updatable, self.drawable)
        for sprite in state["exp_orbs"]:
            sprite.add(self.exp_orbs, self.updatable, self.drawable)
        for sprite in state["essence_orbs"]:
            sprite.add(self.essence_orbs, self.updatable, self.drawable)
        self.asteroid_field = state["asteroid_field"]
        self.asteroid_field.add(self.updatable)
        space.active_state = None

    def open_shop(self):
        self.shop_menu = create_shop_menu(
            self.player.drones, self.upgrade_counts,
            self.essence.amount, self.on_shop_buy, self.on_shop_leave)
        self.current_state = C.SHOP

    def on_shop_leave(self):
        self.current_state = C.GAME_RUNNING

    def on_shop_buy(self, drone_class, upgrade_type):
        self.apply_upgrade(drone_class, upgrade_type)
        self.shop_menu = create_shop_menu(
            self.player.drones, self.upgrade_counts,
            self.essence.amount, self.on_shop_buy, self.on_shop_leave)

    def apply_upgrade(self, drone_class, upgrade_type):
        from drone import LaserDrone, SentinelDrone
        cls_name = drone_class.__name__
        key = (cls_name, upgrade_type)
        count = self.upgrade_counts.get(key, 0)
        price = C.SHOP_UPGRADE_BASE_PRICE + count * C.SHOP_UPGRADE_PRICE_STEP
        if not self.essence.spend(price):
            return
        self.upgrade_counts[key] = count + 1
        for drone in self.player.drones:
            if not isinstance(drone, drone_class):
                continue
            if upgrade_type == "damage":
                if isinstance(drone, LaserDrone):
                    drone.damage = int(drone.damage * (1 + C.SHOP_DAMAGE_INCREASE))
                else:
                    drone.damage_multiplier *= (1 + C.SHOP_DAMAGE_INCREASE)
            elif upgrade_type == "fire_rate":
                drone.weapons_free_timer_max *= (1 - C.SHOP_FIRE_RATE_INCREASE)
            elif upgrade_type == "shield_health" and isinstance(drone, SentinelDrone):
                drone.shield_max_health += C.SHOP_SHIELD_HEALTH_INCREASE
                if drone.player_shield:
                    drone.player_shield.max_health += C.SHOP_SHIELD_HEALTH_INCREASE
            elif upgrade_type == "repair_rate" and isinstance(drone, SentinelDrone):
                drone.shield_repair_timer_base *= (1 - C.SHOP_SHIELD_REPAIR_INCREASE)

    def update_shop(self, events):
        self.draw_game()
        self.draw_overlay(140)
        self.shop_menu.update(events)
        self.shop_menu.draw(self.screen)

    def on_game_over(self):
        score = self.HUD.score if hasattr(self.HUD, "score") else 0
        self.game_over_menu = create_game_over_menu(self.on_new_game, 
            self.on_main_menu, self.exit, score=score, combat_stats=self.combat_stats)
        self.current_state = C.GAME_OVER

    def exit(self):
        pygame.quit()
        sys.exit()