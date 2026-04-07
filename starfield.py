import pygame
import random
import constants as C


class StarField:
    def __init__(self, star_count=180):
        self.offset_x = 0.0
        self.offset_y = 0.0
        self.stars = []
        self._generate(star_count)

    def _generate(self, count):
        for _ in range(count):
            x = random.randint(0, C.SCREEN_WIDTH)
            y = random.randint(0, C.SCREEN_HEIGHT)
            radius = random.choices([1, 2], weights=[3, 1])[0]
            brightness = random.randint(60, 220)
            self.stars.append((x, y, radius, brightness))

    def update(self, player_velocity, dt):
        parallax = 0.08
        self.offset_x = (self.offset_x - player_velocity.x * dt * parallax) % C.SCREEN_WIDTH
        self.offset_y = (self.offset_y - player_velocity.y * dt * parallax) % C.SCREEN_HEIGHT

    def draw(self, surface):
        for (x, y, radius, brightness) in self.stars:
            draw_x = int((x + self.offset_x) % C.SCREEN_WIDTH)
            draw_y = int((y + self.offset_y) % C.SCREEN_HEIGHT)
            color = (brightness, brightness, brightness)
            if radius == 1:
                surface.set_at((draw_x, draw_y), color)
            else:
                pygame.draw.circle(surface, color, (draw_x, draw_y), radius)
