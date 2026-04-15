class EssenceSystem:
    def __init__(self, game):
        self.game = game
        self.amount = 0
        self.elemental_amount = 0

    def add(self, amount):
        self.amount += amount
        self.game.HUD.update_essence(self.amount)

    def spend(self, amount):
        if self.amount >= amount:
            self.amount -= amount
            self.game.HUD.update_essence(self.amount)
            return True
        return False

    def can_afford(self, amount):
        return self.amount >= amount

    def add_elemental(self, amount):
        self.elemental_amount += amount
        self.game.HUD.update_elemental_essence(self.elemental_amount)

    def spend_elemental(self, amount):
        if self.elemental_amount >= amount:
            self.elemental_amount -= amount
            self.game.HUD.update_elemental_essence(self.elemental_amount)
            return True
        return False

    def can_afford_elemental(self, amount):
        return self.elemental_amount >= amount
