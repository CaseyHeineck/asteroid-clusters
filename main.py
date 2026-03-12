import pygame
import sys
from screen import *
from constants import *
from player import *
from asteroid import *
from asteroidfield import *
from shot import *
from logger import log_state, log_event

def main():
    pygame.init()
    clock = pygame.time.Clock()
    dt = 0
    updatable = pygame.sprite.Group()
    drawable = pygame.sprite.Group()
    asteroids = pygame.sprite.Group()
    shots = pygame.sprite.Group()
    Player.containers = (updatable, drawable)
    Asteroid.containers = (asteroids, updatable, drawable)
    AsteroidField.containers = (updatable,)
    Shot.containers = (shots, drawable, updatable)    
    asteroid_field = AsteroidField()
    player = Player((SCREEN_WIDTH / 2), (SCREEN_HEIGHT / 2))
    
    while screen:
        log_state()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
        screen.fill("black")
        show_score(10, 10)
        for object in drawable:
            object.draw(screen)
        pygame.display.flip()        
        time = clock.tick(60)
        dt = time / 1000
        updatable.update(dt)
        for asteroid in asteroids:
            if asteroid.collides_with(player):
                log_event("player_hit")
                if player.lives > 0:
                    player.lives -= 1
                    player.position.x = SCREEN_WIDTH / 2
                    player.position.y = SCREEN_HEIGHT / 2
                else:
                    log_event("game_over")    
                    print("Game over!")
                    sys.exit()
            for shot in shots:
                if shot.collides_with(asteroid):                    
                    log_event("asteroid_shot")
                    update_score(50)
                    asteroid.split()
                    shot.kill()
                    
        
    print(f"Starting Asteroids with pygame version: {pygame.version.ver}")
    print(f"Screen width: {SCREEN_WIDTH}")
    print(f"Screen height: {SCREEN_HEIGHT}")

if __name__ == "__main__":
    main()
