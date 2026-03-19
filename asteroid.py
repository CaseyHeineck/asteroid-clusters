import random
from circleshape import *
from constants import *
from logger import log_event

class Asteroid(CircleShape):
    def __init__(self, x, y, radius):
        super().__init__(x, y, radius)

    def draw(self, screen):
        pygame.draw.circle(screen, "white", self.position, self.radius, LINE_WIDTH)

    def update(self, dt):
        self.position += self.velocity * dt

    def split(self):
        self.kill()
        if self.radius <= ASTEROID_MIN_RADIUS:
            log_event("asteroid_destroyed")
            return
        else:
            log_event("asteroid_split")
            angle1 = random.uniform(1, 180)
            angle2 = random.uniform(181, 360)
            first = self.velocity.rotate(angle1)
            second = self.velocity.rotate(angle2)
            new_radius = self.radius - ASTEROID_MIN_RADIUS
            asteroid1 = Asteroid(self.position.x, self.position.y, new_radius)
            asteroid1.velocity = first * self.split_factor(angle1) * ASTEROID_SPLIT_ACCELERATION
            asteroid2 = Asteroid(self.position.x, self.position.y, new_radius)
            asteroid2.velocity = second * self.split_factor(angle2) * ASTEROID_SPLIT_ACCELERATION
    
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