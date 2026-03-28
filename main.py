import os
import pygame
import sys
import constants as C
from asteroid import *
from asteroidfield import *
from display import *
from drone import *
from player import *
from projectile import *
from logger import *
from menus import *
from visualeffect import *
from shield import *

def main():
    os.environ["SDL_VIDEO_FULLSCREEN_DISPLAY"] = "1"
    pygame.init()
    screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    C.SCREEN_WIDTH, C.SCREEN_HEIGHT = screen.get_size()
    
    clock = pygame.time.Clock()
    current_state = C.MAIN_MENU
    dt = 0

    updatable = None
    drawable = None
    asteroids = None
    asteroid_field = None
    drones = None
    shields = None
    visual_effects = None    
    HUD = None
    projectiles = None
    player = None

    def create_game():
        nonlocal updatable, drawable, asteroids, drones, shields, visual_effects, projectiles, HUD, player, asteroid_field

        updatable = pygame.sprite.Group()
        drawable = pygame.sprite.Group()
        asteroids = pygame.sprite.Group()
        projectiles = pygame.sprite.Group()
        drones = pygame.sprite.Group()
        shields = pygame.sprite.Group()
        visual_effects = pygame.sprite.Group()

        Asteroid.containers = (asteroids, updatable, drawable)
        AsteroidField.containers = (updatable,)
        Projectile.containers = (projectiles, drawable, updatable)
        Player.containers = (updatable, drawable)
        Drone.containers = (drones, drawable, updatable)
        Shield.containers = (shields, drawable, updatable)
        VisualEffect.containers = (visual_effects, drawable, updatable)  

        asteroid_field = AsteroidField()
        HUD = Display(10, 10)
        player = Player((C.SCREEN_WIDTH / 2), (C.SCREEN_HEIGHT / 2))
        player.add_drone(PlasmaDrone, asteroids, HUD)
        player.add_drone(KineticDrone, asteroids, HUD)
        player.add_drone(ExplosiveDrone, asteroids, HUD)
        player.add_drone(LaserDrone, asteroids, HUD)
        player.add_drone(SentinelDrone, asteroids, HUD)

    def on_new_game():
        nonlocal current_state, game_over_menu
        create_game()
        game_over_menu = create_game_over_menu(on_new_game, on_main_menu, on_exit, score=0)
        current_state = C.GAME_RUNNING

    def on_resume():
        nonlocal current_state
        current_state = C.GAME_RUNNING

    def on_restart():
        nonlocal current_state, game_over_menu
        create_game()
        game_over_menu = create_game_over_menu(on_new_game, on_main_menu, on_exit, score=0)
        current_state = C.GAME_RUNNING

    def on_main_menu():
        nonlocal current_state
        current_state = C.MAIN_MENU

    def on_exit():
        pygame.quit()
        sys.exit()

    def on_game_over():
        nonlocal current_state, game_over_menu
        score = 0
        if hasattr(HUD, "score"):
            score = HUD.score
        game_over_menu = create_game_over_menu(
            on_new_game,
            on_main_menu,
            on_exit,
            score = score
        )
        current_state = C.GAME_OVER

    def draw_game():
        screen.fill(C.BLACK)
        if drawable:
            for obj in drawable:
                obj.draw(screen)
        if HUD:
            HUD.draw(screen)

    def draw_overlay(alpha=140):
        overlay = pygame.Surface((C.SCREEN_WIDTH, C.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        screen.blit(overlay, (0, 0))
    
    def wrap_object(obj):
        if obj.position.x < 0:
            obj.position.x += C.SCREEN_WIDTH
        elif obj.position.x > C.SCREEN_WIDTH:
            obj.position.x -= C.SCREEN_WIDTH

        if obj.position.y < 0:
            obj.position.y += C.SCREEN_HEIGHT
        elif obj.position.y > C.SCREEN_HEIGHT:
            obj.position.y -= C.SCREEN_HEIGHT

    main_menu = create_main_menu(on_new_game, on_exit)
    pause_menu = create_pause_menu(on_resume, on_restart, on_main_menu, on_exit)
    game_over_menu = create_game_over_menu(on_new_game, on_main_menu, on_exit, score=0)

    while screen:
        time = clock.tick(60)
        dt = time / 1000
        events = pygame.event.get()

        for event in events:
            if event.type == pygame.QUIT:
                on_exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:    
                    if current_state == C.GAME_RUNNING:
                        current_state = C.PAUSED
                    elif current_state == C.PAUSED:
                        current_state = C.GAME_RUNNING

        if current_state == C.MAIN_MENU:
            screen.fill(C.BLACK)
            main_menu.update(events)
            main_menu.draw(screen)

        elif current_state == C.GAME_RUNNING:
            log_state()        
            updatable.update(dt)
            wrap_object(player)
            for asteroid in asteroids:
                wrap_object(asteroid)
                if player.life:       
                    if player.collides_with(asteroid):
                        player.respawn(HUD)
                        if player.game_over is True:
                            on_game_over()
                for projectile in projectiles:
                    if projectile.collides_with(asteroid):
                        projectile.on_hit(asteroid, HUD)
                for shield in shields:
                    if asteroid.collides_with(shield):
                        asteroid.split(shield.damage, HUD)
                        shield.health -= 1
                        
            draw_game()

        elif current_state == C.PAUSED:
            draw_game()
            draw_overlay(120)
            pause_menu.update(events)
            pause_menu.draw(screen)

        elif current_state == C.GAME_OVER:
            draw_game()
            draw_overlay(170)
            game_over_menu.update(events)
            game_over_menu.draw(screen)
      
        pygame.display.flip()          
               
    print(f"Starting Asteroids with pygame version: {pygame.version.ver}")
    print(f"Screen width: {C.SCREEN_WIDTH}")
    print(f"Screen height: {C.SCREEN_HEIGHT}")

if __name__ == "__main__":
    main()


