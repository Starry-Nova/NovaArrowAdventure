import pygame
import sys
import math
import random
import os

pygame.init()

WIDTH = 900
HEIGHT = 700

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("一箭又一箭 · 太空探索")

clock = pygame.time.Clock()

BG = (245, 241, 232)
TEXT_COLOR = (70, 64, 58)
SUB_TEXT = (120, 112, 102)
WHITE = (255, 255, 255)

BUTTON_COLOR = (90, 150, 190)
BUTTON_HOVER = (110, 170, 205)

RED = (235, 75, 70)
YELLOW = (255, 215, 70)

BOARD_X = 185
BOARD_Y = 125
BOARD_SIZE = 530

GRID_SIZE = 7
CELL_SIZE = BOARD_SIZE // GRID_SIZE

FONT_NAMES = ",".join([
    "microsoftyaheiui",
    "microsoftyahei",
    "msyh",
    "pingfangsc",
    "heitisc",
    "dengxian",
    "notosanscjksc",
    "notosanssc",
    "sourcehansanssc",
    "wenquanyimicrohei",
    "wenquanyizenhei",
    "simhei",
    "simsun",
])

FALLBACK_FONT_FILES = [
    "C:/Windows/Fonts/msyh.ttc",
    "C:/Windows/Fonts/msyhbd.ttc",
    "C:/Windows/Fonts/Deng.ttf",
    "C:/Windows/Fonts/simhei.ttf",
    "/System/Library/Fonts/PingFang.ttc",
    "/System/Library/Fonts/STHeiti Medium.ttc",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
]


def get_font(size, bold=False):
    path = pygame.font.match_font(FONT_NAMES, bold=bold)
    if path:
        try:
            return pygame.font.Font(path, size)
        except Exception:
            pass
    for fallback in FALLBACK_FONT_FILES:
        if os.path.exists(fallback):
            try:
                return pygame.font.Font(fallback, size)
            except Exception:
                pass
    return pygame.font.Font(None, size)


font_title = get_font(38, bold=True)
font_big = get_font(28, bold=True)
font_normal = get_font(21)
font_small = get_font(17)
font_button = get_font(19, bold=True)


def blit_text(text, font, color, shadow_alpha=50, **rect_kwargs):
    image = font.render(text, True, color)
    rect = image.get_rect(**rect_kwargs)
    shadow = font.render(text, True, (12, 14, 20))
    shadow.set_alpha(shadow_alpha)
    screen.blit(shadow, (rect.x + 1, rect.y + 2))
    screen.blit(image, rect)
    return rect


rocket_colors = [
    (80, 150, 225),
    (235, 100, 85),
    (105, 185, 135),
    (165, 105, 205),
    (240, 165, 70),
    (70, 185, 190),
    (220, 105, 155),
    (120, 145, 220)
]


levels = [
    [(1, 2, "right"), (4, 1, "left"), (1, 4, "right"), (6, 3, "up")],
    [(5, 2, "down"), (1, 5, "down"), (4, 6, "left"), (3, 1, "right"), (4, 1, "down"), (0, 3, "left")],
    [(1, 2, "down"), (6, 1, "down"), (5, 4, "up"), (3, 1, "up"), (1, 3, "down"), (5, 0, "right"), (6, 0, "down"), (5, 3, "down")],
    [(6, 3, "down"), (4, 1, "left"), (6, 4, "down"), (6, 2, "right"), (1, 6, "right"), (0, 4, "down"), (5, 3, "down"), (1, 0, "up"), (3, 3, "left"), (6, 5, "down")],
    [(0, 1, "up"), (1, 5, "up"), (6, 4, "left"), (2, 0, "left"), (3, 4, "up"), (3, 0, "down"), (0, 0, "left"), (1, 1, "right"), (6, 6, "left"), (1, 3, "down"), (0, 6, "left"), (1, 2, "right")],
    [(5, 2, "up"), (3, 1, "right"), (6, 6, "left"), (0, 6, "down"), (0, 0, "right"), (2, 5, "right"), (4, 5, "right"), (5, 1, "right"), (3, 0, "down"), (2, 4, "down"), (1, 3, "left"), (6, 5, "left"), (5, 3, "up"), (1, 2, "left")],
    [(6, 3, "up"), (4, 2, "up"), (0, 1, "up"), (5, 0, "left"), (4, 5, "up"), (6, 5, "down"), (0, 3, "left"), (2, 2, "right"), (0, 4, "left"), (1, 5, "left"), (4, 3, "right"), (3, 2, "right"), (3, 6, "right"), (4, 0, "down"), (2, 4, "down"), (2, 0, "down")]
]


level_names = [
    "地面点火台",
    "冲破大气层",
    "近地轨道巡航",
    "地月转移航线",
    "月球环绕轨道",
    "行星际深空",
    "新星港湾"
]


level_stories = [
    "火箭矗立地面发射台，准备点火，开启太空探索之旅。",
    "点火升空，穿越厚重大气层，抵御高空气流冲击。",
    "成功抵达近地轨道，调整飞船姿态，稳定环绕地球。",
    "告别地球，踏上前往月球的转移轨道。",
    "抵达月球附近，进入环月轨道，短暂休整。",
    "离开地月系统，驶入孤寂的星际空间。",
    "跨越遥远星际，终于抵达目标新星，完成太空探索任务。"
]


best_times = [None for _ in levels]

current_level = 0
arrows = []

mistakes = 3

game_state = "start"

animation = None

star_explosion = None

explosions = []

hint_cell = None
hint_timer = 0

pause_started = 0
paused_total = 0

level_start_time = 0
current_elapsed = 0

final_explosion_timer = 0


background_stars = []

random.seed(42)

for i in range(130):
    background_stars.append(
        {
            "x": random.randint(0, WIDTH),
            "y": random.randint(0, HEIGHT),
            "size": random.choice([1, 1, 1, 2]),
            "phase": random.random() * math.pi * 2
        }
    )


def load_level(level_index):

    global arrows
    global mistakes
    global animation
    global star_explosion
    global explosions
    global hint_cell
    global hint_timer
    global paused_total
    global level_start_time
    global current_elapsed
    global final_explosion_timer

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
            target = find_arrow(r, col)
            if target:
                return target
    elif direction == "down":
        for r in range(row + 1, GRID_SIZE):
            target = find_arrow(r, col)
            if target:
                return target
    elif direction == "left":
        for c in range(col - 1, -1, -1):
            target = find_arrow(row, c)
            if target:
                return target
    elif direction == "right":
        for c in range(col + 1, GRID_SIZE):
            target = find_arrow(row, c)
            if target:
                return target

    return None


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

        pygame.draw.rect(screen, (95, 100, 110), (400, 500, 100, 30), border_radius=6)
        pygame.draw.line(screen, (75, 80, 90), (420, 530), (395, 570), 5)
        pygame.draw.line(screen, (75, 80, 90), (480, 530), (505, 570), 5)

    elif level == 1:

        for y in range(HEIGHT):
            ratio = y / HEIGHT
            r = int(80 + 50 * ratio)
            g = int(100 + 30 * ratio)
            b = int(180 + 40 * ratio)
            pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))

        for i in range(10):
            x = 40 + i * 95
            y = 480 + int(math.sin(i) * 18)
            pygame.draw.ellipse(screen, (150, 170, 215), (x, y, 130, 35))

        pygame.draw.rect(screen, (35, 45, 90), (0, 0, WIDTH, 70))

    elif level == 2:

        screen.fill((16, 35, 83))
        draw_stars(80)

        pygame.draw.ellipse(screen, (40, 85, 145), (-180, 470, 1260, 500))
        pygame.draw.ellipse(screen, (65, 125, 185), (-100, 520, 1100, 400))
        pygame.draw.arc(screen, (120, 185, 225), (-80, 470, 1060, 600), math.pi, math.pi * 2, 4)

    elif level == 3:

        screen.fill((8, 18, 45))
        draw_stars(90)

        pygame.draw.circle(screen, (215, 215, 205), (765, 135), 42)
        pygame.draw.circle(screen, (185, 185, 180), (750, 120), 9)
        pygame.draw.circle(screen, (190, 190, 185), (780, 150), 7)

    elif level == 4:

        screen.fill((30, 31, 38))
        draw_stars(120)

        pygame.draw.circle(screen, (125, 125, 120), (805, 360), 115)
        pygame.draw.circle(screen, (105, 105, 102), (775, 330), 24)
        pygame.draw.circle(screen, (95, 95, 94), (835, 390), 18)
        pygame.draw.circle(screen, (145, 145, 138), (850, 320), 12)

    elif level == 5:

        screen.fill((5, 7, 15))
        draw_stars(130)

    elif level == 6:

        screen.fill((7, 5, 22))
        draw_stars(120)

        pulse = (math.sin(pygame.time.get_ticks() / 500) + 1) / 2

        for radius in range(130, 20, -12):
            alpha = int(12 + pulse * 15)
            nova_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            pygame.draw.circle(nova_surface, (120, 170, 255, alpha), (450, 330), radius)
            screen.blit(nova_surface, (0, 0))

        pygame.draw.circle(screen, (150, 205, 255), (450, 330), 42)
        pygame.draw.circle(screen, (235, 245, 255), (450, 330), 23)


def draw_stars(count):

    current_time = pygame.time.get_ticks()

    for star in background_stars[:count]:
        wave = (math.sin(current_time / 700 + star["phase"]) + 1) / 2
        brightness = int(130 + wave * 125)
        pygame.draw.circle(
            screen,
            (brightness, brightness, min(255, brightness + 15)),
            (star["x"], star["y"]),
            star["size"]
        )


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

    for i in range(6):
        distance = i * 15

        if direction == "up":
            tx = x
            ty = y + distance
        elif direction == "down":
            tx = x
            ty = y - distance
        elif direction == "left":
            tx = x + distance
            ty = y
        else:
            tx = x - distance
            ty = y

        alpha = max(0, 110 - i * 17)

        pygame.draw.circle(
            trail_surface,
            (color[0], color[1], color[2], alpha),
            (int(tx), int(ty)),
            max(2, 8 - i)
        )

    screen.blit(trail_surface, (0, 0))


def draw_board():

    board_rect = pygame.Rect(BOARD_X, BOARD_Y, BOARD_SIZE, BOARD_SIZE)

    pygame.draw.rect(screen, (245, 248, 252), board_rect, border_radius=18)
    pygame.draw.rect(screen, (190, 205, 220), board_rect, width=3, border_radius=18)

    for i in range(1, GRID_SIZE):
        x = BOARD_X + i * CELL_SIZE
        y = BOARD_Y + i * CELL_SIZE
        pygame.draw.line(screen, (210, 220, 230), (x, BOARD_Y), (x, BOARD_Y + BOARD_SIZE), 2)
        pygame.draw.line(screen, (210, 220, 230), (BOARD_X, y), (BOARD_X + BOARD_SIZE, y), 2)


def draw_arrows():

    current_time = pygame.time.get_ticks()

    for arrow in arrows:

        row, col, direction, color_index = arrow

        x, y = get_arrow_position(row, col)

        color = rocket_colors[color_index % len(rocket_colors)]

        scale = 1.0

        if hint_cell is not None:
            if row == hint_cell[0] and col == hint_cell[1]:
                pulse = (math.sin(current_time / 100) + 1) / 2
                scale = 1.0 + pulse * 0.12
                pygame.draw.circle(
                    screen,
                    (255, 220, 70),
                    (int(x), int(y)),
                    int(37 + pulse * 6),
                    4
                )

        draw_rocket(screen, x, y, direction, color, scale=scale, flame=True)


def draw_animation():

    if animation is None:
        return

    if animation["type"] == "fly":
        draw_trail(animation["x"], animation["y"], animation["direction"], animation["color"])
        draw_rocket(screen, animation["x"], animation["y"], animation["direction"], animation["color"], scale=1.0, flame=True)

    elif animation["type"] == "collision":
        color = animation["color"]
        if animation["phase"] == "red":
            color = RED
        draw_trail(animation["x"], animation["y"], animation["direction"], color)
        draw_rocket(screen, animation["x"], animation["y"], animation["direction"], color, scale=1.0, flame=True)


def draw_button(rect, text):

    mouse_pos = pygame.mouse.get_pos()

    color = BUTTON_HOVER if rect.collidepoint(mouse_pos) else BUTTON_COLOR

    pygame.draw.rect(screen, (52, 92, 122), rect.move(0, 3), border_radius=11)
    pygame.draw.rect(screen, color, rect, border_radius=11)

    text_surface = font_button.render(text, True, WHITE)
    screen.blit(text_surface, text_surface.get_rect(center=rect.center))


def format_time(seconds):
    return f"{seconds:.2f}s"


def draw_star(surface, x, y, radius, alpha, scale):

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
        px = x + math.cos(angle) * r
        py = y + math.sin(angle) * r
        points.append((int(px), int(py)))

    pygame.draw.polygon(surface, (255, 215, 70, int(alpha)), points)
    pygame.draw.polygon(surface, (255, 242, 155, int(alpha)), points, 2)


def draw_durability():

    current_time = pygame.time.get_ticks()

    positions = [745, 780, 815]

    for i in range(mistakes):
        phase = current_time - i * 170
        wave = (math.sin(phase / 400) + 1) / 2
        alpha = int(178 + 77 * wave)
        scale = 1.0 + 0.1 * wave

        draw_star(screen, positions[i], 55, 12, alpha, scale)

    draw_star_explosion()


def draw_star_explosion():
    """星星位置的爆炸效果（用于提示耐久减少）。"""

    if star_explosion is None:
        return

    x = star_explosion["x"]
    y = star_explosion["y"]
    timer = star_explosion["timer"]
    duration = star_explosion["duration"]

    progress = timer / duration
    alpha = int(255 * (1 - progress))

    surf_size = 170
    surface = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
    center = (surf_size // 2, surf_size // 2)

    glow_radius = int(12 + progress * 52)
    if glow_radius > 0:
        pygame.draw.circle(surface, (255, 200, 80, alpha // 4), center, glow_radius)
        pygame.draw.circle(surface, (255, 230, 140, alpha // 3), center, int(glow_radius * 0.6))

    ray_count = 16
    for i in range(ray_count):
        angle = i * math.pi * 2 / ray_count
        start_distance = 5
        end_distance = 12 + progress * 58

        sx = center[0] + math.cos(angle) * start_distance
        sy = center[1] + math.sin(angle) * start_distance
        ex = center[0] + math.cos(angle) * end_distance
        ey = center[1] + math.sin(angle) * end_distance

        pygame.draw.line(surface, (255, 210, 60, alpha), (int(sx), int(sy)), (int(ex), int(ey)), 3)
        pygame.draw.line(
            surface,
            (255, 255, 220, alpha),
            (int(sx), int(sy)),
            (
                int(center[0] + math.cos(angle) * end_distance * 0.6),
                int(center[1] + math.sin(angle) * end_distance * 0.6)
            ),
            2
        )

    radius = int(6 + progress * 26)
    if radius > 0:
        pygame.draw.circle(surface, (255, 245, 200, alpha), center, radius)
        pygame.draw.circle(surface, (255, 255, 255, alpha), center, max(1, radius // 2))

    screen.blit(surface, (x - surf_size // 2, y - surf_size // 2))


# ---------------------------------------------------------------------------
# 火箭碰撞爆炸特效
# ---------------------------------------------------------------------------

def start_explosion(x, y, size=1.0):
    """在指定位置生成一个爆炸效果。"""

    particles = []
    particle_count = int(22 * size)

    for _ in range(particle_count):
        angle = random.random() * math.pi * 2
        speed = random.uniform(2.5, 8.5) * size

        particles.append({
            "x": x,
            "y": y,
            "vx": math.cos(angle) * speed,
            "vy": math.sin(angle) * speed,
            "r": random.uniform(2.5, 6.5) * size,
            "color_choice": random.random(),
        })

    explosions.append({
        "x": x,
        "y": y,
        "timer": 0,
        "duration": 60,
        "size": size,
        "particles": particles,
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
    """绘制所有正在播放的爆炸效果。"""

    for e in explosions:

        progress = e["timer"] / e["duration"]
        x = e["x"]
        y = e["y"]
        size = e["size"]

        # --- 冲击波圆环 ---
        ring_p = min(1.0, progress * 1.5)
        ring_radius = int((6 + ring_p * 62) * size)
        ring_alpha = max(0, int(220 * (1 - ring_p)))

        if ring_alpha > 0 and ring_radius > 1:
            surf_size = ring_radius * 2 + 12
            ring_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
            center = (surf_size // 2, surf_size // 2)
            ring_width = max(1, int(7 * (1 - ring_p)))

            pygame.draw.circle(ring_surf, (255, 210, 90, ring_alpha), center, ring_radius, ring_width)
            pygame.draw.circle(
                ring_surf,
                (255, 110, 45, ring_alpha // 2),
                center,
                max(1, ring_radius - ring_width),
                max(1, ring_width // 2)
            )

            screen.blit(ring_surf, (int(x - surf_size // 2), int(y - surf_size // 2)))

        # --- 中心闪光 ---
        if progress < 0.4:
            flash_p = progress / 0.4
            flash_alpha = int(255 * (1 - flash_p))
            flash_r = int(50 * size * (1 - flash_p * 0.4))

            if flash_r > 0:
                surf_size = flash_r * 2 + 4
                flash_surf = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
                center = (surf_size // 2, surf_size // 2)

                pygame.draw.circle(flash_surf, (255, 180, 70, flash_alpha // 4), center, flash_r)
                pygame.draw.circle(flash_surf, (255, 220, 110, flash_alpha * 3 // 4), center, int(flash_r * 0.72))
                pygame.draw.circle(flash_surf, (255, 255, 245, flash_alpha), center, max(1, int(flash_r * 0.4)))

                screen.blit(flash_surf, (int(x - surf_size // 2), int(y - surf_size // 2)))

        # --- 火花粒子 ---
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


def draw_top_ui():

    main_color = TEXT_COLOR if current_level == 0 else WHITE
    sub_color = SUB_TEXT if current_level == 0 else (198, 214, 238)

    blit_text("一箭又一箭", font_title, main_color, center=(350, 50))
    blit_text(f"第{current_level + 1}/7关", font_normal, main_color, midright=(535, 52))
    blit_text(f"剩余火箭 {len(arrows)}", font_normal, main_color, midleft=(555, 52))

    best = best_times[current_level]

    if best is None:
        best_text = "本关最佳：--"
    else:
        best_text = "本关最佳：" + format_time(best)

    blit_text(best_text, font_small, sub_color, midleft=(555, 82))

    draw_durability()


def draw_game_screen():

    draw_background()
    draw_top_ui()
    draw_board()
    draw_arrows()
    draw_animation()

    # 爆炸绘制在火箭之上
    draw_explosions()

    blit_text(
        f"时间：{format_time(current_elapsed)}",
        font_small,
        TEXT_COLOR if current_level == 0 else WHITE,
        center=(450, 108)
    )

    restart_rect = pygame.Rect(35, 620, 125, 45)
    draw_button(restart_rect, "重新开始")

    pause_rect = pygame.Rect(690, 610, 80, 45)
    draw_button(pause_rect, "暂停")

    hint_rect = pygame.Rect(780, 610, 80, 45)
    draw_button(hint_rect, "提示")

    blit_text(
        "点击火箭，让它沿方向飞出",
        font_small,
        SUB_TEXT if current_level == 0 else (190, 206, 232),
        center=(450, 675)
    )


def draw_start_screen():

    draw_background()

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 35))
    screen.blit(overlay, (0, 0))

    blit_text("一箭又一箭", font_title, WHITE, center=(450, 210))
    blit_text("太空火箭探索任务", font_normal, WHITE, center=(450, 270))
    blit_text("从地面点火台出发，向着未知星空前进", font_small, (240, 246, 255), center=(450, 315))

    start_rect = pygame.Rect(350, 380, 200, 60)
    draw_button(start_rect, "开始探索")


def draw_pause_screen():

    draw_game_screen()

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 125))
    screen.blit(overlay, (0, 0))

    panel = pygame.Rect(275, 205, 350, 270)

    pygame.draw.rect(screen, (245, 248, 252), panel, border_radius=20)
    pygame.draw.rect(screen, (190, 205, 220), panel, width=3, border_radius=20)

    blit_text("游戏暂停", font_big, TEXT_COLOR, center=(450, 255))
    blit_text("火箭和计时器已经暂停", font_normal, SUB_TEXT, center=(450, 305))

    continue_rect = pygame.Rect(350, 350, 200, 52)
    draw_button(continue_rect, "继续探索")

    restart_rect = pygame.Rect(350, 415, 200, 45)
    draw_button(restart_rect, "重新开始")


def draw_fail_screen():

    draw_background()

    overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 110))
    screen.blit(overlay, (0, 0))

    blit_text("任务失败", font_title, (255, 120, 110), center=(450, 245))
    blit_text("飞船耐久已经耗尽", font_normal, WHITE, center=(450, 305))
    blit_text(f"本次用时：{format_time(current_elapsed)}", font_small, (225, 232, 245), center=(450, 345))

    restart_rect = pygame.Rect(350, 395, 200, 55)
    draw_button(restart_rect, "重新挑战")


def draw_win_screen():

    global final_explosion_timer

    draw_background()

    if current_level == 6:

        progress = min(final_explosion_timer / 90, 1)
        flash_alpha = int(180 * (1 - progress))

        flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        flash.fill((210, 235, 255, flash_alpha))
        screen.blit(flash, (0, 0))

        radius = int(50 + progress * 360)

        nova_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(nova_surface, (210, 235, 255, int(80 * (1 - progress))), (450, 330), radius)
        screen.blit(nova_surface, (0, 0))

    panel = pygame.Rect(230, 165, 440, 365)

    panel_surface = pygame.Surface((panel.width, panel.height), pygame.SRCALPHA)
    panel_surface.fill((245, 248, 252, 225))
    screen.blit(panel_surface, panel.topleft)

    blit_text("探索任务完成！", font_title, (58, 116, 182), center=(450, 235))
    blit_text("恭喜抵达新星港湾", font_normal, TEXT_COLOR, center=(450, 295))
    blit_text("全部7个关卡已经完成", font_small, SUB_TEXT, center=(450, 335))

    restart_rect = pygame.Rect(350, 390, 200, 55)
    draw_button(restart_rect, "重新探索")


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
        target_x = start_x
        target_y = BOARD_Y - 90
    elif direction == "down":
        target_x = start_x
        target_y = BOARD_Y + BOARD_SIZE + 90
    elif direction == "left":
        target_x = BOARD_X - 90
        target_y = start_y
    else:
        target_x = BOARD_X + BOARD_SIZE + 90
        target_y = start_y

    animation = {
        "type": "fly",
        "x": start_x,
        "y": start_y,
        "target_x": target_x,
        "target_y": target_y,
        "direction": direction,
        "color": color,
        "speed": 16,
        "arrow": arrow
    }


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

    global current_level
    global game_state

    if len(arrows) != 0:
        return

    finish_time = current_elapsed

    old_best = best_times[current_level]

    if old_best is None or finish_time < old_best:
        best_times[current_level] = finish_time

    if current_level == len(levels) - 1:
        game_state = "win"
    else:
        current_level += 1
        load_level(current_level)


def start_collision_animation(arrow, blocker):

    global animation

    row, col, direction, color_index = arrow

    start_x, start_y = get_arrow_position(row, col)
    blocker_x, blocker_y = get_arrow_position(blocker[0], blocker[1])

    if direction == "up":
        target_x = start_x
        target_y = blocker_y + 32
    elif direction == "down":
        target_x = start_x
        target_y = blocker_y - 32
    elif direction == "left":
        target_x = blocker_x + 32
        target_y = start_y
    else:
        target_x = blocker_x - 32
        target_y = start_y

    color = rocket_colors[color_index % len(rocket_colors)]

    animation = {
        "type": "collision",
        "phase": "move",
        "x": start_x,
        "y": start_y,
        "start_x": start_x,
        "start_y": start_y,
        "target_x": target_x,
        "target_y": target_y,
        "direction": direction,
        "color": color,
        "arrow": arrow,
        "speed": 11,
        "timer": 0
    }


def update_collision_animation():

    global animation
    global mistakes
    global star_explosion
    global game_state

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

            # ---- 碰撞瞬间：明显爆炸 + 星星爆炸同时触发 ----
            start_explosion(animation["x"], animation["y"], size=1.25)

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
                game_state = "fail"

        else:
            animation["x"] += dx / distance * animation["speed"]
            animation["y"] += dy / distance * animation["speed"]


def start_star_explosion(star_index):

    global star_explosion

    if star_index < 0:
        star_index = 0

    if star_index > 2:
        star_index = 2

    star_x = 745 + star_index * 35

    star_explosion = {
        "x": star_x,
        "y": 55,
        "timer": 0,
        "duration": 36
    }


def update_star_explosion():

    global star_explosion

    if star_explosion is None:
        return

    star_explosion["timer"] += 1

    if star_explosion["timer"] >= star_explosion["duration"]:
        star_explosion = None


def show_hint():

    global hint_cell
    global hint_timer

    target = find_hint_arrow()

    if target is None:
        return

    hint_cell = (target[0], target[1])
    hint_timer = 180


def update_hint():

    global hint_cell
    global hint_timer

    if hint_cell is None:
        return

    hint_timer -= 1

    if hint_timer <= 0:
        hint_cell = None


def get_game_time():
    return (pygame.time.get_ticks() - level_start_time - paused_total) / 1000


load_level(current_level)

running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:

            if event.key == pygame.K_ESCAPE:

                if game_state == "game":
                    game_state = "pause"
                    pause_started = pygame.time.get_ticks()

                elif game_state == "pause":
                    paused_total += pygame.time.get_ticks() - pause_started
                    game_state = "game"

        if event.type == pygame.MOUSEBUTTONDOWN:

            mouse_x, mouse_y = event.pos

            if game_state == "start":

                start_rect = pygame.Rect(350, 380, 200, 60)

                if start_rect.collidepoint(mouse_x, mouse_y):
                    current_level = 0
                    load_level(current_level)
                    game_state = "game"

            elif game_state == "game":

                restart_rect = pygame.Rect(35, 620, 125, 45)
                pause_rect = pygame.Rect(690, 610, 80, 45)
                hint_rect = pygame.Rect(780, 610, 80, 45)

                if restart_rect.collidepoint(mouse_x, mouse_y):
                    load_level(current_level)

                elif pause_rect.collidepoint(mouse_x, mouse_y):
                    pause_started = pygame.time.get_ticks()
                    game_state = "pause"

                elif hint_rect.collidepoint(mouse_x, mouse_y):
                    show_hint()

                elif animation is None:

                    if (
                        BOARD_X <= mouse_x < BOARD_X + BOARD_SIZE
                        and BOARD_Y <= mouse_y < BOARD_Y + BOARD_SIZE
                    ):

                        col = (mouse_x - BOARD_X) // CELL_SIZE
                        row = (mouse_y - BOARD_Y) // CELL_SIZE

                        clicked = find_arrow(row, col)

                        if clicked:

                            blocker = get_blocking_arrow(clicked)

                            if blocker is None:
                                arrows.remove(clicked)
                                start_fly_animation(clicked)
                            else:
                                arrows.remove(clicked)
                                start_collision_animation(clicked, blocker)

            elif game_state == "pause":

                continue_rect = pygame.Rect(350, 350, 200, 52)
                restart_rect = pygame.Rect(350, 415, 200, 45)

                if continue_rect.collidepoint(mouse_x, mouse_y):
                    paused_total += pygame.time.get_ticks() - pause_started
                    game_state = "game"

                elif restart_rect.collidepoint(mouse_x, mouse_y):
                    load_level(current_level)
                    game_state = "game"

            elif game_state == "fail":

                restart_rect = pygame.Rect(350, 395, 200, 55)

                if restart_rect.collidepoint(mouse_x, mouse_y):
                    load_level(current_level)
                    game_state = "game"

            elif game_state == "win":

                restart_rect = pygame.Rect(350, 390, 200, 55)

                if restart_rect.collidepoint(mouse_x, mouse_y):
                    current_level = 0
                    load_level(current_level)
                    game_state = "game"

    if game_state == "game":

        current_elapsed = get_game_time()

        if animation is not None:
            if animation["type"] == "fly":
                update_fly_animation()
            elif animation["type"] == "collision":
                update_collision_animation()

        update_hint()
        update_star_explosion()
        update_explosions()

    elif game_state == "pause":
        current_elapsed = get_game_time()
        update_star_explosion()
        update_explosions()

    elif game_state == "win":
        if current_level == 6:
            final_explosion_timer += 1

    if game_state == "start":
        draw_start_screen()
    elif game_state == "game":
        draw_game_screen()
    elif game_state == "pause":
        draw_pause_screen()
    elif game_state == "fail":
        draw_fail_screen()
    elif game_state == "win":
        draw_win_screen()

    pygame.display.flip()
    clock.tick(60)


pygame.quit()
sys.exit()