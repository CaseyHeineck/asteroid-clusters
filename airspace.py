import random
import constants as C
from portal import Portal
from shop import Shop

class AirSpace:
    def __init__(self, gx, gy, back_direction=None, grid=None, cell_states=None, active_portal_count=0):
        self.gx = gx
        self.gy = gy
        self.portals = {}
        self.active_state = None  
        self.shop = Shop() if random.random() < C.SHOP_SPAWN_CHANCE else None
        grid = grid or {}
        cell_states = cell_states if cell_states is not None else {}
        self._generate_portals(back_direction, grid, cell_states, active_portal_count)
        self._update_cell_states(cell_states)

    def _generate_portals(self, back_direction, grid, cell_states, active_portal_count):
        for direction in C.ALL_DIRECTIONS:
            dx, dy = C.DIRECTION_DELTA[direction]
            adj_pos = (self.gx + dx, self.gy + dy)
            neighbor = grid.get(adj_pos)
            neighbor_state = cell_states.get(adj_pos)
            if direction == back_direction:
                self.portals[direction] = Portal(direction, unlocked=True)
            elif neighbor is not None:
                neighbor_portal = neighbor.portals.get(C.OPPOSITE[direction])
                if neighbor_portal is not None:
                    self.portals[direction] = Portal(direction, unlocked=True)
                    neighbor_portal.unlocked = True
            elif neighbor_state == C.POTENTIALLY_ACTIVE:
                self.portals[direction] = Portal(direction)
            elif neighbor_state != C.RESTRICTED:
                if random.random() < C.PORTAL_SPAWN_CHANCE:
                    self.portals[direction] = Portal(direction)
        locked_outgoing = [
            d for d in self.portals
            if d != back_direction and not self.portals[d].unlocked
        ]
        if not locked_outgoing and active_portal_count == 0:
            eligible = [
                d for d in C.ALL_DIRECTIONS
                if d != back_direction
                and grid.get((self.gx + C.DIRECTION_DELTA[d][0],
                    self.gy + C.DIRECTION_DELTA[d][1])) is None
                and cell_states.get((self.gx + C.DIRECTION_DELTA[d][0],
                    self.gy + C.DIRECTION_DELTA[d][1])) != C.RESTRICTED
            ]
            if eligible:
                forced = random.choice(eligible)
                self.portals[forced] = Portal(forced)

    def _update_cell_states(self, cell_states):
        cell_states[(self.gx, self.gy)] = "active"
        for direction, (dx, dy) in C.DIRECTION_DELTA.items():
            adj_pos = (self.gx + dx, self.gy + dy)
            if cell_states.get(adj_pos) == "active":
                continue  
            if direction in self.portals:
                cell_states[adj_pos] = C.POTENTIALLY_ACTIVE
            elif cell_states.get(adj_pos) != C.POTENTIALLY_ACTIVE:
                cell_states[adj_pos] = C.RESTRICTED
