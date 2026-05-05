import random
from core import constants as C
from entities.projectile import Kinetic, Plasma, Rocket
from systems.gameplayeffect import BurnSTE, RocketHitAOE

class CollisionSystem:
    def __init__(self, game):
        self.game = game

    def _update_player_hp_hud(self, hp):
        if self.game.player.uses_health:
            self.game.HUD.update_player_health(hp)
        else:
            self.game.HUD.update_player_lives(hp)

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
                    score_delta, hp = self.game.player.damaged()
                    if score_delta:
                        self.game.HUD.update_score(score_delta)
                    self._update_player_hp_hud(hp)
                    if self.game.player.game_over:
                        self.game.on_game_over()
            for projectile in self.game.projectiles:
                if projectile.collides_with(asteroid):
                    result = projectile.on_hit(asteroid)
                    if isinstance(result, tuple):
                        score, xp = result
                    else:
                        score, xp = result, 0
                    if score:
                        self.game.HUD.update_score(score)
                    if xp and hasattr(self.game, 'experience'):
                        self.game.experience.add_xp(xp)
                    if (getattr(projectile, 'player', None) is not None
                            and self.game.player.can_be_damaged
                            and asteroid.position.distance_to(
                                self.game.player.position) <= C.ROCKET_HIT_RADIUS):
                        score_delta, hp = self.game.player.damaged()
                        if score_delta:
                            self.game.HUD.update_score(score_delta)
                        self._update_player_hp_hud(hp)
                        if self.game.player.game_over:
                            self.game.on_game_over()

    def _try_spread_burn(self, source, target):
        if not hasattr(source, 'gameplay_effects') or not hasattr(target, 'add_gameplay_effect'):
            return
        for effect in source.gameplay_effects:
            if isinstance(effect, BurnSTE) and not effect.expired:
                if random.random() < effect.spread_chance:
                    new_burn = BurnSTE(
                        damage_per_tick=effect.damage_per_tick,
                        tick_rate=effect.tick_rate,
                        duration=C.PLASMA_BURN_DURATION,
                        spread_chance=effect.spread_chance)
                    new_burn.stat_source = effect.stat_source
                    new_burn.combat_stats = effect.combat_stats
                    target.add_gameplay_effect(new_burn)
                break

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
                    if projectile.collides_with(enemy):
                        if isinstance(projectile, Rocket):
                            result = projectile.on_hit(enemy)
                            if isinstance(result, tuple):
                                score, xp = result
                            else:
                                score, xp = result, 0
                            if score:
                                self.game.HUD.update_score(score)
                            if xp:
                                self.game.experience.add_xp(xp)
                            if (getattr(projectile, 'player', None) is not None
                                    and self.game.player.can_be_damaged
                                    and enemy.position.distance_to(
                                        self.game.player.position) <= C.ROCKET_HIT_RADIUS):
                                score_delta, hp = self.game.player.damaged()
                                if score_delta:
                                    self.game.HUD.update_score(score_delta)
                                self._update_player_hp_hud(hp)
                                if self.game.player.game_over:
                                    self.game.on_game_over()
                        elif getattr(projectile, 'handles_own_kill', False):
                            result = projectile.on_hit(enemy)
                            if isinstance(result, tuple):
                                score, xp = result
                            else:
                                score, xp = result, 0
                            if score:
                                self.game.HUD.update_score(score)
                            if xp:
                                self.game.experience.add_xp(xp)
                        else:
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
                                projectile.weight = (Kinetic.weight_override if Kinetic.weight_override is not None
                                                     else C.KINETIC_PROJECTILE_WEIGHT_BASE)
                                projectile.separate_from(enemy)
                                projectile.resolve_impact(enemy)
                                enemy.impact_timer = C.ENEMY_IMPACT_STUN_DURATION
                            if enemy.health > 0 and (
                                    isinstance(projectile, Plasma)
                                    or "burn" in getattr(projectile, 'extra_abilities', set())):
                                burn = BurnSTE()
                                burn.stat_source = projectile.stat_source
                                burn.combat_stats = getattr(projectile, 'combat_stats', None)
                                enemy.add_gameplay_effect(burn)
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
                        score_delta, hp = self.game.player.damaged()
                        if score_delta:
                            self.game.HUD.update_score(score_delta)
                        self._update_player_hp_hud(hp)
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
                        self._try_spread_burn(asteroid, enemy)
                        self._try_spread_burn(enemy, asteroid)
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
                if isinstance(projectile, Rocket):
                    all_aoe_targets = list(projectile.asteroids) if projectile.asteroids else []
                    if projectile.enemies:
                        all_aoe_targets.extend(projectile.enemies)
                    aoe = RocketHitAOE(impact_position=projectile.position,
                        targets=all_aoe_targets, radius=C.ROCKET_HIT_RADIUS,
                        damage=C.ROCKET_HIT_DAMAGE)
                    aoe.stat_source = projectile.stat_source
                    aoe.combat_stats = getattr(projectile, 'combat_stats', None)
                    aoe_score, aoe_xp = aoe.apply()
                    if aoe_score:
                        self.game.HUD.update_score(aoe_score)
                    if aoe_xp:
                        self.game.experience.add_xp(aoe_xp)
                    projectile.kill()
                else:
                    projectile.kill()
                score_delta, hp = self.game.player.damaged()
                if score_delta:
                    self.game.HUD.update_score(score_delta)
                self._update_player_hp_hud(hp)
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