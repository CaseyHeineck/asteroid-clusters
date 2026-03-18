import pygame
import sys
from asteroid import *
from asteroidfield import *
from constants import *
from display import *
from shot import *
from player import *
from logger import log_state, log_event

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    clock = pygame.time.Clock()
    dt = 0
    updatable = pygame.sprite.Group()
    drawable = pygame.sprite.Group()
    asteroids = pygame.sprite.Group()
    shots = pygame.sprite.Group()
    HUD = Display(10, 10)
    Player.containers = (updatable, drawable)
    Asteroid.containers = (asteroids, updatable, drawable)
    AsteroidField.containers = (updatable,)
    Shot.containers = (shots, drawable, updatable)
    Display.containers = (HUD, drawable, updatable)    
    asteroid_field = AsteroidField()
    player = Player((SCREEN_WIDTH / 2), (SCREEN_HEIGHT / 2))
      
    while screen:
        log_state()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
        screen.fill("black")
        HUD.draw(screen)
        for object in drawable:
            object.draw(screen)
        pygame.display.flip()        
        time = clock.tick(60)
        dt = time / 1000
        updatable.update(dt)
        for asteroid in asteroids:
            if player.life is True:       
                if asteroid.collides_with(player):
                    player.respawn(HUD)
            for shot in shots:
                if shot.collides_with(asteroid):
                    shot.hits(asteroid, HUD)                    
        
    print(f"Starting Asteroids with pygame version: {pygame.version.ver}")
    print(f"Screen width: {SCREEN_WIDTH}")
    print(f"Screen height: {SCREEN_HEIGHT}")

if __name__ == "__main__":
    main()

