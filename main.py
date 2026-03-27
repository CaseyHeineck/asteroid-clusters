import pygame
import sys
from asteroid import *
from asteroidfield import *
from constants import *
from display import *
from drone import *
from explosion import *
from player import *
from projectile import *
from logger import *
from menus import *

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()

    current_state = MAIN_MENU
    dt = 0

    updatable = None
    drawable = None
    asteroids = None
    asteroid_field = None
    drones = None
    explosions = None    
    HUD = None
    projectiles = None
    player = None

    def create_game():
        nonlocal updatable, drawable, asteroids, drones, explosions, projectiles, HUD, player, asteroid_field

        updatable = pygame.sprite.Group()
        drawable = pygame.sprite.Group()
        asteroids = pygame.sprite.Group()
        projectiles = pygame.sprite.Group()
        drones = pygame.sprite.Group()
        explosions = pygame.sprite.Group()
        HUD = Display(10, 10)

        Asteroid.containers = (asteroids, updatable, drawable)
        AsteroidField.containers = (updatable,)
        Projectile.containers = (projectiles, drawable, updatable)
        Player.containers = (updatable, drawable)
        Display.containers = (HUD, drawable, updatable)
        Drone.containers = (drones, drawable, updatable)
        Explosion.containers = (explosions, drawable, updatable)  

        asteroid_field = AsteroidField()
        player = Player((SCREEN_WIDTH / 2), (SCREEN_HEIGHT / 2))
        player.add_drone(PlasmaDrone, asteroids)
        player.add_drone(KineticDrone, asteroids)
        player.add_drone(ExplosiveDrone, asteroids)

    def on_new_game():
        nonlocal current_state, game_over_menu
        create_game()
        game_over_menu = create_game_over_menu(on_new_game, on_main_menu, on_exit, score=0)
        current_state = GAME_RUNNING

    def on_resume():
        nonlocal current_state
        current_state = GAME_RUNNING

    def on_restart():
        nonlocal current_state, game_over_menu
        create_game()
        game_over_menu = create_game_over_menu(on_new_game, on_main_menu, on_exit, score=0)
        current_state = GAME_RUNNING

    def on_main_menu():
        nonlocal current_state
        current_state = MAIN_MENU

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
        current_state = GAME_OVER

    def draw_game():
        screen.fill(BLACK)
        if drawable:
            for obj in drawable:
                obj.draw(screen)
        if HUD:
            HUD.draw(screen)

    def draw_overlay(alpha=140):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, alpha))
        screen.blit(overlay, (0, 0))
    
    def wrap_object(obj):
        if obj.position.x < 0:
            obj.position.x += SCREEN_WIDTH
        elif obj.position.x > SCREEN_WIDTH:
            obj.position.x -= SCREEN_WIDTH

        if obj.position.y < 0:
            obj.position.y += SCREEN_HEIGHT
        elif obj.position.y > SCREEN_HEIGHT:
            obj.position.y -= SCREEN_HEIGHT

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
                    if current_state == GAME_RUNNING:
                        current_state = PAUSED
                    elif current_state == PAUSED:
                        current_state = GAME_RUNNING

        if current_state == MAIN_MENU:
            screen.fill(BLACK)
            main_menu.update(events)
            main_menu.draw(screen)

        elif current_state == GAME_RUNNING:
            log_state()        
            updatable.update(dt)
            wrap_object(player)
            for asteroid in asteroids:
                wrap_object(asteroid)
                if player.life:       
                    if asteroid.collides_with(player):
                        player.respawn(HUD)
                        if player.game_over is True:
                            on_game_over()
                for projectile in projectiles:
                    if projectile.collides_with(asteroid):
                        projectile.on_hit(asteroid, HUD)
                        
            draw_game()

        elif current_state == PAUSED:
            draw_game()
            draw_overlay(120)
            pause_menu.update(events)
            pause_menu.draw(screen)

        elif current_state == GAME_OVER:
            draw_game()
            draw_overlay(170)
            game_over_menu.update(events)
            game_over_menu.draw(screen)
      
        pygame.display.flip()          
               
    print(f"Starting Asteroids with pygame version: {pygame.version.ver}")
    print(f"Screen width: {SCREEN_WIDTH}")
    print(f"Screen height: {SCREEN_HEIGHT}")

if __name__ == "__main__":
    main()


