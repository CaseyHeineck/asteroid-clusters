import pygame
from core import constants as C
from core.circleshape import CircleShape
from core.element import get_damage_multiplier, get_element_primary_color
from systems.gameplayeffect import OverkillSTE, PlasmaBurnSTE, RocketHitAOE
from ui.visualeffect import LaserBeamVE, RocketExhaustVE


def _elemental_damage(base_damage, attacker_element, target):
    target_element = getattr(target, "element", None)
    mult = get_damage_multiplier(attacker_element, target_element)
    return max(1, int(base_damage * mult))

class Projectile(CircleShape):
    def __init__(self, x, y, radius=C.PROJECTILE_RADIUS, color=C.PROJECTILE_COLOR,
        damage=C.PROJECTILE_DAMAGE, weight=C.PROJECTILE_WEIGHT, bounciness=C.PROJECTILE_BOUNCINESS,
        drag=C.PROJECTILE_DRAG, rotation=0, angular_velocity=0):
        super().__init__(x, y, radius, weight=weight, bounciness=bounciness,
            drag=drag, rotation=rotation, angular_velocity=angular_velocity)
        self.color = color
        self.damage = damage
        self.element = None
        self.stat_source = None
        self.combat_stats = None
        self.extra_abilities = set()
        self.asteroids = None

    def on_hit(self, asteroid):
        effective_damage = _elemental_damage(self.damage, self.element, asteroid)
        health_before = asteroid.health
        score = asteroid.damaged(effective_damage)
        self.combat_stats.record_damage_event(source=self.stat_source,
            health_before=health_before, attempted_damage=effective_damage)
        self.kill()
        return score

    def pre_hit_extras(self, asteroid, skip_abilities=None):
        if skip_abilities is None:
            skip_abilities = set()
        if "overkill" in self.extra_abilities and "overkill" not in skip_abilities:
            if self.damage >= (asteroid.health + asteroid.full_health):
                asteroid.add_gameplay_effect(OverkillSTE(
                    child_size_reduction=1, child_count_reduction=1))

    def post_hit_extras(self, asteroid, skip_abilities=None):
        if skip_abilities is None:
            skip_abilities = set()
        if "impact" in self.extra_abilities and "impact" not in skip_abilities:
            normal = self.get_collision_normal(asteroid)
            asteroid.velocity += normal * (self.velocity.length() * C.KINETIC_PROJECTILE_COLLISION_IMPACT_SCALE)
            if asteroid.velocity.length() > C.ASTEROID_MAX_SPEED:
                asteroid.velocity.scale_to_length(C.ASTEROID_MAX_SPEED)
        if "burn" in self.extra_abilities and "burn" not in skip_abilities and asteroid.alive():
            burn = PlasmaBurnSTE()
            burn.stat_source = self.stat_source
            burn.combat_stats = self.combat_stats
            asteroid.add_gameplay_effect(burn)
        if "explosion" in self.extra_abilities and "explosion" not in skip_abilities and self.asteroids is not None:
            aoe = RocketHitAOE(impact_position=asteroid.position, targets=self.asteroids,
                radius=C.ROCKET_HIT_RADIUS, damage=C.ROCKET_HIT_DAMAGE)
            aoe.stat_source = self.stat_source
            aoe.combat_stats = self.combat_stats
            aoe.apply(ignored_targets=[asteroid])

    def draw(self, screen):
        draw_color = get_element_primary_color(self.element) if self.element else self.color
        pygame.draw.circle(screen, draw_color, self.position, self.radius)

    def update(self, dt):
        self.physics_move(dt)

class Kinetic(Projectile):
    def __init__(self, x, y):
        super().__init__(x, y, C.KINETIC_PROJECTILE_RADIUS, C.KINETIC_PROJECTILE_COLOR,
            C.KINETIC_PROJECTILE_DAMAGE, weight=C.KINETIC_PROJECTILE_WEIGHT,
            bounciness=C.KINETIC_PROJECTILE_BOUNCINESS, drag=C.KINETIC_PROJECTILE_DRAG)
        self.impact_scale = C.KINETIC_PROJECTILE_COLLISION_IMPACT_SCALE

    def on_hit(self, asteroid):
        effective_damage = _elemental_damage(self.damage, self.element, asteroid)
        health_before = asteroid.health
        self.pre_hit_extras(asteroid)
        score = asteroid.damaged(effective_damage)
        self.combat_stats.record_damage_event(source=self.stat_source,
            health_before=health_before, attempted_damage=effective_damage)
        normal = self.get_collision_normal(asteroid)
        asteroid.velocity += normal * (self.velocity.length() * C.KINETIC_PROJECTILE_COLLISION_IMPACT_SCALE)
        if asteroid.velocity.length() > C.ASTEROID_MAX_SPEED:
            asteroid.velocity.scale_to_length(C.ASTEROID_MAX_SPEED)
        self.post_hit_extras(asteroid, skip_abilities={"impact"})
        self.kill()
        return score

class LaserBeam(Projectile):
    def __init__(self, x, y, target, damage=C.LASER_DRONE_DAMAGE,
            stat_source=None, combat_stats=None, extra_abilities=None, asteroids=None,
            element=None):
        super().__init__(x, y, radius=0, color=C.LASER_BEAM_COLOR, damage=damage,
            weight=0, bounciness=0, drag=0)
        self.target = target
        self.stat_source = stat_source
        self.combat_stats = combat_stats
        self.element = element
        if extra_abilities:
            self.extra_abilities = set(extra_abilities)
        if asteroids is not None:
            self.asteroids = asteroids
        self.score = self.fire()

    def fire(self):
        if not self.target or not self.target.alive():
            self.kill()
            return 0
        start_position = pygame.Vector2(self.position)
        end_position = self.target.position.copy()
        beam_color = get_element_primary_color(self.element) if self.element else C.LASER_BEAM_COLOR
        LaserBeamVE(start_position, end_position, color=beam_color,
            width=C.LASER_BEAM_WIDTH, duration=C.LASER_BEAM_DURATION)
        effective_damage = _elemental_damage(self.damage, self.element, self.target)
        target_health = self.target.health
        full_health = self.target.full_health
        overkill = effective_damage >= (target_health + full_health)
        if overkill:
            self.target.add_gameplay_effect(OverkillSTE(
                child_size_reduction=1, child_count_reduction=1))
        self.pre_hit_extras(self.target, skip_abilities={"overkill"})
        score = self.target.damaged(effective_damage)
        if self.combat_stats:
            self.combat_stats.record_damage_event(
                source=self.stat_source, health_before=target_health,
                attempted_damage=effective_damage, overkill=overkill)
        self.post_hit_extras(self.target)
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
        effective_damage = _elemental_damage(self.damage, self.element, asteroid)
        health_before = asteroid.health
        self.pre_hit_extras(asteroid)
        score = asteroid.damaged(effective_damage)
        if self.combat_stats:
            self.combat_stats.record_damage_event(source=self.stat_source,
                health_before=health_before, attempted_damage=effective_damage)
        burn = PlasmaBurnSTE()
        burn.stat_source = self.stat_source
        burn.combat_stats = self.combat_stats
        asteroid.add_gameplay_effect(burn)
        self.post_hit_extras(asteroid, skip_abilities={"burn"})
        self.kill()
        return score

class Rocket(Projectile):
    def __init__(self, x, y, asteroids):
        super().__init__(x, y, C.ROCKET_PROJECTILE_RADIUS, C.ROCKET_PROJECTILE_COLOR,
            C.ROCKET_PROJECTILE_DAMAGE, weight=C.ROCKET_PROJECTILE_WEIGHT,
            bounciness=C.ROCKET_PROJECTILE_BOUNCINESS, drag=C.ROCKET_PROJECTILE_DRAG)
        self.asteroids = asteroids

    def on_hit(self, asteroid):
        effective_damage = _elemental_damage(self.damage, self.element, asteroid)
        total_score = 0
        health_before = asteroid.health
        self.pre_hit_extras(asteroid)
        score = asteroid.damaged(effective_damage)
        total_score += score or 0
        if self.combat_stats:
            self.combat_stats.record_damage_event(source=self.stat_source,
                health_before=health_before, attempted_damage=effective_damage)
        aoe = RocketHitAOE(impact_position=asteroid.position, targets=self.asteroids,
            radius=C.ROCKET_HIT_RADIUS, damage=C.ROCKET_HIT_DAMAGE)
        aoe.stat_source = self.stat_source
        aoe.combat_stats = self.combat_stats
        total_score += aoe.apply(ignored_targets=[asteroid])
        self.post_hit_extras(asteroid, skip_abilities={"explosion"})
        self.kill()
        return total_score
    
    def update(self, dt):
        self.physics_move(dt)
        if self.alive() and self.velocity.length_squared() > 0 and RocketExhaustVE.containers:
            backward = -self.velocity.normalize()
            exhaust_pos = self.position + backward * 10
            RocketExhaustVE(exhaust_pos.x, exhaust_pos.y)

    def draw(self, screen):
        forward = self.velocity.normalize() if self.velocity.length_squared() > 0 else pygame.Vector2(0, -1)
        angle = pygame.Vector2(0, -1).angle_to(forward)
        body_w, body_h = 6, 14
        nose_h = 7
        fin_w, fin_h = 5, 6
        surf = pygame.Surface((body_w + fin_w * 2 + 2, nose_h + body_h + fin_h + 2), pygame.SRCALPHA)
        cx = surf.get_width() // 2
        pygame.draw.polygon(surf, C.SILVER, [(cx, 0), (cx - body_w // 2, nose_h), (cx + body_w // 2, nose_h)])
        body_rect = pygame.Rect(cx - body_w // 2, nose_h, body_w, body_h)
        pygame.draw.rect(surf, C.GRAY, body_rect)
        pygame.draw.rect(surf, C.SILVER, body_rect, 1)
        tail_y = nose_h + body_h
        pygame.draw.polygon(surf, C.LIGHT_GRAY, [
            (cx - body_w // 2, tail_y),
            (cx - body_w // 2 - fin_w, tail_y + fin_h),
            (cx - body_w // 2, tail_y + fin_h)])
        pygame.draw.polygon(surf, C.LIGHT_GRAY, [
            (cx + body_w // 2, tail_y),
            (cx + body_w // 2 + fin_w, tail_y + fin_h),
            (cx + body_w // 2, tail_y + fin_h)])
        rotated = pygame.transform.rotate(surf, -angle)
        screen.blit(rotated, rotated.get_rect(center=(int(self.position.x), int(self.position.y))))