# home_screen.py
import pygame
import math
import random

import config
import audio_system
from config import (
    WIDTH, HEIGHT, screen,
    WHITE,
    font_micro,
    blit_text,
    _button_state, trigger_button_press, update_button_state,
    draw_space_decor, draw_small_star,
    background_stars, meteors,
)
from game_screen import rocket_colors


# ---------------------------------------------------------------------------
# 首页按钮矩形
# ---------------------------------------------------------------------------
START_BUTTON_NEW = pygame.Rect(215, 592, 215, 60)
START_BUTTON_CONT = pygame.Rect(470, 592, 215, 60)


# ---------------------------------------------------------------------------
# 缓存
# ---------------------------------------------------------------------------
_start_space_base = None
_galaxy_cache = {}


def _c(v):
    return max(0, min(255, int(v)))


def _glow_circle(target, x, y, radius, color, alpha=90, layers=7):
    for i in range(layers, 0, -1):
        r = int(radius * (1 + i * 0.12))
        a = int(alpha * (1 - i / (layers + 2)) ** 1.5)
        if a <= 0:
            continue
        s = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
        c = s.get_width() // 2
        pygame.draw.circle(s, (*color, _c(a)), (c, c), r)
        target.blit(s, (int(x - c), int(y - c)))


def _make_start_bg():
    global _start_space_base
    if _start_space_base is not None:
        return _start_space_base
    s = pygame.Surface((WIDTH, HEIGHT)).convert()
    top = (7, 16, 62)
    bottom = (96, 30, 118)
    for y in range(HEIGHT):
        t = y / max(1, HEIGHT - 1)
        r = int(top[0] * (1 - t) + bottom[0] * t)
        g = int(top[1] * (1 - t) + bottom[1] * t)
        b = int(top[2] * (1 - t) + bottom[2] * t)
        pygame.draw.line(s, (r, g, b), (0, y), (WIDTH, y))
    haze = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.ellipse(haze, (190, 80, 190, 75), (-220, 80, 850, 410))
    pygame.draw.ellipse(haze, (70, 90, 220, 55), (390, 120, 760, 430))
    s.blit(haze, (0, 0))
    _start_space_base = s
    return s


def _cross_star(x, y, size, alpha=210, color=(255, 243, 194)):
    alpha = _c(alpha)
    _glow_circle(screen, x, y, max(3, size), color, alpha // 2, 5)
    pygame.draw.line(screen, (*color, alpha),
                     (int(x - size * 2.2), int(y)), (int(x + size * 2.2), int(y)),
                     max(1, size // 2))
    pygame.draw.line(screen, (*color, alpha),
                     (int(x), int(y - size * 2.2)), (int(x), int(y + size * 2.2)),
                     max(1, size // 2))
    pygame.draw.circle(screen, (*color, alpha), (int(x), int(y)), max(1, size // 2))


def _draw_home_stars():
    now = pygame.time.get_ticks()
    for i, s in enumerate(background_stars):
        wave = (math.sin(now / 720 * s['speed'] + s['phase']) + 1) / 2
        b = _c(s['bright_base'] + wave * s['bright_range'])
        if s['size'] >= 2 and i % 8 == 0:
            _cross_star(s['x'], s['y'], s['size'] + 1, 120 + int(120 * wave))
        else:
            pygame.draw.circle(screen, (b, b, min(255, b + 28)), (s['x'], s['y']), s['size'])


def _draw_home_meteors(dt_scale=0.55):
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


def _draw_galaxy(cx=452, cy=318):
    t = pygame.time.get_ticks() / 1000.0
    size = 430
    g = pygame.Surface((size, size), pygame.SRCALPHA)
    c = size // 2
    for rr in range(115, 10, -9):
        a = int(5 + (115 - rr) * 0.12)
        pygame.draw.circle(g, (210, 110, 235, _c(a)), (c, c), rr)
    for arm in range(2):
        off = arm * math.pi
        for i in range(34):
            u = i / 34
            th = off + u * math.pi * 1.85 + t * 0.55
            rx = 35 + 155 * u
            ry = 14 + 65 * u
            x = c + math.cos(th) * rx
            y = c + math.sin(th) * ry
            a = int(88 * (1 - u) + 10)
            pygame.draw.circle(g, (237, 125, 222, a), (int(x), int(y)), max(1, int(7 - 4 * u)))
    for arm in range(2):
        off = arm * math.pi + 0.8
        for i in range(28):
            u = i / 28
            th = off + u * math.pi * 1.7 - t * 0.35
            rx = 55 + 165 * u
            ry = 20 + 62 * u
            x = c + math.cos(th) * rx
            y = c + math.sin(th) * ry
            pygame.draw.circle(g, (108, 105, 236, int(65 * (1 - u) + 8)), (int(x), int(y)),
                               max(1, int(5 - 3 * u)))
    g = pygame.transform.rotate(g, (t * 8) % 360)
    screen.blit(g, g.get_rect(center=(cx, cy)))
    _glow_circle(screen, cx, cy, 18, (255, 193, 244), 120, 7)
    pygame.draw.circle(screen, (255, 245, 255), (cx, cy), 7)


def _draw_earth_horizon():
    cx, cy = 450, 1035
    w, h = 1380, 650
    glow = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    for i in range(8, 0, -1):
        r = pygame.Rect(cx - w // 2 - i * 10, cy - h // 2 - i * 10, w + i * 20, h + i * 20)
        pygame.draw.arc(glow, (112, 203, 255, _c(18 + i * 5)), r, math.pi, math.pi * 2, 10)
    screen.blit(glow, (0, 0))

    earth = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    r = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
    pygame.draw.ellipse(earth, (17, 42, 120, 255), r)
    for i in range(7):
        rr = r.inflate(-i * 20, -i * 20)
        pygame.draw.ellipse(earth, (30 + i * 4, 56 + i * 7, 130 + i * 8, 42), rr, 8)
    pygame.draw.polygon(earth, (75, 128, 194, 130),
                        [(80, 660), (175, 600), (260, 635), (215, 687), (120, 690)])
    pygame.draw.polygon(earth, (110, 83, 183, 120),
                        [(650, 610), (760, 590), (850, 635), (810, 690), (700, 680)])
    screen.blit(earth, (0, 0))

    hi = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    pygame.draw.arc(hi, (160, 232, 255, 235), r.inflate(0, -16), math.pi, math.pi * 2, 8)
    screen.blit(hi, (0, 0))


def _draw_home_planet(cx, cy, radius, color, ring):
    _glow_circle(screen, cx, cy, radius, color, 65, 6)
    pygame.draw.circle(screen, color, (cx, cy), radius)
    pygame.draw.circle(screen, (_c(color[0] + 32), _c(color[1] + 32), _c(color[2] + 32)),
                       (cx - radius // 3, cy - radius // 3), max(4, radius // 3))
    pygame.draw.circle(screen, (_c(color[0] - 28), _c(color[1] - 20), _c(color[2] - 10)),
                       (cx + radius // 3, cy + radius // 4), max(5, radius // 4))
    rs = pygame.Surface((radius * 5, radius * 3), pygame.SRCALPHA)
    rr = pygame.Rect(radius // 4, radius, radius * 4, radius // 2)
    pygame.draw.ellipse(rs, (*ring, 170), rr, 4)
    pygame.draw.ellipse(rs, (*ring, 70), rr.inflate(12, 6), 2)
    rs = pygame.transform.rotate(rs, -14)
    screen.blit(rs, rs.get_rect(center=(cx, cy + radius // 8)))


def _draw_rose(cx, cy, scale=1.0):
    pygame.draw.line(screen, (80, 170, 98), (cx, cy + 5), (cx + 2, cy + 36),
                     max(2, int(4 * scale)))
    pygame.draw.ellipse(screen, (88, 182, 103), (cx - 28, cy + 21, 25, 11))
    pygame.draw.ellipse(screen, (72, 150, 90), (cx + 3, cy + 20, 25, 11))
    _glow_circle(screen, cx, cy, int(17 * scale), (255, 120, 184), 65, 5)
    for i in range(7):
        a = i * math.pi * 2 / 7
        px = cx + math.cos(a) * 13 * scale
        py = cy + math.sin(a) * 10 * scale
        pygame.draw.circle(screen, (255, 126, 178), (int(px), int(py)), max(4, int(9 * scale)))
    pygame.draw.circle(screen, (255, 185, 215), (cx - 2, cy - 2), max(3, int(7 * scale)))


def _draw_astronaut(cx, cy, scale=1.0):
    t = pygame.time.get_ticks() / 1000.0
    y = cy + math.sin(t * 1.25) * 6
    s = scale
    surf = pygame.Surface((230, 250), pygame.SRCALPHA)
    body = pygame.Rect(int(84 * s), int(91 * s), int(60 * s), int(78 * s))
    pygame.draw.rect(surf, (242, 247, 252, 255), body, border_radius=int(18 * s))
    pygame.draw.rect(surf, (185, 205, 231, 255), body, width=3, border_radius=int(18 * s))
    hc = (114, 64)
    pygame.draw.circle(surf, (248, 250, 255, 255), (int(hc[0] * s), int(hc[1] * s)), int(34 * s))
    pygame.draw.circle(surf, (150, 180, 216, 255), (int(hc[0] * s), int(hc[1] * s)), int(30 * s), 3)
    pygame.draw.ellipse(surf, (24, 42, 78, 255),
                        (int((hc[0] - 23) * s), int((hc[1] - 15) * s), int(46 * s), int(30 * s)))
    pygame.draw.ellipse(surf, (82, 126, 185, 175),
                        (int((hc[0] - 15) * s), int((hc[1] - 11) * s), int(25 * s), int(11 * s)))
    pygame.draw.line(surf, (242, 247, 252, 255),
                     (int(85 * s), int(114 * s)), (int(48 * s), int(91 * s)), int(12 * s))
    pygame.draw.circle(surf, (248, 250, 255, 255), (int(43 * s), int(89 * s)), int(10 * s))
    pygame.draw.line(surf, (242, 247, 252, 255),
                     (int(142 * s), int(113 * s)), (int(174 * s), int(84 * s)), int(12 * s))
    pygame.draw.circle(surf, (248, 250, 255, 255), (int(180 * s), int(81 * s)), int(10 * s))
    pygame.draw.line(surf, (238, 243, 250, 255),
                     (int(102 * s), int(165 * s)), (int(78 * s), int(205 * s)), int(13 * s))
    pygame.draw.line(surf, (238, 243, 250, 255),
                     (int(126 * s), int(165 * s)), (int(154 * s), int(202 * s)), int(13 * s))
    pygame.draw.rect(surf, (177, 204, 230, 255),
                     (int(101 * s), int(119 * s), int(27 * s), int(23 * s)), border_radius=5)
    pygame.draw.circle(surf, (120, 240, 210, 255), (int(109 * s), int(127 * s)), int(3 * s))
    pygame.draw.circle(surf, (255, 185, 95, 255), (int(119 * s), int(127 * s)), int(3 * s))
    surf = pygame.transform.rotozoom(surf, -4, 1)
    _glow_circle(screen, cx, int(y), int(58 * s), (150, 210, 255), 50, 6)
    screen.blit(surf, surf.get_rect(center=(int(cx), int(y))))


def _draw_glow_text(text, font, center, color=(255, 255, 255), glow=(135, 195, 255)):
    base = font.render(text, True, color)
    g = font.render(text, True, glow)
    g.set_alpha(95)
    r = base.get_rect(center=center)
    for dx, dy in [(-4, 0), (4, 0), (0, -4), (0, 4), (-3, -3), (3, 3), (-3, 3), (3, -3)]:
        screen.blit(g, g.get_rect(center=(r.centerx + dx, r.centery + dy)))
    screen.blit(base, r)


def _draw_start_button(key, rect, text, primary=True, disabled=False):
    st = _button_state(key)
    scale, glow = st['scale'], st['glow']
    sr = pygame.Rect(0, 0, int(rect.width * scale), int(rect.height * scale))
    sr.center = rect.center

    if primary:
        top, bottom, gc, shadow = (255, 220, 95), (242, 145, 45), (255, 185, 65), (126, 70, 35)
    else:
        top, bottom, gc, shadow = (110, 138, 230), (124, 72, 184), (126, 145, 255), (48, 48, 100)
    if disabled:
        top, bottom, gc, shadow = (88, 98, 140), (64, 69, 105), (110, 120, 165), (35, 38, 63)

    for i in range(8, 0, -1):
        ex = i * 4
        a = int((48 if primary else 30) * (0.25 + glow) * (1 - i / 9))
        if disabled:
            a = int(a * 0.45)
        gs = pygame.Surface((sr.width + ex * 2, sr.height + ex * 2), pygame.SRCALPHA)
        pygame.draw.rect(gs, (*gc, _c(a)), gs.get_rect(), border_radius=18 + ex // 2)
        screen.blit(gs, gs.get_rect(center=sr.center))

    pygame.draw.rect(screen, shadow, sr.move(0, 5), border_radius=16)

    button = pygame.Surface(sr.size, pygame.SRCALPHA)
    for yy in range(sr.height):
        q = yy / max(1, sr.height - 1)
        rr = int(top[0] * (1 - q) + bottom[0] * q)
        gg = int(top[1] * (1 - q) + bottom[1] * q)
        bb = int(top[2] * (1 - q) + bottom[2] * q)
        pygame.draw.line(button, (rr, gg, bb, 235), (0, yy), (sr.width, yy))

    pygame.draw.rect(button, (255, 255, 255, 45),
                     (4, 3, sr.width - 8, max(8, sr.height // 2 - 4)), border_radius=12)
    pygame.draw.rect(button, (255, 255, 255, 175), button.get_rect(), 2, border_radius=16)
    screen.blit(button, sr.topleft)

    f = config.get_font(23, bold=True)
    img = f.render(text, True, (190, 198, 220) if disabled else WHITE)
    screen.blit(img, img.get_rect(center=sr.center))


def draw_start_background():
    screen.blit(_make_start_bg(), (0, 0))
    _draw_home_stars()
    _draw_home_meteors(0.55)
    _draw_galaxy(452, 318)
    _draw_earth_horizon()


def draw_start_screen(has_progress):
    draw_start_background()

    _draw_home_planet(108, 523, 54, (221, 100, 102), (255, 211, 130))
    _draw_rose(108, 476, 1.0)
    _draw_home_planet(808, 500, 48, (90, 98, 205), (176, 184, 255))

    t = pygame.time.get_ticks() / 1000.0
    bob = math.sin(t * 1.25) * 5
    _glow_circle(screen, 450, 430, 32, (255, 160, 70), 95, 7)
    _draw_rocket_mini(screen, 450, int(362 + bob), (232, 70, 70), scale=2.3, flame=True)

    pad = pygame.Surface((250, 72), pygame.SRCALPHA)
    pygame.draw.ellipse(pad, (35, 35, 68, 130), (8, 35, 234, 28))
    pygame.draw.rect(pad, (125, 130, 150, 255), (35, 16, 180, 26), border_radius=8)
    pygame.draw.rect(pad, (176, 182, 200, 255), (48, 11, 158, 8), border_radius=4)
    pygame.draw.rect(pad, (70, 76, 103, 255), (48, 43, 154, 10), border_radius=5)
    for x in (70, 96, 122, 148, 174):
        pygame.draw.circle(pad, (255, 205, 108, 190), (x, 31), 3)
    screen.blit(pad, pad.get_rect(center=(450, 450)))

    _draw_glow_text('一箭又一箭', config.get_font(63, bold=True), (450, 88),
                    (255, 255, 255), (120, 192, 255))
    for i, (sx, sy, sr) in enumerate([(300, 62, 7), (350, 125, 5), (545, 123, 5),
                                      (593, 64, 7), (635, 96, 4)]):
        _cross_star(sx, sy, sr, 150 + int(105 * ((math.sin(t * 3 + i) + 1) / 2)),
                    (255, 226, 115))

    draw_space_decor(screen, 705, 72, 'rocket', size=12, alpha=240)

    arc = pygame.Surface((620, 85), pygame.SRCALPHA)
    pygame.draw.arc(arc, (150, 218, 255, 180), (18, 10, 584, 60),
                    math.pi * 0.08, math.pi * 0.92, 5)
    screen.blit(arc, (140, 108))

    _draw_glow_text('太空火箭探索任务', config.get_font(20, bold=True), (450, 145),
                    (245, 248, 255), (100, 165, 255))

    _draw_glow_text('神秘的宇宙，', config.get_font(25, bold=True), (145, 265),
                    (255, 255, 255), (130, 185, 255))
    _draw_glow_text('等待你来发现新星', config.get_font(25, bold=True), (155, 303),
                    (255, 255, 255), (130, 185, 255))
    pygame.draw.line(screen, (255, 218, 128), (72, 340), (245, 340), 3)

    _draw_astronaut(735, 302, 0.94)

    _draw_glow_text('每一次点火，', config.get_font(24, bold=True), (770, 422),
                    (255, 255, 255), (140, 188, 255))
    _draw_glow_text('都是奔赴未知的浪漫', config.get_font(24, bold=True), (760, 458),
                    (255, 255, 255), (140, 188, 255))
    pygame.draw.line(screen, (255, 218, 128), (670, 490), (855, 490), 3)

    # 右上飞行小火箭
    mini = pygame.Surface((80, 80), pygame.SRCALPHA)
    _draw_rocket_mini(mini, 40, 40, (236, 80, 78), scale=0.42, flame=True)
    mini = pygame.transform.rotate(mini, -38)
    screen.blit(mini, (790, 132))

    _draw_start_button('new', START_BUTTON_NEW, '新的探索', primary=False)
    if has_progress:
        _draw_start_button('cont', START_BUTTON_CONT, '继续探索', primary=True)
    else:
        _draw_start_button('cont_disabled', START_BUTTON_CONT, '继续探索',
                           primary=True, disabled=True)

    blit_text('探索星海 · 点亮每一道航线', font_micro, (214, 224, 255),
              shadow_alpha=55, center=(450, 686))


def _draw_rocket_mini(surface, x, y, color, scale=1.0, flame=True):
    """简易小火箭绘制（首页专用，避免和 game_screen 循环依赖）。"""
    base = 120
    canvas = pygame.Surface((base, base), pygame.SRCALPHA)
    body = color
    dark = (max(0, int(color[0] * 0.70)), max(0, int(color[1] * 0.70)),
            max(0, int(color[2] * 0.70)))
    darker = (max(0, int(color[0] * 0.46)), max(0, int(color[1] * 0.46)),
              max(0, int(color[2] * 0.46)))
    light = (min(255, int(color[0] * 1.32)), min(255, int(color[1] * 1.32)),
             min(255, int(color[2] * 1.32)))
    cx = base // 2

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

    size = max(8, int(38 * scale))
    canvas = pygame.transform.smoothscale(canvas, (size, size))
    surface.blit(canvas, canvas.get_rect(center=(int(x), int(y))))


# ---------------------------------------------------------------------------
# 更新 & 点击处理
# ---------------------------------------------------------------------------
def update_start_scene(has_progress):
    mouse_pos = pygame.mouse.get_pos()
    update_button_state("new", START_BUTTON_NEW, mouse_pos)
    if has_progress:
        update_button_state("cont", START_BUTTON_CONT, mouse_pos)
    else:
        update_button_state("cont_disabled",
                            pygame.Rect(-9999, -9999, 1, 1), mouse_pos)


def handle_click(mouse_x, mouse_y, has_progress):
    """返回 'new' / 'continue' / None。"""
    if START_BUTTON_NEW.collidepoint(mouse_x, mouse_y):
        trigger_button_press("new")
        audio_system.play_click()
        return "new"
    if has_progress and START_BUTTON_CONT.collidepoint(mouse_x, mouse_y):
        trigger_button_press("cont")
        audio_system.play_click()
        return "continue"
    return None


# ---------------------------------------------------------------------------
# 像素风首页覆盖
# ---------------------------------------------------------------------------
def _px_rect(rect, color, outline=(12, 18, 39), width=3):
    pygame.draw.rect(screen, color, rect)
    pygame.draw.rect(screen, outline, rect, width)


def draw_start_background():
    screen.fill((7, 10, 28))
    # 分层像素星空与棋盘式地平线
    for i, star in enumerate(background_stars[:150]):
        x, y = int(star["x"]), int(star["y"])
        size = 2 if i % 5 else 4
        col = (116, 168, 220) if i % 4 else (245, 221, 126)
        config.art_star(screen,x,y,size+1,180)
    pygame.draw.rect(screen, (16, 27, 62), (0, 470, WIDTH, 230))
    for y in range(486, HEIGHT, 24):
        pygame.draw.line(screen, (24, 55, 91), (0, y), (WIDTH, y), 2)
    for x in range(-80, WIDTH + 80, 64):
        pygame.draw.line(screen, (24, 55, 91), (WIDTH//2, 470), (x, HEIGHT), 2)
    config.art_planet(screen,95,260,37,(132,160,203))
    config.art_planet(screen,793,330,48,(167,129,191))


def _draw_start_button(key, rect, text, primary=True, disabled=False):
    color = (188, 119, 44) if primary else (44, 84, 137)
    hover = (234, 165, 60) if primary else (61, 119, 177)
    config.draw_animated_button(key, rect, text, color=color, hover=hover,
                                target=screen, font=config.font_button, disabled=disabled)


def _draw_rocket_mini(surface, x, y, color, scale=1.0, flame=True):
    s = max(2, int(4 * scale))
    # 朝右的 8-bit 火箭
    blocks = [
        (0, 3, 2, 3, (244, 107, 48)), (2, 2, 2, 5, (248, 194, 68)),
        (4, 1, 6, 7, color), (10, 2, 3, 5, (211, 222, 225)),
        (13, 3, 2, 3, (238, 235, 210)), (7, 3, 2, 2, (73, 169, 205)),
        (4, 0, 3, 2, (44, 61, 104)), (4, 7, 3, 2, (44, 61, 104)),
    ]
    for bx, by, bw, bh, col in blocks:
        pygame.draw.rect(surface, col, (int(x+(bx-7)*s), int(y+(by-4)*s), bw*s, bh*s))


def draw_start_screen(has_progress):
    draw_start_background()
    t=pygame.time.get_ticks()/1000.0
    config.draw_art_title_with_decor(screen,450,116,scale=1.12)
    blit_text("P I X E L   S P A C E   Q U E S T",config.font_small,
              (149,202,216),shadow_alpha=0,center=(450,192))
    config.art_rocket(screen,450,366+int(math.sin(t*2)*5),300,cover=True)
    for x,y,r in [(235,295,25),(647,280,25),(294,432,13),(617,417,15)]:
        draw_small_star(screen,x,y,r,color=(255,233,122))

    blit_text("清除所有火箭，继续你的宇宙远征",config.font_normal,
              (221,229,237),shadow_alpha=0,center=(450,543))
    START_BUTTON_NEW.centerx=342 if has_progress else 450
    _draw_start_button("new",START_BUTTON_NEW,"新游戏",primary=True)
    if has_progress:
        _draw_start_button("cont",START_BUTTON_CONT,"继续游戏",primary=False)
    blit_text("方向由火箭决定 · 无阻挡即可发射",config.font_tiny,
              (133,167,197),shadow_alpha=0,center=(450,674))


"""最终关卡结尾。225×175 逻辑画布，整数放大，时间单位为秒。"""
import math
import pygame
import config

ENDING_DURATION = 15.0
_ending_started = 0

def start_ending():
    global _ending_started
    _ending_started = pygame.time.get_ticks()

def ending_elapsed():
    return (pygame.time.get_ticks() - _ending_started) / 1000.0

def ending_finished():
    return ending_elapsed() >= ENDING_DURATION

def draw_ending(t=None):
    if t is None:
        t = ending_elapsed()
    s = pygame.Surface((225, 175))
    s.fill((8, 12, 32))
    def box(c, x, y, w, h):
        pygame.draw.rect(s, c, (round(x), round(y), max(1, round(w)), max(1, round(h))))
    for i in range(65):
        x, y = (i*73+19)%225, (i*31+9)%110
        c = (180, 213, 235) if int(t*2+i)%5 else (245, 216, 137)
        config.art_star(s,x,y,2 if i%5==0 else 1,190)
    config.art_planet(s,187,30,12,(154,132,187))
    pygame.draw.ellipse(s, (90, 77, 105), (-65, 113, 355, 124))
    pygame.draw.ellipse(s, (140, 115, 131), (-65, 116, 355, 124), 3)
    for x,y,w in [(15,140,14),(85,152,19),(181,138,22),(112,132,7),(42,160,10)]:
        box((66, 58, 86), x,y,w,2)
    # 火箭减速着陆，3 秒后稳定，4 秒开启舱门。
    p = min(1, max(0,t/3))
    ry = -45 + 167*(1-(1-p)**2)
    if t < 3:
        flame = 7 + int(3*math.sin(t*28))
        box((245,111,47), 60,ry-2,9,flame)
        box((255,219,113), 63,ry-2,3,flame-2)
    box((70,86,128), 50,ry-14,7,16)
    box((70,86,128), 71,ry-14,7,16)
    box((191,209,215), 56,ry-31,17,29)
    box((224,230,211), 59,ry-38,11,9)
    box((224,230,211), 62,ry-42,5,6)
    box((100,157,189), 60,ry-28,9,7)
    box((178,235,237), 61,ry-27,3,2)
    box((38,49,77) if t>=4 else (111,132,164), 62,ry-14,7,12)
    if t>=3:
        for i in range(5):
            if t<4:
                box((188,158,154), 48+i*9+(t-3)*(i-2)*7,125,4,2)
    if t>=4:
        box((154,168,179),69,121,10,2)
        box((154,168,179),76,123,10,2)
        # 出舱步行，弯腰种植，然后退一步欣赏。
        walk = min(1,(t-4)/3)
        ax = 77 + 53*walk
        if t>9:
            ax -= 9*min(1,(t-9)/1)
        crouch = 3 if 7<=t<9 else 0
        ay = 124+crouch
        step = int(t*9)%2 if 4<t<7 or 9<t<10 else 0
        box((102,125,158),ax-7,ay-12,5,9)
        box((232,232,216),ax-4,ay-18,10,9)
        box((53,88,123),ax-2,ay-16,8,5)
        box((137,209,226),ax-1,ay-16,3,2)
        box((209,221,217),ax-3,ay-9,8,8)
        box((224,175,81),ax-1,ay-7,3,3)
        box((209,221,217),ax-3,ay-1,3,4-step)
        box((209,221,217),ax+2,ay-1,3,3+step)
        box((181,198,205),ax+5,ay-7 if crouch else ay-8,5,3)
        if 7<=t<9:
            box((223,185,115),140,124,2,2)
    # 种子在 9 秒后生根发芽；11 秒起玫瑰逐瓣绽放。
    box((52,42,65),137,127,9,2)
    if t>=9:
        growth = min(1,(t-9)/2)
        height = int(21*growth)
        box((68,153,91),141,127-height,2,height)
        if growth>.35:
            box((93,183,104),136,120-height//3,5,3)
        if growth>.7:
            box((113,198,117),143,114,5,3)
        if t>=11:
            bloom = min(1,(t-11)/1.5)
            for dx,dy,w,h,c in [(-4,-4,8,7,(167,37,77)),(-6,-2,5,5,(219,55,94)),(2,-3,5,6,(239,87,121)),(-3,-6,6,4,(246,117,143)),(-2,-2,4,3,(255,172,168))]:
                box(c,142+dx*bloom,106+dy*bloom,w*bloom,h*bloom)
            if t>12:
                for i in range(6):
                    a=i*math.pi/3+t*.4
                    x=142+math.cos(a)*17; y=105+math.sin(a)*14
                    box((243,217,138),x,y,1,2)
    config.screen.blit(pygame.transform.scale(s,(config.WIDTH,config.HEIGHT)),(0,0))
    caption = ('抵达遥远的星球' if t<4 else '宇航员踏上新的土地' if t<7 else
               '种下一颗小小的希望' if t<9 else '让生命在星海中绽放' if t<12.5 else '旅程的终点，是一朵玫瑰的起点')
    config.blit_text(caption,config.font_normal,(245,225,186),shadow_alpha=80,center=(450,590))
