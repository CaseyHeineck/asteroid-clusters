import pygame
import constants as C
from circleshape import CircleShape
from projectile import Kinetic, LaserBeam, Plasma, Rocket
from shield import Shield

class Drone(CircleShape):
    def __init__(self, player, asteroids):
        super().__init__(player.position.x, player.position.y, C.DRONE_RADIUS,
            weight=C.DRONE_WEIGHT, bounciness=C.DRONE_BOUNCINESS, 
            drag=C.DRONE_DRAG, rotation=0, angular_velocity=0)
        self.asteroids = asteroids
        self.player = player
        self.orbit_angle = C.DRONE_ORBIT_ANGLE_OFFSET
        self.orbit_radius = C.DRONE_ORBIT_RADIUS
        self.orbit_speed = C.DRONE_ORBIT_SPEED
        self.target = None
        self.range = float("inf")
        self.weapons_free_timer = 0
        self.weapons_free_timer_max = C.DRONE_WEAPONS_FREE_TIMER
        self.body_color = C.WHITE
        self.body_line_width = C.DRONE_LINE_WIDTH
        self.stat_source = None

    def acquire_target(self):
        closest_so_far = float("inf")
        self.target = None
        for asteroid in self.asteroids:
            player_distance = self.player.position.distance_to(asteroid.position)
            drone_distance = self.position.distance_to(asteroid.position)
            if drone_distance <= self.range and player_distance < closest_so_far:
                closest_so_far = player_distance
                self.target = asteroid

    def aim_at_target(self):
        if self.target is None:
            return
        direction = self.target.position - self.position
        if direction.length_squared() > 0:
            self.rotation = pygame.Vector2(0, -1).angle_to(direction)

    def get_projectile_spawn_position(self):
        forward = self.get_forward_vector()
        return self.position + forward * self.radius

    def weapons_free(self):
        raise NotImplementedError("Drone subclass not instantiated")

    def shoot(self):
        if self.weapons_free_timer > 0 or self.target is None:
            return 0
        score = self.weapons_free()
        self.weapons_free_timer = self.weapons_free_timer_max
        return score or 0

    def draw_body(self, screen):
        pygame.draw.circle(screen, self.body_color, self.position, self.radius, self.body_line_width)

    def draw_weapons_platform(self, screen):
        raise NotImplementedError("Drone subclass not instantiated")

    def draw(self, screen):
        self.draw_body(screen)
        self.draw_weapons_platform(screen)

    def update(self, dt):
        self.orbit_player(dt)
        self.weapons_free_timer = max(0, self.weapons_free_timer - dt)
        self.acquire_target()
        self.aim_at_target()
        return self.shoot()

    def orbit_player(self, dt):
        self.orbit_angle += self.orbit_speed * dt
        offset = pygame.Vector2(self.orbit_radius, 0).rotate(self.orbit_angle)
        self.position = self.player.position + offset

    def collides_with(self, other):
        return False

class ExplosiveDrone(Drone):
    def __init__(self, player, asteroids):
        super().__init__(player, asteroids)
        self.body_color = C.EXPLOSIVE_DRONE_BODY_COLOR
        self.body_line_width = 0
        self.range = C.EXPLOSIVE_DRONE_WEAPONS_RANGE
        self.weapons_free_timer_max = C.EXPLOSIVE_DRONE_WEAPONS_FREE_TIMER
        self.projectile_speed = C.EXPLOSIVE_DRONE_PROJECTILE_SPEED
        self.launcher_color = C.EXPLOSIVE_DRONE_WEAPONS_PLATFORM_COLOR
        self.launcher_radius = C.EXPLOSIVE_DRONE_LAUNCHER_RADIUS
        self.door_offset = C.EXPLOSIVE_DRONE_DOOR_OFFSET
        self.door_width = C.EXPLOSIVE_DRONE_DOOR_WIDTH
        self.door_length = C.EXPLOSIVE_DRONE_DOOR_LENGTH
        self.launch_animation_timer = 0
        self.launch_animation_duration = C.EXPLOSIVE_DRONE_DOOR_ANIMATION_TIME
        self.stat_source = C.EXPLOSIVE_DRONE
        self.damage_multiplier = 1.0

    def get_projectile_spawn_position(self):
        forward = self.get_forward_vector()
        return self.position + forward * (self.radius + 4)

    def weapons_free(self):
        spawn_position = self.get_projectile_spawn_position()
        forward = self.get_forward_vector()
        projectile = Rocket(spawn_position.x, spawn_position.y, self.asteroids)
        projectile.damage = int(C.ROCKET_PROJECTILE_DAMAGE * self.damage_multiplier)
        projectile.velocity = forward * self.projectile_speed
        projectile.stat_source = self.stat_source
        projectile.combat_stats = self.player.game.combat_stats
        self.launch_animation_timer = self.launch_animation_duration
        return 0

    def update(self, dt):
        super().update(dt)
        self.launch_animation_timer = max(0, self.launch_animation_timer - dt)

    def draw_weapons_platform(self, screen):
        surface_size = self.radius * 3
        platform_surface = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        center_x = surface_size // 2
        center_y = surface_size // 2
        pygame.draw.circle(platform_surface, self.launcher_color, (center_x, center_y),
            self.launcher_radius, 0)
        open_ratio = 0
        if self.launch_animation_duration > 0:
            open_ratio = self.launch_animation_timer / self.launch_animation_duration
        door_slide = int(6 * open_ratio)
        left_door = pygame.Rect(center_x - self.door_offset - self.door_width - door_slide,
            center_y - self.door_length // 2, self.door_width, self.door_length)
        right_door = pygame.Rect(center_x + self.door_offset + door_slide,
            center_y - self.door_length // 2, self.door_width, self.door_length)
        pygame.draw.rect(platform_surface, self.launcher_color, left_door)
        pygame.draw.rect(platform_surface, self.launcher_color, right_door)
        rotated_platform = pygame.transform.rotate(platform_surface, -self.rotation)
        rotated_rect = rotated_platform.get_rect(center=(self.position.x, self.position.y))
        screen.blit(rotated_platform, rotated_rect)

class KineticDrone(Drone):
    def __init__(self, player, asteroids):
        super().__init__(player, asteroids)
        self.body_color = C.KINETIC_DRONE_BODY_COLOR
        self.body_line_width = 0
        self.range = C.KINETIC_DRONE_WEAPONS_RANGE
        self.weapons_free_timer_max = C.KINETIC_DRONE_WEAPONS_FREE_TIMER
        self.projectile_speed = C.KINETIC_DRONE_PROJECTILE_SPEED
        self.weapons_platform_color = C.KINETIC_DRONE_WEAPONS_PLATFORM_COLOR
        self.weapons_platform_length = C.KINETIC_DRONE_WEAPONS_PLATFORM_LENGTH
        self.weapons_platform_front_width = C.KINETIC_DRONE_WEAPONS_PLATFORM_FRONT_WIDTH
        self.weapons_platform_back_width = C.KINETIC_DRONE_WEAPONS_PLATFORM_BACK_WIDTH
        self.stat_source = C.KINETIC_DRONE
        self.damage_multiplier = 1.0

    def get_projectile_spawn_position(self):
        forward = self.get_forward_vector()
        return self.position + forward * self.weapons_platform_length

    def weapons_free(self):
        spawn_position = self.get_projectile_spawn_position()
        forward = self.get_forward_vector()
        projectile = Kinetic(spawn_position.x, spawn_position.y)
        projectile.damage = int(C.KINETIC_PROJECTILE_DAMAGE * self.damage_multiplier)
        projectile.velocity = forward * self.projectile_speed
        projectile.stat_source = self.stat_source
        projectile.combat_stats = self.player.game.combat_stats
        return 0

    def draw_weapons_platform(self, screen):
        surface_size = self.weapons_platform_length * 2
        platform_surface = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        center_x = surface_size // 2
        center_y = surface_size // 2
        front_half = self.weapons_platform_front_width / 2
        back_half = self.weapons_platform_back_width / 2
        length = self.weapons_platform_length
        points = [(center_x - front_half, center_y - length), (center_x + front_half, center_y - length),
            (center_x + back_half, center_y + 2), (center_x - back_half, center_y + 2)]
        pygame.draw.polygon(platform_surface, self.weapons_platform_color, points)
        rotated_platform = pygame.transform.rotate(platform_surface, -self.rotation)
        rotated_rect = rotated_platform.get_rect(center=(self.position.x, self.position.y))
        screen.blit(rotated_platform, rotated_rect)

class LaserDrone(Drone):
    def __init__(self, player, asteroids):
        super().__init__(player, asteroids)
        self.body_color = C.LASER_DRONE_BODY_COLOR
        self.body_line_width = 4
        self.range = C.LASER_DRONE_WEAPONS_RANGE
        self.weapons_free_timer_max = C.LASER_DRONE_WEAPONS_FREE_TIMER
        self.damage = C.LASER_DRONE_DAMAGE
        self.weapons_platform_length = C.LASER_DRONE_WEAPONS_PLATFORM_LENGTH
        self.weapons_platform_width = C.LASER_DRONE_WEAPONS_PLATFORM_WIDTH
        self.weapons_platform_offset = C.LASER_DRONE_WEAPONS_PLATFORM_OFFSET
        self.stat_source = C.LASER_DRONE

    def acquire_target(self):
        self.target = None
        valid_targets = []
        for asteroid in self.asteroids:
            drone_distance = self.position.distance_to(asteroid.position)
            if drone_distance <= self.range:
                valid_targets.append(asteroid)
        if not valid_targets:
            return
        highest_health = max(asteroid.health for asteroid in valid_targets)
        healthiest_targets = [asteroid for asteroid in valid_targets
            if asteroid.health == highest_health]
        self.target = min(healthiest_targets,
            key=lambda asteroid: self.player.position.distance_to(asteroid.position))

    def get_projectile_spawn_position(self):
        forward = self.get_forward_vector()
        return self.position + forward * (self.radius + self.weapons_platform_offset)

    def weapons_free(self):
        if self.target is None:
            return 0
        spawn_position = self.get_projectile_spawn_position()
        projectile = LaserBeam(spawn_position.x, spawn_position.y, self.target,
            self.damage, stat_source=self.stat_source, combat_stats=self.player.game.combat_stats)
        return projectile.score

    def lerp_color(self, start_color, end_color, t):
        t = max(0, min(1, t))
        return tuple(int(start + (end - start) * t)
            for start, end in zip(start_color, end_color))

    def get_charge_ratio(self):
        if self.weapons_free_timer_max <= 0:
            return 1
        return 1 - (self.weapons_free_timer / self.weapons_free_timer_max)

    def get_platform_color(self):
        charge_colors = [C.INDIGO, C.PURPLE, C.MAGENTA,
            C.DEEP_PINK, C.RED, C.LASER_RED]
        ratio = self.get_charge_ratio()
        if ratio >= 1:
            return charge_colors[-1]
        scaled = ratio * (len(charge_colors) - 1)
        index = int(scaled)
        local_t = scaled - index
        start_color = charge_colors[index]
        end_color = charge_colors[min(index + 1, len(charge_colors) - 1)]
        return self.lerp_color(start_color, end_color, local_t)

    def draw_weapons_platform(self, screen):
        platform_color = self.get_platform_color()
        surface_size = (self.radius + self.weapons_platform_offset + self.weapons_platform_length) * 2
        platform_surface = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        center_x = surface_size // 2
        center_y = surface_size // 2
        emitter_center_y = center_y - (self.radius + self.weapons_platform_offset)
        points = [(center_x, emitter_center_y - self.weapons_platform_length),
            (center_x - self.weapons_platform_width // 2, emitter_center_y),
            (center_x + self.weapons_platform_width // 2, emitter_center_y)]
        pygame.draw.polygon(platform_surface, platform_color, points)
        rotated_platform = pygame.transform.rotate(platform_surface, -self.rotation)
        rotated_rect = rotated_platform.get_rect(center=(self.position.x, self.position.y))
        screen.blit(rotated_platform, rotated_rect)

class PlasmaDrone(Drone):
    def __init__(self, player, asteroids):
        super().__init__(player, asteroids)
        self.body_color = C.PLASMA_DRONE_BODY_COLOR
        self.range = C.PLASMA_DRONE_WEAPONS_RANGE
        self.weapons_free_timer_max = C.PLASMA_DRONE_WEAPONS_FREE_TIMER
        self.projectile_speed = C.PLASMA_DRONE_PROJECTILE_SPEED
        self.weapons_platform_color = C.PLASMA_DRONE_WEAPONS_PLATFORM_COLOR
        self.weapons_platform_length = self.radius + C.PLASMA_DRONE_WEAPONS_PLATFORM_LENGTH_OFFSET
        self.weapons_platform_width = C.PLASMA_DRONE_WEAPONS_PLATFORM_WIDTH
        self.stat_source = C.PLASMA_DRONE
        self.damage_multiplier = 1.0

    def get_projectile_spawn_position(self):
        forward = self.get_forward_vector()
        return self.position + forward * self.weapons_platform_length

    def weapons_free(self):
        spawn_position = self.get_projectile_spawn_position()
        forward = self.get_forward_vector()
        projectile = Plasma(spawn_position.x, spawn_position.y)
        projectile.damage = int(C.PLASMA_PROJECTILE_DAMAGE * self.damage_multiplier)
        projectile.velocity = forward * self.projectile_speed
        projectile.stat_source = self.stat_source
        projectile.combat_stats = self.player.game.combat_stats
        return 0

    def draw_weapons_platform(self, screen):
        surface_size = self.weapons_platform_length * 2
        platform_surface = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        center_x = surface_size // 2
        center_y = surface_size // 2
        platform_rect = pygame.Rect(center_x - self.weapons_platform_width // 2,
            center_y - self.weapons_platform_length, self.weapons_platform_width,
            self.weapons_platform_length)
        pygame.draw.rect(platform_surface, self.weapons_platform_color, platform_rect)
        rotated_platform = pygame.transform.rotate(platform_surface, -self.rotation)
        rotated_rect = rotated_platform.get_rect(center=(self.position.x, self.position.y))
        screen.blit(rotated_platform, rotated_rect)

class SentinelDrone(Drone):
    def __init__(self, player, asteroids):
        super().__init__(player, asteroids)
        self.body_color = C.SENTINEL_DRONE_BODY_COLOR
        self.body_line_width = 0
        self.player_shield = None
        self.shield_create_timer = 0
        self.shield_max_health = C.SHIELD_MAX_HEALTH
        self.shield_repair_timer_base = C.SENTINEL_DRONE_SHIELD_REPAIR_TIMER
        self.shield_repair_timer = self.shield_repair_timer_base
        self.stat_source = C.SENTINEL_DRONE

    def update(self, dt):
        self.shield_sentinel(dt)
        self.orbit_player(dt)
        return 0

    def shield_sentinel(self, dt):
        self.shield_create_timer = max(0, self.shield_create_timer - dt)
        self.shield_repair_timer = max(0, self.shield_repair_timer - dt)
        if not self.player_shield:
            self.player.shield = False
            if self.shield_create_timer == 0:
                self.player_shield = Shield(owner=self.player, source=self,
                                            max_health=self.shield_max_health)
                self.player.shield = True
                self.shield_create_timer = C.SENTINEL_DRONE_SHIELD_CREATE_TIMER
        else:
            self.player.shield = True
            if self.player_shield and not self.player_shield.alive():
                self.player_shield = None
                self.player.shield = False
        if self.player_shield:
            if self.player_shield.health < self.player_shield.max_health:
                if self.shield_repair_timer == 0:
                    before = self.player_shield.health
                    self.player_shield.health = min(self.player_shield.max_health,
                        self.player_shield.health + 1)
                    repaired = self.player_shield.health - before
                    if repaired > 0:
                        self.player.game.combat_stats.add_repaired(
                            self.stat_source, repaired)
                    self.shield_repair_timer = self.shield_repair_timer_base

    def draw_weapons_platform(self, screen):
        direction = self.player.position - self.position
        if direction.length_squared() == 0:
            return
        angle = pygame.Vector2(0, -1).angle_to(direction)
        size = self.radius * 3
        surf = pygame.Surface((size, size), pygame.SRCALPHA)
        c = size // 2
        pygame.draw.circle(surf, C.SENTINEL_DRONE_BODY_COLOR, (c, c), self.radius, 2)
        pygame.draw.circle(surf, (0, 0, 0, 0), (c + int(self.radius * 0.4), c), self.radius, 0)
        rotated = pygame.transform.rotate(surf, -angle)
        rect = rotated.get_rect(center=(self.position.x, self.position.y))
        screen.blit(rotated, rect)