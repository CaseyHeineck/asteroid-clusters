import math
import pygame
from core import constants as C
from core.element import get_damage_multiplier
from entities.decoy import Decoy
from entities.projectile import Bouncer, Cannonball, ContagionPlasma, CorrodePlasma, FuseBomb, Grenade, HomingMissile, Kinetic, LaserBeam, MarkPlasma, NeedleSlug, Plasma, ProximityMine, Rocket, SlowPlasma
from entities.shield import Shield
from systems.gameplayeffect import RocketHitAOE
from ui.visualeffect import MuzzleFlareVE

class WeaponsPlatform:
    variant_name = ""
    variant_description = ""
    banish_ability = None

    def __init__(self):
        self.weapons_free_timer = 0.0
        self.weapons_free_timer_max = 0.0
        self.range = float("inf")
        self.damage_multiplier = 1.0
        self.upgrade_paths = []

    def tick(self, dt):
        self.weapons_free_timer = max(0.0, self.weapons_free_timer - dt)

    def sentinel_update(self, drone, dt):
        pass

    def can_fire(self):
        return self.weapons_free_timer <= 0.0

    def fire(self, owner):
        raise NotImplementedError

    def draw(self, screen, owner):
        raise NotImplementedError

    def _muzzle_position(self, owner):
        forward = owner.get_forward_vector()
        muzzle_dist = int(owner.radius * 0.1) + max(6, int(owner.radius * 0.9))
        return owner.position + forward * muzzle_dist

    def _draw_kinetic_barrel(self, screen, owner, muzzle_scale=0.22, base_scale=0.55, height_scale=0.9):
        surf_size = int(owner.radius * 6)
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        c = surf_size // 2
        muzzle_half = max(2, int(owner.radius * muzzle_scale))
        base_half   = max(4, int(owner.radius * base_scale))
        height      = max(6, int(owner.radius * height_scale))
        top_y  = c - int(owner.radius * 0.1) - height
        base_y = c - int(owner.radius * 0.1)
        trap_pts = [(c - muzzle_half, top_y), (c + muzzle_half, top_y),
            (c + base_half, base_y), (c - base_half, base_y)]
        pygame.draw.polygon(surf, C.GRAY, trap_pts)
        pygame.draw.polygon(surf, C.SILVER, trap_pts, 1)
        rotated = pygame.transform.rotate(surf, -owner.rotation)
        screen.blit(rotated, rotated.get_rect(center=(int(owner.position.x), int(owner.position.y))))

    def apply_upgrade(self, upgrade_type, tier):
        if upgrade_type == "damage":
            self.damage_multiplier *= (1 + C.SHOP_DAMAGE_INCREASE)
        elif upgrade_type == "fire_rate":
            self.weapons_free_timer_max *= (1 - C.SHOP_FIRE_RATE_INCREASE)
        elif upgrade_type == "projectile_speed" and hasattr(self, "projectile_speed"):
            self.projectile_speed *= (1 + C.SHOP_PROJECTILE_SPEED_INCREASE)


class KineticPlatform(WeaponsPlatform):
    variant_name = "Peashooter"
    variant_description = "Fast, direct rounds. Single target with impact knockback."
    banish_ability = "impact"

    def __init__(self, projectile_color=None):
        super().__init__()
        self.weapons_free_timer_max = C.KINETIC_DRONE_WEAPONS_FREE_TIMER
        self.range = C.KINETIC_DRONE_WEAPONS_RANGE
        self.projectile_speed = C.KINETIC_DRONE_PROJECTILE_SPEED
        self.projectile_color = projectile_color
        self.projectile_radius = C.KINETIC_PROJECTILE_RADIUS
        self.upgrade_paths = [
            {"type": "damage",          "label": "Damage +15%",        "is_generic": True},
            {"type": "fire_rate",       "label": "Fire Rate +12%",     "is_generic": True},
            {"type": "kinetic_mass",    "label": "Kinetic Mass +60%",  "is_generic": False},
            {"type": "projectile_speed","label": "Proj Speed +15%",    "is_generic": False},
        ]

    def fire(self, owner):
        spawn_pos = self._muzzle_position(owner)
        forward = owner.get_forward_vector()
        projectile = Kinetic(spawn_pos.x, spawn_pos.y)
        projectile.radius = self.projectile_radius
        projectile.damage = int(C.KINETIC_PROJECTILE_DAMAGE * self.damage_multiplier)
        projectile.velocity = forward * self.projectile_speed
        projectile.stat_source = owner.stat_source
        projectile.combat_stats = owner.game.combat_stats
        projectile.extra_abilities = set(owner.extra_abilities)
        projectile.asteroids = owner.asteroids
        projectile.element = owner.element
        if self.projectile_color is not None:
            projectile.color = self.projectile_color
        if MuzzleFlareVE.containers:
            MuzzleFlareVE(spawn_pos.x, spawn_pos.y, size=5)
        self.weapons_free_timer = self.weapons_free_timer_max
        return 0

    def draw(self, screen, owner):
        self._draw_kinetic_barrel(screen, owner)


class BurnPlatform(WeaponsPlatform):
    variant_name = "Burn"
    variant_description = "Plasma bolts that apply stacking burn damage over time."
    banish_ability = "burn"

    def __init__(self, base_damage=C.PLASMA_PROJECTILE_DAMAGE, projectile_color=None):
        super().__init__()
        self.weapons_free_timer_max = C.BURN_WEAPONS_FREE_TIMER
        self.range = C.BURN_WEAPONS_RANGE
        self.projectile_speed = C.DEBUFF_DRONE_PROJECTILE_SPEED
        self.base_damage = base_damage
        self.projectile_color = projectile_color
        self.upgrade_paths = [
            {"type": "damage",         "label": "Damage +15%",        "is_generic": True},
            {"type": "fire_rate",      "label": "Fire Rate +12%",     "is_generic": True},
            {"type": "burn_tick_rate", "label": "Burn Ticks +",       "is_generic": False},
            {"type": "burn_spread",    "label": "Spread Chance +10%", "is_generic": False},
        ]

    def _muzzle_position(self, owner):
        forward = owner.get_forward_vector()
        platform_length = owner.radius + C.DEBUFF_DRONE_PLATFORM_LENGTH_OFFSET
        return owner.position + forward * platform_length

    def fire(self, owner):
        spawn_pos = self._muzzle_position(owner)
        forward = owner.get_forward_vector()
        projectile = Plasma(spawn_pos.x, spawn_pos.y)
        projectile.damage = int(self.base_damage * self.damage_multiplier)
        projectile.velocity = forward * self.projectile_speed
        projectile.stat_source = owner.stat_source
        projectile.combat_stats = owner.game.combat_stats
        projectile.extra_abilities = set(owner.extra_abilities)
        projectile.asteroids = owner.asteroids
        projectile.element = owner.element
        if self.projectile_color is not None:
            projectile.color = self.projectile_color
        self.weapons_free_timer = self.weapons_free_timer_max
        return 0

    def draw(self, screen, owner):
        platform_length = owner.radius + C.DEBUFF_DRONE_PLATFORM_LENGTH_OFFSET
        surf_size = int(platform_length * 3)
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        c = surf_size // 2
        bw = C.DEBUFF_DRONE_PLATFORM_WIDTH
        bh = int(platform_length)
        barrel_rect = pygame.Rect(c - bw // 2, c - bh, bw, bh)
        pygame.draw.rect(surf, C.SILVER, barrel_rect)
        pygame.draw.rect(surf, C.GRAY, barrel_rect, 1)
        muzzle_w = bw + 4
        muzzle_h = max(4, bw // 2 + 1)
        muzzle_rect = pygame.Rect(c - muzzle_w // 2, c - bh - muzzle_h + 2, muzzle_w, muzzle_h)
        pygame.draw.rect(surf, C.LIGHT_GRAY, muzzle_rect)
        pygame.draw.rect(surf, C.GRAY, muzzle_rect, 1)
        rotated = pygame.transform.rotate(surf, -owner.rotation)
        screen.blit(rotated, rotated.get_rect(center=(int(owner.position.x), int(owner.position.y))))


class LaserPlatform(WeaponsPlatform):
    variant_name = "Laser Beam"
    variant_description = "Instant hitscan. High single-target damage, targets highest HP."
    banish_ability = "overkill"

    def __init__(self):
        super().__init__()
        self.weapons_free_timer_max = C.LASER_BEAM_WEAPONS_FREE_TIMER
        self.range = C.LASER_BEAM_WEAPONS_RANGE
        self.damage = C.LASER_BEAM_DAMAGE
        self.upgrade_paths = [
            {"type": "damage",    "label": "Damage +15%",    "is_generic": True},
            {"type": "fire_rate", "label": "Fire Rate +12%", "is_generic": True},
        ]

    def apply_upgrade(self, upgrade_type, tier):
        if upgrade_type == "damage":
            self.damage = int(self.damage * (1 + C.SHOP_DAMAGE_INCREASE))
        else:
            super().apply_upgrade(upgrade_type, tier)

    def fire(self, owner):
        if owner.target is None:
            return 0
        forward = owner.get_forward_vector()
        spawn_pos = owner.position + forward * (owner.radius + C.LASER_BEAM_PLATFORM_OFFSET)
        projectile = LaserBeam(spawn_pos.x, spawn_pos.y, owner.target,
            self.damage, stat_source=owner.stat_source,
            combat_stats=owner.game.combat_stats,
            extra_abilities=owner.extra_abilities,
            asteroids=owner.asteroids, element=owner.element)
        if projectile.xp and owner.game and hasattr(owner.game, 'experience'):
            owner.game.experience.add_xp(projectile.xp)
        self.weapons_free_timer = self.weapons_free_timer_max
        return projectile.score

    def get_charge_ratio(self):
        if self.weapons_free_timer_max <= 0:
            return 1
        return 1 - (self.weapons_free_timer / self.weapons_free_timer_max)

    def get_platform_color(self):
        charge_colors = [C.INDIGO, C.PURPLE, C.MAGENTA, C.DEEP_PINK, C.RED, C.LASER_RED]
        ratio = self.get_charge_ratio()
        if ratio >= 1:
            return charge_colors[-1]
        scaled = ratio * (len(charge_colors) - 1)
        index = int(scaled)
        local_t = scaled - index
        return self.lerp_color(charge_colors[index],
            charge_colors[min(index + 1, len(charge_colors) - 1)], local_t)

    def lerp_color(self, start_color, end_color, t):
        t = max(0, min(1, t))
        return tuple(int(s + (e - s) * t) for s, e in zip(start_color, end_color))

    def draw(self, screen, owner):
        platform_color = self.get_platform_color()
        offset = C.LASER_BEAM_PLATFORM_OFFSET
        length = C.LASER_BEAM_PLATFORM_LENGTH
        width = C.LASER_BEAM_PLATFORM_WIDTH
        surface_size = (owner.radius + offset + length) * 2
        surf = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        cx = surface_size // 2
        cy = surface_size // 2
        emitter_y = cy - (owner.radius + offset)
        points = [(cx, emitter_y - length),
            (cx - width // 2, emitter_y),
            (cx + width // 2, emitter_y)]
        pygame.draw.polygon(surf, platform_color, points)
        rotated = pygame.transform.rotate(surf, -owner.rotation)
        screen.blit(rotated, rotated.get_rect(center=(owner.position.x, owner.position.y)))


class BreachPlatform(WeaponsPlatform):
    variant_name = "Breach"
    variant_description = "Laser that ignores elemental resistance. Always hits for full damage."
    banish_ability = "overkill"

    def __init__(self):
        super().__init__()
        self.weapons_free_timer_max = C.BREACH_WEAPONS_FREE_TIMER
        self.range = C.BREACH_WEAPONS_RANGE
        self.damage = C.BREACH_BASE_DAMAGE
        self.upgrade_paths = [
            {"type": "damage",    "label": "Damage +15%",    "is_generic": True},
            {"type": "fire_rate", "label": "Fire Rate +12%", "is_generic": True},
        ]

    def apply_upgrade(self, upgrade_type, tier):
        if upgrade_type == "damage":
            self.damage = int(self.damage * (1 + C.SHOP_DAMAGE_INCREASE))
        else:
            super().apply_upgrade(upgrade_type, tier)

    def fire(self, owner):
        if owner.target is None:
            return 0
        target = owner.target
        target_element = getattr(target, 'element', None)
        elemental_mult = max(1.0, get_damage_multiplier(owner.element, target_element))
        effective_damage = int(self.damage * elemental_mult)
        forward = owner.get_forward_vector()
        spawn_pos = owner.position + forward * (owner.radius + C.LASER_BEAM_PLATFORM_OFFSET)
        projectile = LaserBeam(spawn_pos.x, spawn_pos.y, target,
            effective_damage, stat_source=owner.stat_source,
            combat_stats=owner.game.combat_stats,
            extra_abilities=owner.extra_abilities,
            asteroids=owner.asteroids, element=None)
        if projectile.xp and owner.game and hasattr(owner.game, 'experience'):
            owner.game.experience.add_xp(projectile.xp)
        self.weapons_free_timer = self.weapons_free_timer_max
        return projectile.score

    def get_charge_ratio(self):
        if self.weapons_free_timer_max <= 0:
            return 1
        return 1 - (self.weapons_free_timer / self.weapons_free_timer_max)

    def get_platform_color(self):
        charge_colors = [C.STEEL_GRAY, C.SILVER, C.WHITE, C.LIGHT_BLUE, C.ELECTRIC_BLUE]
        ratio = self.get_charge_ratio()
        if ratio >= 1:
            return charge_colors[-1]
        scaled = ratio * (len(charge_colors) - 1)
        index = int(scaled)
        local_t = scaled - index
        c1, c2 = charge_colors[index], charge_colors[min(index + 1, len(charge_colors) - 1)]
        return tuple(int(s + (e - s) * local_t) for s, e in zip(c1, c2))

    def draw(self, screen, owner):
        platform_color = self.get_platform_color()
        offset = C.LASER_BEAM_PLATFORM_OFFSET
        length = C.LASER_BEAM_PLATFORM_LENGTH
        width = C.LASER_BEAM_PLATFORM_WIDTH
        surface_size = (owner.radius + offset + length) * 2
        surf = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        cx = surface_size // 2
        cy = surface_size // 2
        emitter_y = cy - (owner.radius + offset)
        points = [(cx, emitter_y - length),
            (cx - width // 2, emitter_y),
            (cx + width // 2, emitter_y)]
        pygame.draw.polygon(surf, platform_color, points)
        rotated = pygame.transform.rotate(surf, -owner.rotation)
        screen.blit(rotated, rotated.get_rect(center=(owner.position.x, owner.position.y)))


class CascadePlatform(WeaponsPlatform):
    variant_name = "Cascade"
    variant_description = "Laser that spreads overkill damage to nearby enemies on kill."
    banish_ability = "overkill"

    def __init__(self):
        super().__init__()
        self.weapons_free_timer_max = C.CASCADE_WEAPONS_FREE_TIMER
        self.range = C.LASER_BEAM_WEAPONS_RANGE
        self.damage = C.LASER_BEAM_DAMAGE
        self.cascade_radius = C.CASCADE_RADIUS
        self.cascade_multiplier = C.CASCADE_MULTIPLIER
        self.upgrade_paths = [
            {"type": "damage",         "label": "Damage +15%",         "is_generic": True},
            {"type": "fire_rate",      "label": "Fire Rate +12%",      "is_generic": True},
            {"type": "cascade_radius", "label": "Cascade Radius +20%", "is_generic": False},
        ]

    def apply_upgrade(self, upgrade_type, tier):
        if upgrade_type == "damage":
            self.damage = int(self.damage * (1 + C.SHOP_DAMAGE_INCREASE))
        elif upgrade_type == "cascade_radius":
            self.cascade_radius *= (1 + C.SHOP_CASCADE_RADIUS_INCREASE)
        else:
            super().apply_upgrade(upgrade_type, tier)

    def fire(self, owner):
        if owner.target is None:
            return 0
        target = owner.target
        target_pos = pygame.Vector2(target.position)
        overkill_damage = 0
        target_element = getattr(target, 'element', None)
        mult = get_damage_multiplier(owner.element, target_element)
        effective_damage = max(1, int(self.damage * mult))
        if effective_damage > target.health:
            overkill_damage = effective_damage - target.health
        forward = owner.get_forward_vector()
        spawn_pos = owner.position + forward * (owner.radius + C.LASER_BEAM_PLATFORM_OFFSET)
        projectile = LaserBeam(spawn_pos.x, spawn_pos.y, target,
            self.damage, stat_source=owner.stat_source,
            combat_stats=owner.game.combat_stats,
            extra_abilities=owner.extra_abilities,
            asteroids=owner.asteroids, element=owner.element)
        if projectile.xp and owner.game and hasattr(owner.game, 'experience'):
            owner.game.experience.add_xp(projectile.xp)
        score = projectile.score
        if overkill_damage > 0 and not target.alive():
            cascade_damage = int(overkill_damage * self.cascade_multiplier)
            game = getattr(owner, 'game', None)
            all_targets = list(owner.asteroids) if owner.asteroids else []
            if game and hasattr(game, 'enemies'):
                all_targets.extend(game.enemies)
            aoe = RocketHitAOE(impact_position=target_pos, targets=all_targets,
                radius=self.cascade_radius, damage=cascade_damage)
            aoe.stat_source = owner.stat_source
            aoe.combat_stats = owner.game.combat_stats
            aoe_score, aoe_xp = aoe.apply()
            if aoe_xp and hasattr(owner.game, 'experience'):
                owner.game.experience.add_xp(aoe_xp)
            score += aoe_score
        self.weapons_free_timer = self.weapons_free_timer_max
        return score

    def get_charge_ratio(self):
        if self.weapons_free_timer_max <= 0:
            return 1
        return 1 - (self.weapons_free_timer / self.weapons_free_timer_max)

    def get_platform_color(self):
        charge_colors = [C.DARK_RED, C.RED, C.ORANGE, C.GOLD, C.YELLOW]
        ratio = self.get_charge_ratio()
        if ratio >= 1:
            return charge_colors[-1]
        scaled = ratio * (len(charge_colors) - 1)
        index = int(scaled)
        local_t = scaled - index
        c1, c2 = charge_colors[index], charge_colors[min(index + 1, len(charge_colors) - 1)]
        return tuple(int(s + (e - s) * local_t) for s, e in zip(c1, c2))

    def draw(self, screen, owner):
        platform_color = self.get_platform_color()
        offset = C.LASER_BEAM_PLATFORM_OFFSET
        length = C.LASER_BEAM_PLATFORM_LENGTH
        width = C.LASER_BEAM_PLATFORM_WIDTH
        surface_size = (owner.radius + offset + length) * 2
        surf = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        cx = surface_size // 2
        cy = surface_size // 2
        emitter_y = cy - (owner.radius + offset)
        points = [(cx, emitter_y - length),
            (cx - width // 2, emitter_y),
            (cx + width // 2, emitter_y)]
        pygame.draw.polygon(surf, platform_color, points)
        rotated = pygame.transform.rotate(surf, -owner.rotation)
        screen.blit(rotated, rotated.get_rect(center=(owner.position.x, owner.position.y)))


class FinisherPlatform(WeaponsPlatform):
    variant_name = "Finisher"
    variant_description = "Deals bonus damage proportional to target's missing HP. Devastating near death."
    banish_ability = "overkill"

    def __init__(self):
        super().__init__()
        self.weapons_free_timer_max = C.FINISHER_WEAPONS_FREE_TIMER
        self.range = C.FINISHER_WEAPONS_RANGE
        self.damage = C.FINISHER_BASE_DAMAGE
        self.bonus_multiplier = C.FINISHER_BONUS_MULTIPLIER
        self.upgrade_paths = [
            {"type": "damage",       "label": "Damage +15%",   "is_generic": True},
            {"type": "fire_rate",    "label": "Fire Rate +12%", "is_generic": True},
            {"type": "finisher_amp", "label": "Finisher Amp +25%", "is_generic": False},
        ]

    def apply_upgrade(self, upgrade_type, tier):
        if upgrade_type == "damage":
            self.damage = int(self.damage * (1 + C.SHOP_DAMAGE_INCREASE))
        elif upgrade_type == "finisher_amp":
            self.bonus_multiplier += C.SHOP_FINISHER_AMP_INCREASE
        else:
            super().apply_upgrade(upgrade_type, tier)

    def fire(self, owner):
        if owner.target is None:
            return 0
        target = owner.target
        max_health = getattr(target, 'max_health', getattr(target, 'full_health', 0))
        missing_ratio = 0.0
        if max_health > 0:
            missing_ratio = max(0.0, 1.0 - target.health / max_health)
        effective_damage = int(self.damage * (1.0 + missing_ratio * self.bonus_multiplier))
        forward = owner.get_forward_vector()
        spawn_pos = owner.position + forward * (owner.radius + C.LASER_BEAM_PLATFORM_OFFSET)
        projectile = LaserBeam(spawn_pos.x, spawn_pos.y, target,
            effective_damage, stat_source=owner.stat_source,
            combat_stats=owner.game.combat_stats,
            extra_abilities=owner.extra_abilities,
            asteroids=owner.asteroids, element=owner.element)
        if projectile.xp and owner.game and hasattr(owner.game, 'experience'):
            owner.game.experience.add_xp(projectile.xp)
        self.weapons_free_timer = self.weapons_free_timer_max
        return projectile.score

    def get_charge_ratio(self):
        if self.weapons_free_timer_max <= 0:
            return 1
        return 1 - (self.weapons_free_timer / self.weapons_free_timer_max)

    def get_platform_color(self):
        charge_colors = [C.DARK_GREEN, C.FOREST_GREEN, C.LIME_GREEN, C.NEON_GREEN, C.SPRING_GREEN]
        ratio = self.get_charge_ratio()
        if ratio >= 1:
            return charge_colors[-1]
        scaled = ratio * (len(charge_colors) - 1)
        index = int(scaled)
        local_t = scaled - index
        c1, c2 = charge_colors[index], charge_colors[min(index + 1, len(charge_colors) - 1)]
        return tuple(int(s + (e - s) * local_t) for s, e in zip(c1, c2))

    def draw(self, screen, owner):
        platform_color = self.get_platform_color()
        offset = C.LASER_BEAM_PLATFORM_OFFSET
        length = C.LASER_BEAM_PLATFORM_LENGTH
        width = C.LASER_BEAM_PLATFORM_WIDTH
        surface_size = (owner.radius + offset + length) * 2
        surf = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        cx = surface_size // 2
        cy = surface_size // 2
        emitter_y = cy - (owner.radius + offset)
        points = [(cx, emitter_y - length),
            (cx - width // 2, emitter_y),
            (cx + width // 2, emitter_y)]
        pygame.draw.polygon(surf, platform_color, points)
        rotated = pygame.transform.rotate(surf, -owner.rotation)
        screen.blit(rotated, rotated.get_rect(center=(owner.position.x, owner.position.y)))


class OverchargePlatform(WeaponsPlatform):
    variant_name = "Overcharge"
    variant_description = "Charges slowly, then fires a single devastating burst. Patience is the mechanic."
    banish_ability = "overkill"

    def __init__(self):
        super().__init__()
        self.weapons_free_timer_max = C.OVERCHARGE_WEAPONS_FREE_TIMER
        self.range = C.OVERCHARGE_WEAPONS_RANGE
        self.damage = C.OVERCHARGE_DAMAGE
        self.upgrade_paths = [
            {"type": "damage",    "label": "Damage +15%",    "is_generic": True},
            {"type": "fire_rate", "label": "Fire Rate +12%", "is_generic": True},
        ]

    def apply_upgrade(self, upgrade_type, tier):
        if upgrade_type == "damage":
            self.damage = int(self.damage * (1 + C.SHOP_DAMAGE_INCREASE))
        else:
            super().apply_upgrade(upgrade_type, tier)

    def fire(self, owner):
        if owner.target is None:
            return 0
        forward = owner.get_forward_vector()
        spawn_pos = owner.position + forward * (owner.radius + C.LASER_BEAM_PLATFORM_OFFSET)
        projectile = LaserBeam(spawn_pos.x, spawn_pos.y, owner.target,
            self.damage, stat_source=owner.stat_source,
            combat_stats=owner.game.combat_stats,
            extra_abilities=owner.extra_abilities,
            asteroids=owner.asteroids, element=owner.element)
        if projectile.xp and owner.game and hasattr(owner.game, 'experience'):
            owner.game.experience.add_xp(projectile.xp)
        self.weapons_free_timer = self.weapons_free_timer_max
        return projectile.score

    def get_charge_ratio(self):
        if self.weapons_free_timer_max <= 0:
            return 1
        return 1 - (self.weapons_free_timer / self.weapons_free_timer_max)

    def get_platform_color(self):
        charge_colors = [C.MIDNIGHT_BLUE, C.INDIGO, C.PURPLE, C.MAGENTA, C.HOT_PINK, C.DEEP_PINK]
        ratio = self.get_charge_ratio()
        if ratio >= 1:
            return charge_colors[-1]
        scaled = ratio * (len(charge_colors) - 1)
        index = int(scaled)
        local_t = scaled - index
        c1, c2 = charge_colors[index], charge_colors[min(index + 1, len(charge_colors) - 1)]
        return tuple(int(s + (e - s) * local_t) for s, e in zip(c1, c2))

    def draw(self, screen, owner):
        platform_color = self.get_platform_color()
        offset = C.LASER_BEAM_PLATFORM_OFFSET
        length = C.LASER_BEAM_PLATFORM_LENGTH + 6
        width = C.LASER_BEAM_PLATFORM_WIDTH + 4
        surface_size = (owner.radius + offset + length) * 2
        surf = pygame.Surface((surface_size, surface_size), pygame.SRCALPHA)
        cx = surface_size // 2
        cy = surface_size // 2
        emitter_y = cy - (owner.radius + offset)
        points = [(cx, emitter_y - length),
            (cx - width // 2, emitter_y),
            (cx + width // 2, emitter_y)]
        pygame.draw.polygon(surf, platform_color, points)
        rotated = pygame.transform.rotate(surf, -owner.rotation)
        screen.blit(rotated, rotated.get_rect(center=(owner.position.x, owner.position.y)))


class ExplosivePlatform(WeaponsPlatform):
    variant_name = "Rocket"
    variant_description = "Self-propelled rocket. Explodes on impact with area-of-effect blast."
    banish_ability = "explosion"

    def __init__(self):
        super().__init__()
        self.weapons_free_timer_max = C.EXPLOSIVE_DRONE_WEAPONS_FREE_TIMER
        self.range = C.EXPLOSIVE_DRONE_WEAPONS_RANGE
        self.projectile_speed = C.EXPLOSIVE_DRONE_PROJECTILE_SPEED
        self.launch_animation_timer = 0.0
        self.launch_animation_duration = C.EXPLOSIVE_DRONE_DOOR_ANIMATION_TIME
        self.upgrade_paths = [
            {"type": "damage",    "label": "Damage +15%",    "is_generic": True},
            {"type": "fire_rate", "label": "Fire Rate +12%", "is_generic": True},
        ]

    def tick(self, dt):
        super().tick(dt)
        self.launch_animation_timer = max(0.0, self.launch_animation_timer - dt)

    def fire(self, owner):
        forward = owner.get_forward_vector()
        spawn_pos = owner.position + forward * (owner.radius + 4)
        game = getattr(owner, 'game', None)
        enemies = getattr(game, 'enemies', None) if game else None
        is_enemy = getattr(owner, 'stat_source', None) == C.ENEMY
        player = getattr(game, 'player', None) if (is_enemy and game) else None
        projectile = Rocket(spawn_pos.x, spawn_pos.y, owner.asteroids, enemies=enemies, player=player)
        projectile.damage = int(C.ROCKET_PROJECTILE_DAMAGE * self.damage_multiplier)
        projectile.velocity = forward * self.projectile_speed
        projectile.stat_source = owner.stat_source
        projectile.combat_stats = owner.game.combat_stats
        projectile.extra_abilities = set(owner.extra_abilities)
        projectile.element = owner.element
        self.launch_animation_timer = self.launch_animation_duration
        self.weapons_free_timer = self.weapons_free_timer_max
        return 0

    def draw(self, screen, owner):
        open_ratio = 0.0
        if self.launch_animation_duration > 0:
            open_ratio = self.launch_animation_timer / self.launch_animation_duration
        surf_size = int(owner.radius * 6)
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        c = surf_size // 2
        door_half_w = int(owner.radius * 0.65)
        door_h = int(owner.radius * 0.62)
        slide = int(door_half_w * open_ratio)
        if open_ratio > 0.05:
            silo_r = max(2, int(owner.radius * 0.32))
            alpha = min(255, int(255 * open_ratio))
            pygame.draw.circle(surf, (20, 20, 20, alpha), (c, c), silo_r)
        left_rect  = pygame.Rect(c - door_half_w - slide, c - door_h // 2, door_half_w, door_h)
        right_rect = pygame.Rect(c + slide,               c - door_h // 2, door_half_w, door_h)
        pygame.draw.rect(surf, C.GRAY,   left_rect)
        pygame.draw.rect(surf, C.GRAY,   right_rect)
        pygame.draw.rect(surf, C.SILVER, left_rect,  1)
        pygame.draw.rect(surf, C.SILVER, right_rect, 1)
        if open_ratio < 0.15:
            fade = int(160 * (1 - open_ratio / 0.15))
            pygame.draw.line(surf, (20, 20, 20, fade),
                (c, c - door_h // 2), (c, c + door_h // 2), 1)
        rotated = pygame.transform.rotate(surf, -owner.rotation)
        screen.blit(rotated, rotated.get_rect(center=(int(owner.position.x), int(owner.position.y))))


class SentinelPlatform(WeaponsPlatform):
    variant_name = "Shield"
    variant_description = "Creates and repairs a damage-absorbing shield around the player."
    banish_ability = None

    def __init__(self):
        super().__init__()
        self.range = 0.0
        self.weapons_free_timer_max = 0.0
        self.upgrade_paths = [
            {"type": "effect_strength",   "label": "Shield Health +2",    "is_generic": True},
            {"type": "cooldown_reduction","label": "Repair Speed +15%",   "is_generic": True},
        ]

    def sentinel_update(self, drone, dt):
        drone.shield_create_timer = max(0, drone.shield_create_timer - dt)
        drone.shield_repair_timer = max(0, drone.shield_repair_timer - dt)
        if not drone.player_shield:
            drone.player.shield = False
            if drone.shield_create_timer == 0:
                drone.player_shield = Shield(owner=drone.player, source=drone,
                    max_health=drone.shield_max_health)
                drone.player.shield = True
                drone.shield_create_timer = C.SENTINEL_DRONE_SHIELD_CREATE_TIMER
        else:
            drone.player.shield = True
            if not drone.player_shield.alive():
                drone.player_shield = None
                drone.player.shield = False
        if drone.player_shield:
            if drone.player_shield.health < drone.player_shield.max_health:
                if drone.shield_repair_timer == 0:
                    before = drone.player_shield.health
                    drone.player_shield.health = min(drone.player_shield.max_health,
                        drone.player_shield.health + 1)
                    repaired = drone.player_shield.health - before
                    if repaired > 0:
                        drone.player.game.combat_stats.add_repaired(
                            drone.stat_source, repaired)
                    drone.shield_repair_timer = drone.shield_repair_timer_base

    def apply_upgrade(self, upgrade_type, tier):
        pass

    def can_fire(self):
        return False

    def fire(self, owner):
        return 0

    def draw(self, screen, owner):
        direction = owner.player.position - owner.position
        if direction.length_squared() == 0:
            return
        angle = pygame.Vector2(0, -1).angle_to(direction)
        r = owner.radius
        n = 14
        fang_len   = int(r * 1.5)
        base_sep   = int(r * 0.72)
        tip_inward = int(r * 0.55)
        base_w     = max(2, int(r * 0.22))
        tip_w      = max(1, int(r * 0.07))
        surf_size  = int(r * 8)
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        c = surf_size // 2
        root_y = c - r
        for side in (-1, 1):
            root_cx = c + side * base_sep
            tip_cx  = c + side * (base_sep - tip_inward)
            outer_pts = []
            inner_pts = []
            for i in range(n + 1):
                t = i / n
                y = root_y - int(t * fang_len)
                spine_x = root_cx + (tip_cx - root_cx) * (t ** 0.7)
                hw = base_w + (tip_w - base_w) * t
                bow = side * hw * (1.0 + 0.9 * math.sin(t * math.pi))
                outer_pts.append((spine_x + bow, y))
                inner_pts.append((spine_x - bow * 0.35, y))
            fang_poly = outer_pts + list(reversed(inner_pts))
            pygame.draw.polygon(surf, C.SENTINEL_DRONE_WEAPONS_PLATFORM_COLOR, fang_poly)
            pygame.draw.polygon(surf, C.LIGHT_GRAY, fang_poly, 1)
        rotated = pygame.transform.rotate(surf, -angle)
        screen.blit(rotated, rotated.get_rect(center=(int(owner.position.x), int(owner.position.y))))


class BouncerPlatform(WeaponsPlatform):
    variant_name = "Bouncer"
    variant_description = "Rounds reflect off targets and keep moving. Each bounce hits a new enemy."
    banish_ability = "impact"

    def __init__(self):
        super().__init__()
        self.weapons_free_timer_max = C.BOUNCER_WEAPONS_FREE_TIMER
        self.range = C.BOUNCER_WEAPONS_RANGE
        self.projectile_speed = C.BOUNCER_SPEED
        self.bounce_count = C.BOUNCER_MAX_BOUNCES
        self.upgrade_paths = [
            {"type": "damage",           "label": "Damage +15%",     "is_generic": True},
            {"type": "fire_rate",        "label": "Fire Rate +12%",  "is_generic": True},
            {"type": "bounce_count",     "label": "Bounce +1",       "is_generic": False},
            {"type": "projectile_speed", "label": "Proj Speed +15%", "is_generic": False},
        ]

    def apply_upgrade(self, upgrade_type, tier):
        if upgrade_type == "bounce_count":
            self.bounce_count += C.SHOP_BOUNCE_COUNT_INCREASE
        else:
            super().apply_upgrade(upgrade_type, tier)

    def fire(self, owner):
        spawn_pos = self._muzzle_position(owner)
        forward = owner.get_forward_vector()
        projectile = Bouncer(spawn_pos.x, spawn_pos.y)
        projectile.bounce_count = self.bounce_count
        projectile.damage = int(C.BOUNCER_DAMAGE * self.damage_multiplier)
        projectile.velocity = forward * self.projectile_speed
        projectile.stat_source = owner.stat_source
        projectile.combat_stats = owner.game.combat_stats
        projectile.extra_abilities = set(owner.extra_abilities)
        projectile.asteroids = owner.asteroids
        projectile.element = owner.element
        if MuzzleFlareVE.containers:
            MuzzleFlareVE(spawn_pos.x, spawn_pos.y, size=5)
        self.weapons_free_timer = self.weapons_free_timer_max
        return 0

    def draw(self, screen, owner):
        self._draw_kinetic_barrel(screen, owner)


class BuckshotPlatform(WeaponsPlatform):
    variant_name = "Buckshot"
    variant_description = "Fires a spread of pellets. Devastating at close range."
    banish_ability = "impact"

    def __init__(self):
        super().__init__()
        self.weapons_free_timer_max = C.BUCKSHOT_WEAPONS_FREE_TIMER
        self.range = C.BUCKSHOT_WEAPONS_RANGE
        self.projectile_speed = C.BUCKSHOT_PELLET_SPEED
        self.pellet_count = C.BUCKSHOT_PELLET_COUNT
        self.cone_half_angle = C.BUCKSHOT_CONE_HALF_ANGLE
        self.upgrade_paths = [
            {"type": "damage",       "label": "Damage +15%",        "is_generic": True},
            {"type": "fire_rate",    "label": "Fire Rate +12%",     "is_generic": True},
            {"type": "pellet_count", "label": "Pellet Count +1",    "is_generic": False},
            {"type": "cone_tighten", "label": "Tighten Cone 20%",   "is_generic": False},
        ]

    def apply_upgrade(self, upgrade_type, tier):
        if upgrade_type == "pellet_count":
            self.pellet_count += C.SHOP_PELLET_COUNT_INCREASE
        elif upgrade_type == "cone_tighten":
            self.cone_half_angle = max(5, self.cone_half_angle * C.SHOP_CONE_TIGHTEN)
        else:
            super().apply_upgrade(upgrade_type, tier)

    def fire(self, owner):
        spawn_pos = self._muzzle_position(owner)
        forward = owner.get_forward_vector()
        for i in range(self.pellet_count):
            if self.pellet_count > 1:
                t = i / (self.pellet_count - 1)
                angle_offset = -self.cone_half_angle + t * 2 * self.cone_half_angle
            else:
                angle_offset = 0
            direction = forward.rotate(angle_offset)
            projectile = Kinetic(spawn_pos.x, spawn_pos.y)
            projectile.radius = C.BUCKSHOT_PELLET_RADIUS
            projectile.damage = int(C.BUCKSHOT_PELLET_DAMAGE * self.damage_multiplier)
            projectile.velocity = direction * self.projectile_speed
            projectile.stat_source = owner.stat_source
            projectile.combat_stats = owner.game.combat_stats
            projectile.extra_abilities = set(owner.extra_abilities)
            projectile.asteroids = owner.asteroids
            projectile.element = owner.element
        if MuzzleFlareVE.containers:
            MuzzleFlareVE(spawn_pos.x, spawn_pos.y, size=7)
        self.weapons_free_timer = self.weapons_free_timer_max
        return 0

    def draw(self, screen, owner):
        self._draw_kinetic_barrel(screen, owner, muzzle_scale=0.45, base_scale=0.80, height_scale=0.65)


class CannonballPlatform(WeaponsPlatform):
    variant_name = "Cannonball"
    variant_description = "Slow, massive rounds. Enormous knockback on impact."
    banish_ability = "impact"

    def __init__(self):
        super().__init__()
        self.weapons_free_timer_max = C.CANNONBALL_WEAPONS_FREE_TIMER
        self.range = C.CANNONBALL_WEAPONS_RANGE
        self.projectile_speed = C.CANNONBALL_SPEED
        self.kinetic_mass = C.CANNONBALL_WEIGHT
        self.upgrade_paths = [
            {"type": "damage",          "label": "Damage +15%",       "is_generic": True},
            {"type": "fire_rate",       "label": "Fire Rate +12%",    "is_generic": True},
            {"type": "kinetic_mass",    "label": "Kinetic Mass +60%", "is_generic": False},
            {"type": "projectile_speed","label": "Proj Speed +15%",   "is_generic": False},
        ]

    def apply_upgrade(self, upgrade_type, tier):
        if upgrade_type == "kinetic_mass":
            self.kinetic_mass *= C.SHOP_KINETIC_MASS_INCREASE
        else:
            super().apply_upgrade(upgrade_type, tier)

    def fire(self, owner):
        spawn_pos = self._muzzle_position(owner)
        forward = owner.get_forward_vector()
        projectile = Cannonball(spawn_pos.x, spawn_pos.y)
        projectile.weight = self.kinetic_mass
        projectile.damage = int(C.CANNONBALL_DAMAGE * self.damage_multiplier)
        projectile.velocity = forward * self.projectile_speed
        projectile.stat_source = owner.stat_source
        projectile.combat_stats = owner.game.combat_stats
        projectile.extra_abilities = set(owner.extra_abilities)
        projectile.asteroids = owner.asteroids
        projectile.element = owner.element
        if MuzzleFlareVE.containers:
            MuzzleFlareVE(spawn_pos.x, spawn_pos.y, size=8)
        self.weapons_free_timer = self.weapons_free_timer_max
        return 0

    def draw(self, screen, owner):
        self._draw_kinetic_barrel(screen, owner, muzzle_scale=0.60, base_scale=0.80, height_scale=0.55)


class ContagionPlatform(WeaponsPlatform):
    variant_name = "Contagion"
    variant_description = "Infects targets with a DoT that spreads to nearby enemies on death."
    banish_ability = "contagion"

    def __init__(self):
        super().__init__()
        self.weapons_free_timer_max = C.CONTAGION_WEAPONS_FREE_TIMER
        self.range = C.CONTAGION_WEAPONS_RANGE
        self.projectile_speed = C.DEBUFF_DRONE_PROJECTILE_SPEED
        self.contagion_duration = C.CONTAGION_DURATION
        self.contagion_spread_radius = C.CONTAGION_SPREAD_RADIUS
        self.upgrade_paths = [
            {"type": "damage",             "label": "Damage +15%",             "is_generic": True},
            {"type": "fire_rate",          "label": "Fire Rate +12%",          "is_generic": True},
            {"type": "contagion_duration", "label": "Contagion Duration +15%", "is_generic": False},
            {"type": "contagion_spread",   "label": "Spread Radius +20%",      "is_generic": False},
        ]

    def apply_upgrade(self, upgrade_type, tier):
        if upgrade_type == "contagion_duration":
            self.contagion_duration *= (1 + C.SHOP_DEBUFF_DURATION_INCREASE)
        elif upgrade_type == "contagion_spread":
            self.contagion_spread_radius *= (1 + C.SHOP_CONTAGION_SPREAD_INCREASE)
        else:
            super().apply_upgrade(upgrade_type, tier)

    def _muzzle_position(self, owner):
        forward = owner.get_forward_vector()
        platform_length = owner.radius + C.DEBUFF_DRONE_PLATFORM_LENGTH_OFFSET
        return owner.position + forward * platform_length

    def fire(self, owner):
        spawn_pos = self._muzzle_position(owner)
        forward = owner.get_forward_vector()
        game = getattr(owner, 'game', None)
        nearby_targets = []
        if owner.asteroids:
            nearby_targets.extend(owner.asteroids)
        if game and hasattr(game, 'enemies'):
            nearby_targets.extend(game.enemies)
        projectile = ContagionPlasma(spawn_pos.x, spawn_pos.y)
        projectile.contagion_duration = self.contagion_duration
        projectile.spread_radius = self.contagion_spread_radius
        projectile.damage = int(C.CONTAGION_PROJECTILE_DAMAGE * self.damage_multiplier)
        projectile.velocity = forward * self.projectile_speed
        projectile.stat_source = owner.stat_source
        projectile.combat_stats = owner.game.combat_stats
        projectile.extra_abilities = set(owner.extra_abilities)
        projectile.asteroids = owner.asteroids
        projectile.enemies = getattr(game, 'enemies', None)
        projectile.element = owner.element
        self.weapons_free_timer = self.weapons_free_timer_max
        return 0

    def draw(self, screen, owner):
        platform_length = owner.radius + C.DEBUFF_DRONE_PLATFORM_LENGTH_OFFSET
        surf_size = int(platform_length * 3)
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        c = surf_size // 2
        bw = C.DEBUFF_DRONE_PLATFORM_WIDTH - 2
        bh = int(platform_length)
        barrel_rect = pygame.Rect(c - bw // 2, c - bh, bw, bh)
        pygame.draw.rect(surf, C.NEON_GREEN, barrel_rect, 2)
        rotated = pygame.transform.rotate(surf, -owner.rotation)
        screen.blit(rotated, rotated.get_rect(center=(int(owner.position.x), int(owner.position.y))))


class CorrodePlatform(WeaponsPlatform):
    variant_name = "Corrode"
    variant_description = "Corrodes target armor, amplifying all damage they take for a duration."
    banish_ability = "corrode"

    def __init__(self):
        super().__init__()
        self.weapons_free_timer_max = C.CORRODE_WEAPONS_FREE_TIMER
        self.range = C.CORRODE_WEAPONS_RANGE
        self.projectile_speed = C.DEBUFF_DRONE_PROJECTILE_SPEED
        self.corrode_amplification = C.CORRODE_AMPLIFICATION
        self.corrode_duration = C.CORRODE_DURATION
        self.upgrade_paths = [
            {"type": "damage",               "label": "Damage +15%",           "is_generic": True},
            {"type": "fire_rate",            "label": "Fire Rate +12%",         "is_generic": True},
            {"type": "corrode_amplification","label": "Corrode Amp +5%",        "is_generic": False},
            {"type": "corrode_duration",     "label": "Corrode Duration +15%",  "is_generic": False},
        ]

    def apply_upgrade(self, upgrade_type, tier):
        if upgrade_type == "corrode_amplification":
            self.corrode_amplification += C.SHOP_CORRODE_AMPLIFICATION_INCREASE
        elif upgrade_type == "corrode_duration":
            self.corrode_duration *= (1 + C.SHOP_DEBUFF_DURATION_INCREASE)
        else:
            super().apply_upgrade(upgrade_type, tier)

    def _muzzle_position(self, owner):
        forward = owner.get_forward_vector()
        platform_length = owner.radius + C.DEBUFF_DRONE_PLATFORM_LENGTH_OFFSET
        return owner.position + forward * platform_length

    def fire(self, owner):
        spawn_pos = self._muzzle_position(owner)
        forward = owner.get_forward_vector()
        projectile = CorrodePlasma(spawn_pos.x, spawn_pos.y)
        projectile.corrode_amplification = self.corrode_amplification
        projectile.corrode_duration = self.corrode_duration
        projectile.damage = int(C.CORRODE_PROJECTILE_DAMAGE * self.damage_multiplier)
        projectile.velocity = forward * self.projectile_speed
        projectile.stat_source = owner.stat_source
        projectile.combat_stats = owner.game.combat_stats
        projectile.extra_abilities = set(owner.extra_abilities)
        projectile.asteroids = owner.asteroids
        projectile.element = owner.element
        self.weapons_free_timer = self.weapons_free_timer_max
        return 0

    def draw(self, screen, owner):
        platform_length = owner.radius + C.DEBUFF_DRONE_PLATFORM_LENGTH_OFFSET
        surf_size = int(platform_length * 3)
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        c = surf_size // 2
        bw = C.DEBUFF_DRONE_PLATFORM_WIDTH
        bh = int(platform_length)
        barrel_rect = pygame.Rect(c - bw // 2, c - bh, bw, bh)
        pygame.draw.rect(surf, C.SILVER, barrel_rect)
        pygame.draw.rect(surf, C.KHAKI, barrel_rect, 2)
        rotated = pygame.transform.rotate(surf, -owner.rotation)
        screen.blit(rotated, rotated.get_rect(center=(int(owner.position.x), int(owner.position.y))))


class MarkPlatform(WeaponsPlatform):
    variant_name = "Mark"
    variant_description = "Tags targets so the next hit from any source deals amplified damage."
    banish_ability = "mark"

    def __init__(self):
        super().__init__()
        self.weapons_free_timer_max = C.MARK_WEAPONS_FREE_TIMER
        self.range = C.MARK_WEAPONS_RANGE
        self.projectile_speed = C.DEBUFF_DRONE_PROJECTILE_SPEED
        self.mark_amplification = C.MARK_AMPLIFICATION
        self.mark_duration = C.MARK_DURATION
        self.upgrade_paths = [
            {"type": "damage",            "label": "Damage +15%",        "is_generic": True},
            {"type": "fire_rate",         "label": "Fire Rate +12%",     "is_generic": True},
            {"type": "mark_amplification","label": "Mark Amp +25%",      "is_generic": False},
            {"type": "mark_duration",     "label": "Mark Duration +15%", "is_generic": False},
        ]

    def apply_upgrade(self, upgrade_type, tier):
        if upgrade_type == "mark_amplification":
            self.mark_amplification += C.SHOP_MARK_AMPLIFICATION_INCREASE
        elif upgrade_type == "mark_duration":
            self.mark_duration *= (1 + C.SHOP_DEBUFF_DURATION_INCREASE)
        else:
            super().apply_upgrade(upgrade_type, tier)

    def _muzzle_position(self, owner):
        forward = owner.get_forward_vector()
        platform_length = owner.radius + C.DEBUFF_DRONE_PLATFORM_LENGTH_OFFSET
        return owner.position + forward * platform_length

    def fire(self, owner):
        spawn_pos = self._muzzle_position(owner)
        forward = owner.get_forward_vector()
        projectile = MarkPlasma(spawn_pos.x, spawn_pos.y)
        projectile.mark_amplification = self.mark_amplification
        projectile.mark_duration = self.mark_duration
        projectile.damage = int(C.MARK_PROJECTILE_DAMAGE * self.damage_multiplier)
        projectile.velocity = forward * self.projectile_speed
        projectile.stat_source = owner.stat_source
        projectile.combat_stats = owner.game.combat_stats
        projectile.extra_abilities = set(owner.extra_abilities)
        projectile.asteroids = owner.asteroids
        projectile.element = owner.element
        self.weapons_free_timer = self.weapons_free_timer_max
        return 0

    def draw(self, screen, owner):
        platform_length = owner.radius + C.DEBUFF_DRONE_PLATFORM_LENGTH_OFFSET
        surf_size = int(platform_length * 3)
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        c = surf_size // 2
        bw = C.DEBUFF_DRONE_PLATFORM_WIDTH
        bh = int(platform_length)
        barrel_rect = pygame.Rect(c - bw // 2, c - bh, bw, bh)
        pygame.draw.rect(surf, C.SILVER, barrel_rect)
        pygame.draw.rect(surf, C.PLUM, barrel_rect, 2)
        rotated = pygame.transform.rotate(surf, -owner.rotation)
        screen.blit(rotated, rotated.get_rect(center=(int(owner.position.x), int(owner.position.y))))


class SlowPlatform(WeaponsPlatform):
    variant_name = "Slow"
    variant_description = "Fires bolts that reduce enemy movement speed for a duration."
    banish_ability = "slow"

    def __init__(self):
        super().__init__()
        self.weapons_free_timer_max = C.SLOW_WEAPONS_FREE_TIMER
        self.range = C.SLOW_WEAPONS_RANGE
        self.projectile_speed = C.DEBUFF_DRONE_PROJECTILE_SPEED
        self.slow_factor = C.SLOW_FACTOR
        self.slow_duration = C.SLOW_DURATION
        self.upgrade_paths = [
            {"type": "damage",      "label": "Damage +15%",          "is_generic": True},
            {"type": "fire_rate",   "label": "Fire Rate +12%",       "is_generic": True},
            {"type": "slow_duration","label": "Slow Duration +15%",  "is_generic": False},
            {"type": "slow_potency", "label": "Slow Potency +5%",    "is_generic": False},
        ]

    def apply_upgrade(self, upgrade_type, tier):
        if upgrade_type == "slow_duration":
            self.slow_duration *= (1 + C.SHOP_DEBUFF_DURATION_INCREASE)
        elif upgrade_type == "slow_potency":
            self.slow_factor = min(0.9, self.slow_factor + C.SHOP_SLOW_POTENCY_INCREASE)
        else:
            super().apply_upgrade(upgrade_type, tier)

    def _muzzle_position(self, owner):
        forward = owner.get_forward_vector()
        platform_length = owner.radius + C.DEBUFF_DRONE_PLATFORM_LENGTH_OFFSET
        return owner.position + forward * platform_length

    def fire(self, owner):
        spawn_pos = self._muzzle_position(owner)
        forward = owner.get_forward_vector()
        projectile = SlowPlasma(spawn_pos.x, spawn_pos.y)
        projectile.slow_factor = self.slow_factor
        projectile.slow_duration = self.slow_duration
        projectile.damage = int(C.SLOW_PROJECTILE_DAMAGE * self.damage_multiplier)
        projectile.velocity = forward * self.projectile_speed
        projectile.stat_source = owner.stat_source
        projectile.combat_stats = owner.game.combat_stats
        projectile.extra_abilities = set(owner.extra_abilities)
        projectile.asteroids = owner.asteroids
        projectile.element = owner.element
        self.weapons_free_timer = self.weapons_free_timer_max
        return 0

    def draw(self, screen, owner):
        platform_length = owner.radius + C.DEBUFF_DRONE_PLATFORM_LENGTH_OFFSET
        surf_size = int(platform_length * 3)
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        c = surf_size // 2
        bw = C.DEBUFF_DRONE_PLATFORM_WIDTH
        bh = int(platform_length)
        barrel_rect = pygame.Rect(c - bw // 2, c - bh, bw, bh)
        pygame.draw.rect(surf, C.SILVER, barrel_rect)
        pygame.draw.rect(surf, C.LIGHT_BLUE, barrel_rect, 2)
        rotated = pygame.transform.rotate(surf, -owner.rotation)
        screen.blit(rotated, rotated.get_rect(center=(int(owner.position.x), int(owner.position.y))))


class NeedleSlugPlatform(WeaponsPlatform):
    variant_name = "Needle Slug"
    variant_description = "Thin, fast rounds that pierce through multiple targets."
    banish_ability = "impact"

    def __init__(self):
        super().__init__()
        self.weapons_free_timer_max = C.NEEDLE_SLUG_WEAPONS_FREE_TIMER
        self.range = C.NEEDLE_SLUG_WEAPONS_RANGE
        self.projectile_speed = C.NEEDLE_SLUG_SPEED
        self.pierce_count = C.NEEDLE_SLUG_MAX_PIERCES
        self.upgrade_paths = [
            {"type": "damage",           "label": "Damage +15%",     "is_generic": True},
            {"type": "fire_rate",        "label": "Fire Rate +12%",  "is_generic": True},
            {"type": "pierce_count",     "label": "Pierce +1",       "is_generic": False},
            {"type": "projectile_speed", "label": "Proj Speed +15%", "is_generic": False},
        ]

    def apply_upgrade(self, upgrade_type, tier):
        if upgrade_type == "pierce_count":
            self.pierce_count += C.SHOP_PIERCE_COUNT_INCREASE
        else:
            super().apply_upgrade(upgrade_type, tier)

    def fire(self, owner):
        spawn_pos = self._muzzle_position(owner)
        forward = owner.get_forward_vector()
        projectile = NeedleSlug(spawn_pos.x, spawn_pos.y)
        projectile.pierce_count = self.pierce_count
        projectile.damage = int(C.NEEDLE_SLUG_DAMAGE * self.damage_multiplier)
        projectile.velocity = forward * self.projectile_speed
        projectile.stat_source = owner.stat_source
        projectile.combat_stats = owner.game.combat_stats
        projectile.extra_abilities = set(owner.extra_abilities)
        projectile.asteroids = owner.asteroids
        projectile.element = owner.element
        if MuzzleFlareVE.containers:
            MuzzleFlareVE(spawn_pos.x, spawn_pos.y, size=3)
        self.weapons_free_timer = self.weapons_free_timer_max
        return 0

    def draw(self, screen, owner):
        self._draw_kinetic_barrel(screen, owner, muzzle_scale=0.10, base_scale=0.25, height_scale=1.3)


class ProximityMinePlatform(WeaponsPlatform):
    variant_name = "Proximity Mine"
    variant_description = "Deployed at player position. Detonates when an enemy enters its trigger range."
    banish_ability = "explosion"

    def __init__(self):
        super().__init__()
        self.weapons_free_timer_max = C.PROXIMITY_MINE_WEAPONS_FREE_TIMER
        self.range = C.EXPLOSIVE_DRONE_WEAPONS_RANGE
        self.trigger_radius = C.PROXIMITY_MINE_TRIGGER_RADIUS
        self.explosion_radius = C.PROXIMITY_MINE_EXPLOSION_RADIUS
        self.upgrade_paths = [
            {"type": "damage",      "label": "Damage +15%",    "is_generic": True},
            {"type": "fire_rate",   "label": "Fire Rate +12%", "is_generic": True},
            {"type": "mine_radius", "label": "Blast +20%",     "is_generic": False},
        ]

    def apply_upgrade(self, upgrade_type, tier):
        if upgrade_type == "mine_radius":
            self.explosion_radius = int(self.explosion_radius * (1 + C.SHOP_BLAST_RADIUS_INCREASE))
            self.trigger_radius = int(self.trigger_radius * (1 + C.SHOP_BLAST_RADIUS_INCREASE))
        else:
            super().apply_upgrade(upgrade_type, tier)

    def fire(self, owner):
        game = getattr(owner, 'game', None)
        enemies = getattr(game, 'enemies', None) if game else None
        projectile = ProximityMine(owner.player.position.x, owner.player.position.y,
            owner.asteroids, enemies=enemies)
        projectile.trigger_radius = self.trigger_radius
        projectile.explosion_radius = self.explosion_radius
        projectile.explosion_damage = int(C.PROXIMITY_MINE_EXPLOSION_DAMAGE * self.damage_multiplier)
        projectile.stat_source = owner.stat_source
        projectile.combat_stats = owner.game.combat_stats
        projectile.extra_abilities = set(owner.extra_abilities)
        projectile.element = owner.element
        self.weapons_free_timer = self.weapons_free_timer_max
        return 0

    def draw(self, screen, owner):
        surf_size = int(owner.radius * 6)
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        c = surf_size // 2
        door_half_w = int(owner.radius * 0.65)
        door_h = int(owner.radius * 0.62)
        left_rect  = pygame.Rect(c - door_half_w, c - door_h // 2, door_half_w, door_h)
        right_rect = pygame.Rect(c,               c - door_h // 2, door_half_w, door_h)
        pygame.draw.rect(surf, C.GRAY,   left_rect)
        pygame.draw.rect(surf, C.GRAY,   right_rect)
        pygame.draw.rect(surf, C.ORANGE, left_rect,  1)
        pygame.draw.rect(surf, C.ORANGE, right_rect, 1)
        rotated = pygame.transform.rotate(surf, -owner.rotation)
        screen.blit(rotated, rotated.get_rect(center=(int(owner.position.x), int(owner.position.y))))


class GrenadePlatform(WeaponsPlatform):
    variant_name = "Grenade"
    variant_description = "Lobbed slowly toward targets. Detonates on impact or when its fuse expires."
    banish_ability = "explosion"

    def __init__(self):
        super().__init__()
        self.weapons_free_timer_max = C.GRENADE_WEAPONS_FREE_TIMER
        self.range = C.GRENADE_WEAPONS_RANGE
        self.projectile_speed = C.GRENADE_SPEED
        self.fuse_timer_max = C.GRENADE_FUSE_TIMER
        self.explosion_radius = C.GRENADE_EXPLOSION_RADIUS
        self.upgrade_paths = [
            {"type": "damage",         "label": "Damage +15%",    "is_generic": True},
            {"type": "fire_rate",      "label": "Fire Rate +12%", "is_generic": True},
            {"type": "grenade_fuse",   "label": "Fuse -0.3s",     "is_generic": False},
            {"type": "grenade_radius", "label": "Blast +20%",     "is_generic": False},
        ]

    def apply_upgrade(self, upgrade_type, tier):
        if upgrade_type == "grenade_radius":
            self.explosion_radius = int(self.explosion_radius * (1 + C.SHOP_BLAST_RADIUS_INCREASE))
        elif upgrade_type == "grenade_fuse":
            self.fuse_timer_max = max(0.5, self.fuse_timer_max - C.SHOP_FUSE_TIME_DECREASE)
        else:
            super().apply_upgrade(upgrade_type, tier)

    def fire(self, owner):
        spawn_pos = self._muzzle_position(owner)
        target = owner.target
        if target is None:
            return 0
        direction = target.position - spawn_pos
        if direction.length_squared() > 0:
            direction = direction.normalize()
        else:
            direction = owner.get_forward_vector()
        game = getattr(owner, 'game', None)
        enemies = getattr(game, 'enemies', None) if game else None
        projectile = Grenade(spawn_pos.x, spawn_pos.y, owner.asteroids, enemies=enemies)
        projectile.velocity = direction * self.projectile_speed
        projectile.fuse_timer = self.fuse_timer_max
        projectile.explosion_radius = self.explosion_radius
        projectile.explosion_damage = int(C.GRENADE_EXPLOSION_DAMAGE * self.damage_multiplier)
        projectile.damage = int(C.GRENADE_DIRECT_DAMAGE * self.damage_multiplier)
        projectile.stat_source = owner.stat_source
        projectile.combat_stats = owner.game.combat_stats
        projectile.extra_abilities = set(owner.extra_abilities)
        projectile.element = owner.element
        self.weapons_free_timer = self.weapons_free_timer_max
        return 0

    def draw(self, screen, owner):
        self._draw_kinetic_barrel(screen, owner, muzzle_scale=0.22, base_scale=0.40, height_scale=0.9)


class HomingMissilePlatform(WeaponsPlatform):
    variant_name = "Homing Missile"
    variant_description = "Self-guided missile that locks onto and pursues the acquired target."
    banish_ability = "explosion"

    def __init__(self):
        super().__init__()
        self.weapons_free_timer_max = C.HOMING_MISSILE_WEAPONS_FREE_TIMER
        self.range = C.HOMING_MISSILE_WEAPONS_RANGE
        self.projectile_speed = C.HOMING_MISSILE_SPEED
        self.turn_rate = C.HOMING_MISSILE_TURN_RATE
        self.explosion_radius = C.HOMING_MISSILE_EXPLOSION_RADIUS
        self.upgrade_paths = [
            {"type": "damage",           "label": "Damage +15%",    "is_generic": True},
            {"type": "fire_rate",        "label": "Fire Rate +12%", "is_generic": True},
            {"type": "homing_turn_rate", "label": "Turn Rate +20%", "is_generic": False},
        ]

    def apply_upgrade(self, upgrade_type, tier):
        if upgrade_type == "homing_turn_rate":
            self.turn_rate *= (1 + C.SHOP_HOMING_TURN_RATE_INCREASE)
        else:
            super().apply_upgrade(upgrade_type, tier)

    def fire(self, owner):
        spawn_pos = self._muzzle_position(owner)
        forward = owner.get_forward_vector()
        game = getattr(owner, 'game', None)
        enemies = getattr(game, 'enemies', None) if game else None
        projectile = HomingMissile(spawn_pos.x, spawn_pos.y, owner.asteroids,
            enemies=enemies, homing_target=owner.target)
        projectile.velocity = forward * self.projectile_speed
        projectile.turn_rate = self.turn_rate
        projectile.explosion_radius = self.explosion_radius
        projectile.explosion_damage = int(C.HOMING_MISSILE_EXPLOSION_DAMAGE * self.damage_multiplier)
        projectile.damage = int(C.HOMING_MISSILE_DIRECT_DAMAGE * self.damage_multiplier)
        projectile.stat_source = owner.stat_source
        projectile.combat_stats = owner.game.combat_stats
        projectile.extra_abilities = set(owner.extra_abilities)
        projectile.element = owner.element
        self.weapons_free_timer = self.weapons_free_timer_max
        return 0

    def draw(self, screen, owner):
        surf_size = int(owner.radius * 6)
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        c = surf_size // 2
        door_half_w = int(owner.radius * 0.65)
        door_h = int(owner.radius * 0.62)
        left_rect  = pygame.Rect(c - door_half_w, c - door_h // 2, door_half_w, door_h)
        right_rect = pygame.Rect(c,               c - door_h // 2, door_half_w, door_h)
        pygame.draw.rect(surf, C.GRAY,       left_rect)
        pygame.draw.rect(surf, C.GRAY,       right_rect)
        pygame.draw.rect(surf, C.LIGHT_GRAY, left_rect,  1)
        pygame.draw.rect(surf, C.LIGHT_GRAY, right_rect, 1)
        rotated = pygame.transform.rotate(surf, -owner.rotation)
        screen.blit(rotated, rotated.get_rect(center=(int(owner.position.x), int(owner.position.y))))


class FuseBombPlatform(WeaponsPlatform):
    variant_name = "Fuse Bomb"
    variant_description = "Placed at player position. Detonates with a large blast after a countdown."
    banish_ability = "explosion"

    def __init__(self):
        super().__init__()
        self.weapons_free_timer_max = C.FUSE_BOMB_WEAPONS_FREE_TIMER
        self.range = C.EXPLOSIVE_DRONE_WEAPONS_RANGE
        self.fuse_timer_max = C.FUSE_BOMB_FUSE_TIMER
        self.explosion_radius = C.FUSE_BOMB_EXPLOSION_RADIUS
        self.upgrade_paths = [
            {"type": "damage",      "label": "Damage +15%",    "is_generic": True},
            {"type": "fire_rate",   "label": "Fire Rate +12%", "is_generic": True},
            {"type": "fuse_radius", "label": "Blast +20%",     "is_generic": False},
            {"type": "fuse_timer",  "label": "Fuse -0.5s",     "is_generic": False},
        ]

    def apply_upgrade(self, upgrade_type, tier):
        if upgrade_type == "fuse_radius":
            self.explosion_radius = int(self.explosion_radius * (1 + C.SHOP_BLAST_RADIUS_INCREASE))
        elif upgrade_type == "fuse_timer":
            self.fuse_timer_max = max(1.0, self.fuse_timer_max - C.SHOP_FUSE_TIME_DECREASE)
        else:
            super().apply_upgrade(upgrade_type, tier)

    def fire(self, owner):
        game = getattr(owner, 'game', None)
        enemies = getattr(game, 'enemies', None) if game else None
        projectile = FuseBomb(owner.player.position.x, owner.player.position.y,
            owner.asteroids, enemies=enemies)
        projectile.fuse_timer = self.fuse_timer_max
        projectile.explosion_radius = self.explosion_radius
        projectile.explosion_damage = int(C.FUSE_BOMB_EXPLOSION_DAMAGE * self.damage_multiplier)
        projectile.stat_source = owner.stat_source
        projectile.combat_stats = owner.game.combat_stats
        projectile.extra_abilities = set(owner.extra_abilities)
        projectile.element = owner.element
        self.weapons_free_timer = self.weapons_free_timer_max
        return 0

    def draw(self, screen, owner):
        surf_size = int(owner.radius * 6)
        surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
        c = surf_size // 2
        door_half_w = int(owner.radius * 0.65)
        door_h = int(owner.radius * 0.62)
        left_rect  = pygame.Rect(c - door_half_w, c - door_h // 2, door_half_w, door_h)
        right_rect = pygame.Rect(c,               c - door_h // 2, door_half_w, door_h)
        pygame.draw.rect(surf, C.GRAY, left_rect)
        pygame.draw.rect(surf, C.GRAY, right_rect)
        pygame.draw.rect(surf, C.RED,  left_rect,  1)
        pygame.draw.rect(surf, C.RED,  right_rect, 1)
        rotated = pygame.transform.rotate(surf, -owner.rotation)
        screen.blit(rotated, rotated.get_rect(center=(int(owner.position.x), int(owner.position.y))))


class DecoyPlatform(WeaponsPlatform):
    variant_name = "Decoy"
    variant_description = "Periodically deploys a decoy that redirects enemy targeting."
    banish_ability = None

    def __init__(self):
        super().__init__()
        self.range = 0.0
        self.weapons_free_timer_max = 0.0
        self.decoy_duration = C.DECOY_DURATION
        self.decoy_cooldown = C.DECOY_COOLDOWN
        self._active_timer = 0.0
        self._cooldown_timer = 0.0
        self._deployed = False
        self._active_decoy = None
        self.upgrade_paths = [
            {"type": "decoy_duration", "label": "Duration +2s",   "is_generic": False},
            {"type": "fire_rate",      "label": "Cooldown -12%",  "is_generic": True},
        ]

    def apply_upgrade(self, upgrade_type, tier):
        pass

    def can_fire(self):
        return False

    def fire(self, owner):
        return 0

    def draw(self, screen, owner):
        pass

    def sentinel_update(self, drone, dt):
        game = getattr(drone.player, 'game', None)
        if self._deployed:
            if self._active_decoy is None or not self._active_decoy.alive():
                if game:
                    game.decoy = None
                self._deployed = False
                self._cooldown_timer = self.decoy_cooldown
            else:
                self._active_timer += dt
                if self._active_timer >= self.decoy_duration:
                    self._active_decoy.kill()
                    self._active_decoy = None
                    if game:
                        game.decoy = None
                    self._deployed = False
                    self._cooldown_timer = self.decoy_cooldown
        elif self._cooldown_timer > 0:
            self._cooldown_timer = max(0.0, self._cooldown_timer - dt)
        else:
            if game:
                decoy = Decoy(drone.player.position.x, drone.player.position.y)
                self._active_decoy = decoy
                game.decoy = decoy
                self._deployed = True
                self._active_timer = 0.0


class EvasionPlatform(WeaponsPlatform):
    variant_name = "Evasion"
    variant_description = "Grants the player a chance to dodge incoming damage."
    banish_ability = None

    def __init__(self):
        super().__init__()
        self.range = 0.0
        self.weapons_free_timer_max = 0.0
        self.evasion_chance = C.EVASION_CHANCE
        self.upgrade_paths = [
            {"type": "evasion_chance",  "label": "Evasion +5%",    "is_generic": False},
            {"type": "effect_strength", "label": "Max Health +1",  "is_generic": True},
        ]

    def apply_upgrade(self, upgrade_type, tier):
        pass

    def can_fire(self):
        return False

    def fire(self, owner):
        return 0

    def draw(self, screen, owner):
        pass

    def sentinel_update(self, drone, dt):
        drone.player.evasion_chance = self.evasion_chance


class HealPlatform(WeaponsPlatform):
    variant_name = "Heal"
    variant_description = "Converts lives to a health bar and slowly restores health over time."
    banish_ability = None

    def __init__(self):
        super().__init__()
        self.range = 0.0
        self.weapons_free_timer_max = 0.0
        self.heal_interval = C.HEAL_INTERVAL
        self.heal_timer = 0.0
        self._activated = False
        self.upgrade_paths = [
            {"type": "heal_rate",       "label": "Heal Rate +15%", "is_generic": False},
            {"type": "effect_strength", "label": "Max Health +1",  "is_generic": True},
        ]

    def apply_upgrade(self, upgrade_type, tier):
        pass

    def can_fire(self):
        return False

    def fire(self, owner):
        return 0

    def draw(self, screen, owner):
        pass

    def sentinel_update(self, drone, dt):
        player = drone.player
        if not self._activated:
            player.max_health = player.max_lives * 10
            player.health = player.max_health
            player.uses_health = True
            game = getattr(player, 'game', None)
            if game:
                game.HUD.activate_health_mode(player.max_health)
            self._activated = True
        self.heal_timer += dt
        if self.heal_timer >= self.heal_interval and player.health < player.max_health:
            player.health += 1
            game = getattr(player, 'game', None)
            if game:
                game.HUD.update_player_health(player.health)
            self.heal_timer = 0.0


class ResourceBoostPlatform(WeaponsPlatform):
    variant_name = "Resource Boost"
    variant_description = "Passively generates essence over time."
    banish_ability = None

    def __init__(self):
        super().__init__()
        self.range = 0.0
        self.weapons_free_timer_max = 0.0
        self.generation_interval = C.RESOURCE_BOOST_INTERVAL
        self.generation_amount = C.RESOURCE_BOOST_AMOUNT
        self.generation_timer = 0.0
        self.upgrade_paths = [
            {"type": "resource_yield", "label": "Yield +1",    "is_generic": False},
            {"type": "fire_rate",      "label": "Rate +12%",   "is_generic": True},
        ]

    def apply_upgrade(self, upgrade_type, tier):
        pass

    def can_fire(self):
        return False

    def fire(self, owner):
        return 0

    def draw(self, screen, owner):
        pass

    def sentinel_update(self, drone, dt):
        self.generation_timer += dt
        if self.generation_timer >= self.generation_interval:
            game = getattr(drone.player, 'game', None)
            if game:
                game.essence.add(self.generation_amount)
            self.generation_timer = 0.0
