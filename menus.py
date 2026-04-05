import pygame
import pygame_menu
import constants as C

def create_main_menu(on_new_game, on_exit):
    menu = pygame_menu.Menu(title="ASTEROID CLUSTER****S", width=C.SCREEN_WIDTH,
        height=C.SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_DARK)
    menu.add.button("START GAME", on_new_game)
    menu.add.button("EXIT GAME", on_exit)
    return menu

def create_pause_menu(on_resume, on_restart, on_main_menu, on_exit):
    menu = pygame_menu.Menu(title="PAUSED", width=C.SCREEN_WIDTH,
        height=C.SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_DARK)
    menu.add.button("RESUME", on_resume)
    menu.add.button("RESTART", on_restart)
    menu.add.button("MAIN MENU", on_main_menu)
    menu.add.button("EXIT GAME", on_exit)
    return menu

def create_game_over_menu(on_new_game, on_main_menu, on_exit, score=0, combat_stats=None):
    menu = pygame_menu.Menu(title="GAME OVER!", width=C.SCREEN_WIDTH,
        height=C.SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_DARK)
    menu.add.label(f"SCORE: {score}")
    if combat_stats:
        total_damage = sum(combat_stats.damage_dealt.values())
        total_kills = sum(combat_stats.kills.values()) + sum(combat_stats.overkills.values())
        total_absorbed = sum(combat_stats.damage_absorbed.values())
        total_repaired = sum(combat_stats.shield_repaired.values())
        menu.add.label(f"TOTAL DAMAGE: {total_damage}")
        menu.add.label(f"TOTAL KILLS: {total_kills}")
        menu.add.label(f"SHIELD ABSORBED: {total_absorbed}")
        menu.add.label(f"SHIELD REPAIRED: {total_repaired}")
        menu.add.vertical_margin(10)
        offense_surface = build_offense_chart_surface(combat_stats, 900, 280)
        support_surface = build_support_chart_surface(combat_stats, 900, 170)
        menu.add.surface(offense_surface, selectable=False)
        menu.add.vertical_margin(10)
        menu.add.surface(support_surface, selectable=False)
        menu.add.vertical_margin(20)
    menu.add.button("NEW GAME", on_new_game)
    menu.add.button("MAIN MENU", on_main_menu)
    menu.add.button("EXIT GAME", on_exit)
    return menu

def build_offense_chart_surface(combat_stats, width, height):
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    surface.fill((20, 20, 20, 220))
    pygame.draw.rect(surface, C.LIGHT_GRAY, surface.get_rect(), 2)
    title_font = pygame.font.SysFont(None, 34)
    row_font = pygame.font.SysFont(None, 24)
    small_font = pygame.font.SysFont(None, 20)
    title = title_font.render("OFFENSE", True, C.WHITE)
    surface.blit(title, (16, 12))
    source_rows = [
        (C.PLAYER, "Player"),
        (C.KINETIC_DRONE, "Kinetic Drone"),
        (C.PLASMA_DRONE, "Plasma Drone"),
        (C.LASER_DRONE, "Laser Drone"),
        (C.EXPLOSIVE_DRONE, "Explosive Drone"),
        (C.SENTINEL_DRONE, "Sentinel Drone"),
    ]
    rows = []
    for source, label in source_rows:
        damage = combat_stats.damage_dealt.get(source, 0)
        kills = combat_stats.kills.get(source, 0)
        overkills = combat_stats.overkills.get(source, 0)
        if damage > 0 or kills > 0 or overkills > 0:
            rows.append({
                "label": label,
                "value": damage,
                "kills": kills,
                "overkills": overkills,
                "color": get_source_color(source),
            })
    rows.sort(key=lambda row: row["value"], reverse=True)
    if not rows:
        empty = row_font.render("No offensive stats recorded", True, C.LIGHT_GRAY)
        surface.blit(empty, (16, 60))
        return surface
    max_value = max(row["value"] for row in rows) or 1
    total_value = sum(row["value"] for row in rows) or 1
    row_y = 56
    label_x = 16
    bar_x = 240
    bar_width = width - bar_x - 20
    bar_height = 18
    row_gap = 36
    for row in rows:
        value = row["value"]
        percent = int((value / total_value) * 100) if total_value > 0 else 0
        label = row_font.render(row["label"], True, C.WHITE)
        surface.blit(label, (label_x, row_y))
        stat_text = f"{value} ({percent}%)"
        if row["kills"]:
            stat_text += f" | K {row['kills']}"
        if row["overkills"]:
            stat_text += f" | OK {row['overkills']}"
        stat = small_font.render(stat_text, True, C.LIGHT_GRAY)
        surface.blit(stat, (label_x, row_y + 18))
        fill_width = int((value / max_value) * bar_width)
        bar_rect = pygame.Rect(bar_x, row_y + 8, bar_width, bar_height)
        fill_rect = pygame.Rect(bar_x, row_y + 8, fill_width, bar_height)
        pygame.draw.rect(surface, C.DARK_GRAY, bar_rect)
        pygame.draw.rect(surface, row["color"], fill_rect)
        pygame.draw.rect(surface, C.WHITE, bar_rect, 1)
        row_y += row_gap
    return surface

def build_support_chart_surface(combat_stats, width, height):
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    surface.fill((20, 20, 20, 220))
    pygame.draw.rect(surface, C.LIGHT_GRAY, surface.get_rect(), 2)
    title_font = pygame.font.SysFont(None, 34)
    row_font = pygame.font.SysFont(None, 24)
    small_font = pygame.font.SysFont(None, 20)
    title = title_font.render("DEFENSE / SUPPORT", True, C.WHITE)
    surface.blit(title, (16, 12))
    rows = []
    absorbed = combat_stats.damage_absorbed.get(C.PLAYER_SHIELD, 0)
    if absorbed > 0:
        rows.append({
            "label": "Player Shield Absorbed",
            "value": absorbed,
            "color": C.AQUA,
        })
    repaired = combat_stats.shield_repaired.get(C.SENTINEL_DRONE, 0)
    if repaired > 0:
        rows.append({
            "label": "Sentinel Shield Repaired",
            "value": repaired,
            "color": C.GOLD,
        })
    rows.sort(key=lambda row: row["value"], reverse=True)
    if not rows:
        empty = row_font.render("No defensive/support stats recorded", True, C.LIGHT_GRAY)
        surface.blit(empty, (16, 60))
        return surface
    max_value = max(row["value"] for row in rows) or 1
    total_value = sum(row["value"] for row in rows) or 1
    row_y = 56
    label_x = 16
    bar_x = 280
    bar_width = width - bar_x - 20
    bar_height = 20
    row_gap = 52
    for row in rows:
        value = row["value"]
        percent = int((value / total_value) * 100) if total_value > 0 else 0
        label = row_font.render(row["label"], True, C.WHITE)
        surface.blit(label, (label_x, row_y))
        stat = small_font.render(f"{value} ({percent}%)", True, C.LIGHT_GRAY)
        surface.blit(stat, (label_x, row_y + 20))
        fill_width = int((value / max_value) * bar_width)
        bar_rect = pygame.Rect(bar_x, row_y + 10, bar_width, bar_height)
        fill_rect = pygame.Rect(bar_x, row_y + 10, fill_width, bar_height)
        pygame.draw.rect(surface, C.DARK_GRAY, bar_rect)
        pygame.draw.rect(surface, row["color"], fill_rect)
        pygame.draw.rect(surface, C.WHITE, bar_rect, 1)
        row_y += row_gap
    return surface

def get_source_color(source):
    return {
        C.PLAYER: C.RED,
        C.KINETIC_DRONE: C.SILVER,
        C.PLASMA_DRONE: C.MAGENTA,
        C.LASER_DRONE: C.LASER_RED,
        C.EXPLOSIVE_DRONE: C.ORANGE,
        C.SENTINEL_DRONE: C.GOLD,
    }.get(source, C.CYAN)