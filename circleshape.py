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

    def draw(self, screen):
        pass

    def update(self, dt):
        pass

    def collides_with(self, other):
        distance = self.position.distance_to(other.position)
        return distance <= (self.radius + other.radius)