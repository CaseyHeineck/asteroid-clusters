import pygame
import constants as C
from visualeffect import RocketHitExplosionVE

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
    def __init__(self, child_size_reduction=C.OVERKILL_CHILD_SIZE_REDUCTION,
            child_count_reduction=C.OVERKILL_CHILD_COUNT_REDUCTION,
            duration=C.OVERKILL_DURATION):
        super().__init__(duration)
        self.child_size_reduction = child_size_reduction
        self.child_count_reduction = child_count_reduction

    def apply_to(self, target):
        self.target = target
        self.on_apply()
        self.expired = True

    def on_apply(self):
        if hasattr(self.target, "child_size_reduction"):
            self.target.child_size_reduction = max(
                self.target.child_size_reduction,
                self.child_size_reduction)
        if hasattr(self.target, "child_count_reduction"):
            self.target.child_count_reduction = max(
                self.target.child_count_reduction,
                self.child_count_reduction)
        if hasattr(self.target, "overkill_triggered"):
            self.target.overkill_triggered = True

class PlasmaBurnSTE(SingleTargetEffect):
    def __init__(self, damage_per_tick=C.PLASMA_BURN_DAMAGE,
            tick_rate=C.PLASMA_BURN_TICK_RATE, duration=C.PLASMA_BURN_DURATION):
        super().__init__(duration)
        self.damage_per_tick = damage_per_tick
        self.tick_rate = tick_rate
        self.tick_timer = tick_rate

    def merge(self, other):
        self.duration = max(self.duration, other.duration)
        self.damage_per_tick = max(self.damage_per_tick, other.damage_per_tick)
        self.tick_rate = min(self.tick_rate, other.tick_rate)
        self.tick_timer = min(self.tick_timer, other.tick_timer)

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
                score = self.target.damaged(self.damage_per_tick)
                if score:
                    total_score += score
                    self.expired = True
                    break
            self.tick_timer += self.tick_rate
        return total_score
    
class RocketHitAOE(AreaOfEffect):
    def __init__(self, impact_position, targets, radius=C.ROCKET_HIT_RADIUS,
            damage=C.ROCKET_HIT_DAMAGE):
        super().__init__(impact_position, targets, radius, duration=0)
        self.damage = damage

    def apply(self, ignored_targets=None):
        total_score = 0
        self.on_apply()
        RocketHitExplosionVE(self.impact_position.x, self.impact_position.y,
            self.radius)
        valid_targets = self.get_targets_in_radius(ignored_targets)
        for target in valid_targets:
            if hasattr(target, "damaged"):
                score = target.damaged(self.damage)
                if score:
                    total_score += score
        self.expired = True
        return total_score