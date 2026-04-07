import constants as C


class ExperienceSystem:
    def __init__(self, game):
        self.game = game
        self.total_xp = 0
        self.level = 1
        self.choices_pending = 0

        from drone import (ExplosiveDrone, KineticDrone, LaserDrone,
                           PlasmaDrone, SentinelDrone)
        self.all_drone_classes = [PlasmaDrone, KineticDrone, ExplosiveDrone,
                                  LaserDrone, SentinelDrone]
        self.pending_drones = list(self.all_drone_classes)
        self.added_drones = []
        self.banished_drones = []

    def xp_to_reach_level(self, level):
        """Total cumulative XP needed to reach this level from level 1."""
        if level <= 1:
            return 0
        total = 0
        for l in range(1, level):
            total += int(C.EXP_LEVEL_BASE * (l ** C.EXP_LEVEL_EXPONENT))
        return total

    def xp_this_level(self):
        return self.total_xp - self.xp_to_reach_level(self.level)

    def xp_needed_this_level(self):
        return self.xp_to_reach_level(self.level + 1) - self.xp_to_reach_level(self.level)

    def add_starting_drone(self, drone_class):
        self.pending_drones.remove(drone_class)
        self.added_drones.append(drone_class)
        self.game.player.add_drone(drone_class, self.game.asteroids)

    def is_drone_choice_level(self, level):
        if level == C.EXP_DRONE_EARLY_LEVEL:
            return True
        return level >= C.EXP_DRONE_CHOICE_INTERVAL and level % C.EXP_DRONE_CHOICE_INTERVAL == 0

    def add_xp(self, amount):
        old_level = self.level
        self.total_xp += amount
        while self.total_xp >= self.xp_to_reach_level(self.level + 1):
            self.level += 1
        for l in range(old_level + 1, self.level + 1):
            if self.is_drone_choice_level(l) and self.pending_drones:
                self.choices_pending += 1
        self.update_hud()
        if self.choices_pending > 0:
            self.game.enter_drone_choice()

    def resolve_choice(self):
        self.choices_pending = max(0, self.choices_pending - 1)
        if self.choices_pending > 0 and self.pending_drones:
            self.game.enter_drone_choice()
        else:
            self.game.current_state = C.GAME_RUNNING

    def update_hud(self):
        self.game.HUD.update_level(self.level, self.xp_this_level(),
                                   self.xp_needed_this_level())
