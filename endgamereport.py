class CombatStats:
    def __init__(self):
        self.damage_dealt = {}
        self.kills = {}
        self.overkills = {}
        self.damage_absorbed = {}
        self.shield_repaired = {}

    def add_amount(self, bucket, source, amount):
        if amount <= 0:
            return
        bucket[source] = bucket.get(source, 0) + amount

    def add_damage(self, source, amount):
        self.add_amount(self.damage_dealt, source, amount)

    def add_kill(self, source):
        self.kills[source] = self.kills.get(source, 0) + 1

    def add_overkill(self, source):
        self.overkills[source] = self.overkills.get(source, 0) + 1

    def add_absorbed(self, source, amount):
        self.add_amount(self.damage_absorbed, source, amount)

    def add_repaired(self, source, amount):
        self.add_amount(self.shield_repaired, source, amount)

    def record_damage_event(self, source, health_before, attempted_damage, overkill=False):
        if health_before <= 0 or attempted_damage <= 0:
            return
        actual_damage = min(health_before, attempted_damage)
        self.add_damage(source, actual_damage)
        if actual_damage >= health_before:
            if overkill:
                self.add_overkill(source)
            else:
                self.add_kill(source)