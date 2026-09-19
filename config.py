"""共享太空插画：手绘颗粒、白色火箭和可换色的倾斜环形星球。"""
import math
import random
from functools import lru_cache
import pygame

ART_INK = (32, 39, 77)

def art_shade(c, k):
    return tuple(min(255, max(0, int(v*k))) for v in c)

@lru_cache(maxsize=80)
def art_rocket_sprite(size, accent=(235, 103, 72), cover=False, flame_frame=0):
    s = pygame.Surface((160, 240), pygame.SRCALPHA)
    def poly(points,c):
        pygame.draw.polygon(s,c,points)
        pygame.draw.lines(s,ART_INK,True,points,3)
    if flame_frame>=0:
        length = 30+flame_frame*4
        poly([(62,187),(98,187),(99,211),(89,204),(81,211+length//2),(72,211),(61,221)],(247,166,49))
        pygame.draw.polygon(s,(255,235,119),[(71,191),(88,191),(87,210),(80,221+length//3),(74,207)])
    fin = (250,170,65) if cover else accent
    poly([(49,117),(23,143),(19,190),(51,168)],fin)
    poly([(111,117),(137,143),(141,190),(109,168)],fin)
    poly([(56,168),(104,168),(98,185),(62,185)],(113,134,163))
    body=[(80,15),(63,34),(51,60),(44,94),(44,134),(51,164),(109,164),(116,134),(116,94),(109,60),(97,34)]
    poly(body,(247,248,232))
    pygame.draw.polygon(s,(219,227,225),[(109,61),(116,94),(116,134),(109,164),(98,164),(105,126),(105,87)])
    poly([(80,15),(63,34),(55,48),(105,48),(97,34)],accent)
    pygame.draw.circle(s,ART_INK,(80,88),19)
    pygame.draw.circle(s,(112,156,192),(80,88),15)
    pygame.draw.circle(s,(130,213,229),(80,88),12)
    pygame.draw.circle(s,(242,252,237),(75,83),4)
    poly([(77,143),(84,143),(87,190),(74,190)],fin)
    if cover:
        rng=random.Random(8)
        for _ in range(1800):
            x,y=rng.randrange(160),rng.randrange(240)
            c=s.get_at((x,y))
            if c.a and tuple(c[:3])!=ART_INK:
                pygame.draw.line(s,(*art_shade(c[:3],rng.uniform(.89,1.04)),255),(x,y),(x+1,y-2))
    return pygame.transform.scale(s,(int(size*2/3),size))

def art_rocket(target,x,y,size,direction='up',accent=(235,103,72),cover=False,flame=True,alpha=255):
    frame=(pygame.time.get_ticks()//140)%3 if flame else -1
    sprite=art_rocket_sprite(int(size),tuple(accent),cover,frame)
    angle={'up':0,'right':-90,'down':180,'left':90}[direction]
    if angle: sprite=pygame.transform.rotate(sprite,angle)
    if alpha<255:
        sprite=sprite.copy();sprite.set_alpha(alpha)
    target.blit(sprite,sprite.get_rect(center=(int(x),int(y))))

@lru_cache(maxsize=64)
def art_planet_sprite(radius,color):
    # 先画球体和椭圆环，再整体倾斜；确定性颗粒不会逐帧闪烁。
    s=pygame.Surface((220,150),pygame.SRCALPHA)
    pygame.draw.ellipse(s,art_shade(color,.65),(12,34,196,85),3)
    pygame.draw.ellipse(s,art_shade(color,1.15),(18,39,184,75),2)
    pygame.draw.ellipse(s,(244,217,113),(35,49,150,52),5)
    pygame.draw.circle(s,art_shade(color,.77),(110,72),46)
    pygame.draw.circle(s,color,(106,67),42)
    pygame.draw.circle(s,art_shade(color,1.2),(97,60),31)
    pygame.draw.circle(s,art_shade(color,1.43),(90,55),15)
    pygame.draw.arc(s,(250,224,133),(35,49,150,52),math.pi,2*math.pi,5)
    rng=random.Random(12)
    for _ in range(2600):
        x,y=rng.randrange(220),rng.randrange(150)
        c=s.get_at((x,y))
        if c.a:
            s.set_at((x,y),(*art_shade(c[:3],rng.uniform(.78,1.16)),255))
    for _ in range(650):
        a=rng.random()*math.tau; r=rng.uniform(.91,1.12)
        x=int(110+96*r*math.cos(a));y=int(77+42*r*math.sin(a))
        if 0<=x<220 and 0<=y<150 and s.get_at((x,y)).a==0:
            s.set_at((x,y),(*art_shade(color,1.4),rng.randrange(70,170)))
    s=pygame.transform.rotate(s,18)
    f=radius/46
    return pygame.transform.scale(s,(max(1,int(s.get_width()*f)),max(1,int(s.get_height()*f))))

def art_planet(target,x,y,radius,color=(164,131,193)):
    s=art_planet_sprite(int(radius),tuple(color))
    target.blit(s,s.get_rect(center=(int(x),int(y))))

@lru_cache(maxsize=50)
def art_star_sprite(radius):
    """参考图五角星：暖金边、奶黄填充和白色十字亮斑。"""
    s=pygame.Surface((100,100),pygame.SRCALPHA)
    points=[]
    for i in range(10):
        a=-math.pi/2+i*math.pi/5
        r=43 if i%2==0 else 23
        points.append((round(50+math.cos(a)*r),round(49+math.sin(a)*r)))
    pygame.draw.polygon(s,(196,151,80),[(x,y+3) for x,y in points])
    pygame.draw.polygon(s,(250,232,123),points)
    pygame.draw.lines(s,(255,244,163),True,points,2)
    rng=random.Random(17)
    for _ in range(200):
        x,y=rng.randrange(100),rng.randrange(100)
        if s.get_at((x,y)).a:
            s.set_at((x,y),(244,219,116,255))
    pygame.draw.rect(s,(255,255,226),(48,32,6,19))
    pygame.draw.rect(s,(255,255,226),(42,39,18,6))
    pygame.draw.rect(s,(255,255,226),(30,54,6,6))
    pygame.draw.rect(s,(255,255,226),(61,59,5,7))
    size=max(5,int(radius*2.35))
    return pygame.transform.scale(s,(size,size))

def art_star(target,x,y,radius,alpha=255):
    sprite=art_star_sprite(max(2,int(radius)))
    if alpha<255:
        sprite=sprite.copy();sprite.set_alpha(max(0,int(alpha)))
    target.blit(sprite,sprite.get_rect(center=(round(x),round(y))))


# config.py
import pygame
import sys
import math
import random
import os

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

clock = pygame.time.Clock()

# ---------------------------------------------------------------------------
# 颜色
# ---------------------------------------------------------------------------
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
# 棋盘和面板布局
# ---------------------------------------------------------------------------
BOARD_X = 40
BOARD_Y = 120
BOARD_SIZE = 530

GRID_SIZE = 7
CELL_SIZE = BOARD_SIZE // GRID_SIZE

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
    bundled = os.path.join(os.path.dirname(__file__), "assets", "Chinese.ttf")
    if os.path.exists(bundled):
        font = pygame.font.Font(bundled, size)
        font.set_bold(bold)
        return font
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
font_button_tiny = get_font(13, bold=True)


# ---------------------------------------------------------------------------
# 文本工具
# ---------------------------------------------------------------------------
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
        if char == "\n":
            lines.append(current)
            current = ""
            continue
        test = current + char
        if font.size(test)[0] > max_width and current:
            lines.append(current)
            current = char
        else:
            current = test
    if current:
        lines.append(current)
    return lines


def format_time(seconds):
    seconds = max(0.0, float(seconds))
    minutes = int(seconds // 60)
    remain = seconds - minutes * 60
    return f"{minutes:02d}:{remain:05.2f}"


# ---------------------------------------------------------------------------
# 按钮动画系统（通用）
# ---------------------------------------------------------------------------
button_states = {}


def _button_state(key):
    if key not in button_states:
        button_states[key] = {"scale": 1.0, "glow": 0.0, "press": 0}
    return button_states[key]


def trigger_button_press(key):
    """只负责视觉回弹，音效由调用方处理。"""
    _button_state(key)["press"] = 12


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


# ---------------------------------------------------------------------------
# 标题艺术字（供 game_screen 使用）
# ---------------------------------------------------------------------------
_art_title_cache = {}


def _build_art_title(scale):
    chars = "一箭又一箭"
    sizes = [40, 54, 34, 40, 54]
    y_offsets = [6, -6, 10, 6, -6]
    colors = [
        (55, 105, 190), (90, 175, 255), (255, 210, 70),
        (240, 248, 255), (90, 175, 255),
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
    """太空装饰图标：star / planet / rocket / comet。"""
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
                               (int(size * 0.5 + i * size * 0.5), size), max(1, rr))
        target.blit(tail, (x - size * 0.5, y - size))
        pygame.draw.circle(target, (235, 248, 255, alpha), (int(x), int(y)), int(r * 1.1))
        pygame.draw.circle(target, (255, 255, 255, alpha), (int(x), int(y)), max(1, int(r * 0.5)))


def draw_art_title_with_decor(target, cx, cy, scale=1.0):
    surface = get_art_title(scale)
    rect = surface.get_rect(center=(cx, cy))
    target.blit(surface, rect)

    t = pygame.time.get_ticks() / 1000.0
    draw_space_decor(target, rect.left - 22, rect.top + 18, "rocket", size=11, alpha=255)
    draw_space_decor(target, rect.left - 6, rect.bottom - 10, "star", size=8, alpha=220)
    draw_space_decor(target, rect.right + 24, rect.top + 16, "planet", size=10, alpha=255)
    draw_space_decor(target, rect.right + 8, rect.bottom - 8, "comet", size=13, alpha=230)

    pulse = (math.sin(t * 2.0) + 1) / 2
    draw_space_decor(target, rect.centerx - 70, rect.top - 8, "star",
                     size=6, alpha=int(160 + 80 * pulse))
    pulse2 = (math.sin(t * 2.0 + 1.6) + 1) / 2
    draw_space_decor(target, rect.centerx + 76, rect.top - 6, "star",
                     size=7, alpha=int(160 + 80 * pulse2))


# ---------------------------------------------------------------------------
# 背景星星 / 流星数据（供 home_screen 和 game_screen 共享）
# ---------------------------------------------------------------------------
random.seed(42)

background_stars = []
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

# ---------------------------------------------------------------------------
# 像素风主题覆盖（绘制到低分辨率逻辑画布，再用 nearest 放大）
# ---------------------------------------------------------------------------
PIXEL = 4
INK = (16, 20, 38)
PIXEL_BLUE = (54, 104, 170)
PIXEL_BLUE_HOVER = (74, 137, 205)
PIXEL_GOLD = (232, 166, 55)


def pixel_rect(target, rect, fill, border=INK, width=3, shadow=True):
    rect = pygame.Rect(rect)
    rect.x = (rect.x // PIXEL) * PIXEL
    rect.y = (rect.y // PIXEL) * PIXEL
    rect.w = max(PIXEL, (rect.w // PIXEL) * PIXEL)
    rect.h = max(PIXEL, (rect.h // PIXEL) * PIXEL)
    if shadow:
        pygame.draw.rect(target, (7, 10, 23), rect.move(PIXEL, PIXEL))
    pygame.draw.rect(target, fill, rect)
    pygame.draw.rect(target, border, rect, width)
    pygame.draw.line(target, tuple(min(255, c + 48) for c in fill),
                     (rect.left + width, rect.top + width),
                     (rect.right - width - 1, rect.top + width), 2)


def draw_animated_button(key, base_rect, text, color=None, hover=None,
                         target=None, font=None, disabled=False):
    if target is None:
        target = screen
    if font is None:
        font = font_button
    state = _button_state(key)
    pressed = state["press"] > 0
    is_hover = state["glow"] > 0.35 and not disabled
    fill = color or PIXEL_BLUE
    if is_hover:
        fill = hover or PIXEL_BLUE_HOVER
    if disabled:
        fill = (61, 68, 84)
    rect = pygame.Rect(base_rect).move(0, PIXEL if pressed else 0)
    pixel_rect(target, rect, fill, border=(13, 18, 35), width=3, shadow=not pressed)
    # 像素角切口
    for px, py in ((rect.left, rect.top), (rect.right-PIXEL, rect.top),
                   (rect.left, rect.bottom-PIXEL), (rect.right-PIXEL, rect.bottom-PIXEL)):
        pygame.draw.rect(target, INK, (px, py, PIXEL, PIXEL))
    text_color = (145, 150, 165) if disabled else (248, 246, 226)
    blit_text(text, font, text_color, shadow_alpha=0, target=target, center=rect.center)


def _build_art_title(scale):
    w, h = int(560 * scale), int(92 * scale)
    surf = pygame.Surface((w, h), pygame.SRCALPHA)
    title_font = get_font(max(18, int(48 * scale)), bold=True)
    title = title_font.render("一箭又一箭", False, (248, 224, 108))
    shadow = title_font.render("一箭又一箭", False, (58, 46, 92))
    r = title.get_rect(center=(w // 2, h // 2 - 2))
    surf.blit(shadow, r.move(max(2, int(4*scale)), max(2, int(5*scale))))
    surf.blit(title, r)
    pygame.draw.rect(surf, (106, 183, 220),
                     (int(52*scale), h-int(13*scale), w-int(104*scale), max(2, int(4*scale))))
    return surf


# 黄色粗字、藏蓝描边、浅蓝外框，与封面及关卡共享。
def _build_art_title(scale):
    font = get_font(max(20, round(70*scale)), bold=True)
    text = font.render("一箭又一箭", True, (255,237,114))
    pad=max(10,round(16*scale))
    result=pygame.Surface((text.get_width()+2*pad,text.get_height()+2*pad+8),pygame.SRCALPHA)
    mask=pygame.mask.from_surface(text)
    def outline(color,radius,dy=0):
        ink=mask.to_surface(setcolor=color,unsetcolor=(0,0,0,0))
        for x in range(-radius,radius+1):
            for y in range(-radius,radius+1):
                if x*x+y*y<=radius*radius:
                    result.blit(ink,(pad+x,pad+y+dy))
    outline((22,27,55),max(5,round(12*scale)),5)
    outline((140,213,228),max(4,round(9*scale)),1)
    outline((32,39,76),max(2,round(5*scale)))
    result.blit(text,(pad,pad))
    return result


def draw_art_title_with_decor(target,cx,cy,scale=1.0):
    title=get_art_title(scale)
    target.blit(title,title.get_rect(center=(cx,cy)))

_original_space_decor=draw_space_decor

def draw_space_decor(target,x,y,kind,size=14,alpha=255,t=0.0):
    if kind=='planet':
        art_planet(target,x,y,size,(166,132,190))
    elif kind=='rocket':
        art_rocket(target,x,y,size*3,cover=True)
    else:
        _original_space_decor(target,x,y,kind,size,alpha,t)


def draw_small_star(target,x,y,r,alpha=255,color=(255,235,130)):
    art_star(target,x,y,r,alpha)
