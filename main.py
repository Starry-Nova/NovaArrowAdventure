import pygame
import sys
import math
import random
import os
import array

# ---------------------------------------------------------------------------
# mixer 预初始化（必须在 pygame.init() 之前）
# ---------------------------------------------------------------------------

try:
    pygame.mixer.pre_init(frequency=22050, size=-16, channels=2, buffer=512)
except Exception:
    pass

pygame.init()

WIDTH = 900
HEIGHT = 700

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("一箭又一箭 · 太空探索")


# ===========================================================================
# 音效系统：纯 Python 实时合成
# ===========================================================================

audio_enabled = False
try:
    if pygame.mixer.get_init():
        audio_enabled = True
    else:
        pygame.mixer.init()
        audio_enabled = bool(pygame.mixer.get_init())
except Exception:
    audio_enabled = False

# 全局音效开关（游戏内按钮可切换）
sound_on = True


def _synth_sound(duration, sr, fn):
    """用回调 fn(t) -> [-1, 1] 生成一段立体声 Sound。"""
    n = int(sr * duration)
    buf = array.array('h')
    for i in range(n):
        t = i / sr
        v = fn(t)
        if v > 1.0:
            v = 1.0
        elif v < -1.0:
            v = -1.0
        s = int(v * 30000)
        buf.append(s)
        buf.append(s)
    return pygame.mixer.Sound(buffer=buf.tobytes())


def _make_launch_sound(sr=22050):
    """火箭发射：柔和的上升音（降低音高、去高频、平滑包络）。"""
    duration = 0.62
    # 用 C5 E5 G5 C6，比原来低两个八度，听感温和不刺耳
    notes = [523.25, 659.25, 783.99, 1046.5]

    def fn(t):
        v = 0.0
        for j, f in enumerate(notes):
            delay = j * 0.055
            if t < delay:
                continue
            tt = t - delay

            # 平滑起音，避免"啪"的一声
            attack = min(1.0, tt * 45)
            # 柔和衰减
            env = math.exp(-tt * 3.2) * attack

            # 基频为主 + 少量二次谐波，音色更圆润
            gain = 1.0 / (j * 0.5 + 2.0)
            v += math.sin(2 * math.pi * f * tt) * env * gain * 0.90
            v += math.sin(2 * math.pi * f * 2 * tt) * env * gain * 0.14

        # 整体首尾淡入淡出
        v *= min(1.0, t * 80)
        v *= min(1.0, (duration - t) * 10)
        return v * 0.52

    return _synth_sound(duration, sr, fn)


def _make_explosion_sound(sr=22050):
    """碰撞爆炸：高频冲击 + 低频隆隆。"""
    duration = 0.65
    rnd = random.Random(7)
    n = int(sr * duration)

    high_noise = [rnd.uniform(-1, 1) for _ in range(n)]

    low_noise = []
    prev = 0.0
    for _ in range(n):
        x = rnd.uniform(-1, 1)
        prev += 0.03 * (x - prev)
        low_noise.append(prev * 4.5)

    def fn(t):
        i = int(t * sr)
        if i >= n:
            return 0.0
        high_env = math.exp(-t * 55)
        mid_env = math.exp(-t * 11)
        low_env = math.exp(-t * 3.8)

        v = high_noise[i] * high_env * 0.55
        v += low_noise[i] * mid_env * 0.55
        v += math.sin(2 * math.pi * 42 * t) * low_env * 0.55
        v += math.sin(2 * math.pi * 78 * t) * low_env * 0.28

        v *= min(1.0, t * 400)
        v *= min(1.0, (duration - t) * 14)
        return v * 0.85

    return _synth_sound(duration, sr, fn)


def _make_star_lost_sound(sr=22050):
    """星星破碎：柔和的下滑短音。"""
    duration = 0.40

    def fn(t):
        f = 1200 - 500 * (t / duration)
        env = math.exp(-t * 6)
        v = math.sin(2 * math.pi * f * t) * env * 0.40
        v += math.sin(2 * math.pi * f * 1.5 * t) * env * 0.10
        v *= min(1.0, t * 200)
        v *= min(1.0, (duration - t) * 20)
        return v

    return _synth_sound(duration, sr, fn)


def _make_click_sound(sr=22050):
    """按钮点击。"""
    duration = 0.08

    def fn(t):
        env = math.exp(-t * 45)
        v = math.sin(2 * math.pi * 880 * t) * env * 0.5
        v += math.sin(2 * math.pi * 1320 * t) * env * 0.3
        v *= min(1.0, t * 400)
        return v

    return _synth_sound(duration, sr, fn)


def _make_win_sound(sr=22050):
    """关卡完成：上行琶音。"""
    duration = 0.9
    notes = [523.25, 659.25, 783.99, 1046.5]  # C5 E5 G5 C6

    def fn(t):
        v = 0.0
        for j, f in enumerate(notes):
            delay = j * 0.12
            if t < delay:
                continue
            tt = t - delay
            env = math.exp(-tt * 3.5)
            v += math.sin(2 * math.pi * f * tt) * env * 0.22
            v += math.sin(2 * math.pi * f * 2 * tt) * env * 0.08
        v *= min(1.0, t * 100)
        v *= min(1.0, (duration - t) * 10)
        return v

    return _synth_sound(duration, sr, fn)


def _make_fail_sound(sr=22050):
    """失败：下行低音。"""
    duration = 0.85
    notes = [392.0, 349.23, 293.66, 220.0]  # G4 F4 D4 A3

    def fn(t):
        v = 0.0
        for j, f in enumerate(notes):
            delay = j * 0.13
            if t < delay:
                continue
            tt = t - delay
            env = math.exp(-tt * 3.0)
            v += math.sin(2 * math.pi * f * tt) * env * 0.25
        v *= min(1.0, t * 100)
        v *= min(1.0, (duration - t) * 8)
        return v

    return _synth_sound(duration, sr, fn)


sfx_launch = None
sfx_explosion = None
sfx_star_lost = None
sfx_click = None
sfx_win = None
sfx_fail = None

if audio_enabled:
    try:
        sfx_launch = _make_launch_sound()
        sfx_explosion = _make_explosion_sound()
        sfx_star_lost = _make_star_lost_sound()
        sfx_click = _make_click_sound()
        sfx_win = _make_win_sound()
        sfx_fail = _make_fail_sound()

        sfx_launch.set_volume(0.50)      # 发射音音量略降，更温和
        sfx_explosion.set_volume(0.65)
        sfx_star_lost.set_volume(0.42)
        sfx_click.set_volume(0.40)
        sfx_win.set_volume(0.55)
        sfx_fail.set_volume(0.50)
    except Exception:
        audio_enabled = False


def play_sound(sfx):
    """播放音效；受全局开关和音频设备可用性双重控制。"""
    if not sound_on:
        return
    if audio_enabled and sfx is not None:
        try:
            sfx.play()
        except Exception:
            pass


def play_launch():
    play_sound(sfx_launch)


def play_explosion():
    play_sound(sfx_explosion)


def play_star_lost():
    play_sound(sfx_star_lost)


def play_click():
    play_sound(sfx_click)


def play_win():
    play_sound(sfx_win)


def play_fail():
    play_sound(sfx_fail)


# ===========================================================================
# 时间格式
# ===========================================================================

def format_time(seconds):
    seconds = max(0.0, float(seconds))
    minutes = int(seconds // 60)
    remain = seconds - minutes * 60
    return f"{minutes:02d}:{remain:05.2f}"


clock = pygame.time.Clock()

BG = (245, 241, 232)
TEXT_COLOR = (70, 64, 58)
SUB_TEXT = (120, 112, 102)
WHITE = (255, 255, 255)

BUTTON_COLOR = (90, 150, 190)
BUTTON_HOVER = (110, 170, 205)
BUTTON_HOME = (140, 165, 190)
BUTTON_HOME_HOVER = (160, 185, 210)
BUTTON_GOLD = (240, 175, 65)
BUTTON_GOLD_HOVER = (255, 195, 85)

RED = (235, 75, 70)
YELLOW = (255, 215, 70)

# ---------------------------------------------------------------------------
# 棋盘布局：左侧 2/3
# ---------------------------------------------------------------------------

BOARD_X = 40
BOARD_Y = 120
BOARD_SIZE = 530

GRID_SIZE = 7
CELL_SIZE = BOARD_SIZE // GRID_SIZE

# 右侧信息面板
PANEL_X = 610
PANEL_Y = 110
PANEL_W = 280
PANEL_H = 560

# 关卡内按钮（面板底部，四个并排）
GAME_BTN_RESTART = pygame.Rect(618, 612, 64, 42)
GAME_BTN_PAUSE = pygame.Rect(686, 612, 64, 42)
GAME_BTN_HINT = pygame.Rect(754, 612, 64, 42)
GAME_BTN_SOUND = pygame.Rect(822, 612, 64, 42)

# ---------------------------------------------------------------------------
# 字体
# ---------------------------------------------------------------------------

FONT_NAMES = ",".join([
    "microsoftyaheiui", "microsoftyahei", "msyh",
    "pingfangsc", "heitisc", "dengxian",
    "notosanscjksc", "notosanssc", "sourcehansanssc",
    "wenquanyimicrohei", "wenquanyizenhei", "simhei", "simsun",
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


font_title = get_font(40, bold=True)
font_main_title = get_font(54, bold=True)
font_subtitle = get_font(17)
font_big = get_font(28, bold=True)
font_modal_title = get_font(38, bold=True)
font_normal = get_font(21)
font_small = get_font(17)
font_tiny = get_font(15)
font_micro = get_font(14)
font_button = get_font(17, bold=True)
font_button_small = get_font(15, bold=True)
font_button_tiny = get_font(13, bold=True)   # 关卡内 4 个按钮用


def blit_text(text, font, color, shadow_alpha=50, target=None, **rect_kwargs):
    if target is None:
        target = screen
    image = font.render(text, True, color)
    rect = image.get_rect(**rect_kwargs)

    if shadow_alpha > 0:
        shadow = font.render(text, True, (10, 14, 22))
        shadow.set_alpha(shadow_alpha)
        target.blit(shadow, (rect.x + 1, rect.y + 2))

    target.blit(image, rect)
    return rect


def wrap_text(text, font, max_width):
    lines = []
    current = ""
    for char in text:
        test = current + char
        if font.size(test)[0] > max_width and current:
            lines.append(current)
            current = char
        else:
            current = test
    if current:
        lines.append(current)
    return lines


# ---------------------------------------------------------------------------
# 游戏数据
# ---------------------------------------------------------------------------

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
    "跨越遥远星际，终于抵达目标新星，完成太空探索任务。"
]

level_congrats = [
    "点火成功！你已经迈出了星际探索的第一步。",
    "穿越大气，你离星空更近了一步。",
    "稳定入轨，地球在脚下缓缓转动。",
    "告别家园，勇敢驶向更远的星海。",
    "抵达月球轨道，深空探索继续推进。",
    "穿越行星际，孤独星空里仍保持前进。",
    "新星已在眼前，这是属于你的荣耀时刻！"
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

has_progress = False
continue_level = 0
level_complete_info = None

button_states = {}
_pending_action = None

level_complete_anim = 0
_blur_cache = None

# ---------------------------------------------------------------------------
# 背景星星
# ---------------------------------------------------------------------------

background_stars = []
random.seed(42)

for i in range(260):
    background_stars.append({
        "x": random.randint(0, WIDTH),
        "y": random.randint(0, HEIGHT),
        "size": random.choice([1, 1, 1, 1, 2]),
        "phase": random.random() * math.pi * 2,
        "speed": random.uniform(0.55, 1.4),
        "bright_base": random.uniform(90, 160),
        "bright_range": random.uniform(50, 95),
    })

# 流星数据
meteors = []
for i in range(3):
    meteors.append({
        "x": random.uniform(0, WIDTH),
        "y": random.uniform(0, HEIGHT * 0.5),
        "vx": random.uniform(1.2, 2.0),
        "vy": random.uniform(0.6, 1.2),
        "len": random.uniform(50, 90),
        "life": random.uniform(0, 6),
        "max_life": random.uniform(5, 9),
    })


# ===========================================================================
# 标题艺术字
# ===========================================================================

_art_title_cache = {}


def _build_art_title(scale):
    chars = "一箭又一箭"
    sizes = [40, 54, 34, 40, 54]
    y_offsets = [6, -6, 10, 6, -6]
    colors = [
        (55, 105, 190),
        (90, 175, 255),
        (255, 210, 70),
        (240, 248, 255),
        (90, 175, 255),
    ]

    gap = 4

    rendered = []
    total_w = 0
    max_h = 0
    for i, ch in enumerate(chars):
        f = get_font(int(sizes[i] * scale), bold=True)
        img = f.render(ch, True, colors[i])
        w, h = img.get_size()
        rendered.append({"img": img, "w": w, "h": h, "font": f, "y_off": y_offsets[i]})
        total_w += w
        max_h = max(max_h, h)
    total_w += gap * (len(chars) - 1)

    pad = 34
    surface = pygame.Surface((total_w + pad * 2, max_h + pad * 2), pygame.SRCALPHA)

    x = pad
    cy = pad + max_h // 2
    for i, item in enumerate(rendered):
        img = item["img"]
        w, h = item["w"], item["h"]
        cx = x + w // 2
        char_y = cy + int(item["y_off"] * scale)

        glow = item["font"].render(chars[i], True, (110, 190, 255))
        glow.set_alpha(70)
        for dx, dy in [(-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, 2), (-2, 2), (2, -2)]:
            surface.blit(glow, glow.get_rect(center=(cx + dx, char_y + dy)))

        outline = item["font"].render(chars[i], True, (250, 252, 255))
        for dx, dy in [(-2, 0), (2, 0), (0, -2), (0, 2)]:
            surface.blit(outline, outline.get_rect(center=(cx + dx, char_y + dy)))

        surface.blit(img, img.get_rect(center=(cx, char_y)))

        x += w + gap

    return surface


def get_art_title(scale=1.0):
    key = round(scale, 2)
    if key not in _art_title_cache:
        _art_title_cache[key] = _build_art_title(key)
    return _art_title_cache[key]


def draw_small_star(target, x, y, r, alpha=255, color=(255, 235, 130)):
    points = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        rr = r if i % 2 == 0 else r * 0.42
        points.append((x + math.cos(angle) * rr, y + math.sin(angle) * rr))
    pygame.draw.polygon(target, (*color, alpha), points)


def draw_space_decor(target, x, y, kind, size=14, alpha=255, t=0.0):
    if kind == "star":
        draw_small_star(target, x, y, size, alpha)

    elif kind == "planet":
        r = size
        halo = pygame.Surface((r * 4, r * 4), pygame.SRCALPHA)
        hc = r * 2
        pygame.draw.ellipse(halo, (200, 160, 255, alpha // 2),
                            (hc - r * 1.7, hc - r * 0.35, r * 3.4, r * 0.7), 2)
        target.blit(halo, (x - hc, y - hc))
        pygame.draw.circle(target, (170, 130, 220, alpha), (int(x), int(y)), r)
        pygame.draw.circle(target, (210, 180, 250, alpha),
                           (int(x - r * 0.3), int(y - r * 0.3)), max(2, int(r * 0.4)))

    elif kind == "rocket":
        r = size
        body_pts = [(x, y - r * 1.3), (x - r * 0.45, y + r * 0.4),
                    (x + r * 0.45, y + r * 0.4)]
        pygame.draw.polygon(target, (240, 120, 100, alpha), body_pts)
        pygame.draw.polygon(target, (255, 190, 90, alpha),
                            [(x - r * 0.45, y + r * 0.4), (x - r * 0.8, y + r * 0.9),
                             (x - r * 0.35, y + r * 0.7)])
        pygame.draw.polygon(target, (255, 190, 90, alpha),
                            [(x + r * 0.45, y + r * 0.4), (x + r * 0.8, y + r * 0.9),
                             (x + r * 0.35, y + r * 0.7)])
        pygame.draw.circle(target, (150, 220, 255, alpha),
                           (int(x), int(y - r * 0.25)), max(2, int(r * 0.28)))

    elif kind == "comet":
        r = size * 0.6
        tail = pygame.Surface((size * 6, size * 2), pygame.SRCALPHA)
        for i in range(10):
            a = int(alpha * (1 - i / 10) * 0.6)
            rr = int(r * (1 - i / 12))
            pygame.draw.circle(tail, (170, 215, 255, a),
                               (int(size * 0.5 + i * size * 0.5), size),
                               max(1, rr))
        target.blit(tail, (x - size * 0.5, y - size))
        pygame.draw.circle(target, (235, 248, 255, alpha), (int(x), int(y)), int(r * 1.1))
        pygame.draw.circle(target, (255, 255, 255, alpha), (int(x), int(y)), max(1, int(r * 0.5)))


def draw_art_title_with_decor(target, cx, cy, scale=1.0):
    surface = get_art_title(scale)
    rect = surface.get_rect(center=(cx, cy))
    target.blit(surface, rect)

    t = pygame.time.get_ticks() / 1000.0

    draw_space_decor(target, rect.left - 22, rect.top + 18, "rocket",
                     size=11, alpha=255)
    draw_space_decor(target, rect.left - 6, rect.bottom - 10, "star",
                     size=8, alpha=220)
    draw_space_decor(target, rect.right + 24, rect.top + 16, "planet",
                     size=10, alpha=255)
    draw_space_decor(target, rect.right + 8, rect.bottom - 8, "comet",
                     size=13, alpha=230)

    pulse = (math.sin(t * 2.0) + 1) / 2
    draw_space_decor(target, rect.centerx - 70, rect.top - 8, "star",
                     size=6, alpha=int(160 + 80 * pulse))
    pulse2 = (math.sin(t * 2.0 + 1.6) + 1) / 2
    draw_space_decor(target, rect.centerx + 76, rect.top - 6, "star",
                     size=7, alpha=int(160 + 80 * pulse2))


# ===========================================================================
# 开始界面场景
# ===========================================================================

start_clouds = []
start_grass = []
start_flowers = []

_CLOUD_BASE = None


def _get_cloud_base():
    global _CLOUD_BASE
    if _CLOUD_BASE is not None:
        return _CLOUD_BASE

    w, h = 220, 130
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    color = (255, 255, 255, 255)
    cx, cy = w // 2, h // 2

    pygame.draw.circle(surf, color, (cx - 58, cy + 22), 30)
    pygame.draw.circle(surf, color, (cx - 20, cy + 26), 36)
    pygame.draw.circle(surf, color, (cx + 22, cy + 26), 36)
    pygame.draw.circle(surf, color, (cx + 58, cy + 22), 30)
    pygame.draw.circle(surf, color, (cx - 38, cy - 6), 34)
    pygame.draw.circle(surf, color, (cx + 4, cy - 16), 42)
    pygame.draw.circle(surf, color, (cx + 44, cy - 4), 34)
    pygame.draw.rect(surf, color, (cx - 78, cy + 12, 156, 44))

    surf = pygame.transform.smoothscale(surf, (w, h))
    _CLOUD_BASE = surf
    return surf


def make_cloud_surface(scale):
    base = _get_cloud_base()
    w = max(10, int(base.get_width() * scale))
    h = max(10, int(base.get_height() * scale))
    return pygame.transform.smoothscale(base, (w, h))


def init_start_scene():
    global start_clouds, start_grass, start_flowers

    start_clouds = []
    start_grass = []
    start_flowers = []

    rnd = random.Random(2024)

    cloud_specs = [
        (0.45, 40, 0.10), (0.62, 100, 0.15), (0.85, 160, 0.24),
        (0.55, 225, 0.13), (0.95, 185, 0.32), (0.68, 250, 0.18),
        (1.10, 72, 0.36), (0.55, 200, 0.11), (0.78, 130, 0.27),
        (1.18, 222, 0.44), (0.60, 60, 0.08),
    ]
    for scale, y, speed in cloud_specs:
        surf = make_cloud_surface(scale)
        x = rnd.uniform(-160, WIDTH + 80)
        surf.set_alpha(min(245, int(160 + 80 * scale)))
        start_clouds.append({"x": x, "y": y, "speed": speed, "surf": surf})

    for _ in range(240):
        start_grass.append({
            "x": rnd.uniform(0, WIDTH),
            "y": rnd.uniform(495, HEIGHT + 20),
            "height": rnd.uniform(7, 21),
            "phase": rnd.uniform(0, math.pi * 2),
            "speed": rnd.uniform(1.4, 2.6),
            "shade": rnd.uniform(0.88, 1.15),
        })

    flower_colors = [
        (255, 150, 180), (255, 200, 100), (255, 120, 120),
        (200, 160, 255), (255, 240, 150), (240, 160, 220),
        (255, 175, 200), (255, 225, 130),
    ]
    for _ in range(46):
        start_flowers.append({
            "x": rnd.uniform(20, WIDTH - 20),
            "y": rnd.uniform(515, HEIGHT - 14),
            "size": rnd.uniform(4.2, 7.8),
            "phase": rnd.uniform(0, math.pi * 2),
            "color": rnd.choice(flower_colors),
        })


init_start_scene()


# ===========================================================================
# 按钮动画系统
# ===========================================================================

def _button_state(key):
    if key not in button_states:
        button_states[key] = {"scale": 1.0, "glow": 0.0, "press": 0}
    return button_states[key]


def trigger_button_press(key):
    _button_state(key)["press"] = 12
    play_click()


def schedule_button_action(delay, action):
    global _pending_action
    _pending_action = {"timer": delay, "action": action}


def update_button_state(key, base_rect, mouse_pos):
    state = _button_state(key)
    hovered = base_rect.collidepoint(mouse_pos)

    if state["press"] > 0:
        state["press"] -= 1
        p = state["press"] / 12.0
        state["scale"] = 1.0 - 0.10 * math.sin(math.pi * (1 - p))
    else:
        target_scale = 1.05 if hovered else 1.0
        state["scale"] += (target_scale - state["scale"]) * 0.25

    target_glow = 1.0 if hovered else 0.0
    state["glow"] += (target_glow - state["glow"]) * 0.2


def draw_animated_button(key, base_rect, text, color=None, hover=None,
                         target=None, font=None):
    if target is None:
        target = screen
    if color is None:
        color = BUTTON_COLOR
    if hover is None:
        hover = BUTTON_HOVER
    if font is None:
        font = font_button

    state = _button_state(key)
    scale = state["scale"]
    glow = state["glow"]

    scaled_w = max(4, int(base_rect.width * scale))
    scaled_h = max(4, int(base_rect.height * scale))
    scaled_rect = pygame.Rect(0, 0, scaled_w, scaled_h)
    scaled_rect.center = base_rect.center

    if glow > 0.02:
        for i in range(7, 0, -1):
            expand = i * 3
            alpha = int(58 * glow * (1 - i / 8))
            if alpha <= 0:
                continue
            glow_rect = scaled_rect.inflate(expand * 2, expand * 2)
            gs = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(
                gs, (hover[0], hover[1], hover[2], alpha),
                gs.get_rect(), border_radius=11 + expand
            )
            target.blit(gs, glow_rect.topleft)

    shadow_rect = scaled_rect.move(0, 3)
    pygame.draw.rect(target, (42, 72, 102), shadow_rect, border_radius=11)

    r = int(color[0] * (1 - glow) + hover[0] * glow)
    g = int(color[1] * (1 - glow) + hover[1] * glow)
    b = int(color[2] * (1 - glow) + hover[2] * glow)
    pygame.draw.rect(target, (r, g, b), scaled_rect, border_radius=11)

    hl_rect = pygame.Rect(
        scaled_rect.x + 4, scaled_rect.y + 3,
        scaled_rect.width - 8,
        max(6, scaled_rect.height // 2 - 4)
    )
    hl_surf = pygame.Surface((hl_rect.width, hl_rect.height), pygame.SRCALPHA)
    pygame.draw.rect(
        hl_surf, (255, 255, 255, int(40 + 40 * glow)),
        hl_surf.get_rect(), border_radius=8
    )
    target.blit(hl_surf, hl_rect.topleft)

    text_img = font.render(text, True, WHITE)
    if abs(scale - 1.0) > 0.005:
        new_w = max(1, int(text_img.get_width() * scale))
        new_h = max(1, int(text_img.get_height() * scale))
        text_img = pygame.transform.smoothscale(text_img, (new_w, new_h))
    target.blit(text_img, text_img.get_rect(center=scaled_rect.center))


START_BUTTON_NEW = pygame.Rect(230, 620, 200, 58)
START_BUTTON_CONT = pygame.Rect(470, 620, 200, 58)
START_BUTTON_SINGLE = pygame.Rect(350, 620, 200, 58)


# ===========================================================================
# 关卡逻辑
# ===========================================================================

def load_level(level_index):
    global arrows, mistakes, animation, star_explosion, explosions
    global hint_cell, hint_timer, paused_total, level_start_time
    global current_elapsed, final_explosion_timer, level_complete_anim

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


# ===========================================================================
# 背景绘制
# ===========================================================================

def draw_stars(count):
    current_time = pygame.time.get_ticks()
    for star in background_stars[:count]:
        wave = (math.sin(current_time / 700 * star["speed"] + star["phase"]) + 1) / 2
        brightness = int(star["bright_base"] + wave * star["bright_range"])
        pygame.draw.circle(
            screen, (brightness, brightness, min(255, brightness + 18)),
            (star["x"], star["y"]), star["size"]
        )


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

        steps = 8
        for i in range(steps):
            t = i / steps
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
            pygame.draw.line(
                screen,
                (int(80 + 50 * ratio), int(100 + 30 * ratio), int(180 + 40 * ratio)),
                (0, y), (WIDTH, y)
            )
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


# ===========================================================================
# 火箭绘制
# ===========================================================================

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


# ===========================================================================
# 棋盘
# ===========================================================================

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
            pygame.draw.circle(
                screen, (255, 220, 70), (int(x), int(y)),
                int(37 + pulse * 6), 4
            )

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


# ===========================================================================
# 特效
# ===========================================================================

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
                pygame.draw.circle(flash_surf, (255, 220, 110, flash_alpha * 3 // 4), center, int(flash_r * 0.72))
                pygame.draw.circle(flash_surf, (255, 255, 245, flash_alpha), center, max(1, int(flash_r * 0.4)))
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


# ===========================================================================
# 右侧信息面板
# ===========================================================================

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


def draw_game_screen():
    draw_background()
    draw_art_title_with_decor(screen, BOARD_X + BOARD_SIZE // 2, 54, scale=0.72)
    draw_side_panel()
    draw_board()
    draw_arrows()
    draw_animation()
    draw_explosions()

    # 面板底部四个按钮
    draw_animated_button("game_restart", GAME_BTN_RESTART, "重新开始",
                         target=screen, font=font_button_tiny)
    draw_animated_button("game_pause", GAME_BTN_PAUSE, "暂停",
                         target=screen, font=font_button_tiny)
    draw_animated_button("game_hint", GAME_BTN_HINT, "提示",
                         target=screen, font=font_button_tiny)

    # 音效开关：开启金色 / 关闭灰蓝
    if sound_on:
        draw_animated_button("game_sound", GAME_BTN_SOUND, "音效开",
                             color=BUTTON_GOLD, hover=BUTTON_GOLD_HOVER,
                             target=screen, font=font_button_tiny)
    else:
        draw_animated_button("game_sound", GAME_BTN_SOUND, "音效关",
                             color=BUTTON_HOME, hover=BUTTON_HOME_HOVER,
                             target=screen, font=font_button_tiny)


# ===========================================================================
# 开始界面
# ===========================================================================

def draw_start_sky():
    for y in range(0, HEIGHT):
        ratio = min(1.0, y / 470)
        r = int(150 + (205 - 150) * ratio)
        g = int(205 + (232 - 205) * ratio)
        b = int(240 + (250 - 240) * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (WIDTH, y))


def draw_start_sun():
    t = pygame.time.get_ticks() / 1000.0
    sun_pulse = (math.sin(t * 0.9) + 1) / 2
    sun_x, sun_y = 790, 82

    for i in range(6, 0, -1):
        r = int(58 + i * 14 + sun_pulse * (10 + i * 3))
        alpha = int(38 * (1 - i / 7) * (0.55 + 0.45 * sun_pulse))
        if alpha <= 0:
            continue
        glow_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, (255, 235, 160, alpha), (r, r), r)
        screen.blit(glow_surf, (sun_x - r, sun_y - r))

    pygame.draw.circle(screen, (255, 242, 195), (sun_x, sun_y), 62)
    pygame.draw.circle(screen, (255, 248, 215), (sun_x, sun_y), 48)
    pygame.draw.circle(screen, (255, 252, 235), (sun_x, sun_y), 34)
    pygame.draw.circle(screen, (255, 255, 250), (sun_x, sun_y), 22)


def draw_start_grass_ground():
    grass_top = 460
    grass_h = HEIGHT - grass_top

    grass_grad = pygame.Surface((WIDTH, grass_h), pygame.SRCALPHA)
    for y in range(grass_h):
        ratio = y / grass_h
        r = int(150 - 44 * ratio)
        g = int(210 - 44 * ratio)
        b = int(120 - 34 * ratio)
        pygame.draw.line(grass_grad, (r, g, b), (0, y), (WIDTH, y))

    mask = pygame.Surface((WIDTH, grass_h), pygame.SRCALPHA)
    pts = []
    for x in range(0, WIDTH + 4, 2):
        wy = 12 + math.sin(x / 130) * 5 + math.sin(x / 60 + 1.7) * 2.5
        pts.append((x, wy))
    pts.append((WIDTH, grass_h))
    pts.append((0, grass_h))
    pygame.draw.polygon(mask, (255, 255, 255, 255), pts)

    grass_grad.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    screen.blit(grass_grad, (0, grass_top))

    edge_pts = []
    for x in range(0, WIDTH + 4, 3):
        wy = grass_top + 13 + math.sin(x / 130) * 5 + math.sin(x / 60 + 1.7) * 2.5
        edge_pts.append((x, wy))
    for i in range(len(edge_pts) - 1):
        pygame.draw.line(screen, (176, 228, 148), edge_pts[i], edge_pts[i + 1], 2)


def draw_start_background():
    draw_start_sky()
    draw_start_sun()
    for cloud in start_clouds:
        surf = cloud["surf"]
        screen.blit(surf, (int(cloud["x"] - surf.get_width() // 2),
                           int(cloud["y"] - surf.get_height() // 2)))
    draw_start_grass_ground()


def draw_grass_and_flowers():
    t = pygame.time.get_ticks() / 1000.0

    for blade in start_grass:
        wave = math.sin(t * blade["speed"] + blade["phase"])
        sway = wave * blade["height"] * 0.38
        x = blade["x"]
        y = blade["y"]
        top = (x + sway, y - blade["height"])
        shade = blade["shade"]
        color = (int(110 * shade), int(180 * shade), int(85 * shade))
        pygame.draw.line(screen, color, (x, y), top, 2)

    for flower in start_flowers:
        wave = math.sin(t * 2 + flower["phase"])
        sway_x = wave * 2.5
        sway_y = math.sin(t * 1.7 + flower["phase"] * 1.3) * 0.9
        x = flower["x"] + sway_x
        y = flower["y"] + sway_y
        size = flower["size"]
        for i in range(5):
            angle = i * math.pi * 2 / 5
            px = x + math.cos(angle) * size * 0.65
            py = y + math.sin(angle) * size * 0.65
            pygame.draw.circle(screen, flower["color"], (int(px), int(py)), int(size * 0.7))
        pygame.draw.circle(screen, (255, 235, 110), (int(x), int(y)), int(size * 0.5))


def draw_launch_pad_and_rocket():
    t = pygame.time.get_ticks() / 1000.0
    bob = math.sin(t * 1.35) * 3.2

    cx = 450
    pad_y = 505

    pygame.draw.ellipse(screen, (66, 112, 52), (cx - 138, pad_y + 20, 276, 42))
    pygame.draw.ellipse(screen, (84, 132, 66), (cx - 128, pad_y + 18, 256, 36))
    pygame.draw.ellipse(screen, (100, 150, 78), (cx - 116, pad_y + 16, 232, 30))

    pygame.draw.rect(screen, (155, 160, 172), (cx - 95, pad_y - 6, 190, 30), border_radius=8)
    pygame.draw.rect(screen, (125, 130, 142), (cx - 105, pad_y + 18, 210, 12), border_radius=5)
    pygame.draw.rect(screen, (185, 190, 200), (cx - 88, pad_y - 2, 176, 6), border_radius=3)

    draw_rocket(screen, cx, pad_y - 82 + bob, "up", (245, 130, 115),
                scale=2.8, flame=False, alpha=255)


def draw_start_screen():
    draw_start_background()
    draw_grass_and_flowers()
    draw_launch_pad_and_rocket()

    title_panel_w, title_panel_h = 620, 130
    title_panel = pygame.Surface((title_panel_w, title_panel_h), pygame.SRCALPHA)
    pygame.draw.rect(title_panel, (255, 255, 255, 135),
                     title_panel.get_rect(), border_radius=26)
    screen.blit(title_panel, (450 - title_panel_w // 2, 42))

    draw_art_title_with_decor(screen, 450, 100, scale=0.9)

    blit_text("太空火箭探索任务", font_subtitle, (85, 115, 155),
              shadow_alpha=15, center=(450, 152))

    if has_progress:
        draw_animated_button("new", START_BUTTON_NEW, "新的探索",
                             BUTTON_HOME, BUTTON_HOME_HOVER)
        draw_animated_button("cont", START_BUTTON_CONT, "继续探索",
                             BUTTON_GOLD, BUTTON_GOLD_HOVER)
    else:
        draw_animated_button("start", START_BUTTON_SINGLE, "开始探索",
                             BUTTON_GOLD, BUTTON_GOLD_HOVER)


# ===========================================================================
# 暂停 / 失败
# ===========================================================================

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

    draw_animated_button("pause_continue", pygame.Rect(350, 350, 200, 52), "继续探索")
    draw_animated_button("pause_restart", pygame.Rect(350, 415, 200, 45),
                         "重新开始", color=BUTTON_HOME, hover=BUTTON_HOME_HOVER)


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


# ===========================================================================
# 关卡总结框
# ===========================================================================

def blur_surface(surf, factor=7):
    w, h = surf.get_size()
    sw = max(1, w // factor)
    sh = max(1, h // factor)
    small = pygame.transform.smoothscale(surf, (sw, sh))
    return pygame.transform.smoothscale(small, (w, h))


def draw_modal_decor(target, panel):
    t = pygame.time.get_ticks() / 1000.0

    draw_space_decor(target, panel.left + 26, panel.top + 24, "planet",
                     size=10, alpha=230)
    draw_space_decor(target, panel.right - 32, panel.top + 26, "comet",
                     size=12, alpha=225)
    draw_space_decor(target, panel.left + 28, panel.bottom - 28, "rocket",
                     size=12, alpha=230)

    pulse = (math.sin(t * 2.2) + 1) / 2
    draw_space_decor(target, panel.right - 30, panel.bottom - 30, "star",
                     size=9, alpha=int(180 + 70 * pulse))

    p2 = (math.sin(t * 2.2 + 1.4) + 1) / 2
    draw_space_decor(target, panel.centerx - 130, panel.top + 18, "star",
                     size=6, alpha=int(160 + 70 * p2))
    p3 = (math.sin(t * 2.2 + 2.8) + 1) / 2
    draw_space_decor(target, panel.centerx + 130, panel.top + 18, "star",
                     size=7, alpha=int(160 + 70 * p3))


def draw_modal_panel(target, info, ease):
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
                    pygame.draw.circle(glow, (255, 225, 120, ga), (gc, gc),
                                       int(glow_r * k / 7))
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

    draw_modal_decor(target, panel)

    if is_final:
        home_rect = pygame.Rect(0, 0, 200, 52)
        home_rect.center = (cx, panel.bottom - 58)
        draw_animated_button("modal_home", home_rect, "返回首页",
                             color=BUTTON_GOLD, hover=BUTTON_GOLD_HOVER,
                             target=target)
    else:
        home_rect = pygame.Rect(0, 0, 170, 52)
        next_rect = pygame.Rect(0, 0, 170, 52)
        home_rect.center = (cx - 96, panel.bottom - 58)
        next_rect.center = (cx + 96, panel.bottom - 58)
        draw_animated_button("modal_home", home_rect, "返回首页",
                             color=BUTTON_HOME, hover=BUTTON_HOME_HOVER,
                             target=target)
        draw_animated_button("modal_next", next_rect, "下一关",
                             color=BUTTON_GOLD, hover=BUTTON_GOLD_HOVER,
                             target=target)


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
        _blur_cache = blur_surface(captured, factor=8)

    overlay_alpha = int(200 * ease)
    blurred = _blur_cache.copy()
    darken = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    darken.fill((6, 10, 22, 165))
    blurred.blit(darken, (0, 0))
    blurred.set_alpha(overlay_alpha)
    screen.blit(blurred, (0, 0))

    scale = 0.90 + 0.10 * ease

    tmp = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
    draw_modal_panel(tmp, info, ease)

    panel_region = tmp.subsurface((190, 100, 520, 500)).copy()
    scaled_w = int(520 * scale)
    scaled_h = int(500 * scale)
    scaled = pygame.transform.smoothscale(panel_region, (scaled_w, scaled_h))
    scaled.set_alpha(int(255 * ease))

    screen.blit(scaled, scaled.get_rect(center=(WIDTH // 2, HEIGHT // 2)))


# ===========================================================================
# 游戏逻辑函数
# ===========================================================================

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
        "arrow": arrow
    }

    play_launch()


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
    global current_level, game_state, level_complete_info
    global has_progress, continue_level, level_complete_anim, _blur_cache

    if len(arrows) != 0:
        return

    finish_time = current_elapsed
    old_best = best_times[current_level]
    is_record = old_best is None or finish_time < old_best

    if is_record:
        best_times[current_level] = finish_time
        best = finish_time
    else:
        best = old_best

    is_final = current_level == len(levels) - 1

    level_complete_info = {
        "level": current_level,
        "time": finish_time,
        "is_record": is_record,
        "best": best,
        "mistakes": mistakes,
        "is_final": is_final,
    }

    has_progress = True

    if not is_final:
        continue_level = current_level + 1
    else:
        continue_level = len(levels) - 1

    level_complete_anim = 0
    _blur_cache = None

    play_win()

    game_state = "level_complete"


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
        "timer": 0
    }


def update_collision_animation():
    global animation, mistakes, star_explosion, game_state

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

            play_explosion()
            play_star_lost()

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
                play_fail()
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

    m = max(1, mistakes + 1)
    spacing = 40
    total_w = (m - 1) * spacing
    cx = PANEL_X + PANEL_W // 2
    start_x = cx - total_w // 2

    star_explosion = {
        "x": start_x + star_index * spacing,
        "y": PANEL_Y + 112,
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
    global best_times, current_level, continue_level
    best_times = [None for _ in levels]
    current_level = 0
    continue_level = 0


# ===========================================================================
# 开始界面更新
# ===========================================================================

def update_start_scene():
    for cloud in start_clouds:
        cloud["x"] += cloud["speed"]
        half_w = cloud["surf"].get_width() // 2
        if cloud["x"] - half_w > WIDTH + 30:
            cloud["x"] = -half_w - 30

    mouse_pos = pygame.mouse.get_pos()
    if has_progress:
        update_button_state("new", START_BUTTON_NEW, mouse_pos)
        update_button_state("cont", START_BUTTON_CONT, mouse_pos)
    else:
        update_button_state("start", START_BUTTON_SINGLE, mouse_pos)


def _do_start_new():
    global current_level, continue_level, has_progress, game_state
    reset_progress()
    has_progress = True
    continue_level = 0
    current_level = 0
    load_level(current_level)
    game_state = "game"


def _do_start_continue():
    global current_level, game_state
    current_level = continue_level
    load_level(current_level)
    game_state = "game"


def _do_return_home():
    global game_state, has_progress
    has_progress = True
    game_state = "start"


def _do_next_level(level_index):
    global current_level, game_state
    current_level = level_index
    load_level(current_level)
    game_state = "game"


# ===========================================================================
# 主循环
# ===========================================================================

load_level(current_level)

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
                    paused_total += pygame.time.get_ticks() - pause_started
                    game_state = "game"

        if event.type == pygame.MOUSEBUTTONDOWN:
            mouse_x, mouse_y = event.pos

            # ---------------- 开始界面 ----------------
            if game_state == "start":
                if _pending_action is None:
                    if has_progress:
                        if START_BUTTON_NEW.collidepoint(mouse_x, mouse_y):
                            trigger_button_press("new")
                            schedule_button_action(10, _do_start_new)
                        elif START_BUTTON_CONT.collidepoint(mouse_x, mouse_y):
                            trigger_button_press("cont")
                            schedule_button_action(10, _do_start_continue)
                    else:
                        if START_BUTTON_SINGLE.collidepoint(mouse_x, mouse_y):
                            trigger_button_press("start")
                            schedule_button_action(10, _do_start_new)

            # ---------------- 关卡内 ----------------
            elif game_state == "game":
                if GAME_BTN_RESTART.collidepoint(mouse_x, mouse_y):
                    trigger_button_press("game_restart")
                    load_level(current_level)

                elif GAME_BTN_PAUSE.collidepoint(mouse_x, mouse_y):
                    trigger_button_press("game_pause")
                    pause_started = pygame.time.get_ticks()
                    game_state = "pause"

                elif GAME_BTN_HINT.collidepoint(mouse_x, mouse_y):
                    trigger_button_press("game_hint")
                    show_hint()

                elif GAME_BTN_SOUND.collidepoint(mouse_x, mouse_y):
                    # 音效开关切换
                    trigger_button_press("game_sound")
                    sound_on = not sound_on

                elif animation is None:
                    if (BOARD_X <= mouse_x < BOARD_X + BOARD_SIZE
                            and BOARD_Y <= mouse_y < BOARD_Y + BOARD_SIZE):

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

            # ---------------- 暂停 ----------------
            elif game_state == "pause":
                continue_rect = pygame.Rect(350, 350, 200, 52)
                restart_rect = pygame.Rect(350, 415, 200, 45)

                if continue_rect.collidepoint(mouse_x, mouse_y):
                    trigger_button_press("pause_continue")
                    paused_total += pygame.time.get_ticks() - pause_started
                    game_state = "game"
                elif restart_rect.collidepoint(mouse_x, mouse_y):
                    trigger_button_press("pause_restart")
                    load_level(current_level)
                    game_state = "game"

            # ---------------- 失败 ----------------
            elif game_state == "fail":
                restart_rect = pygame.Rect(230, 390, 200, 55)
                home_rect = pygame.Rect(470, 390, 200, 55)

                if restart_rect.collidepoint(mouse_x, mouse_y):
                    trigger_button_press("fail_restart")
                    load_level(current_level)
                    game_state = "game"
                elif home_rect.collidepoint(mouse_x, mouse_y):
                    trigger_button_press("fail_home")
                    schedule_button_action(10, _do_return_home)

            # ---------------- 关卡总结 ----------------
            elif game_state == "level_complete":
                info = level_complete_info

                if level_complete_anim < 18:
                    continue

                panel_rect = pygame.Rect(0, 0, 520, 500)
                panel_rect.center = (WIDTH // 2, HEIGHT // 2)

                if info["is_final"]:
                    home_rect = pygame.Rect(0, 0, 200, 52)
                    home_rect.center = (panel_rect.centerx, panel_rect.bottom - 58)
                    if home_rect.collidepoint(mouse_x, mouse_y):
                        trigger_button_press("modal_home")
                        schedule_button_action(10, _do_return_home)
                else:
                    home_rect = pygame.Rect(0, 0, 170, 52)
                    next_rect = pygame.Rect(0, 0, 170, 52)
                    home_rect.center = (panel_rect.centerx - 96, panel_rect.bottom - 58)
                    next_rect.center = (panel_rect.centerx + 96, panel_rect.bottom - 58)

                    if home_rect.collidepoint(mouse_x, mouse_y):
                        trigger_button_press("modal_home")
                        schedule_button_action(10, _do_return_home)
                    elif next_rect.collidepoint(mouse_x, mouse_y):
                        trigger_button_press("modal_next")
                        next_level = info["level"] + 1
                        schedule_button_action(10,
                                               lambda nl=next_level: _do_next_level(nl))

    # 延迟按钮动作
    if _pending_action is not None:
        _pending_action["timer"] -= 1
        if _pending_action["timer"] <= 0:
            act = _pending_action["action"]
            _pending_action = None
            act()

    # ---------------- 逻辑更新 ----------------
    if game_state == "start":
        update_start_scene()

    elif game_state == "game":
        current_elapsed = get_game_time()
        update_game_buttons(mouse_pos)

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
        update_button_state("pause_continue", pygame.Rect(350, 350, 200, 52), mouse_pos)
        update_button_state("pause_restart", pygame.Rect(350, 415, 200, 45), mouse_pos)
        update_star_explosion()
        update_explosions()

    elif game_state == "fail":
        update_button_state("fail_restart", pygame.Rect(230, 390, 200, 55), mouse_pos)
        update_button_state("fail_home", pygame.Rect(470, 390, 200, 55), mouse_pos)
        update_explosions()

    elif game_state == "level_complete":
        update_explosions()

        if level_complete_anim < 24:
            level_complete_anim += 1

        info = level_complete_info
        panel_rect = pygame.Rect(0, 0, 520, 500)
        panel_rect.center = (WIDTH // 2, HEIGHT // 2)

        if info["is_final"]:
            final_explosion_timer += 1
            home_rect = pygame.Rect(0, 0, 200, 52)
            home_rect.center = (panel_rect.centerx, panel_rect.bottom - 58)
            update_button_state("modal_home", home_rect, mouse_pos)
        else:
            home_rect = pygame.Rect(0, 0, 170, 52)
            next_rect = pygame.Rect(0, 0, 170, 52)
            home_rect.center = (panel_rect.centerx - 96, panel_rect.bottom - 58)
            next_rect.center = (panel_rect.centerx + 96, panel_rect.bottom - 58)
            update_button_state("modal_home", home_rect, mouse_pos)
            update_button_state("modal_next", next_rect, mouse_pos)

    # ---------------- 绘制 ----------------
    if game_state == "start":
        draw_start_screen()
    elif game_state == "game":
        draw_game_screen()
    elif game_state == "pause":
        draw_pause_screen()
    elif game_state == "fail":
        draw_fail_screen()
    elif game_state == "level_complete":
        draw_level_complete_screen()

    pygame.display.flip()
    clock.tick(60)


pygame.quit()
sys.exit()