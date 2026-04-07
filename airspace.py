import random
import constants as C
from portal import ALL_DIRECTIONS, OPPOSITE, Portal
from shop import Shop

_DIRECTION_DELTA = {
    "north": (0, -1),
    "south": (0,  1),
    "east":  (1,  0),
    "west":  (-1, 0),
}


class AirSpace:
    def __init__(self, gx, gy, back_direction=None, grid=None):
        self.gx = gx
        self.gy = gy
        self.portals = {}
        self.active_state = None  # populated when the room is suspended
        self.shop = Shop() if random.random() < C.SHOP_SPAWN_CHANCE else None
        self._generate_portals(back_direction, grid or {})

    def _generate_portals(self, back_direction, grid):
        for direction in ALL_DIRECTIONS:
            dx, dy = _DIRECTION_DELTA[direction]
            adj_pos = (self.gx + dx, self.gy + dy)
            neighbor = grid.get(adj_pos)

            if direction == back_direction:
                # Always present, pre-unlocked — this is the return path
                self.portals[direction] = Portal(direction, unlocked=True)

            elif neighbor is not None:
                # Neighbor already exists — mirror its portal state toward us
                neighbor_portal = neighbor.portals.get(OPPOSITE[direction])
                if neighbor_portal is not None:
                    self.portals[direction] = Portal(direction,
                                                     unlocked=neighbor_portal.unlocked)
                # If neighbor has no portal toward us, we cannot spawn one

            else:
                # No neighbor yet — roll freely
                if random.random() < C.PORTAL_SPAWN_CHANCE:
                    self.portals[direction] = Portal(direction)

        # Guarantee at least one outgoing portal so the map never dead-ends.
        # "Outgoing" means any portal that isn't the pre-unlocked return path.
        outgoing = [d for d in self.portals if d != back_direction]
        if not outgoing:
            eligible = [
                d for d in ALL_DIRECTIONS
                if d != back_direction
                and grid.get((self.gx + _DIRECTION_DELTA[d][0],
                               self.gy + _DIRECTION_DELTA[d][1])) is None
            ]
            if eligible:
                forced = random.choice(eligible)
                self.portals[forced] = Portal(forced)
