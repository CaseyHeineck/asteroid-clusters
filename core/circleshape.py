import pygame

class CircleShape(pygame.sprite.Sprite):
    def __init__(self, x, y, radius, weight=1, bounciness=1.0,
            drag=0, rotation=0, angular_velocity=0):
        if hasattr(self, "containers"):
            super().__init__(self.containers)
        else:
            super().__init__()
        self.position = pygame.Vector2(x, y)
        self.velocity = pygame.Vector2(0, 0)
        self.radius = radius
        self.weight = weight
        self.bounciness = bounciness
        self.drag = drag
        self.rotation = rotation
        self.angular_velocity = angular_velocity
        self.gameplay_effects = []
        self.burn_stack_limit = None
        self.outline_pulse_color = None
        self.outline_pulse_timer = 0

    def get_forward_vector(self):
        return pygame.Vector2(0, -1).rotate(self.rotation)

    def apply_drag(self, dt):
        if self.drag <= 0:
            return
        if self.velocity.length_squared() == 0:
            return
        speed = self.velocity.length()
        drag_amount = self.drag * dt
        if speed <= drag_amount:
            self.velocity.update(0, 0)
        else:
            self.velocity.scale_to_length(speed - drag_amount)

    def apply_rotation(self, dt):
        if self.angular_velocity == 0:
            return
        self.rotation = (self.rotation + (self.angular_velocity * dt)) % 360

    def physics_move(self, dt):
        self.apply_drag(dt)
        self.apply_rotation(dt)
        self.position += self.velocity * dt

    def add_gameplay_effect(self, effect):
        if getattr(effect, 'stackable', False):
            if self.burn_stack_limit is not None:
                same_type = [e for e in self.gameplay_effects if type(e) is type(effect)]
                if len(same_type) >= self.burn_stack_limit:
                    same_type[0].merge(effect)
                    return
            effect.apply_to(self)
            self.gameplay_effects.append(effect)
            return
        for existing_effect in self.gameplay_effects:
            if existing_effect.can_merge_with(effect):
                existing_effect.merge(effect)
                return
        effect.apply_to(self)
        self.gameplay_effects.append(effect)

    def update_gameplay_effects(self, dt):
        total_score = 0
        expired_effects = []
        for effect in self.gameplay_effects:
            score = effect.update(dt)
            if score:
                total_score += score
            if effect.expired:
                expired_effects.append(effect)
        for effect in expired_effects:
            self.gameplay_effects.remove(effect)
        return total_score

    def pulse_outline(self, color, duration):
        self.outline_pulse_color = color
        self.outline_pulse_timer = duration

    def update_outline_pulse(self, dt):
        if self.outline_pulse_timer > 0:
            self.outline_pulse_timer = max(0, self.outline_pulse_timer - dt)
            if self.outline_pulse_timer == 0:
                self.outline_pulse_color = None

    def get_outline_color(self, default_color):
        if self.outline_pulse_color and self.outline_pulse_timer > 0:
            return self.outline_pulse_color
        return default_color

    def get_collision_normal(self, other):
        normal = other.position - self.position
        if normal.length_squared() == 0:
            return pygame.Vector2(1, 0)
        return normal.normalize()

    def separate_from(self, other):
        normal = self.get_collision_normal(other)
        distance = self.position.distance_to(other.position)
        overlap = (self.radius + other.radius) - distance
        if overlap <= 0:
            return
        self_weight = max(self.weight, 0.0001)
        other_weight = max(other.weight, 0.0001)
        total_weight = self_weight + other_weight
        self_shift = overlap * (other_weight / total_weight)
        other_shift = overlap * (self_weight / total_weight)
        self.position -= normal * self_shift
        other.position += normal * other_shift

    def resolve_impact(self, other, impact_scale=1.0):
        normal = self.get_collision_normal(other)
        relative_velocity = other.velocity - self.velocity
        closing_speed = relative_velocity.dot(normal)
        if closing_speed > 0:
            return
        bounce = min(self.bounciness, other.bounciness)
        self_weight = max(self.weight, 0.0001)
        other_weight = max(other.weight, 0.0001)
        inverse_weight_sum = (1 / self_weight) + (1 / other_weight)
        if inverse_weight_sum == 0:
            return
        impact_strength = -(1 + bounce) * closing_speed
        impact_strength /= inverse_weight_sum
        impact_strength *= impact_scale
        impact_vector = normal * impact_strength
        self.velocity -= impact_vector / self_weight
        other.velocity += impact_vector / other_weight

    def collide_and_impact(self, other, impact_scale=1.0):
        self.separate_from(other)
        self.resolve_impact(other, impact_scale=impact_scale)

    def draw(self, screen):
        pass

    def update(self, dt):
        pass

    def collides_with(self, other):
        distance = self.position.distance_to(other.position)
        return distance <= (self.radius + other.radius)