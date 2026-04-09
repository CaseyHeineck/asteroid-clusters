import pygame
import constants as C

class MiniMap:
    def draw(self, screen, map_system):
        grid = map_system.grid
        current_pos = map_system.current_pos
        if not grid:
            return
        xs = [p[0] for p in grid]
        ys = [p[1] for p in grid]
        min_x, min_y = min(xs), min(ys)
        max_x, max_y = max(xs), max(ys)
        map_px_w = (max_x - min_x) * C.ROOM_STEP + C.ROOM_SIZE
        map_px_h = (max_y - min_y) * C.ROOM_STEP + C.ROOM_SIZE
        origin_x = C.MARGIN
        origin_y = C.SCREEN_HEIGHT - C.MARGIN - map_px_h
        bg_w = map_px_w + C.MARGIN * 2
        bg_h = map_px_h + C.MARGIN * 2
        bg = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 130))
        screen.blit(bg, (origin_x - C.MARGIN, origin_y - C.MARGIN))
        for (gx, gy), space in grid.items():
            rx = origin_x + (gx - min_x) * C.ROOM_STEP
            ry = origin_y + (gy - min_y) * C.ROOM_STEP
            cx = rx + C.ROOM_SIZE // 2
            cy = ry + C.ROOM_SIZE // 2
            is_current = (gx, gy) == current_pos
            room_color = C.AQUA if is_current else C.CHARCOAL
            pygame.draw.rect(screen, room_color, (rx, ry, C.ROOM_SIZE, C.ROOM_SIZE))
            if is_current:
                pygame.draw.rect(screen, C.WHITE, (rx, ry, C.ROOM_SIZE, C.ROOM_SIZE), 1)
            for direction, portal in space.portals.items():
                p_color = C.AQUA if portal.unlocked else C.BRIGHT_PURPLE
                dx, dy = C.DIRECTION_DELTA[direction]
                adj_exists = (gx + dx, gy + dy) in grid
                stub = C.ROOM_GAP if adj_exists else C.STUB_LEN
                if direction == "north":
                    pygame.draw.line(screen, p_color, (cx, ry), (cx, ry - stub))
                elif direction == "south":
                    pygame.draw.line(screen, p_color, (cx, ry + C.ROOM_SIZE), (cx, ry + C.ROOM_SIZE + stub))
                elif direction == "east":
                    pygame.draw.line(screen, p_color, (rx + C.ROOM_SIZE, cy), (rx + C.ROOM_SIZE + stub, cy))
                elif direction == "west":
                    pygame.draw.line(screen, p_color, (rx, cy), (rx - stub, cy))
