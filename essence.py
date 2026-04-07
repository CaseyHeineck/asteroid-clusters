class EssenceSystem:
    def __init__(self, game):
        self.game = game
        self.amount = 0

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
