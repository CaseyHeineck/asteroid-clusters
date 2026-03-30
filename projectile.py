import pygame
import constants as C
from circleshape import CircleShape
from visualeffect import Explosion

class Projectile(CircleShape):    
    def __init__(self, x, y, radius=C.PROJECTILE_RADIUS, color=C.PROJECTILE_COLOR, damage=C.PROJECTILE_DAMAGE):
        super().__init__(x, y, radius)
        self.color = color        
        self.damage = damage
        self.velocity = pygame.Vector2(0, 0)

    def on_hit(self, asteroid):
        score = asteroid.damaged(self.damage)                   
        self.kill()
        return score

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, self.position, self.radius)

    def update(self, dt):
        self.position += self.velocity * dt

class Kinetic(Projectile):
    def __init__(self, x, y):
        super().__init__(x, y, C.KINETIC_PROJECTILE_RADIUS, C.KINETIC_PROJECTILE_COLOR, C.KINETIC_PROJECTILE_DAMAGE)

class Plasma(Projectile):
    def __init__(self, x, y):
        super().__init__(x, y, C.PLASMA_PROJECTILE_RADIUS, C.PLASMA_PROJECTILE_COLOR, C.PLASMA_PROJECTILE_DAMAGE)

class Rocket(Projectile):
    def __init__(self, x, y, asteroids):
        super().__init__(x, y, C.ROCKET_PROJECTILE_RADIUS, C.ROCKET_PROJECTILE_COLOR, C.ROCKET_PROJECTILE_DAMAGE)
        self.asteroids = asteroids

    def on_hit(self, asteroid):
        impact_position = self.position.copy()
        total_score = 0
        score = asteroid.damaged(self.damage)
        if score:
            total_score += score
        Explosion(impact_position.x, impact_position.y, radius=C.ROCKET_EXPLOSION_RADIUS, 
                color=C.ROCKET_EXPLOSION_COLOR, duration=C.ROCKET_EXPLOSION_DURATION, 
                max_alpha=C.ROCKET_EXPLOSION_MAX_ALPHA)
        for other_asteroid in self.asteroids:
            if other_asteroid == asteroid:
                continue
            distance = impact_position.distance_to(other_asteroid.position)
            if distance <= C.ROCKET_EXPLOSION_RADIUS:
                splash_score = other_asteroid.damaged(C.ROCKET_PROJECTILE_SPLASH_DAMAGE)
                if splash_score:
                    total_score += splash_score
        self.kill()
        return total_score

    def draw(self, screen):
        forward = self.velocity.normalize() if self.velocity.length_squared() > 0 else pygame.Vector2(0, -1)
        angle = pygame.Vector2(0, -1).angle_to(forward)
        surface = pygame.Surface((12, 18), pygame.SRCALPHA)
        # rocket body
        pygame.draw.rect(surface, self.color, (4, 4, 4, 10))
        # rocket nose
        pygame.draw.polygon(surface, C.RED, [(6, 0), (3, 4), (9, 4)])
        rotated = pygame.transform.rotate(surface, angle)
        rect = rotated.get_rect(center=(self.position.x, self.position.y))
        screen.blit(rotated, rect)
