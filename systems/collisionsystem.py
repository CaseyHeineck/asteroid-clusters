from core import constants as C

class CollisionSystem:
    def __init__(self, game):
        self.game = game

    def handle(self):
        self.handle_asteroid_collisions()
        self.handle_enemy_collisions()
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

    def _place_at_opposite_edge(self, enemy):
        if enemy.position.x < 0 or enemy.position.x > C.SCREEN_WIDTH:
            enemy.position.x %= C.SCREEN_WIDTH
        if enemy.position.y < 0 or enemy.position.y > C.SCREEN_HEIGHT:
            enemy.position.y %= C.SCREEN_HEIGHT

    def handle_enemy_collisions(self):
        current_space = getattr(self.game, 'current_space', None)
        for enemy in list(self.game.enemies):
            enemy_airspace = getattr(enemy, 'airspace', None)
            same_airspace = (
                enemy_airspace is None
                or current_space is None
                or enemy_airspace == current_space
            )
            if same_airspace:
                for projectile in list(self.game.projectiles):
                    if projectile.stat_source == C.ENEMY:
                        continue
                    if projectile.collides_with(enemy):
                        score, xp = enemy.damaged(projectile.damage,
                            getattr(projectile, "element", None))
                        if score:
                            self.game.HUD.update_score(score)
                        if xp:
                            self.game.experience.add_xp(xp)
                        if getattr(projectile, 'weight', 0) > 0 and enemy.alive():
                            projectile.separate_from(enemy)
                            projectile.resolve_impact(enemy)
                            enemy.impact_timer = C.ENEMY_IMPACT_STUN_DURATION
                        elif "impact" in getattr(projectile, 'extra_abilities', set()) and enemy.alive():
                            normal = enemy.position - projectile.position
                            if normal.length_squared() > 0:
                                normal = normal.normalize()
                            enemy.velocity += normal * (projectile.velocity.length()
                                * C.KINETIC_PROJECTILE_COLLISION_IMPACT_SCALE)
                            enemy.impact_timer = C.ENEMY_IMPACT_STUN_DURATION
                        projectile.kill()
                if self.game.player.can_be_damaged and self.game.player.collides_with(enemy):
                    enemy.collide_and_impact(self.game.player)
                    self.game.player.sync_local_speeds_from_velocity()
                    enemy.impact_timer = C.ENEMY_IMPACT_STUN_DURATION
                    score, xp = enemy.damaged(self.game.player.collision_damage)
                    if score:
                        self.game.HUD.update_score(score)
                    if xp:
                        self.game.experience.add_xp(xp)
                    if enemy.health > 0:
                        score_delta, lives = self.game.player.damaged()
                        if score_delta:
                            self.game.HUD.update_score(score_delta)
                        self.game.HUD.update_player_lives(lives)
                        if self.game.player.game_over:
                            self.game.on_game_over()
                for asteroid in list(self.game.asteroids):
                    if not enemy.alive():
                        break
                    if asteroid.collides_with(enemy):
                        enemy.collide_and_impact(asteroid)
                        if asteroid.velocity.length() > C.ASTEROID_MAX_SPEED:
                            asteroid.velocity.scale_to_length(C.ASTEROID_MAX_SPEED)
                        score, xp = enemy.damaged(asteroid.damage)
                        if score:
                            self.game.HUD.update_score(score)
                        if xp:
                            self.game.experience.add_xp(xp)
                        health_before = asteroid.health
                        ast_score = asteroid.damaged(enemy.damage)
                        if ast_score:
                            self.game.HUD.update_score(ast_score)
                        self.game.combat_stats.record_damage_event(
                            source=C.ENEMY, health_before=health_before,
                            attempted_damage=enemy.damage)
            else:
                pos = enemy.position
                if (pos.x < 0 or pos.x > C.SCREEN_WIDTH
                        or pos.y < 0 or pos.y > C.SCREEN_HEIGHT):
                    enemy.airspace = current_space
                    self._place_at_opposite_edge(enemy)
        for projectile in list(self.game.projectiles):
            if projectile.stat_source != C.ENEMY:
                continue
            if projectile.collides_with(self.game.player):
                projectile.kill()
                score_delta, lives = self.game.player.damaged()
                if score_delta:
                    self.game.HUD.update_score(score_delta)
                self.game.HUD.update_player_lives(lives)
                if self.game.player.game_over:
                    self.game.on_game_over()

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