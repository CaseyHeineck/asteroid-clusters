import pygame
import constants as C
from airspace import AirSpace

class MapSystem:
    def __init__(self, game):
        self.game = game
        self.current_pos = (0, 0)
        self.grid = {}
        self.cell_states = {}
        self.wizard_element_counts = game.wizard_element_counts
        self.grid[(0, 0)] = AirSpace(0, 0, grid=self.grid, cell_states=self.cell_states,
            wizard_element_counts=self.wizard_element_counts)

    def current_space(self):
        return self.grid[self.current_pos]

    def count_locked_portals(self):
        return sum(
            1 for space in self.grid.values()
            for portal in space.portals.values()
            if not portal.unlocked
        )

    def portals(self):
        return self.current_space().portals

    def update(self, dt):
        for portal in self.portals().values():
            portal.update(dt)
        shop = self.current_space().shop
        if shop:
            shop.update(dt)

    def draw(self, screen):
        player_pos = self.game.player.position
        can_afford = self.game.essence.can_afford(C.PORTAL_ESSENCE_COST)
        for portal in self.portals().values():
            portal.draw(screen)
            portal.draw_prompt(screen, player_pos, can_afford)
        shop = self.current_space().shop
        if shop:
            shop.draw(screen)
            shop.draw_prompt(screen, player_pos)

    def try_interact(self):
        player_pos = self.game.player.position
        for direction, portal in self.portals().items():
            if not portal.is_near(player_pos):
                continue
            if not portal.unlocked:
                if not self.game.essence.spend(portal.cost):
                    return True
                portal.unlocked = True
                self._unlock_back_portal(direction)
            self._transit(direction)
            return True
        shop = self.current_space().shop
        if shop and shop.is_near(player_pos):
            self.game.open_shop(shop)
            return True
        return False

    def _unlock_back_portal(self, direction):
        dx, dy = C.DIRECTION_DELTA[direction]
        adj_pos = (self.current_pos[0] + dx, self.current_pos[1] + dy)
        if adj_pos in self.grid:
            back = self.grid[adj_pos].portals.get(C.OPPOSITE[direction])
            if back:
                back.unlocked = True

    def _transit(self, direction):
        dx, dy = C.DIRECTION_DELTA[direction]
        new_pos = (self.current_pos[0] + dx, self.current_pos[1] + dy)
        if new_pos not in self.grid:
            self.grid[new_pos] = AirSpace(new_pos[0], new_pos[1], back_direction=C.OPPOSITE[direction],
                grid=self.grid, cell_states=self.cell_states, active_portal_count=self.count_locked_portals(),
                wizard_element_counts=self.wizard_element_counts)
        prev_space = self.grid[self.current_pos]
        self.current_pos = new_pos
        new_space = self.grid[new_pos]
        back_portal = new_space.portals.get(C.OPPOSITE[direction])
        if back_portal:
            arrival = back_portal.arrival_position()
        else:
            arrival = pygame.Vector2(C.SCREEN_WIDTH / 2, C.SCREEN_HEIGHT / 2)
        self.game.enter_new_airspace(arrival, prev_space, new_space)
