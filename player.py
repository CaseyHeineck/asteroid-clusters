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
        self.blink_timer = 0
        self.vulnerable = True
        self.speed = 0
        self.game_over = False
        
    def draw(self, screen):
        if self.vulnerable:
            pygame.draw.polygon(screen, RED, self.triangle(), LINE_WIDTH)
        else:            
            pygame.draw.polygon(screen, WHITE, self.triangle(), LINE_WIDTH)

    def rotate(self, dt):
        self.rotation += PLAYER_TURN_SPEED * dt
    
    def accelerate(self, dt):
        self.speed += PLAYER_ACCELERATION_RATE * dt

    def decelerate(self, dt):
        if self.speed < 0:
            self.speed += PLAYER_DECELERATION_RATE * dt
        if self.speed > 0:
            self.speed -= PLAYER_DECELERATION_RATE * dt
        if self.speed == 0:
            return

    def brake(self, dt):
        if self.speed < 0:
            self.speed += PLAYER_BRAKE_SPEED * dt
        if self.speed > 0:
            self.speed -= PLAYER_BRAKE_SPEED * dt
        if self.speed == 0:
            return

    def move(self, dt):
        unit_vector = pygame.Vector2(0, 1)
        rotated_vector = unit_vector.rotate(self.rotation)
        rotated_with_speed_vector = rotated_vector * PLAYER_SPEED * dt
        self.position += rotated_with_speed_vector

    def strafe(self, dt):
        unit_vector = pygame.Vector2(0, 1)
        rotated_vector = unit_vector.rotate((self.rotation + 90))
        rotated_with_speed_vector = rotated_vector * PLAYER_STRAFE_SPEED * dt
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
        HUD.update_player_lives(self.lives)
        self.life = False
        self.vulnerable = False
        if self.lives > 0:
            log_event("player_respawned")
            self.position.x = SCREEN_WIDTH / 2
            self.position.y = SCREEN_HEIGHT / 2
        else:
            log_event("game_over")
            HUD.update_score(GAME_OVER_SCORE)
            self.game_over = True
    
    def update(self, dt):
#       self.wrap_edges()
        keys = pygame.key.get_pressed()
        if keys[pygame.K_SPACE]:
            self.shoot()
        
        if keys[pygame.K_RSHIFT] or keys[pygame.K_LSHIFT]:
            if keys[pygame.K_RCTRL] or keys[pygame.K_LCTRL]:
                if keys[pygame.K_w]:
                    self.move(dt * 2)
                if keys[pygame.K_s]:
                    self.move(-dt * 2)
                if keys[pygame.K_a]:
                    self.strafe(-dt)
                if keys[pygame.K_d]:
                    self.strafe(dt)
            else:
                if keys[pygame.K_w]:
                    self.move(dt * 2)
                if keys[pygame.K_s]:
                    self.move(-dt * 2)
                if keys[pygame.K_a]:
                    self.rotate(-dt)
                if keys[pygame.K_d]:
                    self.rotate(dt)                    
        elif keys[pygame.K_RCTRL] or keys[pygame.K_LCTRL]:
            if keys[pygame.K_RSHIFT] or keys[pygame.K_LSHIFT]:
                if keys[pygame.K_a]:
                    self.strafe(-dt)
                if keys[pygame.K_d]:
                    self.strafe(dt)
                if keys[pygame.K_w]:
                    self.move(dt * 2)
                if keys[pygame.K_s]:
                    self.move(-dt * 2)
            else:
                if keys[pygame.K_a]:
                    self.strafe(-dt)
                if keys[pygame.K_d]:
                    self.strafe(dt)
                if keys[pygame.K_w]:
                    self.move(dt)
                if keys[pygame.K_s]:
                    self.move(-dt)                                                           
        else:
            if keys[pygame.K_a]:
                self.rotate(-dt)
            if keys[pygame.K_d]:
                self.rotate(dt)
            if keys[pygame.K_w]:
                self.move(dt)
            if keys[pygame.K_s]:
                self.move(-dt)
        
        self.shot_cooldown -= dt

        if self.life is not True:
            if self.blink_timer < PLAYER_BLINK_TIMER:
                self.blink_timer += dt
            else:
                if self.vulnerable:
                    self.vulnerable = False
                    self.blink_timer = 0
                else:
                    self.vulnerable = True
                    self.blink_timer = 0     
            if self.respawn_timer < PLAYER_RESPAWN_COOLDOWN_SECONDS:
                self.respawn_timer += dt
            else:
                self.life = True
                self.respawn_timer = 0 
        else:
            self.vulnerable = True     

    def triangle(self):    
        forward = pygame.Vector2(0, 1).rotate(self.rotation)
        right = pygame.Vector2(0, 1).rotate(self.rotation + 90) * self.radius / 1.5
        a = self.position + forward * self.radius
        b = self.position - forward * self.radius - right
        c = self.position - forward * self.radius + right
        return [a, b, c]    