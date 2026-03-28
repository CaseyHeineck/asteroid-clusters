import pygame_menu
import constants as C

def create_main_menu(on_new_game, on_exit):
    menu = pygame_menu.Menu(
        title="ASTEROID CLUSTER****S",
        width=C.SCREEN_WIDTH,
        height=C.SCREEN_HEIGHT,
        theme=pygame_menu.themes.THEME_DARK)
    menu.add.button("START GAME", on_new_game)
    menu.add.button("EXIT GAME", on_exit)
    return menu

def create_pause_menu(on_resume, on_restart, on_main_menu, on_exit):
    menu = pygame_menu.Menu(
        title="PAUSED",
        width=C.SCREEN_WIDTH,
        height=C.SCREEN_HEIGHT,
        theme=pygame_menu.themes.THEME_DARK)
    menu.add.button("RESUME", on_resume)
    menu.add.button("RESTART", on_restart)
    menu.add.button("MAIN MENU", on_main_menu)
    menu.add.button("EXIT GAME", on_exit)
    return menu

def create_game_over_menu(on_new_game, on_main_menu, on_exit, score=0):
    menu = pygame_menu.Menu(
        title="GAME OVER!",
        width=C.SCREEN_WIDTH,
        height=C.SCREEN_HEIGHT,
        theme=pygame_menu.themes.THEME_DARK)
    menu.add.label(f"SCORE: {score}")
    menu.add.vertical_margin(20)
    menu.add.button("NEW GAME", on_new_game)
    menu.add.button("MAIN MENU", on_main_menu)
    menu.add.button("EXIT GAME", on_exit)
    return menu