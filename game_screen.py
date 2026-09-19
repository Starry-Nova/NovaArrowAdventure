# game_screen.py
import pygame
import math
import random

import config
import audio_system
from config import (
    WIDTH, HEIGHT, screen,
    BOARD_X, BOARD_Y, BOARD_SIZE, GRID_SIZE, CELL_SIZE,
    PANEL_X, PANEL_Y, PANEL_W, PANEL_H,
    GAME_BTN_RESTART, GAME_BTN_PAUSE, GAME_BTN_HINT, GAME_BTN_SOUND,
    TEXT_COLOR, SUB_TEXT, WHITE, BUTTON_HOME, BUTTON_HOME_HOVER,
    BUTTON_GOLD, BUTTON_GOLD_HOVER, RED, YELLOW,
    font_title, font_big, font_modal_title, font_normal, font_small,
    font_tiny, font_micro, font_button, font_button_tiny,
    blit_text, wrap_text, format_time,
    draw_animated_button, update_button_state, trigger_button_press,
    draw_small_star, draw_space_decor, draw_art_title_with_decor,
    background_stars, meteors,
)

# level_data.py

rocket_colors = [
    (80, 150, 225), (235, 100, 85), (105, 185, 135), (165, 105, 205),
    (240, 165, 70), (70, 185, 190), (220, 105, 155), (120, 145, 220),
]


levels = [
    [(1, 2, "right"), (4, 1, "left"), (1, 4, "right"), (6, 3, "up")],

    [(5, 2, "down"), (1, 5, "down"), (4, 6, "left"), (3, 1, "right"),
     (4, 1, "down"), (0, 3, "left")],

    [(1, 2, "down"), (6, 1, "down"), (5, 4, "up"), (3, 1, "up"),
     (1, 3, "down"), (5, 0, "right"), (6, 0, "down"), (5, 3, "down")],

    [(6, 3, "down"), (4, 1, "left"), (6, 4, "down"), (6, 2, "right"),
     (1, 6, "right"), (0, 4, "down"), (5, 3, "down"), (1, 0, "up"),
     (3, 3, "left"), (6, 5, "down")],

    [(0, 1, "up"), (1, 5, "up"), (6, 4, "left"), (2, 0, "left"),
     (3, 4, "up"), (3, 0, "down"), (0, 0, "left"), (1, 1, "right"),
     (6, 6, "left"), (1, 3, "down"), (0, 6, "left"), (1, 2, "right")],

    [(5, 2, "up"), (3, 1, "right"), (6, 6, "left"), (0, 6, "down"),
     (0, 0, "right"), (2, 5, "right"), (4, 5, "right"), (5, 1, "right"),
     (3, 0, "down"), (2, 4, "down"), (1, 3, "left"), (6, 5, "left"),
     (5, 3, "up"), (1, 2, "left")],

    [(6, 3, "up"), (4, 2, "up"), (0, 1, "up"), (5, 0, "left"),
     (4, 5, "up"), (6, 5, "down"), (0, 3, "left"), (2, 2, "right"),
     (0, 4, "left"), (1, 5, "left"), (4, 3, "right"), (3, 2, "right"),
     (3, 6, "right"), (4, 0, "down"), (2, 4, "down"), (2, 0, "down")]
]


level_names = [
    "地面点火台", "冲破大气层", "近地轨道巡航",
    "地月转移航线", "月球环绕轨道", "行星际深空", "新星港湾"
]


level_stories = [
    "火箭矗立地面发射台，准备点火，开启太空探索之旅。",
    "点火升空，穿越厚重大气层，抵御高空气流冲击。",
    "成功抵达近地轨道，调整飞船姿态，稳定环绕地球。",
    "告别地球，踏上前往月球的转移轨道。",
    "抵达月球附近，进入环月轨道，短暂休整。",
    "离开地月系统，驶入孤寂的星际空间。",
    "跨越遥远星际，终于抵达目标新星，完成太空探索任务。",
]


level_congrats = [
    "点火成功！你已经迈出了星际探索的第一步。",
    "穿越大气，你离星空更近了一步。",
    "稳定入轨，地球在脚下缓缓转动。",
    "告别家园，勇敢驶向更远的星海。",
    "抵达月球轨道，深空探索继续推进。",
    "穿越行星际，孤独星空里仍保持前进。",
    "新星已在眼前，这是属于你的荣耀时刻！",
]


"""每关完成时间与最佳纪录；原子写入用户目录，重开不会清空。"""
import json
import math
import os
from pathlib import Path

RECORDS_SAVE_PATH = Path(os.environ.get('PIXEL_ROCKET_SAVE_DIR', str(Path.home()/'.pixel_rocket_game'))) / 'records.json'

def valid_record_time(value):
    return isinstance(value,(float,int)) and not isinstance(value,bool) and math.isfinite(value) and value>=0

def load_time_records(count):
    result=[{'best':None,'last':None,'runs':[]} for _ in range(count)]
    try:
        data=json.loads(RECORDS_SAVE_PATH.read_text(encoding='utf-8'))
        entries=data.get('levels',[]) if isinstance(data,dict) else []
        for i,item in enumerate(entries[:count]):
            if not isinstance(item,dict): continue
            runs=item.get('runs',[])
            runs=[v for v in runs if valid_record_time(v)] if isinstance(runs,list) else []
            best=item.get('best')
            candidates=runs+([best] if valid_record_time(best) else [])
            result[i]={'best':min(candidates) if candidates else None,
                       'last':runs[-1] if runs else None,'runs':runs}
    except (OSError,ValueError,TypeError):
        pass
    return result

def save_time_records(entries):
    try:
        RECORDS_SAVE_PATH.parent.mkdir(parents=True,exist_ok=True)
        temporary=RECORDS_SAVE_PATH.with_suffix('.tmp')
        temporary.write_text(json.dumps({'version':1,'levels':entries},ensure_ascii=False,indent=2),encoding='utf-8')
        temporary.replace(RECORDS_SAVE_PATH)
        return True
    except OSError:
        return False



# ---------------------------------------------------------------------------
# 关卡状态（模块级）
# ---------------------------------------------------------------------------
current_level = 0
arrows = []
mistakes = 3
animation = None
star_explosion = None
explosions = []
hint_cell = None
hint_timer = 0
paused_total = 0
level_start_time = 0
current_elapsed = 0
final_explosion_timer = 0
level_complete_anim = 0
_blur_cache = None
level_complete_info = None
time_records = load_time_records(len(levels))
best_times = [entry["best"] for entry in time_records]
continue_level = 0

# 状态信号：由 main 检查后清零
# "complete" / "fail" / None
signal = None


# ---------------------------------------------------------------------------
# 关卡加载与基础查询
# ---------------------------------------------------------------------------
def load_level(level_index):
    global current_level, arrows, mistakes, animation, star_explosion, explosions
    global hint_cell, hint_timer, paused_total, level_start_time
    global current_elapsed, final_explosion_timer, level_complete_anim
    global signal, level_complete_info

    level_complete_info = None
    current_level = level_index
    arrows = []
    for index, item in enumerate(levels[level_index]):
        row, col, direction = item
        arrows.append([row, col, direction, index % len(rocket_colors)])

    mistakes = 3
    animation = None
    star_explosion = None
    explosions = []
    hint_cell = None
    hint_timer = 0
    paused_total = 0
    current_elapsed = 0
    level_start_time = pygame.time.get_ticks()
    final_explosion_timer = 0
    level_complete_anim = 0
    signal = None


def get_arrow_position(row, col):
    x = BOARD_X + col * CELL_SIZE + CELL_SIZE // 2
    y = BOARD_Y + row * CELL_SIZE + CELL_SIZE // 2
    return x, y


def find_arrow(row, col):
    for arrow in arrows:
        if arrow[0] == row and arrow[1] == col:
            return arrow
    return None


def get_blocking_arrow(arrow):
    row, col, direction = arrow[:3]
    if direction == "up":
        for r in range(row - 1, -1, -1):
            t = find_arrow(r, col)
            if t:
                return t
    elif direction == "down":
        for r in range(row + 1, GRID_SIZE):
            t = find_arrow(r, col)
            if t:
                return t
    elif direction == "left":
        for c in range(col - 1, -1, -1):
            t = find_arrow(row, c)
            if t:
                return t
    elif direction == "right":
        for c in range(col + 1, GRID_SIZE):
            t = find_arrow(row, c)
            if t:
                return t
    return None


# ---------------------------------------------------------------------------
# 背景绘制
# ---------------------------------------------------------------------------
def draw_stars(count):
    current_time = pygame.time.get_ticks()
    for star in background_stars[:count]:
        wave = (math.sin(current_time / 700 * star["speed"] + star["phase"]) + 1) / 2
        brightness = int(star["bright_base"] + wave * star["bright_range"])
        pygame.draw.circle(screen, (brightness, brightness, min(255, brightness + 18)),
                           (star["x"], star["y"]), star["size"])


def draw_meteors(dt_scale=1.0):
    for m in meteors:
        m["x"] += m["vx"] * dt_scale
        m["y"] += m["vy"] * dt_scale
        m["life"] += 0.016 * dt_scale

        if m["life"] > m["max_life"] or m["x"] > WIDTH + 100 or m["y"] > HEIGHT + 100:
            m["x"] = random.uniform(-200, WIDTH * 0.6)
            m["y"] = random.uniform(-100, HEIGHT * 0.3)
            m["life"] = 0
            m["max_life"] = random.uniform(5, 9)
            continue

        progress = m["life"] / m["max_life"]
        alpha = int(200 * math.sin(progress * math.pi))
        if alpha <= 0:
            continue

        length = m["len"]
        angle = math.atan2(m["vy"], m["vx"])
        ex = m["x"] - math.cos(angle) * length
        ey = m["y"] - math.sin(angle) * length

        for i in range(8):
            t = i / 8
            px = m["x"] + (ex - m["x"]) * t
            py = m["y"] + (ey - m["y"]) * t
            a = int(alpha * (1 - t) * 0.7)
            r = max(1, int(3 * (1 - t)))
            pygame.draw.circle(screen, (200, 230, 255, a), (int(px), int(py)), r)

        pygame.draw.circle(screen, (255, 255, 245, alpha), (int(m["x"]), int(m["y"])), 3)


def draw_planet_decor(cx, cy, radius, color, ring=False, ring_color=None):
    pygame.draw.circle(screen, color, (cx, cy), radius)
    pygame.draw.circle(screen, (max(0, color[0] - 25), max(0, color[1] - 25),
                                max(0, color[2] - 25)), (cx, cy), radius, 2)
    pygame.draw.circle(screen, (min(255, color[0] + 35), min(255, color[1] + 35),
                                min(255, color[2] + 35)),
                       (cx - radius // 3, cy - radius // 3), max(3, radius // 3))
    if ring:
        if ring_color is None:
            ring_color = (200, 180, 240)
        rect = pygame.Rect(cx - radius * 1.9, cy - radius * 0.42,
                           radius * 3.8, radius * 0.84)
        pygame.draw.ellipse(screen, ring_color, rect, 2)


def draw_rotating_moon(cx, cy, radius, angle):
    size = radius * 2 + 8
    moon = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2
    pygame.draw.circle(moon, (215, 215, 205), (c, c), radius)
    pygame.draw.circle(moon, (190, 190, 182), (c, c), radius, 2)
    pygame.draw.circle(moon, (228, 228, 220), (c - 6, c - 6), radius - 10)

    craters = [
        (-0.35, -0.30, 10, (182, 182, 176)),
        (0.40, -0.10, 8, (190, 190, 184)),
        (0.10, 0.42, 9, (185, 185, 178)),
        (-0.30, 0.30, 6, (195, 195, 190)),
        (0.20, -0.45, 5, (188, 188, 182)),
        (-0.05, -0.05, 4, (193, 193, 188)),
    ]
    for dx, dy, r, col in craters:
        rx = dx * math.cos(angle) - dy * math.sin(angle)
        ry = dx * math.sin(angle) + dy * math.cos(angle)
        px = c + rx * radius
        py = c + ry * radius
        pygame.draw.circle(moon, col, (int(px), int(py)), r)

    screen.blit(moon, (cx - c, cy - c))


def draw_background():
    level = current_level

    if level == 0:
        screen.fill((170, 215, 238))
        pygame.draw.rect(screen, (120, 165, 120), (0, 500, WIDTH, 200))
        pygame.draw.line(screen, (80, 115, 95), (0, 540), (WIDTH, 540), 3)
        pygame.draw.line(screen, (90, 125, 105), (0, 585), (WIDTH, 585), 2)
        pygame.draw.circle(screen, (245, 250, 255), (120, 100), 30)
        pygame.draw.circle(screen, (245, 250, 255), (150, 95), 40)
        pygame.draw.circle(screen, (245, 250, 255), (185, 105), 28)

    elif level == 1:
        for y in range(HEIGHT):
            ratio = y / HEIGHT
            pygame.draw.line(screen,
                             (int(80 + 50 * ratio), int(100 + 30 * ratio), int(180 + 40 * ratio)),
                             (0, y), (WIDTH, y))
        for i in range(10):
            x = 40 + i * 95
            y = 480 + int(math.sin(i) * 18)
            pygame.draw.ellipse(screen, (150, 170, 215), (x, y, 130, 35))
        pygame.draw.rect(screen, (35, 45, 90), (0, 0, WIDTH, 70))

    elif level == 2:
        screen.fill((16, 35, 83))
        draw_stars(160)
        draw_meteors(0.6)
        draw_planet_decor(120, 220, 32, (90, 130, 180), ring=True,
                          ring_color=(140, 180, 230))
        pygame.draw.ellipse(screen, (40, 85, 145), (-180, 470, 1260, 500))
        pygame.draw.ellipse(screen, (65, 125, 185), (-100, 520, 1100, 400))
        pygame.draw.arc(screen, (120, 185, 225), (-80, 470, 1060, 600),
                        math.pi, math.pi * 2, 4)

    elif level == 3:
        screen.fill((8, 18, 45))
        draw_stars(200)
        draw_meteors(0.8)
        draw_planet_decor(140, 580, 45, (110, 130, 170), ring=True)
        moon_angle = pygame.time.get_ticks() / 1000.0 * 0.08
        draw_rotating_moon(765, 135, 42, moon_angle)

    elif level == 4:
        screen.fill((30, 31, 38))
        draw_stars(230)
        draw_meteors(0.7)
        draw_planet_decor(110, 180, 38, (130, 120, 110))
        draw_rotating_moon(805, 360, 115, pygame.time.get_ticks() / 1000.0 * 0.05)

    elif level == 5:
        screen.fill((5, 7, 15))
        draw_stars(260)
        draw_meteors(1.0)
        draw_planet_decor(130, 250, 40, (100, 90, 140), ring=True)

    elif level == 6:
        screen.fill((7, 5, 22))
        draw_stars(250)
        draw_meteors(1.2)
        draw_planet_decor(120, 200, 34, (140, 110, 190), ring=True)

        pulse = (math.sin(pygame.time.get_ticks() / 500) + 1) / 2
        for radius in range(130, 20, -12):
            alpha = int(12 + pulse * 15)
            nova_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.circle(nova_surface, (120, 170, 255, alpha), (450, 330), radius)
            screen.blit(nova_surface, (0, 0))
        pygame.draw.circle(screen, (150, 205, 255), (450, 330), 42)
        pygame.draw.circle(screen, (235, 245, 255), (450, 330), 23)


# ---------------------------------------------------------------------------
# 火箭绘制
# ---------------------------------------------------------------------------
ROCKET_BASE = 120


def _shade(color, factor):
    return (
        max(0, min(255, int(color[0] * factor))),
        max(0, min(255, int(color[1] * factor))),
        max(0, min(255, int(color[2] * factor))),
    )


def draw_rocket(surface, x, y, direction, color, scale=1.0, flame=True, alpha=255):
    canvas = pygame.Surface((ROCKET_BASE, ROCKET_BASE), pygame.SRCALPHA)
    body = color
    light = _shade(color, 1.32)
    dark = _shade(color, 0.70)
    darker = _shade(color, 0.46)
    cx = ROCKET_BASE // 2

    if flame:
        t = pygame.time.get_ticks() / 90.0
        flick = 1.0 + 0.16 * math.sin(t) + 0.07 * math.sin(t * 2.7 + 1.1)
        top = 84
        pygame.draw.ellipse(canvas, (255, 128, 36), (cx - 15, top, 30, int(30 * flick)))
        pygame.draw.ellipse(canvas, (255, 192, 60), (cx - 10, top + 3, 20, int(22 * flick)))
        pygame.draw.ellipse(canvas, (255, 250, 214), (cx - 5, top + 6, 10, int(14 * flick)))

    pygame.draw.polygon(canvas, dark, [(48, 58), (24, 100), (48, 92)])
    pygame.draw.polygon(canvas, dark, [(72, 58), (96, 100), (72, 92)])
    pygame.draw.rect(canvas, body, pygame.Rect(44, 30, 32, 66), border_radius=15)
    pygame.draw.polygon(canvas, body, [(60, 4), (44, 42), (76, 42)])
    pygame.draw.polygon(canvas, darker, [(50, 86), (70, 86), (75, 100), (45, 100)])
    pygame.draw.rect(canvas, light, pygame.Rect(48, 38, 6, 46), border_radius=3)
    pygame.draw.circle(canvas, darker, (60, 52), 12)
    pygame.draw.circle(canvas, (140, 210, 248), (60, 52), 9)
    pygame.draw.circle(canvas, (230, 247, 255), (57, 49), 4)

    size = max(8, int(CELL_SIZE * 0.88 * scale))
    canvas = pygame.transform.smoothscale(canvas, (size, size))

    angle = {"up": 0, "right": -90, "down": 180, "left": 90}[direction]
    if angle:
        canvas = pygame.transform.rotate(canvas, angle)
    if alpha < 255:
        canvas.set_alpha(alpha)

    surface.blit(canvas, canvas.get_rect(center=(int(x), int(y))))


def draw_trail(x, y, direction, color):
    trail_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for i in range(9):
        distance = i * 13
        if direction == "up":
            tx, ty = x, y + distance
        elif direction == "down":
            tx, ty = x, y - distance
        elif direction == "left":
            tx, ty = x + distance, y
        else:
            tx, ty = x - distance, y

        alpha = max(0, 150 - i * 17)
        radius = max(2, 10 - i)
        pygame.draw.circle(trail_surface, (255, 200, 110, alpha), (int(tx), int(ty)), radius)
        pygame.draw.circle(trail_surface, (255, 130, 40, alpha // 2), (int(tx), int(ty)), radius + 2)

    screen.blit(trail_surface, (0, 0))


# ---------------------------------------------------------------------------
# 棋盘、箭头
# ---------------------------------------------------------------------------
def draw_board():
    board_rect = pygame.Rect(BOARD_X, BOARD_Y, BOARD_SIZE, BOARD_SIZE)
    shadow = pygame.Surface((BOARD_SIZE, BOARD_SIZE), pygame.SRCALPHA)
    pygame.draw.rect(shadow, (0, 0, 0, 60), shadow.get_rect(), border_radius=20)
    screen.blit(shadow, (BOARD_X + 4, BOARD_Y + 6))

    pygame.draw.rect(screen, (245, 248, 252), board_rect, border_radius=18)
    pygame.draw.rect(screen, (170, 195, 220), board_rect, width=3, border_radius=18)

    for i in range(1, GRID_SIZE):
        x = BOARD_X + i * CELL_SIZE
        y = BOARD_Y + i * CELL_SIZE
        pygame.draw.line(screen, (215, 225, 235), (x, BOARD_Y), (x, BOARD_Y + BOARD_SIZE), 2)
        pygame.draw.line(screen, (215, 225, 235), (BOARD_X, y), (BOARD_X + BOARD_SIZE, y), 2)


def draw_arrows():
    current_time = pygame.time.get_ticks()
    for arrow in arrows:
        row, col, direction, color_index = arrow
        x, y = get_arrow_position(row, col)
        color = rocket_colors[color_index % len(rocket_colors)]
        scale = 1.0

        if hint_cell is not None and row == hint_cell[0] and col == hint_cell[1]:
            pulse = (math.sin(current_time / 100) + 1) / 2
            scale = 1.0 + pulse * 0.12
            pygame.draw.circle(screen, (255, 220, 70), (int(x), int(y)),
                               int(37 + pulse * 6), 4)

        draw_rocket(screen, x, y, direction, color, scale=scale, flame=True)


def draw_animation():
    if animation is None:
        return
    if animation["type"] == "fly":
        draw_trail(animation["x"], animation["y"], animation["direction"], animation["color"])
        draw_rocket(screen, animation["x"], animation["y"], animation["direction"],
                    animation["color"], scale=1.0, flame=True)
    elif animation["type"] == "collision":
        color = animation["color"]
        if animation["phase"] == "red":
            color = RED
        draw_trail(animation["x"], animation["y"], animation["direction"], color)
        draw_rocket(screen, animation["x"], animation["y"], animation["direction"],
                    color, scale=1.0, flame=True)


# ---------------------------------------------------------------------------
# 特效
# ---------------------------------------------------------------------------
def draw_star(surface, x, y, radius, alpha, scale):
    alpha = max(0, min(255, int(alpha)))
    radius = int(radius * scale)
    glow = pygame.Surface((90, 90), pygame.SRCALPHA)
    center = (45, 45)
    for extra in range(25, 3, -3):
        glow_alpha = int(alpha * 0.16 * (1 - extra / 28))
        if glow_alpha > 0:
            pygame.draw.circle(glow, (255, 215, 70, glow_alpha), center, radius + extra)
    surface.blit(glow, (x - 45, y - 45))

    points = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        r = radius if i % 2 == 0 else radius * 0.42
        points.append((int(x + math.cos(angle) * r), int(y + math.sin(angle) * r)))

    pygame.draw.polygon(surface, (255, 215, 70, int(alpha)), points)
    pygame.draw.polygon(surface, (255, 242, 155, int(alpha)), points, 2)


def draw_flowing_star(target, cx, cy, index, base_size=12, alpha_base=190):
    current_time = pygame.time.get_ticks()
    phase = current_time / 420.0 - index * 1.1
    wave = (math.sin(phase) + 1) / 2

    alpha = max(0, min(255, int(alpha_base + 65 * wave)))
    scale = 1.0 + 0.14 * wave

    glow_alpha = int(90 + 90 * wave)
    glow_r = int(24 + 8 * wave)
    glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
    gc = glow_r
    for k in range(6, 0, -1):
        ga = int(glow_alpha * (1 - k / 7) / 2)
        if ga <= 0:
            continue
        pygame.draw.circle(glow, (255, 220, 110, ga), (gc, gc), int(glow_r * k / 6))
    target.blit(glow, (cx - gc, cy - gc))

    draw_star(target, cx, cy, base_size, alpha, scale)


def draw_star_explosion():
    if star_explosion is None:
        return
    x, y = star_explosion["x"], star_explosion["y"]
    progress = star_explosion["timer"] / star_explosion["duration"]
    alpha = int(255 * (1 - progress))

    surf_size = 170
    surface = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
    center = (surf_size // 2, surf_size // 2)

    glow_radius = int(12 + progress * 52)
    if glow_radius > 0:
        pygame.draw.circle(surface, (255, 200, 80, alpha // 4), center, glow_radius)
        pygame.draw.circle(surface, (255, 230, 140, alpha // 3), center, int(glow_radius * 0.6))

    for i in range(16):
        angle = i * math.pi * 2 / 16
        sd = 5
        ed = 12 + progress * 58
        sx = center[0] + math.cos(angle) * sd
        sy = center[1] + math.sin(angle) * sd
        ex = center[0] + math.cos(angle) * ed
        ey = center[1] + math.sin(angle) * ed
        pygame.draw.line(surface, (255, 210, 60, alpha), (int(sx), int(sy)), (int(ex), int(ey)), 3)
        pygame.draw.line(surface, (255, 255, 220, alpha), (int(sx), int(sy)),
                         (int(center[0] + math.cos(angle) * ed * 0.6),
                          int(center[1] + math.sin(angle) * ed * 0.6)), 2)

    radius = int(6 + progress * 26)
    if radius > 0:
        pygame.draw.circle(surface, (255, 245, 200, alpha), center, radius)
        pygame.draw.circle(surface, (255, 255, 255, alpha), center, max(1, radius // 2))

    screen.blit(surface, (x - surf_size // 2, y - surf_size // 2))


def start_explosion(x, y, size=1.0):
    particles = []
    count = int(22 * size)
    for _ in range(count):
        angle = random.random() * math.pi * 2
        speed = random.uniform(2.5, 8.5) * size
        particles.append({
            "x": x, "y": y,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "r": random.uniform(2.5, 6.5) * size,
            "color_choice": random.random(),
        })
    explosions.append({
        "x": x, "y": y, "timer": 0, "duration": 60,
        "size": size, "particles": particles,
    })


def update_explosions():
    global explosions
    if not explosions:
        return
    for e in explosions:
        e["timer"] += 1
        for p in e["particles"]:
            p["x"] += p["vx"]
            p["y"] += p["vy"]
            p["vx"] *= 0.92
            p["vy"] *= 0.92
    explosions = [e for e in explosions if e["timer"] < e["duration"]]


def draw_explosions():
    for e in explosions:
        progress = e["timer"] / e["duration"]
        x, y, size = e["x"], e["y"], e["size"]

        ring_p = min(1.0, progress * 1.5)
        ring_radius = int((6 + ring_p * 62) * size)
        ring_alpha = max(0, int(220 * (1 - ring_p)))

        if ring_alpha > 0 and ring_radius > 1:
            surf_size = ring_radius * 2 + 12
            ring_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
            center = (surf_size // 2, surf_size // 2)
            ring_width = max(1, int(7 * (1 - ring_p)))
            pygame.draw.circle(ring_surf, (255, 210, 90, ring_alpha), center, ring_radius, ring_width)
            pygame.draw.circle(ring_surf, (255, 110, 45, ring_alpha // 2), center,
                               max(1, ring_radius - ring_width), max(1, ring_width // 2))
            screen.blit(ring_surf, (int(x - surf_size // 2), int(y - surf_size // 2)))

        if progress < 0.4:
            flash_p = progress / 0.4
            flash_alpha = int(255 * (1 - flash_p))
            flash_r = int(50 * size * (1 - flash_p * 0.4))
            if flash_r > 0:
                surf_size = flash_r * 2 + 4
                flash_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
                center = (surf_size // 2, surf_size // 2)
                pygame.draw.circle(flash_surf, (255, 180, 70, flash_alpha // 4), center, flash_r)
                pygame.draw.circle(flash_surf, (255, 220, 110, flash_alpha * 3 // 4),
                                   center, int(flash_r * 0.72))
                pygame.draw.circle(flash_surf, (255, 255, 245, flash_alpha), center,
                                   max(1, int(flash_r * 0.4)))
                screen.blit(flash_surf, (int(x - surf_size // 2), int(y - surf_size // 2)))

        for p in e["particles"]:
            p_alpha = max(0, int(255 * (1 - progress)))
            r = max(1, int(p["r"] * (1 - progress * 0.6)))
            c = p["color_choice"]
            if c < 0.35:
                pcolor = (255, 250, 200)
            elif c < 0.7:
                pcolor = (255, 175, 60)
            else:
                pcolor = (240, 90, 40)

            surf_size = r * 4 + 4
            p_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
            center = (surf_size // 2, surf_size // 2)
            pygame.draw.circle(p_surf, (pcolor[0], pcolor[1], pcolor[2], p_alpha // 3), center, r * 2)
            pygame.draw.circle(p_surf, (pcolor[0], pcolor[1], pcolor[2], p_alpha), center, r)
            screen.blit(p_surf, (int(p["x"] - surf_size // 2), int(p["y"] - surf_size // 2)))


# ---------------------------------------------------------------------------
# 右侧信息面板
# ---------------------------------------------------------------------------
def draw_side_panel():
    px, py, pw, ph = PANEL_X, PANEL_Y, PANEL_W, PANEL_H
    cx = px + pw // 2

    panel_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
    panel_surf.fill((14, 24, 44, 178))
    pygame.draw.rect(panel_surf, (90, 135, 190, 165), panel_surf.get_rect(),
                     width=2, border_radius=16)
    screen.blit(panel_surf, (px, py))

    bar = pygame.Surface((pw - 40, 4), pygame.SRCALPHA)
    pygame.draw.rect(bar, (120, 180, 240, 200), bar.get_rect(), border_radius=2)
    screen.blit(bar, (px + 20, py + 12))

    blit_text(f"第 {current_level + 1} / 7 关",
              font_small, (150, 195, 240),
              shadow_alpha=0, center=(cx, py + 34))

    blit_text(level_names[current_level],
              font_big, (245, 250, 255),
              shadow_alpha=60, center=(cx, py + 68))

    star_y = py + 112
    spacing = 40
    if mistakes > 0:
        total_w = (mistakes - 1) * spacing
        start_x = cx - total_w // 2
        for i in range(mistakes):
            draw_flowing_star(screen, start_x + i * spacing, star_y, i,
                              base_size=13, alpha_base=195)

    sep1 = py + 148
    pygame.draw.line(screen, (80, 125, 180), (px + 20, sep1), (px + pw - 20, sep1), 1)

    best = best_times[current_level]
    best_text = "--" if best is None else format_time(best)

    info_items = [
        ("时间", format_time(current_elapsed)),
        ("本关最佳", best_text),
        ("剩余火箭", str(len(arrows))),
    ]
    info_y = sep1 + 24
    for i, (label, value) in enumerate(info_items):
        y = info_y + i * 27
        blit_text(label, font_tiny, (145, 180, 220),
                  shadow_alpha=0, midleft=(px + 24, y))
        blit_text(value, font_small, (240, 246, 255),
                  shadow_alpha=20, midright=(px + pw - 24, y))

    sep2 = info_y + 3 * 27 + 8
    pygame.draw.line(screen, (80, 125, 180), (px + 20, sep2), (px + pw - 20, sep2), 1)

    blit_text("✦ 探险日记 ✦", font_small, (160, 205, 245),
              shadow_alpha=0, center=(cx, sep2 + 24))

    story = level_stories[current_level]
    lines = wrap_text(story, font_tiny, pw - 44)
    story_y = sep2 + 54
    for line in lines:
        blit_text(line, font_tiny, (212, 226, 245),
                  shadow_alpha=0, center=(cx, story_y))
        story_y += 24


def update_game_buttons(mouse_pos):
    update_button_state("game_restart", GAME_BTN_RESTART, mouse_pos)
    update_button_state("game_pause", GAME_BTN_PAUSE, mouse_pos)
    update_button_state("game_hint", GAME_BTN_HINT, mouse_pos)
    update_button_state("game_sound", GAME_BTN_SOUND, mouse_pos)


# ---------------------------------------------------------------------------
# 关卡画面主绘制
# ---------------------------------------------------------------------------
def draw_game_screen():
    draw_background()
    draw_art_title_with_decor(screen, BOARD_X + BOARD_SIZE // 2, 54, scale=0.72)
    draw_side_panel()
    draw_board()
    draw_arrows()
    draw_animation()
    draw_explosions()

    draw_animated_button("game_restart", GAME_BTN_RESTART, "重新开始",
                         target=screen, font=font_button_tiny)
    draw_animated_button("game_pause", GAME_BTN_PAUSE, "暂停",
                         target=screen, font=font_button_tiny)
    draw_animated_button("game_hint", GAME_BTN_HINT, "提示",
                         target=screen, font=font_button_tiny)

    if audio_system.sound_on:
        draw_animated_button("game_sound", GAME_BTN_SOUND, "音效开",
                             color=BUTTON_GOLD, hover=BUTTON_GOLD_HOVER,
                             target=screen, font=font_button_tiny)
    else:
        draw_animated_button("game_sound", GAME_BTN_SOUND, "音效关",
                             color=BUTTON_HOME, hover=BUTTON_HOME_HOVER,
                             target=screen, font=font_button_tiny)


# ---------------------------------------------------------------------------
# 暂停 / 失败 / 关卡完成弹窗
# ---------------------------------------------------------------------------
def draw_pause_screen():
    draw_game_screen()

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 135))
    screen.blit(overlay, (0, 0))

    panel = pygame.Rect(260, 165, 380, 405)
    pygame.draw.rect(screen, (245, 248, 252), panel, border_radius=20)
    pygame.draw.rect(screen, (190, 205, 220), panel, width=3, border_radius=20)

    blit_text("游戏暂停", font_big, TEXT_COLOR, center=(450, 215))
    blit_text("火箭和计时器已经暂停", font_small, SUB_TEXT, center=(450, 260))

    draw_animated_button(
        "pause_continue", pygame.Rect(350, 320, 200, 48),
        "继续探索", color=BUTTON_GOLD, hover=BUTTON_GOLD_HOVER
    )
    draw_animated_button(
        "pause_current", pygame.Rect(350, 378, 200, 48),
        "重新开始本关", color=BUTTON_HOME, hover=BUTTON_HOME_HOVER
    )
    draw_animated_button(
        "pause_first", pygame.Rect(350, 436, 200, 48),
        "从第一关开始", color=BUTTON_HOME, hover=BUTTON_HOME_HOVER
    )
    draw_animated_button(
        "pause_home", pygame.Rect(350, 494, 200, 48),
        "返回首页", color=BUTTON_HOME, hover=BUTTON_HOME_HOVER
    )

def draw_fail_screen():
    draw_background()

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 130))
    screen.blit(overlay, (0, 0))

    blit_text("任务失败", font_title, (255, 120, 110), center=(450, 230))
    blit_text("飞船耐久已经耗尽", font_normal, WHITE, center=(450, 290))
    blit_text(f"本次用时：{format_time(current_elapsed)}", font_small,
              (225, 232, 245), center=(450, 328))

    draw_animated_button("fail_restart", pygame.Rect(230, 390, 200, 55),
                         "重新挑战", color=BUTTON_GOLD, hover=BUTTON_GOLD_HOVER)
    draw_animated_button("fail_home", pygame.Rect(470, 390, 200, 55),
                         "返回首页", color=BUTTON_HOME, hover=BUTTON_HOME_HOVER)


def _blur_surface(surf, factor=7):
    w, h = surf.get_size()
    sw = max(1, w // factor)
    sh = max(1, h // factor)
    small = pygame.transform.smoothscale(surf, (sw, sh))
    return pygame.transform.smoothscale(small, (w, h))


def _draw_modal_decor(target, panel):
    t = pygame.time.get_ticks() / 1000.0
    draw_space_decor(target, panel.left + 26, panel.top + 24, "planet", size=10, alpha=230)
    draw_space_decor(target, panel.right - 32, panel.top + 26, "comet", size=12, alpha=225)
    draw_space_decor(target, panel.left + 28, panel.bottom - 28, "rocket", size=12, alpha=230)

    pulse = (math.sin(t * 2.2) + 1) / 2
    draw_space_decor(target, panel.right - 30, panel.bottom - 30, "star",
                     size=9, alpha=int(180 + 70 * pulse))

    p2 = (math.sin(t * 2.2 + 1.4) + 1) / 2
    draw_space_decor(target, panel.centerx - 130, panel.top + 18, "star",
                     size=6, alpha=int(160 + 70 * p2))
    p3 = (math.sin(t * 2.2 + 2.8) + 1) / 2
    draw_space_decor(target, panel.centerx + 130, panel.top + 18, "star",
                     size=7, alpha=int(160 + 70 * p3))


def _draw_modal_panel(target, info, ease):
    is_final = info["is_final"]

    panel_w, panel_h = 520, 500
    panel = pygame.Rect(0, 0, panel_w, panel_h)
    panel.center = (WIDTH // 2, HEIGHT // 2)
    cx = panel.centerx

    panel_shadow = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel_shadow, (0, 0, 0, 100), panel_shadow.get_rect(), border_radius=26)
    target.blit(panel_shadow, (panel.x + 4, panel.y + 8))

    panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
    pygame.draw.rect(panel_surf, (250, 250, 253, 250), panel_surf.get_rect(), border_radius=24)
    target.blit(panel_surf, panel.topleft)

    if is_final or info["is_record"]:
        border_color = (240, 190, 100)
    else:
        border_color = (170, 200, 230)
    pygame.draw.rect(target, border_color, panel, width=3, border_radius=24)

    bar = pygame.Surface((panel_w - 60, 5), pygame.SRCALPHA)
    bar_color = (240, 190, 100) if (is_final or info["is_record"]) else (130, 180, 230)
    pygame.draw.rect(bar, bar_color, bar.get_rect(), border_radius=3)
    target.blit(bar, (panel.x + 30, panel.y + 20))

    if is_final:
        title_text = "探索完成！"
        title_color = (225, 155, 35)
    else:
        title_text = "关卡完成！"
        title_color = (52, 110, 180)

    title_surf = font_modal_title.render(title_text, True, title_color)
    title_rect = title_surf.get_rect(center=(cx, panel.y + 68))
    glow = font_modal_title.render(title_text, True, (255, 220, 130))
    glow.set_alpha(80)
    for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
        target.blit(glow, glow.get_rect(center=(title_rect.centerx + dx, title_rect.centery + dy)))
    target.blit(title_surf, title_rect)

    pygame.draw.line(target, (225, 230, 238),
                     (panel.x + 60, panel.y + 102), (panel.right - 60, panel.y + 102), 1)

    blit_text(f"本关用时  {info['time']:.2f} 秒",
              font_big, (42, 52, 72),
              shadow_alpha=25, target=target, center=(cx, panel.y + 142))

    if info["is_record"]:
        pulse = (math.sin(pygame.time.get_ticks() / 180) + 1) / 2
        gold = (255, int(175 + pulse * 45), int(35 + pulse * 45))
        rec_text = "新纪录！恭喜！"
        rec_surf = font_big.render(rec_text, True, gold)
        rec_rect = rec_surf.get_rect(center=(cx, panel.y + 194))
        glow = font_big.render(rec_text, True, (255, 200, 90))
        glow.set_alpha(90)
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            target.blit(glow, glow.get_rect(center=(rec_rect.centerx + dx, rec_rect.centery + dy)))
        target.blit(rec_surf, rec_rect)
    else:
        blit_text(f"历史最佳记录  {info['best']:.2f} 秒",
                  font_normal, (130, 145, 165),
                  shadow_alpha=15, target=target, center=(cx, panel.y + 194))

    m = info["mistakes"]
    star_y = panel.y + 258
    spacing = 46

    if m > 0:
        total_w = (m - 1) * spacing
        start_x = cx - total_w // 2
        for i in range(m):
            if is_final:
                pulse = (math.sin(pygame.time.get_ticks() / 220) + 1) / 2
                scale = 1.0 + 0.22 * pulse
                alpha = int(200 + 55 * pulse)
                glow_r = int(30 + 10 * pulse)
                glow = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
                gc = glow_r
                for k in range(7, 0, -1):
                    ga = int((120 + 90 * pulse) * (1 - k / 8) / 2)
                    if ga <= 0:
                        continue
                    pygame.draw.circle(glow, (255, 225, 120, ga), (gc, gc), int(glow_r * k / 7))
                target.blit(glow, (start_x + i * spacing - gc, star_y - gc))
                draw_star(target, start_x + i * spacing, star_y, 17, alpha, scale)
            else:
                draw_flowing_star(target, start_x + i * spacing, star_y, i,
                                  base_size=16, alpha_base=210)

    congrats = level_congrats[info["level"]]
    lines = wrap_text(congrats, font_normal, panel_w - 100)
    text_y = panel.y + 320
    for line in lines:
        blit_text(line, font_normal, (78, 92, 115),
                  shadow_alpha=10, target=target, center=(cx, text_y))
        text_y += 30

    _draw_modal_decor(target, panel)

    if is_final:
        home_rect = pygame.Rect(0, 0, 200, 52)
        home_rect.center = (cx, panel.bottom - 58)
        draw_animated_button("modal_home", home_rect, "返回首页",
                             color=BUTTON_GOLD, hover=BUTTON_GOLD_HOVER, target=target)
    else:
        home_rect = pygame.Rect(0, 0, 170, 52)
        next_rect = pygame.Rect(0, 0, 170, 52)
        home_rect.center = (cx - 96, panel.bottom - 58)
        next_rect.center = (cx + 96, panel.bottom - 58)
        draw_animated_button("modal_home", home_rect, "返回首页",
                             color=BUTTON_HOME, hover=BUTTON_HOME_HOVER, target=target)
        draw_animated_button("modal_next", next_rect, "下一关",
                             color=BUTTON_GOLD, hover=BUTTON_GOLD_HOVER, target=target)


def draw_level_complete_screen():
    global final_explosion_timer, _blur_cache

    info = level_complete_info
    is_final = info["is_final"]

    draw_game_screen()

    if is_final:
        progress = min(final_explosion_timer / 80, 1)
        flash_alpha = int(170 * (1 - progress))
        if flash_alpha > 0:
            flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 240, 200, flash_alpha))
            screen.blit(flash, (0, 0))

        radius = int(80 + progress * 460)
        nova = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(nova, (255, 220, 140, int(130 * (1 - progress))),
                           (WIDTH // 2, HEIGHT // 2), radius)
        pygame.draw.circle(nova, (255, 245, 210, int(95 * (1 - progress))),
                           (WIDTH // 2, HEIGHT // 2), int(radius * 0.6))
        screen.blit(nova, (0, 0))

    t = min(1.0, level_complete_anim / 24.0)
    ease = 1 - (1 - t) ** 3

    if _blur_cache is None:
        captured = screen.copy()
        _blur_cache = _blur_surface(captured, factor=8)

    overlay_alpha = int(200 * ease)
    blurred = _blur_cache.copy()
    darken = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    darken.fill((6, 10, 22, 165))
    blurred.blit(darken, (0, 0))
    blurred.set_alpha(overlay_alpha)
    screen.blit(blurred, (0, 0))

    scale = 0.90 + 0.10 * ease

    tmp = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    _draw_modal_panel(tmp, info, ease)

    panel_region = tmp.subsurface((190, 100, 520, 500)).copy()
    scaled_w = int(520 * scale)
    scaled_h = int(500 * scale)
    scaled = pygame.transform.smoothscale(panel_region, (scaled_w, scaled_h))
    scaled.set_alpha(int(255 * ease))

    screen.blit(scaled, scaled.get_rect(center=(WIDTH // 2, HEIGHT // 2)))


# ---------------------------------------------------------------------------
# 游戏逻辑更新
# ---------------------------------------------------------------------------
def find_hint_arrow():
    for arrow in arrows:
        if get_blocking_arrow(arrow) is None:
            return arrow
    return None


def start_fly_animation(arrow):
    global animation
    row, col, direction, color_index = arrow
    start_x, start_y = get_arrow_position(row, col)
    color = rocket_colors[color_index % len(rocket_colors)]

    if direction == "up":
        target_x, target_y = start_x, BOARD_Y - 90
    elif direction == "down":
        target_x, target_y = start_x, BOARD_Y + BOARD_SIZE + 90
    elif direction == "left":
        target_x, target_y = BOARD_X - 90, start_y
    else:
        target_x, target_y = BOARD_X + BOARD_SIZE + 90, start_y

    animation = {
        "type": "fly",
        "x": start_x, "y": start_y,
        "target_x": target_x, "target_y": target_y,
        "direction": direction,
        "color": color,
        "speed": 16,
        "arrow": arrow,
    }
    audio_system.play_launch()


def update_fly_animation():
    global animation
    if animation is None:
        return

    dx = animation["target_x"] - animation["x"]
    dy = animation["target_y"] - animation["y"]
    distance = math.sqrt(dx * dx + dy * dy)

    if distance <= animation["speed"]:
        animation = None
        check_level_complete()
        return

    animation["x"] += dx / distance * animation["speed"]
    animation["y"] += dy / distance * animation["speed"]


def check_level_complete():
    global level_complete_info, level_complete_anim, _blur_cache
    global continue_level, signal

    if len(arrows) != 0 or level_complete_info is not None:
        return

    finish_time = current_elapsed
    old_best = best_times[current_level]
    is_record = old_best is None or finish_time < old_best

    if is_record:
        best_times[current_level] = finish_time
        best = finish_time
    else:
        best = old_best

    time_records[current_level]["runs"].append(finish_time)
    time_records[current_level]["last"] = finish_time
    time_records[current_level]["best"] = best
    saved = save_time_records(time_records)
    is_final = current_level == len(levels) - 1

    level_complete_info = {
        "level": current_level,
        "time": finish_time,
        "is_record": is_record,
        "best": best,
        "mistakes": mistakes,
        "is_final": is_final,
        "previous_best": old_best,
        "saved": saved,
    }

    if not is_final:
        continue_level = current_level + 1
    else:
        continue_level = len(levels) - 1

    level_complete_anim = 0
    _blur_cache = None
    audio_system.play_win()
    signal = "complete"


def start_collision_animation(arrow, blocker):
    global animation
    row, col, direction, color_index = arrow
    start_x, start_y = get_arrow_position(row, col)
    blocker_x, blocker_y = get_arrow_position(blocker[0], blocker[1])

    if direction == "up":
        target_x, target_y = start_x, blocker_y + 32
    elif direction == "down":
        target_x, target_y = start_x, blocker_y - 32
    elif direction == "left":
        target_x, target_y = blocker_x + 32, start_y
    else:
        target_x, target_y = blocker_x - 32, start_y

    color = rocket_colors[color_index % len(rocket_colors)]

    animation = {
        "type": "collision",
        "phase": "move",
        "x": start_x, "y": start_y,
        "start_x": start_x, "start_y": start_y,
        "target_x": target_x, "target_y": target_y,
        "direction": direction,
        "color": color,
        "arrow": arrow,
        "speed": 11,
        "timer": 0,
    }


def update_collision_animation():
    global animation, mistakes, star_explosion, signal

    if animation is None:
        return
    if animation["type"] != "collision":
        return

    phase = animation.get("phase", "move")

    if phase == "move":
        dx = animation["target_x"] - animation["x"]
        dy = animation["target_y"] - animation["y"]
        distance = math.sqrt(dx * dx + dy * dy)

        if distance <= animation["speed"]:
            animation["x"] = animation["target_x"]
            animation["y"] = animation["target_y"]
            animation["phase"] = "red"
            animation["timer"] = 0
            start_explosion(animation["x"], animation["y"], size=1.25)
            audio_system.play_explosion()
            audio_system.play_star_lost()
            mistakes -= 1
            start_star_explosion(mistakes)
        else:
            animation["x"] += dx / distance * animation["speed"]
            animation["y"] += dy / distance * animation["speed"]

    elif phase == "red":
        animation["timer"] += 1
        if animation["timer"] >= 16:
            animation["phase"] = "return"

    elif phase == "return":
        dx = animation["start_x"] - animation["x"]
        dy = animation["start_y"] - animation["y"]
        distance = math.sqrt(dx * dx + dy * dy)

        if distance <= animation["speed"]:
            animation["x"] = animation["start_x"]
            animation["y"] = animation["start_y"]
            arrows.append(animation["arrow"])
            animation = None
            if mistakes <= 0:
                audio_system.play_fail()
                signal = "fail"
        else:
            animation["x"] += dx / distance * animation["speed"]
            animation["y"] += dy / distance * animation["speed"]


def start_star_explosion(star_index):
    global star_explosion
    if star_index < 0:
        star_index = 0
    if star_index > 2:
        star_index = 2

    m = max(1, mistakes + 1)
    spacing = 40
    total_w = (m - 1) * spacing
    cx = PANEL_X + PANEL_W // 2
    start_x = cx - total_w // 2

    star_explosion = {
        "x": start_x + star_index * spacing,
        "y": PANEL_Y + 112,
        "timer": 0,
        "duration": 36,
    }


def update_star_explosion():
    global star_explosion
    if star_explosion is None:
        return
    star_explosion["timer"] += 1
    if star_explosion["timer"] >= star_explosion["duration"]:
        star_explosion = None


def show_hint():
    global hint_cell, hint_timer
    target = find_hint_arrow()
    if target is None:
        return
    hint_cell = (target[0], target[1])
    hint_timer = 200


def update_hint():
    global hint_cell, hint_timer
    if hint_cell is None:
        return
    hint_timer -= 1
    if hint_timer <= 0:
        hint_cell = None


def get_game_time():
    return (pygame.time.get_ticks() - level_start_time - paused_total) / 1000


def reset_progress():
    global current_level, continue_level
    current_level = 0
    continue_level = 0


# ---------------------------------------------------------------------------
# 像素风关卡绘制覆盖：仅替换视觉，不改变任何玩法状态
# ---------------------------------------------------------------------------
def draw_stars(count):
    for i, s in enumerate(background_stars[:count]):
        size = 2 if i % 7 else 4
        col = (116, 165, 207) if i % 5 else (247, 222, 132)
        pygame.draw.rect(screen, col, (int(s["x"]), int(s["y"]), size, size))


def draw_meteors(dt_scale=1.0):
    for i, m in enumerate(meteors):
        phase = (pygame.time.get_ticks()/700 + i*1.7) % 7
        x = int((m["x"] + phase*38) % (WIDTH+100)) - 50
        y = int((m["y"] + phase*18) % 430)
        pygame.draw.line(screen, (112, 165, 206), (x, y), (x-24, y-12), 3)
        pygame.draw.rect(screen, (236, 235, 206), (x-2, y-2, 5, 5))


def draw_planet_decor(cx, cy, radius, color, ring=False, ring_color=None):
    pygame.draw.circle(screen, _shade(color, .62), (cx+4, cy+4), radius)
    pygame.draw.circle(screen, color, (cx, cy), radius)
    pygame.draw.rect(screen, _shade(color, 1.25), (cx-radius//2, cy-radius//2, radius//2, max(4, radius//5)))
    if ring:
        pygame.draw.ellipse(screen, ring_color or (181, 155, 208),
                            (cx-int(radius*1.7), cy-int(radius*.38), int(radius*3.4), int(radius*.76)), 4)


def draw_rotating_moon(cx, cy, radius, angle):
    pygame.draw.circle(screen, (91, 92, 104), (cx+5, cy+5), radius)
    pygame.draw.circle(screen, (184, 181, 169), (cx, cy), radius)
    for dx, dy, rr in [(-.35,-.25,.16),(.3,-.1,.12),(.1,.35,.14),(-.3,.3,.09)]:
        pygame.draw.circle(screen, (137, 136, 132),
                           (int(cx+dx*radius), int(cy+dy*radius)), max(3,int(rr*radius)))


def draw_background():
    palettes = [(19,43,71),(31,34,81),(12,31,70),(7,15,42),(28,28,38),(5,7,18),(12,5,29)]
    screen.fill(palettes[current_level])
    draw_stars(90 + current_level*22)
    if current_level >= 2:
        draw_meteors(.7)
    if current_level == 0:
        pygame.draw.rect(screen, (72, 105, 93), (0, 500, WIDTH, 200))
        pygame.draw.rect(screen, (44, 66, 70), (0, 540, WIDTH, 12))
        for x in range(0, WIDTH, 48):
            pygame.draw.rect(screen, (99, 130, 104), (x, 492, 30, 8))
    elif current_level == 1:
        for y in range(450, HEIGHT, 24):
            pygame.draw.rect(screen, (50+y//12, 67+y//15, 112+y//18), (0,y,WIDTH,24))
    elif current_level == 2:
        pygame.draw.ellipse(screen, (35,78,137), (-160,500,1220,420))
        pygame.draw.ellipse(screen, (71,133,174), (-100,535,1100,390), 8)
    elif current_level == 3:
        draw_rotating_moon(780, 145, 46, 0)
    elif current_level == 4:
        draw_rotating_moon(805, 355, 118, 0)
    elif current_level == 5:
        draw_planet_decor(130, 245, 44, (77,62,119), True)
    elif current_level == 6:
        pulse = int(8 + 4*math.sin(pygame.time.get_ticks()/180))
        for r, c in [(110,(43,70,130)),(74,(77,129,188)),(40,(177,213,235)),(18,(255,249,215))]:
            pygame.draw.circle(screen, c, (450,330), r+pulse)


def draw_rocket(surface, x, y, direction, color, scale=1.0, flame=True, alpha=255):
    u = max(2, int(4*scale))
    ship = pygame.Surface((17*u, 17*u), pygame.SRCALPHA)
    # 默认朝上，以方块构造清晰 8-bit 轮廓
    cx = 8*u
    dark = _shade(color,.55); light = _shade(color,1.32)
    pygame.draw.rect(ship, dark, (5*u,8*u,3*u,5*u))
    pygame.draw.rect(ship, dark, (9*u,8*u,3*u,5*u))
    pygame.draw.rect(ship, color, (6*u,4*u,5*u,8*u))
    pygame.draw.rect(ship, color, (7*u,2*u,3*u,2*u))
    pygame.draw.rect(ship, light, (7*u,5*u,u,5*u))
    pygame.draw.rect(ship, (105,190,222), (8*u,6*u,2*u,2*u))
    if flame:
        pygame.draw.rect(ship, (249,181,55), (7*u,12*u,3*u,2*u))
        pygame.draw.rect(ship, (241,83,45), (8*u,14*u,u,(2+(pygame.time.get_ticks()//120)%2)*u))
    angle = {"up":0,"right":-90,"down":180,"left":90}[direction]
    if angle: ship = pygame.transform.rotate(ship, angle)
    if alpha < 255: ship.set_alpha(alpha)
    surface.blit(ship, ship.get_rect(center=(int(x),int(y))))


def draw_trail(x, y, direction, color):
    for i in range(6):
        d=i*12; sz=max(3,9-i)
        tx=x+(d if direction=="left" else -d if direction=="right" else 0)
        ty=y+(d if direction=="up" else -d if direction=="down" else 0)
        pygame.draw.rect(screen, (247,156-i*12,48), (int(tx-sz/2),int(ty-sz/2),sz,sz))


def draw_board():
    shadow = pygame.Rect(BOARD_X+8,BOARD_Y+8,BOARD_SIZE,BOARD_SIZE)
    pygame.draw.rect(screen,(5,9,24),shadow)
    board_rect=pygame.Rect(BOARD_X,BOARD_Y,BOARD_SIZE,BOARD_SIZE)
    pygame.draw.rect(screen,(20,31,56),board_rect)
    pygame.draw.rect(screen,(89,145,183),board_rect,4)
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if (row+col)%2==0:
                pygame.draw.rect(screen,(25,41,70),(BOARD_X+col*CELL_SIZE,BOARD_Y+row*CELL_SIZE,CELL_SIZE,CELL_SIZE))
    for i in range(1,GRID_SIZE):
        pygame.draw.line(screen,(47,72,102),(BOARD_X+i*CELL_SIZE,BOARD_Y),(BOARD_X+i*CELL_SIZE,BOARD_Y+BOARD_SIZE),2)
        pygame.draw.line(screen,(47,72,102),(BOARD_X,BOARD_Y+i*CELL_SIZE),(BOARD_X+BOARD_SIZE,BOARD_Y+i*CELL_SIZE),2)
    pygame.draw.rect(screen,(89,145,183),board_rect,4)


def draw_star(surface, x, y, radius, alpha, scale):
    r=max(4,int(radius*scale)); col=(250,210,68, max(0,min(255,int(alpha))))
    pygame.draw.rect(surface,col,(x-r//3,y-r,r//2,2*r))
    pygame.draw.rect(surface,col,(x-r,y-r//3,2*r,r//2))
    pygame.draw.rect(surface,(255,245,174,col[3]),(x-2,y-2,5,5))


def draw_side_panel():
    px,py,pw,ph=PANEL_X,PANEL_Y,PANEL_W,PANEL_H; cx=px+pw//2
    config.pixel_rect(screen,(px,py,pw,ph),(13,25,49),border=(69,119,164),width=3)
    pygame.draw.rect(screen,(36,75,113),(px+10,py+10,pw-20,28))
    blit_text(f"STAGE {current_level+1:02d} / 07",font_small,(129,207,226),shadow_alpha=0,center=(cx,py+24))
    blit_text(level_names[current_level],font_big,(247,235,191),shadow_alpha=0,center=(cx,py+66))
    for i in range(max(0,mistakes)):
        draw_star(screen,cx+(i-1)*40,py+108,13,255,1)
    pygame.draw.line(screen,(54,91,128),(px+18,py+140),(px+pw-18,py+140),2)
    best=best_times[current_level]
    items=[("TIME",format_time(current_elapsed)),("BEST","--" if best is None else format_time(best)),("ROCKET",str(len(arrows)))]
    for i,(label,value) in enumerate(items):
        yy=py+174+i*34
        blit_text(label,font_tiny,(105,160,196),shadow_alpha=0,midleft=(px+22,yy))
        blit_text(value,font_small,(239,240,225),shadow_alpha=0,midright=(px+pw-22,yy))
    pygame.draw.line(screen,(54,91,128),(px+18,py+282),(px+pw-18,py+282),2)
    blit_text("MISSION LOG",font_small,(238,174,65),shadow_alpha=0,center=(cx,py+308))
    story=format_diary(level_stories[current_level])
    lines=wrap_text(story,font_tiny,pw-42)
    yy=py+338
    spacing=min(24, max(17, (GAME_BTN_RESTART.top-16-yy)//max(1,len(lines))))
    for line in lines:
        blit_text(line,font_tiny,(188,205,218),shadow_alpha=0,center=(cx,yy)); yy+=spacing


# 共享参考图风格；颜色仅改变火箭尖头和尾翼，不改变发射方向。
def draw_rocket(surface,x,y,direction,color,scale=1.0,flame=True,alpha=255):
    config.art_rocket(surface,x,y,int(CELL_SIZE*.9*scale),direction,
                            tuple(color),flame=flame,alpha=alpha)

def draw_planet_decor(cx,cy,radius,color,ring=False,ring_color=None):
    config.art_planet(screen,cx,cy,radius,tuple(color))

def draw_rotating_moon(cx,cy,radius,angle):
    config.art_planet(screen,cx,cy,radius,(164,148,192))


def format_diary(text):
    return text.replace("，","\n").replace(",","\n").replace("。","\n……").replace(".","\n……")


def draw_star(surface,x,y,radius,alpha,scale):
    config.art_star(surface,x,y,radius*scale,alpha)


def draw_flowing_star(target,cx,cy,index,base_size=12,alpha_base=190):
    wave=(math.sin(pygame.time.get_ticks()/420-index)+1)/2
    config.art_star(target,cx,cy,base_size*(1+.10*wave),min(255,alpha_base+60*wave))


def draw_stars(count):
    for i,s in enumerate(background_stars[:count]):
        config.art_star(screen,s["x"],s["y"],3 if i%6 else 5,140 if i%3 else 210)


_base_game_screen=draw_game_screen

def draw_game_screen():
    _base_game_screen()
    # 在棋盘与 HUD 之外布置，避免遮挡火箭和按钮。
    for x,y,r in [(23,170,7),(20,340,6),(22,510,8),(90,680,7),(370,680,6),(590,230,6),(590,500,6),(854,55,8)]:
        config.art_star(screen,x,y,r)
    for x,y,r,col in [(78,58,16,(142,163,208)),(540,73,13,(178,136,196)),(745,58,18,(140,184,165)),(230,677,8,(188,145,176))]:
        config.art_planet(screen,x,y,r,col)


_base_modal_panel=_draw_modal_panel

def _draw_modal_panel(target,info,ease):
    _base_modal_panel(target,info,ease)
    if info['is_record']:
        previous=info.get('previous_best')
        detail=(f"最佳记录  {info['best']:.2f} 秒" if previous is None else
                f"最佳 {info['best']:.2f} 秒  ·  提升 {previous-info['best']:.2f} 秒")
        blit_text(detail,font_small,(125,100,55),target=target,shadow_alpha=0,center=(WIDTH//2,HEIGHT//2-20))
    if not info.get('saved',True):
        blit_text("纪录暂未保存到磁盘",font_tiny,(175,65,55),target=target,shadow_alpha=0,center=(WIDTH//2,HEIGHT//2+130))
