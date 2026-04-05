import pygame
import constants as C
from circleshape import CircleShape
from gameplayeffect import OverkillSTE, PlasmaBurnSTE, RocketHitAOE 
from visualeffect import LaserBeamVE

class Projectile(CircleShape):
    def __init__(self, x, y, radius=C.PROJECTILE_RADIUS, color=C.PROJECTILE_COLOR,
        damage=C.PROJECTILE_DAMAGE, weight=C.PROJECTILE_WEIGHT, bounciness=C.PROJECTILE_BOUNCINESS,
        drag=C.PROJECTILE_DRAG, rotation=0, angular_velocity=0):
        super().__init__(x, y, radius, weight=weight, bounciness=bounciness,
            drag=drag, rotation=rotation, angular_velocity=angular_velocity)
        self.color = color
        self.damage = damage
        self.stat_source = None
        self.combat_stats = None

    def on_hit(self, asteroid):
        health_before = asteroid.health
        score = asteroid.damaged(self.damage)
        self.combat_stats.record_damage_event(source=self.stat_source,
            health_before=health_before, attempted_damage=self.damage)
        self.kill()
        return score

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, self.position, self.radius)

    def update(self, dt):
        self.physics_move(dt)

class Kinetic(Projectile):
    def __init__(self, x, y):
        super().__init__(x, y, C.KINETIC_PROJECTILE_RADIUS, C.KINETIC_PROJECTILE_COLOR,
            C.KINETIC_PROJECTILE_DAMAGE, weight=C.KINETIC_PROJECTILE_WEIGHT,
            bounciness=C.KINETIC_PROJECTILE_BOUNCINESS, drag=C.KINETIC_PROJECTILE_DRAG)
        self.impact_scale = C.KINETIC_PROJECTILE_COLLISION_IMPACT_SCALE

    def on_hit(self, asteroid):
        health_before = asteroid.health
        score = asteroid.damaged(self.damage)
        self.combat_stats.record_damage_event(source=self.stat_source,
            health_before=health_before, attempted_damage=self.damage)
        normal = self.get_collision_normal(asteroid)
        asteroid.velocity += normal * (self.velocity.length() * C.KINETIC_PROJECTILE_COLLISION_IMPACT_SCALE)
        if asteroid.velocity.length() > C.ASTEROID_MAX_SPEED:
            asteroid.velocity.scale_to_length(C.ASTEROID_MAX_SPEED)
        self.kill()
        return score

class LaserBeam(Projectile):
    def __init__(self, x, y, target, damage=C.LASER_DRONE_DAMAGE,
            stat_source=None, combat_stats=None):
        super().__init__(x, y, radius=0, color=C.LASER_BEAM_COLOR, damage=damage,
            weight=0, bounciness=0, drag=0)
        self.target = target
        self.stat_source = stat_source
        self.combat_stats = combat_stats
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
        overkill = self.damage >= (target_health + full_health)
        if overkill:
            self.target.add_gameplay_effect(OverkillSTE(
                child_size_reduction=1, child_count_reduction=1))
        score = self.target.damaged(self.damage)
        if self.combat_stats:
            self.combat_stats.record_damage_event(
                source=self.stat_source, health_before=target_health,
                attempted_damage=self.damage, overkill=overkill)
        self.kill()
        return score

    def update(self, dt):
        self.kill()
        return 0

    def draw(self, screen):
        pass

class Plasma(Projectile):
    def __init__(self, x, y):
        super().__init__(x, y, C.PLASMA_PROJECTILE_RADIUS, C.PLASMA_PROJECTILE_COLOR,
            C.PLASMA_PROJECTILE_DAMAGE, weight=C.PLASMA_PROJECTILE_WEIGHT,
            bounciness=C.PLASMA_PROJECTILE_BOUNCINESS, drag=C.PLASMA_PROJECTILE_DRAG)

    def on_hit(self, asteroid):
        health_before = asteroid.health
        score = asteroid.damaged(self.damage)
        if self.combat_stats:
            self.combat_stats.record_damage_event(source=self.stat_source,
                health_before=health_before, attempted_damage=self.damage)
        burn = PlasmaBurnSTE()
        burn.stat_source = self.stat_source
        burn.combat_stats = self.combat_stats
        asteroid.add_gameplay_effect(burn)
        self.kill()
        return score

class Rocket(Projectile):
    def __init__(self, x, y, asteroids):
        super().__init__(x, y, C.ROCKET_PROJECTILE_RADIUS, C.ROCKET_PROJECTILE_COLOR,
            C.ROCKET_PROJECTILE_DAMAGE, weight=C.ROCKET_PROJECTILE_WEIGHT,
            bounciness=C.ROCKET_PROJECTILE_BOUNCINESS, drag=C.ROCKET_PROJECTILE_DRAG)
        self.asteroids = asteroids

    def on_hit(self, asteroid):
        total_score = 0
        health_before = asteroid.health
        score = asteroid.damaged(self.damage)
        total_score += score or 0
        if self.combat_stats:
            self.combat_stats.record_damage_event(source=self.stat_source, 
                health_before=health_before, attempted_damage=self.damage)
        aoe = RocketHitAOE(impact_position=asteroid.position, targets=self.asteroids, 
            radius=C.ROCKET_HIT_RADIUS, damage=C.ROCKET_HIT_DAMAGE)
        aoe.stat_source = self.stat_source
        aoe.combat_stats = self.combat_stats
        total_score += aoe.apply(ignored_targets=[asteroid])
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