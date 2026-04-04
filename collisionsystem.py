import constants as C

class CollisionSystem:
    def __init__(self, game):
        self.game = game

    def handle(self):
        self.handle_asteroid_collisions()

    def handle_asteroid_collisions(self):
        for asteroid in self.game.asteroids:
            self.game.wrap_object(asteroid)
            shield_blocked = False

            for shield in self.game.shields:
                if asteroid.collides_with(shield):
                    shield.block_asteroid(asteroid,
                        impact_scale=C.SHIELD_COLLISION_IMPACT_SCALE)
                    score = asteroid.damaged(shield.damage)
                    if score:
                        self.game.HUD.update_score(score)
                    shield.damaged(asteroid.damage)
                    shield_blocked = True
                    break

            if not shield_blocked and self.game.player.can_be_damaged:
                if self.game.player.collides_with(asteroid):
                    self.game.player.apply_collision_to_asteroid(asteroid,
                        impact_scale=C.PLAYER_COLLISION_IMPACT_SCALE)
                    score_delta, lives = self.game.player.damaged()
                    if score_delta:
                        self.game.HUD.update_score(score_delta)
                    self.game.HUD.update_player_lives(lives)
                    if self.game.player.game_over:
                        self.game.on_game_over()

            for projectile in self.game.projectiles:
                if projectile.collides_with(asteroid):
                    score = projectile.on_hit(asteroid)
                    if score:
                        self.game.HUD.update_score(score)