import pygame
import pygame_menu
from core import constants as C
from core.element import ELEMENT_COLORS, get_element_name
from entities.drone import ExplosiveDrone, KineticDrone, LaserDrone, PlasmaDrone, SentinelDrone

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
    source_rows = [(C.PLAYER, "Player"),
        (C.KINETIC_DRONE, "Kinetic Drone"),
        (C.PLASMA_DRONE, "Plasma Drone"),
        (C.LASER_DRONE, "Laser Drone"),
        (C.EXPLOSIVE_DRONE, "Explosive Drone"),
        (C.SENTINEL_DRONE, "Sentinel Drone")]
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

def create_drone_select_menu(on_select_drone):
    drone_info = [(PlasmaDrone, "PLASMA DRONE", "Medium range | Plasma bolts that burn asteroids over time"),
        (KineticDrone, "KINETIC DRONE", "Short range | Rapid-fire kinetic rounds with high impact"),
        (ExplosiveDrone, "EXPLOSIVE DRONE", "Medium range | Rockets with area-of-effect explosion"),
        (LaserDrone, "LASER DRONE", "Long range | Instant hitscan laser, targets highest HP"),
        (SentinelDrone, "SENTINEL DRONE", "Support | Generates a protective shield around you")]
    menu = pygame_menu.Menu(title="CHOOSE YOUR STARTING DRONE", width=C.SCREEN_WIDTH,
        height=C.SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_DARK)
    menu.add.label("Select the drone that will orbit you from the start of the game.")
    menu.add.vertical_margin(20)
    for drone_class, name, desc in drone_info:
        def make_cb(cls):
            return lambda: on_select_drone(cls)
        menu.add.button(f"{name}  —  {desc}", make_cb(drone_class))
    return menu

def create_drone_choice_menu(pending_drones, level, on_add_drone, on_banish_drone):
    drone_names = {
        PlasmaDrone: "PLASMA DRONE",
        KineticDrone: "KINETIC DRONE",
        ExplosiveDrone: "EXPLOSIVE DRONE",
        LaserDrone: "LASER DRONE",
        SentinelDrone: "SENTINEL DRONE",
    }
    menu = pygame_menu.Menu(title=f"LEVEL {level} — DRONE CHOICE", width=C.SCREEN_WIDTH,
        height=C.SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_DARK)
    menu.add.label("Choose one drone to ADD to your arsenal or BANISH permanently.")
    menu.add.vertical_margin(20)
    for drone_class in pending_drones:
        name = drone_names.get(drone_class, str(drone_class.__name__))
        def make_add(cls):
            return lambda: on_add_drone(cls)
        def make_banish(cls):
            return lambda: on_banish_drone(cls)
        menu.add.button(f"ADD  {name}", make_add(drone_class))
        menu.add.button(f"BANISH  {name}", make_banish(drone_class))
        menu.add.vertical_margin(8)
    return menu

def _draw_mancer_sprite(color, size=72):
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    cx, cy = size // 2, size // 2
    r = size // 2 - 2
    for i in range(4, 0, -1):
        pygame.draw.circle(surf, (*color, 18 * i), (cx, cy), r + i * 3)
    pygame.draw.circle(surf, (*color, 210), (cx, cy), r)
    shadow = tuple(max(0, c - 80) for c in color)
    pygame.draw.circle(surf, (*shadow, 255), (cx, cy), r - 9)
    pygame.draw.line(surf, (*color, 230), (cx, cy - r + 14), (cx, cy + r - 14), 2)
    pygame.draw.line(surf, (*color, 180), (cx - r + 14, cy), (cx + r - 14, cy), 2)
    pygame.draw.circle(surf, (255, 255, 255, 190), (cx, cy), 5)
    pygame.draw.circle(surf, (*color, 255), (cx, cy), 3)
    return surf

def create_mancer_hub_menu(essence, elemental_amount, wizards,
        on_enter_technomancer, on_enter_elementalmancer, on_leave):
    menu = pygame_menu.Menu(title="SORCEROUS SUNDRIES", width=C.SCREEN_WIDTH,
        height=C.SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_DARK)
    menu.add.label(f"Essence: {essence} \u25c6   |   Elemental Essence: {elemental_amount} \u25c6")
    menu.add.vertical_margin(16)
    tech_sprite = _draw_mancer_sprite(C.SILVER, 72)
    menu.add.surface(tech_sprite, selectable=False)
    menu.add.button("TECHNOMANCER  \u2014  Drone Upgrades", on_enter_technomancer)
    menu.add.vertical_margin(16)
    for element in wizards:
        elem_name = get_element_name(element)
        elem_color = ELEMENT_COLORS[element]["primary"]
        elem_sprite = _draw_mancer_sprite(elem_color, 72)
        menu.add.surface(elem_sprite, selectable=False)
        def make_enter_elem(e=element):
            return lambda: on_enter_elementalmancer(e)
        menu.add.button(f"{elem_name.upper()}MANCER  \u2014  Elemental Infusion", make_enter_elem())
        menu.add.vertical_margin(16)
    menu.add.button("LEAVE SHOP", on_leave)
    return menu

def _drone_keywords(drone):
    base_keywords = {
        "KineticDrone":   "impact",
        "PlasmaDrone":    "burn",
        "ExplosiveDrone": "explosion",
        "LaserDrone":     "overkill",
    }
    base = base_keywords.get(type(drone).__name__)
    extras = sorted(drone.extra_abilities)
    all_kw = ([base] if base else []) + [kw for kw in extras if kw != base]
    if not all_kw:
        return ""
    return "  [" + ", ".join(kw.upper() for kw in all_kw) + "]"

def _drone_upgrades(drone):
    cls = type(drone)
    if cls is SentinelDrone:
        return [("shield_health", "Shield Health +2"),
                ("repair_rate",   "Repair Speed +15%")]
    if cls is KineticDrone:
        return [("damage",           "Damage +15%"),
                ("fire_rate",        "Fire Rate +12%"),
                ("kinetic_mass",     "Kinetic Mass +60%"),
                ("projectile_speed", "Projectile Speed +15%")]
    upgrades = [("damage",    "Damage +15%"),
                ("fire_rate", "Fire Rate +12%")]
    if "impact" in drone.extra_abilities and hasattr(drone.platform, "projectile_speed"):
        upgrades += [("kinetic_mass",     "Kinetic Mass +60%"),
                     ("projectile_speed", "Projectile Speed +15%")]
    return upgrades

def create_technomancer_menu(player_drones, upgrade_counts, essence, on_buy, on_back):
    drone_display_names = {
        "ExplosiveDrone": "EXPLOSIVE DRONE",
        "KineticDrone":   "KINETIC DRONE",
        "LaserDrone":     "LASER DRONE",
        "PlasmaDrone":    "PLASMA DRONE",
        "SentinelDrone":  "SENTINEL DRONE",
    }
    menu = pygame_menu.Menu(title="TECHNOMANCER", width=C.SCREEN_WIDTH,
        height=C.SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_DARK)
    menu.add.label(f"Essence: {essence} \u25c6")
    menu.add.vertical_margin(10)
    seen = []
    cls_to_drone = {}
    for drone in player_drones:
        cls = type(drone)
        if cls not in seen:
            seen.append(cls)
            cls_to_drone[cls] = drone
    for cls in seen:
        name = drone_display_names.get(cls.__name__, cls.__name__)
        kw = _drone_keywords(cls_to_drone[cls])
        menu.add.label(f"\u2014 {name}{kw} \u2014")
        for upgrade_type, label in _drone_upgrades(cls_to_drone[cls]):
            count = upgrade_counts.get((cls.__name__, upgrade_type), 0)
            price = C.SHOP_UPGRADE_BASE_PRICE + count * C.SHOP_UPGRADE_PRICE_STEP
            btn_text = f"{label}  \u2014  {price} \u25c6"
            if essence >= price:
                def make_cb(c=cls, ut=upgrade_type):
                    return lambda: on_buy(c, ut)
                menu.add.button(btn_text, make_cb())
            else:
                menu.add.label(f"  {btn_text}  (need more \u25c6)")
        menu.add.vertical_margin(6)
    menu.add.vertical_margin(10)
    menu.add.button("BACK TO SHOP", on_back)
    return menu

def create_elementalmancer_menu(element, player_drones, elemental_amount, on_infuse, on_back):
    drone_display_names = {
        "ExplosiveDrone": "EXPLOSIVE DRONE",
        "KineticDrone":   "KINETIC DRONE",
        "LaserDrone":     "LASER DRONE",
        "PlasmaDrone":    "PLASMA DRONE",
        "SentinelDrone":  "SENTINEL DRONE",
    }
    elem_name = get_element_name(element)
    menu = pygame_menu.Menu(title=f"{elem_name.upper()}MANCER", width=C.SCREEN_WIDTH,
        height=C.SCREEN_HEIGHT, theme=pygame_menu.themes.THEME_DARK)
    menu.add.label(f"Elemental Essence: {elemental_amount} \u25c6")
    menu.add.vertical_margin(10)
    for drone in player_drones:
        drone_name = drone_display_names.get(type(drone).__name__, type(drone).__name__)
        kw = _drone_keywords(drone)
        if drone.element == element:
            menu.add.label(f"  {drone_name}{kw}  \u2014  already {elem_name}")
            continue
        overwrite = drone.element is not None
        cost = C.WIZARD_OVERWRITE_COST if overwrite else C.WIZARD_INFUSE_COST
        current = f" [{get_element_name(drone.element)}]" if overwrite else ""
        action = "Overwrite" if overwrite else "Infuse"
        btn_text = f"{action} {drone_name}{kw}{current} \u2192 {elem_name}  \u2014  {cost} Elemental \u25c6"
        if elemental_amount >= cost:
            def make_infuse(d=drone, e=element):
                return lambda: on_infuse(d, e)
            menu.add.button(btn_text, make_infuse())
        else:
            menu.add.label(f"  {btn_text}  (need more Elemental \u25c6)")
        menu.add.vertical_margin(4)
    menu.add.vertical_margin(10)
    menu.add.button("BACK TO SHOP", on_back)
    return menu

def get_source_color(source):
    return {
        C.PLAYER: C.RED,
        C.KINETIC_DRONE: C.SILVER,
        C.PLASMA_DRONE: C.MAGENTA,
        C.LASER_DRONE: C.LASER_RED,
        C.EXPLOSIVE_DRONE: C.ORANGE,
        C.SENTINEL_DRONE: C.GOLD,
    }.get(source, C.CYAN)