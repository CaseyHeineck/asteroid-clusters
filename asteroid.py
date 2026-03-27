import pygame
import random
from circleshape import CircleShape
from constants import *
from explosion import Explosion
from logger import log_event

class Asteroid(CircleShape):
    def __init__(self, x, y, size):
        super().__init__(x, y, size * ASTEROID_MIN_RADIUS)
        self.size = size
        self.full_health = self.size
        self.health = self.full_health
        self.line_width = int(LINE_WIDTH + (self.size * 2))

    def draw(self, screen):
        pygame.draw.circle(screen, WHITE, self.position, self.radius, self.line_width)
        if self.health < self.full_health:
            self.draw_health_bar(screen)
    
    def draw_health_bar(self, screen):
        health_ratio = self.health / self.full_health
        width = self.radius
        background_rect = pygame.Rect(
            self.position.x - (width / 2), 
            self.position.y - (self.size * 2), 
            width, 
            HEALTH_BAR_HEIGHT + (self.size * 2))
        pygame.draw.rect(screen, BLACK, background_rect)        
        current_width = width * health_ratio
        health_rect = pygame.Rect(
            self.position.x - (width / 2), 
            self.position.y - (self.size * 2), 
            current_width, 
            HEALTH_BAR_HEIGHT + (self.size * 2))        
        pygame.draw.rect(screen, RED, health_rect)
        pygame.draw.rect(screen, WHITE, background_rect, LINE_WIDTH)

    def update(self, dt):
        self.position += self.velocity * dt

    def split(self, damage, HUD):
        self.health -= damage
        if self.health > 0:
            return
        else:
            HUD.update_score(BASE_SCORE * self.size)
            Explosion(self.position.x,
                    self.position.y,
                    radius=max(12, int(self.radius * 1.1)),
                    color=ORANGE,
                    duration=0.12 + (self.radius / 200),
                    max_alpha=150)
            self.kill()
            if self.size == 1:
                log_event("asteroid_destroyed")
                return
            else:
                log_event("asteroid_split")
                for i in range(self.size):
                    range_size = 360 / self.size
                    new_angle = random.uniform(1 + (range_size * i), range_size * (i + 1))    
                    velocity = self.velocity.rotate(new_angle)
                    asteroid = Asteroid(self.position.x, self.position.y, (self.size - 1))
                    asteroid.velocity = velocity * self.split_factor(new_angle) * ASTEROID_SPLIT_ACCELERATION
    
    def split_factor(self, angle):
        factor = 0
        if angle > 270 and angle <= 360:
            angle = angle - 270
            factor = angle / 90   
        elif angle > 180 and angle <= 270:
            angle = angle - 180
            factor = 1 - (angle / 90)
        elif angle > 90 and angle <= 180:
            angle = angle - 90
            factor = angle / 90
        elif angle > 0 and angle <= 90:
            factor = 1 - (angle / 90)
        else:
            raise ValueError
        if factor < MIN_ASTEROID_SPLIT_FACTOR:
            return MIN_ASTEROID_SPLIT_FACTOR
        else:
            return factor