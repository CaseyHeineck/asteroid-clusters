import constants as C

class GameplayEffect:
    def __init__(self, duration=0):
        self.duration = duration
        self.expired = False
        self.target = None

    def apply_to(self, target):
        self.target = target
        self.on_apply()

    def on_apply(self):
        pass

    def can_merge_with(self, other):
        return type(self) is type(other)

    def merge(self, other):
        self.duration = max(self.duration, other.duration)

    def on_expire(self):
        pass

    def update(self, dt):
        if self.duration > 0:
            self.duration -= dt
            if self.duration <= 0:
                self.expired = True
                self.on_expire()
        return 0
    
class OverkillGPE(GameplayEffect):
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
    
class PlasmaBurnGPE(GameplayEffect):
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
                score = self.target.damaged(self.damage_per_tick)
                if score:
                    total_score += score
                    self.expired = True
                    break
            self.tick_timer += self.tick_rate
        return total_score