import pygame
from circleshape import *
from player import *

class Drone(CircleShape):
    def __init__(self, x, y):
        super().__init__(x, y, DRONE_RADIUS)
        self.rotation = 0
        self.shot_cooldown = 0
        self.target = None
        self.range = 200

#   this should end up in update as we want this and shoot to go automatically
#   probably want to add self rotation here so that rotation animation can be updated as targets acquired

    def acquire_target(self, asteroid):
        closest_so_far = float("inf")
        target_distance = self.position.distance_to(asteroid.position)
        if self.target is None:
            if target_distance <= self.range:
                if target_distance < closest_so_far:
                    closest_so_far = target_distance
                    self.target = asteroid
                else:
                    return
            else:
                return
        else:
            if target_distance <= self.range:
                if target_distance < closest_so_far:
                    closest_so_far = target_distance
                    self.target = asteroid
                else:
                    return
    # 
#   this needs to be updated to use the position of the target 
#   to be the desired rotation angle so the drone is facing that target and can then shoot
    # def rotate(self, dt):
    #     self.rotation += DRONE_TURN_SPEED * dt    

    def shoot(self):
        if self.shot_cooldown > 0:
            return
        else:
            shot = Shot(self.position.x, self.position.y, SHOT_RADIUS)
            shot.velocity = pygame.Vector2(0, 1).rotate(self.rotation) * DRONE_SHOT_SPEED
            self.shot_cooldown = DRONE_SHOOT_COOLDOWN_SECONDS

    def draw(self, screen):
        pygame.draw.circle(screen, WHITE, self.position, self.radius, LINE_WIDTH)

    def update(self, dt):
        # must override
        pass

    def collides_with(self, other):
        return False
