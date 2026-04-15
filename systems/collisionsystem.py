from core import constants as C

class CollisionSystem:
    def __init__(self, game):
        self.game = game

    def handle(self):
        self.handle_asteroid_collisions()
        self.handle_exp_orb_pickups()
        self.handle_essence_orb_pickups()
        self.handle_elemental_essence_orb_pickups()

    def handle_asteroid_collisions(self):
        for asteroid in self.game.asteroids:
            self.game.wrap_object(asteroid)
            shield_blocked = False

            for shield in self.game.shields:
                if asteroid.collides_with(shield):
                    shield.block_asteroid(asteroid,
                        impact_scale=C.SHIELD_COLLISION_IMPACT_SCALE)
                    health_before = asteroid.health
                    score = asteroid.damaged(shield.damage)
                    if score:
                        self.game.HUD.update_score(score)
                    self.game.combat_stats.record_damage_event(
                        source=shield.stat_source, health_before=health_before,
                        attempted_damage=shield.damage)
                    shield.damaged(asteroid.damage)
                    shield_blocked = True
                    break
            if not shield_blocked and self.game.player.can_be_damaged:
                if self.game.player.collides_with(asteroid):
                    self.game.player.apply_collision_to_asteroid(asteroid,
                        impact_scale=C.PLAYER_COLLISION_IMPACT_SCALE)
                    health_before = asteroid.health
                    score = asteroid.damaged(self.game.player.collision_damage)
                    if score:
                        self.game.HUD.update_score(score)
                    self.game.combat_stats.record_damage_event(
                        source=self.game.player.stat_source,
                        health_before=health_before,
                        attempted_damage=self.game.player.collision_damage)
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

    def handle_exp_orb_pickups(self):
        if not self.game.exp_orbs:
            return
        player_pos = self.game.player.position
        to_collect = [orb for orb in list(self.game.exp_orbs)
                      if player_pos.distance_to(orb.position) <= C.EXP_ORB_PICKUP_RADIUS]
        for orb in to_collect:
            self.game.experience.add_xp(orb.value)
            orb.kill()

    def handle_essence_orb_pickups(self):
        if not self.game.essence_orbs:
            return
        player_pos = self.game.player.position
        to_collect = [orb for orb in list(self.game.essence_orbs)
                      if player_pos.distance_to(orb.position) <= C.ESSENCE_ORB_PICKUP_RADIUS]
        for orb in to_collect:
            self.game.essence.add(orb.value)
            orb.kill()

    def handle_elemental_essence_orb_pickups(self):
        if not self.game.elemental_essence_orbs:
            return
        player_pos = self.game.player.position
        to_collect = [orb for orb in list(self.game.elemental_essence_orbs)
                      if player_pos.distance_to(orb.position) <= C.ESSENCE_ORB_PICKUP_RADIUS]
        for orb in to_collect:
            self.game.essence.add_elemental(orb.value)
            orb.kill()