import sys
from circleshape import *
from constants import *
from shot import *
from logger import log_event

class Player(CircleShape):
    def __init__(self, x, y):
        super().__init__(x, y, PLAYER_RADIUS)
        self.rotation = 0
        self.shot_cooldown = 0
        self.lives = 3
        self.life = True
        self.respawn_timer = 0
        
    def draw(self, screen):
        pygame.draw.polygon(screen, "white", self.triangle(), LINE_WIDTH)

    def rotate(self, dt):
        self.rotation += PLAYER_TURN_SPEED * dt

    def move(self, dt):
        unit_vector = pygame.Vector2(0, 1)
        rotated_vector = unit_vector.rotate(self.rotation)
        rotated_with_speed_vector = rotated_vector * PLAYER_SPEED * dt
        self.position += rotated_with_speed_vector

    def shoot(self):
        if self.shot_cooldown > 0:
            return
        else:
            shot = Shot(self.position.x, self.position.y, SHOT_RADIUS)
            shot.velocity = pygame.Vector2(0, 1).rotate(self.rotation) * PLAYER_SHOOT_SPEED
            self.shot_cooldown = PLAYER_SHOOT_COOLDOWN_SECONDS

    def respawn(self, HUD):
        log_event("player_hit")
        HUD.update_score(LIFE_LOSS_SCORE * self.lives)
        self.lives -= 1
        self.life = False
        if self.lives > 0:
            log_event("player_respawned")
            self.position.x = SCREEN_WIDTH / 2
            self.position.y = SCREEN_HEIGHT / 2
        else:
            log_event("game_over")
            HUD.update_score(GAME_OVER_SCORE)
            print(f"Score: {int(HUD.score)}")    
            print("Game over!")
            sys.exit()
    
    def update(self, dt):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_a]:
            self.rotate(-dt)
        if keys[pygame.K_d]:
            self.rotate(dt)
        if keys[pygame.K_w]:
            self.move(dt)
        if keys[pygame.K_s]:
            self.move(-dt)
        if keys[pygame.K_SPACE]:
            self.shoot()
        
        self.shot_cooldown -= dt

        if self.life is not True:
            if self.respawn_timer < PLAYER_RESPAWN_COOLDOWN_SECONDS:
                self.respawn_timer += dt
            else:
                self.life = True
                self.respawn_timer = 0

    def triangle(self):
        forward = pygame.Vector2(0, 1).rotate(self.rotation)
        right = pygame.Vector2(0, 1).rotate(self.rotation + 90) * self.radius / 1.5
        a = self.position + forward * self.radius
        b = self.position - forward * self.radius - right
        c = self.position - forward * self.radius + right
        return [a, b, c]    