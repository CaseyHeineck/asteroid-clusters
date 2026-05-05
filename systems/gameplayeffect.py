import pygame
from core import constants as C
from ui.visualeffect import RocketHitExplosionVE

class GameplayEffect:
    def __init__(self, duration=0):
        self.duration = duration
        self.expired = False

    def on_apply(self):
        pass

    def on_expire(self):
        pass

    def update(self, dt):
        if self.duration > 0:
            self.duration = max(0, self.duration - dt)
            if self.duration == 0:
                self.expired = True
                self.on_expire()
        return 0

class SingleTargetEffect(GameplayEffect):
    stackable = False

    def __init__(self, duration=0):
        super().__init__(duration)
        self.target = None

    def apply_to(self, target):
        self.target = target
        self.on_apply()

    def can_merge_with(self, other):
        return type(self) is type(other)

    def merge(self, other):
        self.duration = max(self.duration, other.duration)

class AreaOfEffect(GameplayEffect):
    def __init__(self, impact_position, targets, radius, duration=0):
        super().__init__(duration)
        self.impact_position = pygame.Vector2(impact_position)
        self.targets = targets
        self.radius = radius

    def get_targets_in_radius(self, ignored_targets=None):
        if ignored_targets is None:
            ignored_targets = []
        valid_targets = []
        for target in self.targets:
            if target in ignored_targets:
                continue
            if not target.alive():
                continue
            distance = self.impact_position.distance_to(target.position)
            if distance <= self.radius:
                valid_targets.append(target)
        return valid_targets

    def apply(self, ignored_targets=None):
        self.on_apply()
        return 0
    
class OverkillSTE(SingleTargetEffect):
    def __init__(self, overkill_tier=1, duration=C.OVERKILL_DURATION):
        super().__init__(duration)
        self.overkill_tier = overkill_tier

    def apply_to(self, target):
        self.target = target
        self.on_apply()
        self.expired = True

    def on_apply(self):
        if hasattr(self.target, "child_size_reduction"):
            self.target.child_size_reduction = max(
                self.target.child_size_reduction,
                self.overkill_tier)
        if hasattr(self.target, "overkill_triggered"):
            self.target.overkill_triggered = True

class BurnSTE(SingleTargetEffect):
    stackable = True
    tick_rate_override = None
    spread_chance_override = None

    def __init__(self, damage_per_tick=C.PLASMA_BURN_DAMAGE,
            tick_rate=None, duration=C.PLASMA_BURN_DURATION,
            spread_chance=None):
        super().__init__(duration)
        self.damage_per_tick = damage_per_tick
        if tick_rate is None:
            tick_rate = (BurnSTE.tick_rate_override
                         if BurnSTE.tick_rate_override is not None
                         else C.PLASMA_BURN_TICK_RATE)
        self.tick_rate = tick_rate
        self.tick_timer = tick_rate
        if spread_chance is None:
            spread_chance = (BurnSTE.spread_chance_override
                             if BurnSTE.spread_chance_override is not None
                             else C.PLASMA_BURN_SPREAD_CHANCE)
        self.spread_chance = spread_chance
        self.stat_source = None
        self.combat_stats = None

    def merge(self, other):
        self.duration = max(self.duration, other.duration)
        self.damage_per_tick = max(self.damage_per_tick, other.damage_per_tick)
        self.tick_rate = min(self.tick_rate, other.tick_rate)
        self.tick_timer = min(self.tick_timer, other.tick_timer)
        self.spread_chance = max(self.spread_chance, other.spread_chance)

    def update(self, dt):
        total_score = super().update(dt)
        if self.expired or not self.target or not self.target.alive():
            return total_score
        self.tick_timer -= dt
        while self.tick_timer <= 0:
            if hasattr(self.target, "damaged"):
                if hasattr(self.target, "pulse_outline"):
                    self.target.pulse_outline(C.PLASMA_PROJECTILE_COLOR,
                        C.PLASMA_BURN_FLASH_DURATION)
                health_before = self.target.health
                result = self.target.damaged(self.damage_per_tick)
                score = result[0] if isinstance(result, tuple) else result
                if self.combat_stats:
                    self.combat_stats.record_damage_event(source=self.stat_source,
                        health_before=health_before, attempted_damage=self.damage_per_tick)
                if score:
                    total_score += score
                    self.expired = True
                    break
            self.tick_timer += self.tick_rate
        return total_score
    
class ContagionSTE(SingleTargetEffect):
    stackable = True

    def __init__(self, damage_per_tick=C.CONTAGION_DAMAGE, tick_rate=C.CONTAGION_TICK_RATE,
            duration=C.CONTAGION_DURATION, spread_radius=C.CONTAGION_SPREAD_RADIUS,
            nearby_targets=None):
        super().__init__(duration)
        self.damage_per_tick = damage_per_tick
        self.tick_rate = tick_rate
        self.tick_timer = tick_rate
        self.spread_radius = spread_radius
        self.nearby_targets = nearby_targets or []
        self.stat_source = None
        self.combat_stats = None
        self._spread_applied = False

    def merge(self, other):
        self.duration = max(self.duration, other.duration)
        self.damage_per_tick = max(self.damage_per_tick, other.damage_per_tick)
        self.tick_rate = min(self.tick_rate, other.tick_rate)

    def _apply_spread(self):
        if self._spread_applied:
            return
        self._spread_applied = True
        if not self.target:
            return
        death_pos = self.target.position
        for candidate in self.nearby_targets:
            if candidate is self.target:
                continue
            if not candidate.alive():
                continue
            if death_pos.distance_to(candidate.position) > self.spread_radius:
                continue
            new_contagion = ContagionSTE(
                damage_per_tick=self.damage_per_tick,
                tick_rate=self.tick_rate,
                duration=C.CONTAGION_DURATION,
                spread_radius=self.spread_radius,
                nearby_targets=self.nearby_targets)
            new_contagion.stat_source = self.stat_source
            new_contagion.combat_stats = self.combat_stats
            candidate.add_gameplay_effect(new_contagion)

    def update(self, dt):
        total_score = super().update(dt)
        if self.expired:
            return total_score
        if not self.target or not self.target.alive():
            self._apply_spread()
            self.expired = True
            return total_score
        self.tick_timer -= dt
        while self.tick_timer <= 0:
            if hasattr(self.target, 'damaged'):
                result = self.target.damaged(self.damage_per_tick)
                score = result[0] if isinstance(result, tuple) else result
                if score:
                    total_score += score
                    self._apply_spread()
                    self.expired = True
                    return total_score
            self.tick_timer += self.tick_rate
        return total_score


class CorrodeSTE(SingleTargetEffect):
    def __init__(self, amplification=C.CORRODE_AMPLIFICATION, duration=C.CORRODE_DURATION):
        super().__init__(duration)
        self.amplification = amplification
        self.stat_source = None

    def on_apply(self):
        self.target.corrode_multiplier = 1.0 + self.amplification

    def on_expire(self):
        if self.target:
            self.target.corrode_multiplier = 1.0

    def merge(self, other):
        self.duration = max(self.duration, other.duration)
        new_amp = max(self.amplification, other.amplification)
        self.amplification = new_amp
        if self.target:
            self.target.corrode_multiplier = 1.0 + self.amplification


class MarkedSTE(SingleTargetEffect):
    is_mark_effect = True

    def __init__(self, amplification=C.MARK_AMPLIFICATION, duration=C.MARK_DURATION):
        super().__init__(duration)
        self.amplification = amplification
        self.stat_source = None

    def on_apply(self):
        self.target.mark_multiplier = self.amplification

    def on_expire(self):
        if self.target:
            self.target.mark_multiplier = 1.0

    def merge(self, other):
        self.duration = max(self.duration, other.duration)
        new_amp = max(self.amplification, other.amplification)
        self.amplification = new_amp
        if self.target:
            self.target.mark_multiplier = self.amplification


class SlowSTE(SingleTargetEffect):
    def __init__(self, slow_factor=C.SLOW_FACTOR, duration=C.SLOW_DURATION):
        super().__init__(duration)
        self.slow_factor = slow_factor
        self.stat_source = None
        self._original_speed = None

    def on_apply(self):
        if hasattr(self.target, 'speed'):
            self._original_speed = self.target.speed
            self.target.speed = self.target.speed * (1.0 - self.slow_factor)

    def on_expire(self):
        if self.target and self._original_speed is not None:
            self.target.speed = self._original_speed

    def merge(self, other):
        self.duration = max(self.duration, other.duration)


class RocketHitAOE(AreaOfEffect):
    def __init__(self, impact_position, targets, radius=C.ROCKET_HIT_RADIUS,
            damage=C.ROCKET_HIT_DAMAGE):
        super().__init__(impact_position, targets, radius, duration=0)
        self.damage = damage
        self.stat_source = None
        self.combat_stats = None

    def apply(self, ignored_targets=None):
        total_score = 0
        total_xp = 0
        self.on_apply()
        RocketHitExplosionVE(self.impact_position.x, self.impact_position.y,
            self.radius)
        valid_targets = self.get_targets_in_radius(ignored_targets)
        for target in valid_targets:
            if hasattr(target, "damaged"):
                health_before = target.health
                result = target.damaged(self.damage)
                if isinstance(result, tuple):
                    score, xp = result
                    total_xp += xp or 0
                else:
                    score = result
                if self.combat_stats:
                    self.combat_stats.record_damage_event(source=self.stat_source,
                        health_before=health_before, attempted_damage=self.damage)
                if score:
                    total_score += score
        self.expired = True
        return total_score, total_xp