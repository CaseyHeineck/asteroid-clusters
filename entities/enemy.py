import pygame
import random
from core import constants as C
from core.circleshape import CircleShape
from core.element import draw_elemental_glow_poly, get_damage_multiplier
from core.logger import log_event
from entities.elementalessenceorb import ElementalEssenceOrb
from entities.weaponsplatform import ExplosivePlatform, KineticPlatform, LaserPlatform, PlasmaPlatform
from ui.visualeffect import EnemyKillExplosionVE, LaserBeamVE

class Enemy(CircleShape):
    def __init__(self, x, y, player, game=None):
        super().__init__(x, y, C.ENEMY_RADIUS,
            weight=C.ENEMY_WEIGHT, bounciness=C.ENEMY_BOUNCINESS,
            drag=C.ENEMY_DRAG, rotation=0, angular_velocity=0)
        self.player = player
        self.game = game
        self.health = C.ENEMY_MAX_HEALTH
        self.max_health = C.ENEMY_MAX_HEALTH
        self.element = None
        self.xp_value = C.ENEMY_XP_VALUE
        self.score_value = C.ENEMY_SCORE_VALUE
        self.damage = C.ENEMY_COLLISION_DAMAGE
        self.stat_source = C.ENEMY
        self.platform = None
        self.extra_abilities = set()
        self.asteroids = None
        self.body_color = C.ENEMY_BODY_COLOR
        self.hull_width = C.ENEMY_HULL_WIDTH
        self.hull_length = C.ENEMY_HULL_LENGTH
        self.target = None
        self.speed = C.ENEMY_SPEED
        self.airspace = None
        self.impact_timer = 0

    def damaged(self, amount, attacker_element=None):
        mult = get_damage_multiplier(attacker_element, self.element)
        self.health -= max(1, int(amount * mult))
        if self.health <= 0:
            log_event("enemy_destroyed")
            explosion_radius = max(12, int(self.radius * 1.5))
            EnemyKillExplosionVE(self.position.x, self.position.y, explosion_radius)
            if self.element is not None and ElementalEssenceOrb.containers:
                angle = random.uniform(0, 360)
                dist = random.uniform(0, self.radius)
                offset = pygame.Vector2(dist, 0).rotate(angle)
                ElementalEssenceOrb(self.position.x + offset.x, self.position.y + offset.y,
                    C.ENEMY_ELEMENTAL_ESSENCE_DROP, self.element)
            self.kill()
            xp = self.xp_value if self.element is not None else self.xp_value + C.ENEMY_NON_ELEMENTAL_BONUS_XP
            return self.score_value, xp
        log_event("enemy_hit")
        return 0, 0

    def acquire_target(self):
        self.target = self.player

    def aim_at_target(self):
        if self.target is None:
            return
        direction = self.target.position - self.position
        if direction.length_squared() > 0:
            self.rotation = pygame.Vector2(0, -1).angle_to(direction)

    def _in_current_airspace(self):
        if self.airspace is None or self.game is None:
            return True
        current = getattr(self.game, 'current_space', None)
        return current is None or self.airspace == current

    def shoot(self):
        if not self._in_current_airspace():
            return 0
        if self.platform is None or not self.platform.can_fire() or self.target is None:
            return 0
        return self.platform.fire(self) or 0

    def _calculate_avoidance(self, asteroids):
        avoidance = pygame.Vector2(0, 0)
        for asteroid in asteroids:
            to_enemy = self.position - asteroid.position
            if to_enemy.length_squared() == 0:
                continue
            distance = to_enemy.length()
            if distance > C.ENEMY_ASTEROID_AVOIDANCE_RADIUS:
                continue
            if asteroid.velocity.length_squared() > 0:
                approach_speed = asteroid.velocity.dot(to_enemy.normalize())
                if approach_speed <= 0:
                    continue
            strength = 1.0 - (distance / C.ENEMY_ASTEROID_AVOIDANCE_RADIUS)
            avoidance += to_enemy.normalize() * strength
        if avoidance.length_squared() > 0:
            avoidance = avoidance.normalize()
        return avoidance

    def move_toward_player(self, dt):
        if self.impact_timer > 0:
            return
        direction = self.player.position - self.position
        if direction.length_squared() == 0:
            return
        move_dir = direction.normalize()
        if self.asteroids:
            avoidance = self._calculate_avoidance(self.asteroids)
            if avoidance.length_squared() > 0:
                move_dir = (move_dir * (1.0 - C.ENEMY_ASTEROID_AVOIDANCE_WEIGHT)
                            + avoidance * C.ENEMY_ASTEROID_AVOIDANCE_WEIGHT)
                if move_dir.length_squared() > 0:
                    move_dir = move_dir.normalize()
        self.velocity = move_dir * self.speed

    def rect_corners(self):
        forward = pygame.Vector2(0, -1).rotate(self.rotation)
        right = forward.rotate(90)
        hw = self.hull_width / 2
        hl = self.hull_length / 2
        return [
            self.position + forward * hl + right * hw,
            self.position + forward * hl - right * hw,
            self.position - forward * hl - right * hw,
            self.position - forward * hl + right * hw,
        ]

    def draw_body(self, screen):
        corners = self.rect_corners()
        if self.element is not None:
            draw_elemental_glow_poly(screen, corners, self.element)
        pygame.draw.polygon(screen, self.get_outline_color(self.body_color), corners)

    def draw(self, screen):
        if not self._in_current_airspace():
            return
        self.draw_body(screen)
        if self.platform is not None:
            self.platform.draw(screen, self)

    def update(self, dt):
        if self.impact_timer > 0:
            self.impact_timer = max(0, self.impact_timer - dt)
        if self._in_current_airspace():
            self.move_toward_player(dt)
        self.physics_move(dt)
        if self.platform is not None:
            self.platform.tick(dt)
        self.acquire_target()
        self.aim_at_target()
        self.update_outline_pulse(dt)
        self.update_gameplay_effects(dt)
        return self.shoot()


class PlasmaEnemy(Enemy):
    def __init__(self, x, y, player, game):
        super().__init__(x, y, player, game)
        self.health = C.PLASMA_ENEMY_MAX_HEALTH
        self.max_health = C.PLASMA_ENEMY_MAX_HEALTH
        self.xp_value = C.PLASMA_ENEMY_XP_VALUE
        self.body_color = C.PLASMA_ENEMY_BODY_COLOR
        self.speed = C.PLASMA_ENEMY_SPEED
        self.asteroids = game.asteroids
        self.platform = PlasmaPlatform(base_damage=C.PLASMA_ENEMY_DAMAGE,
            projectile_color=C.PLASMA_ENEMY_PROJECTILE_COLOR)
        self.platform.weapons_free_timer_max = C.PLASMA_ENEMY_WEAPONS_FREE_TIMER
        self.platform.projectile_speed = C.PLASMA_ENEMY_PROJECTILE_SPEED
        self.platform.weapons_free_timer = C.PLASMA_ENEMY_WEAPONS_FREE_TIMER

    def _draw_wings(self, screen):
        forward = pygame.Vector2(0, -1).rotate(self.rotation)
        right = forward.rotate(90)
        hw = self.hull_width / 2
        hl = self.hull_length / 2
        ws = C.PLASMA_ENEMY_WING_SPAN
        wl = C.PLASMA_ENEMY_WING_LENGTH
        fill_color = self.get_outline_color(self.body_color)
        for side in (-1, 1):
            root_front = self.position - forward * (hl * 0.1) + right * (hw * side)
            root_rear = self.position - forward * hl + right * (hw * side)
            tip = self.position - forward * (wl * 0.5) + right * ((hw + ws) * side)
            wing = [root_front, root_rear, tip]
            if self.element is not None:
                draw_elemental_glow_poly(screen, wing, self.element)
            pygame.draw.polygon(screen, fill_color, wing)

    def draw_body(self, screen):
        super().draw_body(screen)
        self._draw_wings(screen)


class KineticEnemy(Enemy):
    def __init__(self, x, y, player, game):
        super().__init__(x, y, player, game)
        self.health = C.KINETIC_ENEMY_MAX_HEALTH
        self.max_health = C.KINETIC_ENEMY_MAX_HEALTH
        self.xp_value = C.KINETIC_ENEMY_XP_VALUE
        self.body_color = C.KINETIC_ENEMY_BODY_COLOR
        self.speed = C.KINETIC_ENEMY_SPEED
        self.hull_width = C.KINETIC_ENEMY_HULL_WIDTH
        self.hull_length = C.KINETIC_ENEMY_HULL_LENGTH
        self.asteroids = game.asteroids
        self.platform = KineticPlatform(projectile_color=C.KINETIC_ENEMY_PROJECTILE_COLOR)
        self.platform.weapons_free_timer_max = C.KINETIC_ENEMY_WEAPONS_FREE_TIMER
        self.platform.weapons_free_timer = C.KINETIC_ENEMY_WEAPONS_FREE_TIMER
        self.platform.projectile_speed = C.KINETIC_ENEMY_PROJECTILE_SPEED
        self.platform.projectile_radius = C.KINETIC_ENEMY_PROJECTILE_RADIUS
        self.platform.range = C.KINETIC_ENEMY_WEAPONS_RANGE

    def _find_largest_asteroid(self):
        largest = None
        for asteroid in self.asteroids:
            if largest is None or asteroid.radius > largest.radius:
                largest = asteroid
        return largest

    def _find_nearest_asteroid(self, exclude=None):
        nearest = None
        nearest_dist_sq = float('inf')
        for asteroid in self.asteroids:
            if exclude is not None and asteroid is exclude:
                continue
            d = self.position.distance_squared_to(asteroid.position)
            if d < nearest_dist_sq:
                nearest_dist_sq = d
                nearest = asteroid
        return nearest

    def _calculate_proximity_avoidance(self, objects):
        avoidance = pygame.Vector2(0, 0)
        for obj in objects:
            to_self = self.position - obj.position
            if to_self.length_squared() == 0:
                continue
            distance = to_self.length()
            if distance > C.ENEMY_ASTEROID_AVOIDANCE_RADIUS:
                continue
            strength = 1.0 - (distance / C.ENEMY_ASTEROID_AVOIDANCE_RADIUS)
            avoidance += to_self.normalize() * strength
        if avoidance.length_squared() > 0:
            avoidance = avoidance.normalize()
        return avoidance

    def acquire_target(self):
        player_dist = self.position.distance_to(self.player.position)
        if player_dist <= C.KINETIC_ENEMY_PLAYER_THREAT_RADIUS:
            self.target = self.player
            return
        largest = self._find_largest_asteroid()
        if largest is None:
            self.target = None
            return
        if self.position.distance_to(largest.position) <= self.platform.range:
            self.target = largest
            return
        nearest = self._find_nearest_asteroid(exclude=largest)
        self.target = nearest if nearest is not None else largest

    def move_toward_asteroid(self, dt):
        if self.impact_timer > 0:
            return
        player_dist = self.position.distance_to(self.player.position)
        if player_dist <= C.KINETIC_ENEMY_PLAYER_THREAT_RADIUS:
            direction = self.player.position - self.position
            if direction.length_squared() == 0:
                return
            self.velocity = direction.normalize() * self.speed
            return
        largest = self._find_largest_asteroid()
        if largest is None:
            return
        direction = largest.position - self.position
        if direction.length_squared() == 0:
            return
        move_dir = direction.normalize()
        obstacles = [a for a in self.asteroids if a is not largest]
        avoidance = self._calculate_proximity_avoidance(obstacles + [self.player])
        if avoidance.length_squared() > 0:
            move_dir = (move_dir * (1.0 - C.ENEMY_ASTEROID_AVOIDANCE_WEIGHT)
                        + avoidance * C.ENEMY_ASTEROID_AVOIDANCE_WEIGHT)
            if move_dir.length_squared() > 0:
                move_dir = move_dir.normalize()
        self.velocity = move_dir * self.speed

    def update(self, dt):
        if self.impact_timer > 0:
            self.impact_timer = max(0, self.impact_timer - dt)
        if self._in_current_airspace():
            self.move_toward_asteroid(dt)
        else:
            self.move_toward_player(dt)
        self.physics_move(dt)
        if self.platform is not None:
            self.platform.tick(dt)
        self.acquire_target()
        self.aim_at_target()
        self.update_outline_pulse(dt)
        self.update_gameplay_effects(dt)
        return self.shoot()

    def _draw_fins(self, screen):
        forward = pygame.Vector2(0, -1).rotate(self.rotation)
        right = forward.rotate(90)
        hw = self.hull_width / 2
        hl = self.hull_length / 2
        fs = C.KINETIC_ENEMY_FIN_SPAN
        fill_color = self.get_outline_color(self.body_color)
        for side in (-1, 1):
            root_front = self.position + forward * hl + right * (hw * side)
            root_mid = self.position + right * (hw * side)
            tip = self.position + forward * (hl * 0.3) + right * ((hw + fs) * side)
            fin = [root_front, root_mid, tip]
            if self.element is not None:
                draw_elemental_glow_poly(screen, fin, self.element)
            pygame.draw.polygon(screen, fill_color, fin)

    def draw_body(self, screen):
        super().draw_body(screen)
        self._draw_fins(screen)


class LaserEnemy(Enemy):
    def __init__(self, x, y, player, game):
        super().__init__(x, y, player, game)
        self.health = C.LASER_ENEMY_MAX_HEALTH
        self.max_health = C.LASER_ENEMY_MAX_HEALTH
        self.score_value = C.LASER_ENEMY_SCORE_VALUE
        self.xp_value = C.LASER_ENEMY_XP_VALUE
        self.body_color = C.LASER_ENEMY_BODY_COLOR
        self.speed = C.LASER_ENEMY_SPEED
        self.hull_length = C.LASER_ENEMY_HULL_LENGTH
        self.hull_width = C.LASER_ENEMY_HULL_WIDTH
        self.asteroids = game.asteroids
        self.platform = LaserPlatform()
        self.platform.weapons_free_timer_max = C.LASER_ENEMY_WEAPONS_FREE_TIMER
        self.platform.weapons_free_timer = C.LASER_ENEMY_WEAPONS_FREE_TIMER
        self.platform.range = float("inf")
        self.platform.damage = C.LASER_ENEMY_DAMAGE
        self.locked_target_pos = None

    def _mirror_position(self):
        cx = C.SCREEN_WIDTH / 2
        cy = C.SCREEN_HEIGHT / 2
        return pygame.Vector2(2 * cx - self.player.position.x, 2 * cy - self.player.position.y)

    def _ray_hits_asteroid(self, start, direction, asteroid):
        to_center = asteroid.position - start
        proj = to_center.dot(direction)
        if proj < 0:
            return False, 0
        perp_sq = max(0, to_center.length_squared() - proj * proj)
        return perp_sq <= asteroid.radius ** 2, proj

    def _screen_edge_endpoint(self, start, direction):
        W, H = C.SCREEN_WIDTH, C.SCREEN_HEIGHT
        t_vals = []
        if direction.x > 0:
            t_vals.append((W - start.x) / direction.x)
        elif direction.x < 0:
            t_vals.append(-start.x / direction.x)
        if direction.y > 0:
            t_vals.append((H - start.y) / direction.y)
        elif direction.y < 0:
            t_vals.append(-start.y / direction.y)
        t = min((v for v in t_vals if v > 0), default=1000)
        return start + direction * t

    def _fire_laser_at(self, target_pos):
        to_target = target_pos - self.position
        if to_target.length_squared() == 0:
            return 0
        dir_norm = to_target.normalize()
        spawn_pos = self.position + dir_norm * (self.radius + C.LASER_DRONE_WEAPONS_PLATFORM_OFFSET)
        closest_obj = None
        closest_dist = float('inf')
        if self.asteroids:
            for obj in self.asteroids:
                hit, dist = self._ray_hits_asteroid(spawn_pos, dir_norm, obj)
                if hit and dist < closest_dist:
                    closest_dist = dist
                    closest_obj = obj
        game = self.game
        enemies = getattr(game, 'enemies', None) if game else None
        if enemies:
            for obj in enemies:
                if obj is self or not obj.alive():
                    continue
                hit, dist = self._ray_hits_asteroid(spawn_pos, dir_norm, obj)
                if hit and dist < closest_dist:
                    closest_dist = dist
                    closest_obj = obj
        if self.player is not None:
            hit, dist = self._ray_hits_asteroid(spawn_pos, dir_norm, self.player)
            if hit and dist < closest_dist:
                closest_dist = dist
                closest_obj = self.player
        if closest_obj is not None:
            end_pos = closest_obj.position.copy()
            if LaserBeamVE.containers:
                LaserBeamVE(spawn_pos, end_pos, color=C.LASER_BEAM_COLOR,
                    width=C.LASER_BEAM_WIDTH, duration=C.LASER_BEAM_DURATION)
            if closest_obj is self.player:
                if self.player.can_be_damaged:
                    score_delta, lives = self.player.damaged()
                    if game and hasattr(game, 'HUD'):
                        game.HUD.update_player_lives(lives)
                        if score_delta:
                            game.HUD.update_score(score_delta)
                    if getattr(self.player, 'game_over', False) and game and hasattr(game, 'on_game_over'):
                        game.on_game_over()
            else:
                health_before = closest_obj.health
                result = closest_obj.damaged(self.platform.damage)
                if game and game.combat_stats:
                    game.combat_stats.record_damage_event(
                        source=self.stat_source, health_before=health_before,
                        attempted_damage=self.platform.damage)
                if isinstance(result, tuple):
                    score, xp = result
                    if score and game and hasattr(game, 'HUD'):
                        game.HUD.update_score(score)
                    if xp and game and hasattr(game, 'experience'):
                        game.experience.add_xp(xp)
                else:
                    score = result
                    if score and game and hasattr(game, 'HUD'):
                        game.HUD.update_score(score)
        else:
            end_pos = self._screen_edge_endpoint(spawn_pos, dir_norm)
            if LaserBeamVE.containers:
                LaserBeamVE(spawn_pos, end_pos, color=C.LASER_BEAM_COLOR,
                    width=C.LASER_BEAM_WIDTH, duration=C.LASER_BEAM_DURATION)
        return 0

    def move_toward_player(self, dt):
        if self.impact_timer > 0:
            return
        dist_to_player = self.position.distance_to(self.player.position)
        if dist_to_player > C.LASER_ENEMY_FOLLOW_FALLBACK_DIST:
            target_pos = self.player.position
        else:
            target_pos = self._mirror_position()
        direction = target_pos - self.position
        if direction.length_squared() == 0:
            return
        move_dir = direction.normalize()
        if self.asteroids:
            avoidance = self._calculate_avoidance(self.asteroids)
            if avoidance.length_squared() > 0:
                move_dir = (move_dir * (1.0 - C.ENEMY_ASTEROID_AVOIDANCE_WEIGHT)
                            + avoidance * C.ENEMY_ASTEROID_AVOIDANCE_WEIGHT)
                if move_dir.length_squared() > 0:
                    move_dir = move_dir.normalize()
        self.velocity = move_dir * self.speed

    def shoot(self):
        if not self._in_current_airspace():
            return 0
        if self.platform is None or not self.platform.can_fire():
            return 0
        if self.locked_target_pos is None:
            return 0
        score = self._fire_laser_at(self.locked_target_pos)
        self.platform.weapons_free_timer = self.platform.weapons_free_timer_max
        self.locked_target_pos = None
        return score

    def update(self, dt):
        if self.impact_timer > 0:
            self.impact_timer = max(0, self.impact_timer - dt)
        if self._in_current_airspace():
            self.move_toward_player(dt)
        self.physics_move(dt)
        if self.platform is not None:
            self.platform.tick(dt)
        self.acquire_target()
        self.aim_at_target()
        warn = C.LASER_ENEMY_CROSSHAIR_WARN_TIME
        timer = self.platform.weapons_free_timer if self.platform else 1.0
        if 0 < timer <= warn:
            if self.locked_target_pos is None:
                self.locked_target_pos = self.player.position.copy()
        elif timer > warn:
            self.locked_target_pos = None
        if self.locked_target_pos is not None:
            direction = self.locked_target_pos - self.position
            if direction.length_squared() > 0:
                self.rotation = pygame.Vector2(0, -1).angle_to(direction)
        self.update_outline_pulse(dt)
        self.update_gameplay_effects(dt)
        return self.shoot()

    def draw_body(self, screen):
        forward = pygame.Vector2(0, -1).rotate(self.rotation)
        right = forward.rotate(90)
        hl = self.hull_length / 2
        hw = self.hull_width / 2
        nose = self.position + forward * hl
        left_base = self.position - forward * hl - right * hw
        right_base = self.position - forward * hl + right * hw
        triangle = [nose, left_base, right_base]
        if self.element is not None:
            draw_elemental_glow_poly(screen, triangle, self.element)
        pygame.draw.polygon(screen, self.get_outline_color(self.body_color), triangle)
        if self.platform is not None:
            em_length = max(6, int(hl * 0.45))
            em_width = max(4, int(hw * 0.45))
            base_center = nose - forward * em_length
            pygame.draw.polygon(screen, self.platform.get_platform_color(),
                [nose, base_center + right * em_width, base_center - right * em_width])

    def _draw_crosshair(self, screen, pos, alpha):
        size = C.LASER_ENEMY_CROSSHAIR_SIZE
        width = C.LASER_ENEMY_CROSSHAIR_WIDTH
        surf_size = size * 2 + 4
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        c = surf_size // 2
        color = (*C.RED, alpha)
        pygame.draw.line(surf, color, (0, c), (surf_size, c), width)
        pygame.draw.line(surf, color, (c, 0), (c, surf_size), width)
        pygame.draw.circle(surf, color, (c, c), size - 2, width)
        screen.blit(surf, surf.get_rect(center=(int(pos.x), int(pos.y))))

    def draw(self, screen):
        if not self._in_current_airspace():
            return
        self.draw_body(screen)
        if self.locked_target_pos is not None and self.platform is not None:
            timer = self.platform.weapons_free_timer
            warn = C.LASER_ENEMY_CROSSHAIR_WARN_TIME
            t = 1.0 - (timer / warn) if warn > 0 else 1.0
            t = max(0.0, min(1.0, t))
            alpha = int(C.LASER_ENEMY_CROSSHAIR_MIN_ALPHA
                        + (255 - C.LASER_ENEMY_CROSSHAIR_MIN_ALPHA) * t)
            self._draw_crosshair(screen, self.locked_target_pos, alpha)


class ExplosiveEnemy(Enemy):
    def __init__(self, x, y, player, game):
        super().__init__(x, y, player, game)
        self.health = C.EXPLOSIVE_ENEMY_MAX_HEALTH
        self.max_health = C.EXPLOSIVE_ENEMY_MAX_HEALTH
        self.score_value = C.EXPLOSIVE_ENEMY_SCORE_VALUE
        self.xp_value = C.EXPLOSIVE_ENEMY_XP_VALUE
        self.body_color = C.EXPLOSIVE_ENEMY_BODY_COLOR
        self.speed = C.EXPLOSIVE_ENEMY_SPEED
        self.hull_width = C.EXPLOSIVE_ENEMY_HULL_SIZE
        self.hull_length = C.EXPLOSIVE_ENEMY_HULL_SIZE
        self.asteroids = game.asteroids
        self.platform = ExplosivePlatform()
        self.platform.weapons_free_timer_max = C.EXPLOSIVE_ENEMY_WEAPONS_FREE_TIMER
        self.platform.weapons_free_timer = C.EXPLOSIVE_ENEMY_WEAPONS_FREE_TIMER
        self.platform.range = C.EXPLOSIVE_ENEMY_WEAPONS_RANGE
        self.platform.projectile_speed = C.EXPLOSIVE_ENEMY_PROJECTILE_SPEED

    def _find_best_explosion_pos(self):
        targets = [self.player] + list(self.asteroids)
        if not targets:
            return self.player.position.copy()
        explosion_r = C.ROCKET_HIT_RADIUS
        best_pos = self.player.position.copy()
        best_count = 0
        for anchor in targets:
            count = sum(
                1 for t in targets
                if anchor.position.distance_to(t.position) <= explosion_r
            )
            if count > best_count:
                best_count = count
                best_pos = anchor.position.copy()
        return best_pos

    def move_toward_player(self, dt):
        if self.impact_timer > 0:
            return
        target_pos = self._find_best_explosion_pos()
        direction = target_pos - self.position
        if direction.length_squared() == 0:
            return
        move_dir = direction.normalize()
        if self.asteroids:
            avoidance = self._calculate_avoidance(self.asteroids)
            if avoidance.length_squared() > 0:
                move_dir = (move_dir * (1.0 - C.ENEMY_ASTEROID_AVOIDANCE_WEIGHT)
                            + avoidance * C.ENEMY_ASTEROID_AVOIDANCE_WEIGHT)
                if move_dir.length_squared() > 0:
                    move_dir = move_dir.normalize()
        self.velocity = move_dir * self.speed

    def draw_body(self, screen):
        corners = self.rect_corners()
        if self.element is not None:
            draw_elemental_glow_poly(screen, corners, self.element)
        pygame.draw.polygon(screen, self.get_outline_color(self.body_color), corners)
