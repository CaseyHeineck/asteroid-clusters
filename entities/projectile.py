import pygame
from core import constants as C
from core.circleshape import CircleShape
from core.element import get_damage_multiplier, get_element_primary_color
from systems.gameplayeffect import ContagionSTE, CorrodeSTE, MarkedSTE, OverkillSTE, BurnSTE, RocketHitAOE, SlowSTE
from ui.visualeffect import LaserBeamVE, RocketExhaustVE


def _elemental_damage(base_damage, attacker_element, target):
    target_element = getattr(target, "element", None)
    mult = get_damage_multiplier(attacker_element, target_element)
    return max(1, int(base_damage * mult))

class Projectile(CircleShape):
    handles_own_kill = False

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
        self.enemies = None

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
            full_health = getattr(asteroid, 'full_health', 0)
            if full_health > 0 and self.damage >= (asteroid.health + full_health):
                tier = max(1, (self.damage - asteroid.health) // full_health)
                asteroid.add_gameplay_effect(OverkillSTE(overkill_tier=tier))

    def post_hit_extras(self, asteroid, skip_abilities=None):
        if skip_abilities is None:
            skip_abilities = set()
        if "impact" in self.extra_abilities and "impact" not in skip_abilities:
            self.weight = (Kinetic.weight_override if Kinetic.weight_override is not None
                           else C.KINETIC_PROJECTILE_WEIGHT_BASE)
            self.separate_from(asteroid)
            self.resolve_impact(asteroid)
            if asteroid.velocity.length() > C.ASTEROID_MAX_SPEED:
                asteroid.velocity.scale_to_length(C.ASTEROID_MAX_SPEED)
        if "burn" in self.extra_abilities and "burn" not in skip_abilities and asteroid.alive():
            burn = BurnSTE()
            burn.stat_source = self.stat_source
            burn.combat_stats = self.combat_stats
            asteroid.add_gameplay_effect(burn)
        if "contagion" in self.extra_abilities and "contagion" not in skip_abilities and asteroid.alive():
            nearby = list(self.asteroids) if self.asteroids else []
            if self.enemies:
                nearby.extend(self.enemies)
            contagion = ContagionSTE(nearby_targets=nearby)
            contagion.stat_source = self.stat_source
            asteroid.add_gameplay_effect(contagion)
        if "corrode" in self.extra_abilities and "corrode" not in skip_abilities and asteroid.alive():
            corrode = CorrodeSTE()
            corrode.stat_source = self.stat_source
            asteroid.add_gameplay_effect(corrode)
        if "mark" in self.extra_abilities and "mark" not in skip_abilities and asteroid.alive():
            mark = MarkedSTE()
            mark.stat_source = self.stat_source
            asteroid.add_gameplay_effect(mark)
        if "slow" in self.extra_abilities and "slow" not in skip_abilities and asteroid.alive():
            slow = SlowSTE()
            slow.stat_source = self.stat_source
            asteroid.add_gameplay_effect(slow)
        if "explosion" in self.extra_abilities and "explosion" not in skip_abilities and self.asteroids is not None:
            aoe = RocketHitAOE(impact_position=asteroid.position, targets=self.asteroids,
                radius=C.ROCKET_HIT_RADIUS, damage=C.ROCKET_HIT_DAMAGE)
            aoe.stat_source = self.stat_source
            aoe.combat_stats = self.combat_stats
            aoe.apply(ignored_targets=[asteroid])

    def draw(self, screen):
        if self.element:
            pygame.draw.circle(screen, self.color, self.position, self.radius)
            ring_color = get_element_primary_color(self.element)
            pygame.draw.circle(screen, ring_color, self.position, self.radius, max(1, self.radius // 3))
        elif self.stat_source == C.ENEMY:
            pygame.draw.circle(screen, self.color, self.position, self.radius)
        else:
            pygame.draw.circle(screen, C.PLAYER_BODY_COLOR, self.position, self.radius)

    def update(self, dt):
        self.physics_move(dt)

class Kinetic(Projectile):
    weight_override = None

    def __init__(self, x, y):
        w = (Kinetic.weight_override if Kinetic.weight_override is not None
             else C.KINETIC_PROJECTILE_WEIGHT_BASE)
        super().__init__(x, y, C.KINETIC_PROJECTILE_RADIUS, C.KINETIC_PROJECTILE_COLOR,
            C.KINETIC_PROJECTILE_DAMAGE, weight=w,
            bounciness=C.KINETIC_PROJECTILE_BOUNCINESS, drag=C.KINETIC_PROJECTILE_DRAG)

    def on_hit(self, asteroid):
        effective_damage = _elemental_damage(self.damage, self.element, asteroid)
        health_before = asteroid.health
        self.pre_hit_extras(asteroid)
        score = asteroid.damaged(effective_damage)
        self.combat_stats.record_damage_event(source=self.stat_source,
            health_before=health_before, attempted_damage=effective_damage)
        self.separate_from(asteroid)
        self.resolve_impact(asteroid)
        if asteroid.velocity.length() > C.ASTEROID_MAX_SPEED:
            asteroid.velocity.scale_to_length(C.ASTEROID_MAX_SPEED)
        self.post_hit_extras(asteroid, skip_abilities={"impact"})
        self.kill()
        return score

class LaserBeam(Projectile):
    def __init__(self, x, y, target, damage=C.LASER_BEAM_DAMAGE,
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
        self.xp = 0
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
        full_health = getattr(self.target, 'full_health', getattr(self.target, 'max_health', 0))
        overkill = full_health > 0 and effective_damage >= (target_health + full_health)
        if overkill:
            tier = max(1, (effective_damage - target_health) // full_health)
            self.target.add_gameplay_effect(OverkillSTE(overkill_tier=tier))
        self.pre_hit_extras(self.target, skip_abilities={"overkill"})
        result = self.target.damaged(effective_damage)
        score = result[0] if isinstance(result, tuple) else result
        self.xp = result[1] if isinstance(result, tuple) else 0
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
        burn = BurnSTE()
        burn.stat_source = self.stat_source
        burn.combat_stats = self.combat_stats
        asteroid.add_gameplay_effect(burn)
        self.post_hit_extras(asteroid, skip_abilities={"burn"})
        self.kill()
        return score

class Rocket(Projectile):
    def __init__(self, x, y, asteroids, enemies=None, player=None):
        super().__init__(x, y, C.ROCKET_PROJECTILE_RADIUS, C.ROCKET_PROJECTILE_COLOR,
            C.ROCKET_PROJECTILE_DAMAGE, weight=C.ROCKET_PROJECTILE_WEIGHT,
            bounciness=C.ROCKET_PROJECTILE_BOUNCINESS, drag=C.ROCKET_PROJECTILE_DRAG)
        self.asteroids = asteroids
        self.enemies = enemies
        self.player = player

    def on_hit(self, target):
        effective_damage = _elemental_damage(self.damage, self.element, target)
        total_score = 0
        total_xp = 0
        health_before = target.health
        self.pre_hit_extras(target)
        result = target.damaged(effective_damage)
        if isinstance(result, tuple):
            score, xp = result
            total_xp += xp or 0
        else:
            score = result
        total_score += score or 0
        if self.combat_stats:
            self.combat_stats.record_damage_event(source=self.stat_source,
                health_before=health_before, attempted_damage=effective_damage)
        all_aoe_targets = list(self.asteroids) if self.asteroids is not None else []
        if self.enemies is not None:
            all_aoe_targets.extend(self.enemies)
        aoe = RocketHitAOE(impact_position=target.position, targets=all_aoe_targets,
            radius=C.ROCKET_HIT_RADIUS, damage=C.ROCKET_HIT_DAMAGE)
        aoe.stat_source = self.stat_source
        aoe.combat_stats = self.combat_stats
        aoe_score, aoe_xp = aoe.apply(ignored_targets=[target])
        total_score += aoe_score
        total_xp += aoe_xp
        self.post_hit_extras(target, skip_abilities={"explosion"})
        self.kill()
        return total_score, total_xp
    
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
        if self.element:
            ring_color = get_element_primary_color(self.element)
            pygame.draw.circle(screen, ring_color, (int(self.position.x), int(self.position.y)),
                self.radius + 2, 2)

class NeedleSlug(Projectile):
    handles_own_kill = True

    def __init__(self, x, y):
        super().__init__(x, y, C.NEEDLE_SLUG_RADIUS, C.NEEDLE_SLUG_COLOR,
            C.NEEDLE_SLUG_DAMAGE, weight=0, bounciness=0, drag=0)
        self.pierce_count = C.NEEDLE_SLUG_MAX_PIERCES

    def on_hit(self, target):
        effective_damage = _elemental_damage(self.damage, self.element, target)
        health_before = target.health
        self.pre_hit_extras(target)
        result = target.damaged(effective_damage)
        if isinstance(result, tuple):
            score, xp = result
        else:
            score, xp = result, 0
        if self.combat_stats:
            self.combat_stats.record_damage_event(source=self.stat_source,
                health_before=health_before, attempted_damage=effective_damage)
        self.post_hit_extras(target)
        self.pierce_count -= 1
        if self.pierce_count <= 0:
            self.kill()
        return score, xp

class Cannonball(Projectile):
    def __init__(self, x, y):
        super().__init__(x, y, C.CANNONBALL_RADIUS, C.CANNONBALL_COLOR,
            C.CANNONBALL_DAMAGE, weight=C.CANNONBALL_WEIGHT,
            bounciness=0, drag=C.CANNONBALL_DRAG)

    def on_hit(self, asteroid):
        effective_damage = _elemental_damage(self.damage, self.element, asteroid)
        health_before = asteroid.health
        self.pre_hit_extras(asteroid)
        score = asteroid.damaged(effective_damage)
        if self.combat_stats:
            self.combat_stats.record_damage_event(source=self.stat_source,
                health_before=health_before, attempted_damage=effective_damage)
        self.separate_from(asteroid)
        self.resolve_impact(asteroid)
        if asteroid.velocity.length() > C.ASTEROID_MAX_SPEED:
            asteroid.velocity.scale_to_length(C.ASTEROID_MAX_SPEED)
        self.post_hit_extras(asteroid)
        self.kill()
        return score

class ContagionPlasma(Projectile):
    handles_own_kill = True

    def __init__(self, x, y):
        super().__init__(x, y, C.CONTAGION_PROJECTILE_RADIUS, C.CONTAGION_PROJECTILE_COLOR,
            C.CONTAGION_PROJECTILE_DAMAGE, weight=0, bounciness=0, drag=0)
        self.contagion_duration = C.CONTAGION_DURATION
        self.spread_radius = C.CONTAGION_SPREAD_RADIUS

    def on_hit(self, target):
        effective_damage = _elemental_damage(self.damage, self.element, target)
        health_before = target.health
        self.pre_hit_extras(target)
        result = target.damaged(effective_damage)
        if isinstance(result, tuple):
            score, xp = result
        else:
            score, xp = result, 0
        if self.combat_stats:
            self.combat_stats.record_damage_event(source=self.stat_source,
                health_before=health_before, attempted_damage=effective_damage)
        if target.alive():
            nearby = list(self.asteroids) if self.asteroids else []
            if self.enemies:
                nearby.extend(self.enemies)
            contagion = ContagionSTE(
                duration=self.contagion_duration,
                spread_radius=self.spread_radius,
                nearby_targets=nearby)
            contagion.stat_source = self.stat_source
            target.add_gameplay_effect(contagion)
        self.post_hit_extras(target, skip_abilities={"contagion"})
        self.kill()
        return score, xp


class CorrodePlasma(Projectile):
    handles_own_kill = True

    def __init__(self, x, y):
        super().__init__(x, y, C.CORRODE_PROJECTILE_RADIUS, C.CORRODE_PROJECTILE_COLOR,
            C.CORRODE_PROJECTILE_DAMAGE, weight=0, bounciness=0, drag=0)
        self.corrode_amplification = C.CORRODE_AMPLIFICATION
        self.corrode_duration = C.CORRODE_DURATION

    def on_hit(self, target):
        effective_damage = _elemental_damage(self.damage, self.element, target)
        health_before = target.health
        self.pre_hit_extras(target)
        result = target.damaged(effective_damage)
        if isinstance(result, tuple):
            score, xp = result
        else:
            score, xp = result, 0
        if self.combat_stats:
            self.combat_stats.record_damage_event(source=self.stat_source,
                health_before=health_before, attempted_damage=effective_damage)
        if target.alive():
            corrode = CorrodeSTE(
                amplification=self.corrode_amplification,
                duration=self.corrode_duration)
            corrode.stat_source = self.stat_source
            target.add_gameplay_effect(corrode)
        self.post_hit_extras(target, skip_abilities={"corrode"})
        self.kill()
        return score, xp


class MarkPlasma(Projectile):
    handles_own_kill = True

    def __init__(self, x, y):
        super().__init__(x, y, C.MARK_PROJECTILE_RADIUS, C.MARK_PROJECTILE_COLOR,
            C.MARK_PROJECTILE_DAMAGE, weight=0, bounciness=0, drag=0)
        self.mark_amplification = C.MARK_AMPLIFICATION
        self.mark_duration = C.MARK_DURATION

    def on_hit(self, target):
        effective_damage = _elemental_damage(self.damage, self.element, target)
        health_before = target.health
        self.pre_hit_extras(target)
        result = target.damaged(effective_damage)
        if isinstance(result, tuple):
            score, xp = result
        else:
            score, xp = result, 0
        if self.combat_stats:
            self.combat_stats.record_damage_event(source=self.stat_source,
                health_before=health_before, attempted_damage=effective_damage)
        if target.alive():
            mark = MarkedSTE(
                amplification=self.mark_amplification,
                duration=self.mark_duration)
            mark.stat_source = self.stat_source
            target.add_gameplay_effect(mark)
        self.post_hit_extras(target, skip_abilities={"mark"})
        self.kill()
        return score, xp


class SlowPlasma(Projectile):
    handles_own_kill = True

    def __init__(self, x, y):
        super().__init__(x, y, C.SLOW_PROJECTILE_RADIUS, C.SLOW_PROJECTILE_COLOR,
            C.SLOW_PROJECTILE_DAMAGE, weight=0, bounciness=0, drag=0)
        self.slow_factor = C.SLOW_FACTOR
        self.slow_duration = C.SLOW_DURATION

    def on_hit(self, target):
        effective_damage = _elemental_damage(self.damage, self.element, target)
        health_before = target.health
        self.pre_hit_extras(target)
        result = target.damaged(effective_damage)
        if isinstance(result, tuple):
            score, xp = result
        else:
            score, xp = result, 0
        if self.combat_stats:
            self.combat_stats.record_damage_event(source=self.stat_source,
                health_before=health_before, attempted_damage=effective_damage)
        if target.alive():
            slow = SlowSTE(
                slow_factor=self.slow_factor,
                duration=self.slow_duration)
            slow.stat_source = self.stat_source
            target.add_gameplay_effect(slow)
        self.post_hit_extras(target, skip_abilities={"slow"})
        self.kill()
        return score, xp


class ProximityMine(Projectile):
    handles_own_kill = True

    def __init__(self, x, y, asteroids, enemies=None):
        super().__init__(x, y, C.PROXIMITY_MINE_RADIUS, C.PROXIMITY_MINE_COLOR,
            0, weight=0, bounciness=0, drag=0)
        self.asteroids = asteroids
        self.enemies = enemies
        self.trigger_radius = C.PROXIMITY_MINE_TRIGGER_RADIUS
        self.explosion_radius = C.PROXIMITY_MINE_EXPLOSION_RADIUS
        self.explosion_damage = C.PROXIMITY_MINE_EXPLOSION_DAMAGE
        self._detonated = False

    def update(self, dt):
        pass

    def collides_with(self, other):
        if self._detonated:
            return False
        return self.position.distance_to(other.position) < self.trigger_radius + other.radius

    def _detonate(self):
        if self._detonated:
            return 0, 0
        self._detonated = True
        all_targets = list(self.asteroids) if self.asteroids else []
        if self.enemies:
            all_targets.extend(self.enemies)
        aoe = RocketHitAOE(self.position, all_targets,
            radius=self.explosion_radius, damage=self.explosion_damage)
        aoe.stat_source = self.stat_source
        aoe.combat_stats = self.combat_stats
        result = aoe.apply()
        self.kill()
        return result

    def on_hit(self, target):
        self.pre_hit_extras(target)
        self.post_hit_extras(target, skip_abilities={"explosion"})
        return self._detonate()


class Grenade(Projectile):
    handles_own_kill = True

    def __init__(self, x, y, asteroids, enemies=None):
        super().__init__(x, y, C.GRENADE_RADIUS, C.GRENADE_COLOR,
            C.GRENADE_DIRECT_DAMAGE, weight=0, bounciness=0, drag=0)
        self.asteroids = asteroids
        self.enemies = enemies
        self.fuse_timer = C.GRENADE_FUSE_TIMER
        self.explosion_radius = C.GRENADE_EXPLOSION_RADIUS
        self.explosion_damage = C.GRENADE_EXPLOSION_DAMAGE
        self._detonated = False

    def _detonate(self, center_pos, ignored_targets=None):
        if self._detonated:
            return 0, 0
        self._detonated = True
        all_targets = list(self.asteroids) if self.asteroids else []
        if self.enemies:
            all_targets.extend(self.enemies)
        aoe = RocketHitAOE(center_pos, all_targets,
            radius=self.explosion_radius, damage=self.explosion_damage)
        aoe.stat_source = self.stat_source
        aoe.combat_stats = self.combat_stats
        result = aoe.apply(ignored_targets=ignored_targets)
        self.kill()
        return result

    def update(self, dt):
        self.physics_move(dt)
        if self._detonated:
            return 0
        self.fuse_timer -= dt
        if self.fuse_timer <= 0:
            score, _xp = self._detonate(self.position)
            return score
        return 0

    def on_hit(self, target):
        total_score = 0
        total_xp = 0
        effective_damage = _elemental_damage(self.damage, self.element, target)
        health_before = target.health
        self.pre_hit_extras(target)
        result = target.damaged(effective_damage)
        if isinstance(result, tuple):
            score, xp = result
            total_xp += xp or 0
        else:
            score = result
        total_score += score or 0
        if self.combat_stats:
            self.combat_stats.record_damage_event(source=self.stat_source,
                health_before=health_before, attempted_damage=effective_damage)
        aoe_score, aoe_xp = self._detonate(target.position, ignored_targets=[target])
        total_score += aoe_score
        total_xp += aoe_xp
        self.post_hit_extras(target, skip_abilities={"explosion"})
        return total_score, total_xp


class HomingMissile(Projectile):
    handles_own_kill = True

    def __init__(self, x, y, asteroids, enemies=None, homing_target=None):
        super().__init__(x, y, C.HOMING_MISSILE_RADIUS, C.HOMING_MISSILE_COLOR,
            C.HOMING_MISSILE_DIRECT_DAMAGE, weight=0, bounciness=0, drag=0)
        self.asteroids = asteroids
        self.enemies = enemies
        self.homing_target = homing_target
        self.turn_rate = C.HOMING_MISSILE_TURN_RATE
        self.explosion_radius = C.HOMING_MISSILE_EXPLOSION_RADIUS
        self.explosion_damage = C.HOMING_MISSILE_EXPLOSION_DAMAGE

    def update(self, dt):
        if (self.homing_target and self.homing_target.alive()
                and self.velocity.length_squared() > 0):
            to_target = self.homing_target.position - self.position
            if to_target.length_squared() > 0:
                speed = self.velocity.length()
                angle = self.velocity.normalize().angle_to(to_target.normalize())
                max_turn = self.turn_rate * dt
                angle = max(-max_turn, min(max_turn, angle))
                self.velocity = self.velocity.rotate(angle)
                self.velocity.scale_to_length(speed)
        self.physics_move(dt)
        if self.alive() and self.velocity.length_squared() > 0 and RocketExhaustVE.containers:
            backward = -self.velocity.normalize()
            exhaust_pos = self.position + backward * 8
            RocketExhaustVE(exhaust_pos.x, exhaust_pos.y)

    def on_hit(self, target):
        total_score = 0
        total_xp = 0
        effective_damage = _elemental_damage(self.damage, self.element, target)
        health_before = target.health
        self.pre_hit_extras(target)
        result = target.damaged(effective_damage)
        if isinstance(result, tuple):
            score, xp = result
            total_xp += xp or 0
        else:
            score = result
        total_score += score or 0
        if self.combat_stats:
            self.combat_stats.record_damage_event(source=self.stat_source,
                health_before=health_before, attempted_damage=effective_damage)
        all_aoe_targets = list(self.asteroids) if self.asteroids else []
        if self.enemies:
            all_aoe_targets.extend(self.enemies)
        aoe = RocketHitAOE(target.position, all_aoe_targets,
            radius=self.explosion_radius, damage=self.explosion_damage)
        aoe.stat_source = self.stat_source
        aoe.combat_stats = self.combat_stats
        aoe_score, aoe_xp = aoe.apply(ignored_targets=[target])
        total_score += aoe_score
        total_xp += aoe_xp
        self.post_hit_extras(target, skip_abilities={"explosion"})
        self.kill()
        return total_score, total_xp


class FuseBomb(Projectile):
    handles_own_kill = True

    def __init__(self, x, y, asteroids, enemies=None):
        super().__init__(x, y, C.FUSE_BOMB_RADIUS, C.FUSE_BOMB_COLOR,
            0, weight=0, bounciness=0, drag=0)
        self.asteroids = asteroids
        self.enemies = enemies
        self.fuse_timer = C.FUSE_BOMB_FUSE_TIMER
        self.explosion_radius = C.FUSE_BOMB_EXPLOSION_RADIUS
        self.explosion_damage = C.FUSE_BOMB_EXPLOSION_DAMAGE
        self._detonated = False

    def update(self, dt):
        if self._detonated:
            return 0
        self.fuse_timer -= dt
        if self.fuse_timer <= 0:
            score, _xp = self._detonate()
            return score
        return 0

    def collides_with(self, other):
        return False

    def _detonate(self):
        if self._detonated:
            return 0, 0
        self._detonated = True
        all_targets = list(self.asteroids) if self.asteroids else []
        if self.enemies:
            all_targets.extend(self.enemies)
        aoe = RocketHitAOE(self.position, all_targets,
            radius=self.explosion_radius, damage=self.explosion_damage)
        aoe.stat_source = self.stat_source
        aoe.combat_stats = self.combat_stats
        result = aoe.apply()
        self.kill()
        return result

    def on_hit(self, target):
        return 0, 0


class Bouncer(Projectile):
    handles_own_kill = True

    def __init__(self, x, y):
        super().__init__(x, y, C.BOUNCER_RADIUS, C.BOUNCER_COLOR,
            C.BOUNCER_DAMAGE, weight=0, bounciness=0, drag=0)
        self.bounce_count = C.BOUNCER_MAX_BOUNCES

    def on_hit(self, target):
        effective_damage = _elemental_damage(self.damage, self.element, target)
        health_before = target.health
        self.pre_hit_extras(target)
        result = target.damaged(effective_damage)
        if isinstance(result, tuple):
            score, xp = result
        else:
            score, xp = result, 0
        if self.combat_stats:
            self.combat_stats.record_damage_event(source=self.stat_source,
                health_before=health_before, attempted_damage=effective_damage)
        self.post_hit_extras(target)
        direction = self.position - target.position
        if direction.length_squared() > 0:
            self.velocity = self.velocity.reflect(direction.normalize())
        self.bounce_count -= 1
        if self.bounce_count <= 0:
            self.kill()
        return score, xp