# main.py
import pygame
import sys

import config
import audio_system
import home_screen
import game_screen


# ---------------------------------------------------------------------------
# 全局状态
# ---------------------------------------------------------------------------
game_state = "start"           # start / game / pause / fail / level_complete
campaign_completed = False
has_progress = False            # 是否已经玩过（用于开始界面按钮显隐）
continue_level = 0              # "继续探索"从哪一关开始
pause_started = 0

_pending_action = None
LEVEL_COMPLETE_DELAY = 10       # 按钮回弹动画帧数


def schedule_button_action(delay, action):
    global _pending_action
    _pending_action = {"timer": delay, "action": action}


# ---------------------------------------------------------------------------
# 状态转换辅助
# ---------------------------------------------------------------------------
def _do_start_new():
    global current_level, has_progress, continue_level, game_state, campaign_completed
    campaign_completed = False
    game_screen.reset_progress()
    has_progress = True
    continue_level = 0
    game_screen.load_level(0)
    game_state = "game"


def _do_start_continue():
    global game_state
    if campaign_completed:
        return
    game_screen.load_level(continue_level)
    game_state = "game"


def _do_return_home():
    global game_state, has_progress
    has_progress = not campaign_completed
    game_state = "start"


def _do_next_level(level_index):
    global game_state
    game_screen.load_level(level_index)
    game_state = "game"


def _do_restart_current_level():
    """暂停菜单：重新开始当前关卡。"""
    global game_state
    game_screen.load_level(game_screen.current_level)
    game_state = "game"


def _do_restart_from_first_level():
    """暂停菜单：从第一关重新开始本次探索。"""
    global game_state, campaign_completed, has_progress, continue_level
    campaign_completed = False
    has_progress = True
    continue_level = 0
    game_screen.load_level(0)
    game_state = "game"


# ---------------------------------------------------------------------------
# 主循环
# ---------------------------------------------------------------------------
game_screen.load_level(0)

running = True

while running:

    mouse_pos = pygame.mouse.get_pos()

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                if game_state == "game":
                    game_state = "pause"
                    pause_started = pygame.time.get_ticks()
                elif game_state == "pause":
                    game_screen.paused_total += pygame.time.get_ticks() - pause_started
                    game_state = "game"

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos

            # ---------------- 开始界面 ----------------
            if game_state == "start":
                if _pending_action is None:
                    action = home_screen.handle_click(mouse_x, mouse_y, has_progress)
                    if action == "new":
                        schedule_button_action(LEVEL_COMPLETE_DELAY, _do_start_new)
                    elif action == "continue":
                        schedule_button_action(LEVEL_COMPLETE_DELAY, _do_start_continue)

            # ---------------- 关卡内 ----------------
            elif game_state == "game":
                gs = game_screen

                if gs.GAME_BTN_RESTART.collidepoint(mouse_x, mouse_y):
                    config.trigger_button_press("game_restart")
                    audio_system.play_click()
                    _do_start_new()

                elif gs.GAME_BTN_PAUSE.collidepoint(mouse_x, mouse_y):
                    config.trigger_button_press("game_pause")
                    audio_system.play_click()
                    pause_started = pygame.time.get_ticks()
                    game_state = "pause"

                elif gs.GAME_BTN_HINT.collidepoint(mouse_x, mouse_y):
                    config.trigger_button_press("game_hint")
                    audio_system.play_click()
                    gs.show_hint()

                elif gs.GAME_BTN_SOUND.collidepoint(mouse_x, mouse_y):
                    config.trigger_button_press("game_sound")
                    audio_system.play_click()
                    audio_system.toggle_sound()

                elif gs.animation is None:
                    if (config.BOARD_X <= mouse_x < config.BOARD_X + config.BOARD_SIZE
                            and config.BOARD_Y <= mouse_y < config.BOARD_Y + config.BOARD_SIZE):

                        col = (mouse_x - config.BOARD_X) // config.CELL_SIZE
                        row = (mouse_y - config.BOARD_Y) // config.CELL_SIZE
                        clicked = gs.find_arrow(row, col)

                        if clicked:
                            blocker = gs.get_blocking_arrow(clicked)
                            if blocker is None:
                                gs.arrows.remove(clicked)
                                gs.start_fly_animation(clicked)
                            else:
                                gs.arrows.remove(clicked)
                                gs.start_collision_animation(clicked, blocker)

            # ---------------- 暂停 ----------------
            elif game_state == "pause":
                continue_rect = pygame.Rect(350, 320, 200, 48)
                current_rect = pygame.Rect(350, 378, 200, 48)
                first_rect = pygame.Rect(350, 436, 200, 48)
                home_rect = pygame.Rect(350, 494, 200, 48)

                if continue_rect.collidepoint(mouse_x, mouse_y):
                    config.trigger_button_press("pause_continue")
                    audio_system.play_click()
                    game_screen.paused_total += pygame.time.get_ticks() - pause_started
                    game_state = "game"

                elif current_rect.collidepoint(mouse_x, mouse_y):
                    config.trigger_button_press("pause_current")
                    audio_system.play_click()
                    _do_restart_current_level()

                elif first_rect.collidepoint(mouse_x, mouse_y):
                    config.trigger_button_press("pause_first")
                    audio_system.play_click()
                    _do_restart_from_first_level()

                elif home_rect.collidepoint(mouse_x, mouse_y):
                    config.trigger_button_press("pause_home")
                    audio_system.play_click()
                    _do_return_home()

            # ---------------- 失败 ----------------
            elif game_state == "fail":
                restart_rect = pygame.Rect(230, 390, 200, 55)
                home_rect = pygame.Rect(470, 390, 200, 55)

                if restart_rect.collidepoint(mouse_x, mouse_y):
                    config.trigger_button_press("fail_restart")
                    audio_system.play_click()
                    game_screen.load_level(game_screen.current_level)
                    game_state = "game"

                elif home_rect.collidepoint(mouse_x, mouse_y):
                    config.trigger_button_press("fail_home")
                    audio_system.play_click()
                    schedule_button_action(LEVEL_COMPLETE_DELAY, _do_return_home)

            # ---------------- 关卡总结 ----------------
            elif game_state == "level_complete":
                info = game_screen.level_complete_info

                if game_screen.level_complete_anim < 18:
                    continue

                panel_rect = pygame.Rect(0, 0, 520, 500)
                panel_rect.center = (config.WIDTH // 2, config.HEIGHT // 2)

                if info["is_final"]:
                    home_rect = pygame.Rect(0, 0, 200, 52)
                    home_rect.center = (panel_rect.centerx, panel_rect.bottom - 58)
                    if home_rect.collidepoint(mouse_x, mouse_y):
                        config.trigger_button_press("modal_home")
                        audio_system.play_click()
                        schedule_button_action(LEVEL_COMPLETE_DELAY, _do_return_home)
                else:
                    home_rect = pygame.Rect(0, 0, 170, 52)
                    next_rect = pygame.Rect(0, 0, 170, 52)
                    home_rect.center = (panel_rect.centerx - 96, panel_rect.bottom - 58)
                    next_rect.center = (panel_rect.centerx + 96, panel_rect.bottom - 58)

                    if home_rect.collidepoint(mouse_x, mouse_y):
                        config.trigger_button_press("modal_home")
                        audio_system.play_click()
                        schedule_button_action(LEVEL_COMPLETE_DELAY, _do_return_home)

                    elif next_rect.collidepoint(mouse_x, mouse_y):
                        config.trigger_button_press("modal_next")
                        audio_system.play_click()
                        next_level = info["level"] + 1
                        schedule_button_action(LEVEL_COMPLETE_DELAY,
                                               lambda nl=next_level: _do_next_level(nl))

    # ---------------- 延迟按钮动作 ----------------
    if _pending_action is not None:
        _pending_action["timer"] -= 1
        if _pending_action["timer"] <= 0:
            act = _pending_action["action"]
            _pending_action = None
            act()

    # ---------------- 逻辑更新 ----------------
    if game_state == "start":
        home_screen.update_start_scene(has_progress)

    elif game_state == "game":
        gs = game_screen
        gs.current_elapsed = gs.get_game_time()
        gs.update_game_buttons(mouse_pos)

        if gs.animation is not None:
            if gs.animation["type"] == "fly":
                gs.update_fly_animation()
            elif gs.animation["type"] == "collision":
                gs.update_collision_animation()

        # 检查关卡状态切换信号
        if gs.signal == "complete":
            gs.signal = None
            if gs.level_complete_info["is_final"]:
                campaign_completed = True
                has_progress = False
                home_screen.start_ending()
                game_state = "ending"
            else:
                game_state = "level_complete"
            continue_level = gs.continue_level
        elif gs.signal == "fail":
            gs.signal = None
            game_state = "fail"

        gs.update_hint()
        gs.update_star_explosion()
        gs.update_explosions()

    elif game_state == "ending":
        if home_screen.ending_finished():
            game_screen.level_complete_anim = 0
            game_screen.final_explosion_timer = 0
            game_screen._blur_cache = None
            game_state = "level_complete"

    elif game_state == "pause":
        gs = game_screen
        config.update_button_state("pause_continue",
                                    pygame.Rect(350, 320, 200, 48), mouse_pos)
        config.update_button_state("pause_current",
                                    pygame.Rect(350, 378, 200, 48), mouse_pos)
        config.update_button_state("pause_first",
                                    pygame.Rect(350, 436, 200, 48), mouse_pos)
        config.update_button_state("pause_home",
                                    pygame.Rect(350, 494, 200, 48), mouse_pos)
        gs.update_star_explosion()
        gs.update_explosions()

    elif game_state == "fail":
        config.update_button_state("fail_restart",
                                    pygame.Rect(230, 390, 200, 55), mouse_pos)
        config.update_button_state("fail_home",
                                    pygame.Rect(470, 390, 200, 55), mouse_pos)
        game_screen.update_explosions()

    elif game_state == "level_complete":
        gs = game_screen
        gs.update_explosions()

        if gs.level_complete_anim < 24:
            gs.level_complete_anim += 1

        info = gs.level_complete_info
        panel_rect = pygame.Rect(0, 0, 520, 500)
        panel_rect.center = (config.WIDTH // 2, config.HEIGHT // 2)

        if info["is_final"]:
            gs.final_explosion_timer += 1
            home_rect = pygame.Rect(0, 0, 200, 52)
            home_rect.center = (panel_rect.centerx, panel_rect.bottom - 58)
            config.update_button_state("modal_home", home_rect, mouse_pos)
        else:
            home_rect = pygame.Rect(0, 0, 170, 52)
            next_rect = pygame.Rect(0, 0, 170, 52)
            home_rect.center = (panel_rect.centerx - 96, panel_rect.bottom - 58)
            next_rect.center = (panel_rect.centerx + 96, panel_rect.bottom - 58)
            config.update_button_state("modal_home", home_rect, mouse_pos)
            config.update_button_state("modal_next", next_rect, mouse_pos)

    # ---------------- 绘制 ----------------
    if game_state == "start":
        home_screen.draw_start_screen(has_progress)
    elif game_state == "game":
        game_screen.draw_game_screen()
    elif game_state == "pause":
        game_screen.draw_pause_screen()
    elif game_state == "fail":
        game_screen.draw_fail_screen()
    elif game_state == "level_complete":
        game_screen.draw_level_complete_screen()

    if game_state == "ending":
        home_screen.draw_ending()

    pygame.display.flip()
    config.clock.tick(60)


pygame.quit()
sys.exit()
