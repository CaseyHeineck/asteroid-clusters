import pygame
import constants as C
from circleshape import CircleShape
from gameplayeffect import PlasmaBurnGPE, OverkillGPE
from visualeffect import ExplosionVE, LaserBeamVE

class Projectile(CircleShape):
    def __init__(self, x, y, radius=C.PROJECTILE_RADIUS, color=C.PROJECTILE_COLOR,
        damage=C.PROJECTILE_DAMAGE, weight=C.PROJECTILE_WEIGHT, bounciness=C.PROJECTILE_BOUNCINESS,
        drag=C.PROJECTILE_DRAG, rotation=0, angular_velocity=0):
        super().__init__(x, y, radius, weight=weight, bounciness=bounciness,
                drag=drag, rotation=rotation, angular_velocity=angular_velocity)
        self.color = color
        self.damage = damage

    def on_hit(self, asteroid):
        score = asteroid.damaged(self.damage)
        self.kill()
        return score

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, self.position, self.radius)

    def update(self, dt):
        self.physics_move(dt)

class Kinetic(Projectile):
    def __init__(self, x, y):
        super().__init__(x, y, C.KINETIC_PROJECTILE_RADIUS,
            C.KINETIC_PROJECTILE_COLOR, C.KINETIC_PROJECTILE_DAMAGE,
            weight=C.KINETIC_PROJECTILE_WEIGHT,
            bounciness=C.KINETIC_PROJECTILE_BOUNCINESS,
            drag=C.KINETIC_PROJECTILE_DRAG)
        
class LaserBeam(Projectile):
    def __init__(self, x, y, target, damage=C.LASER_DRONE_DAMAGE):
        super().__init__(x, y, radius=0, color=C.LASER_BEAM_COLOR, damage=damage,
            weight=0, bounciness=0, drag=0)
        self.target = target
        self.score = self.fire()

    def fire(self):
        if not self.target or not self.target.alive():
            self.kill()
            return 0
        start_position = pygame.Vector2(self.position)
        end_position = self.target.position.copy()
        LaserBeamVE(start_position, end_position, color=C.LASER_BEAM_COLOR,
            width=C.LASER_BEAM_WIDTH, duration=C.LASER_BEAM_DURATION)
        target_health = self.target.health
        full_health = self.target.full_health
        if self.damage >= (target_health + full_health):
            if hasattr(self.target, "add_gameplay_effect"):
                self.target.add_gameplay_effect(OverkillGPE(
                    child_size_reduction=1, child_count_reduction=1))
        score = 0
        if hasattr(self.target, "damaged"):
            score = self.target.damaged(self.damage)
        self.kill()
        return score

    def update(self, dt):
        self.kill()
        return 0

    def draw(self, screen):
        pass

class Plasma(Projectile):
    def __init__(self, x, y):
        super().__init__(x, y, C.PLASMA_PROJECTILE_RADIUS,
            C.PLASMA_PROJECTILE_COLOR, C.PLASMA_PROJECTILE_DAMAGE,
            weight=C.PLASMA_PROJECTILE_WEIGHT,
            bounciness=C.PLASMA_PROJECTILE_BOUNCINESS,
            drag=C.PLASMA_PROJECTILE_DRAG)
    
    def on_hit(self, target):
        score = 0
        if hasattr(target, "damaged"):
            score += target.damaged(self.damage)
        if target.alive() and hasattr(target, "add_gameplay_effect"):
            target.add_gameplay_effect(PlasmaBurnGPE())
        self.kill()
        return score    

class Rocket(Projectile):
    def __init__(self, x, y, asteroids):
        super().__init__(x, y, C.ROCKET_PROJECTILE_RADIUS,
            C.ROCKET_PROJECTILE_COLOR, C.ROCKET_PROJECTILE_DAMAGE,
            weight=C.ROCKET_PROJECTILE_WEIGHT,
            bounciness=C.ROCKET_PROJECTILE_BOUNCINESS,
            drag=C.ROCKET_PROJECTILE_DRAG)
        self.asteroids = asteroids

    def on_hit(self, asteroid):
        impact_position = self.position.copy()
        total_score = 0
        score = asteroid.damaged(self.damage)
        if score:
            total_score += score
        ExplosionVE(impact_position.x, impact_position.y,
            radius=C.ROCKET_EXPLOSION_RADIUS, color=C.ROCKET_EXPLOSION_COLOR,
            duration=C.ROCKET_EXPLOSION_DURATION, max_alpha=C.ROCKET_EXPLOSION_MAX_ALPHA)
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
        pygame.draw.rect(surface, self.color, (4, 4, 4, 10))
        pygame.draw.polygon(surface, C.RED, [(6, 0), (3, 4), (9, 4)])
        rotated = pygame.transform.rotate(surface, angle)
        rect = rotated.get_rect(center=(self.position.x, self.position.y))
        screen.blit(rotated, rect)