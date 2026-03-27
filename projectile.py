import pygame
from circleshape import CircleShape
from constants import *
from explosion import Explosion
from logger import log_event

class Projectile(CircleShape):    
    def __init__(self, x, y, radius=PROJECTILE_RADIUS, color=PROJECTILE_COLOR, damage=PROJECTILE_DAMAGE):
        super().__init__(x, y, radius)
        self.color = color        
        self.damage = damage
        self.velocity = pygame.Vector2(0, 0)

    def on_hit(self, asteroid, HUD):
        log_event("asteroid_hit")                   
        asteroid.split(self.damage, HUD)
        self.kill()

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, self.position, self.radius)

    def update(self, dt):
        self.position += self.velocity * dt

class Kinetic(Projectile):
    def __init__(self, x, y):
        super().__init__(x, y, KINETIC_PROJECTILE_RADIUS, KINETIC_PROJECTILE_COLOR, KINETIC_PROJECTILE_DAMAGE)

class Plasma(Projectile):
    def __init__(self, x, y):
        super().__init__(x, y, PLASMA_PROJECTILE_RADIUS, PLASMA_PROJECTILE_COLOR, PLASMA_PROJECTILE_DAMAGE)

class Rocket(Projectile):
    def __init__(self, x, y, asteroids):
        super().__init__(x, y, ROCKET_PROJECTILE_RADIUS, ROCKET_PROJECTILE_COLOR, ROCKET_PROJECTILE_DAMAGE)
        self.asteroids = asteroids

    def on_hit(self, asteroid, HUD):
        log_event("asteroid_hit")
        impact_position = self.position.copy()
        asteroid.split(self.damage, HUD)
        Explosion(
            impact_position.x,
            impact_position.y,
            radius=ROCKET_EXPLOSION_RADIUS,
            color=ROCKET_EXPLOSION_COLOR,
            duration=ROCKET_EXPLOSION_DURATION,
            max_alpha=ROCKET_EXPLOSION_MAX_ALPHA
        )

        for other_asteroid in self.asteroids:
            distance = impact_position.distance_to(other_asteroid.position)
            if distance <= ROCKET_EXPLOSION_RADIUS:
                other_asteroid.split(ROCKET_PROJECTILE_SPLASH_DAMAGE, HUD)

        self.kill()

    def draw(self, screen):
        forward = self.velocity.normalize() if self.velocity.length_squared() > 0 else pygame.Vector2(0, -1)
        angle = pygame.Vector2(0, -1).angle_to(forward)

        surface = pygame.Surface((12, 18), pygame.SRCALPHA)

        # rocket body
        pygame.draw.rect(surface, self.color, (4, 4, 4, 10))
        # rocket nose
        pygame.draw.polygon(surface, RED, [(6, 0), (3, 4), (9, 4)])

        rotated = pygame.transform.rotate(surface, angle)
        rect = rotated.get_rect(center=(self.position.x, self.position.y))
        screen.blit(rotated, rect)
