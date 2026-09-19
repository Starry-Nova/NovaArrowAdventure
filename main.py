import pygame
import sys
import math

pygame.init()

WIDTH = 900
HEIGHT = 700

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("一箭又一箭")

clock = pygame.time.Clock()

BG = (245, 241, 232)
BOARD_BG = (255, 252, 245)
GRID_COLOR = (220, 214, 202)
TEXT_COLOR = (70, 64, 58)
SUB_TEXT = (120, 112, 102)

ARROW_COLOR = (70, 120, 170)
RED = (225, 80, 75)

WHITE = (255, 255, 255)
BUTTON_COLOR = (90, 150, 190)
BUTTON_HOVER = (110, 170, 205)

STAR_COLOR = (255, 215, 70)
STAR_LIGHT = (255, 240, 150)

BOARD_X = 200
BOARD_Y = 130
BOARD_SIZE = 500

GRID_SIZE = 5
CELL_SIZE = BOARD_SIZE // GRID_SIZE

font_path_1 = "C:/Windows/Fonts/msyh.ttc"
font_path_2 = "C:/Windows/Fonts/simhei.ttf"

try:
    font_title = pygame.font.Font(font_path_1, 42)
    font_big = pygame.font.Font(font_path_1, 30)
    font_normal = pygame.font.Font(font_path_1, 22)
    font_small = pygame.font.Font(font_path_1, 18)
    font_button = pygame.font.Font(font_path_1, 20)
except:
    try:
        font_title = pygame.font.Font(font_path_2, 42)
        font_big = pygame.font.Font(font_path_2, 30)
        font_normal = pygame.font.Font(font_path_2, 22)
        font_small = pygame.font.Font(font_path_2, 18)
        font_button = pygame.font.Font(font_path_2, 20)
    except:
        font_title = pygame.font.Font(None, 42)
        font_big = pygame.font.Font(None, 30)
        font_normal = pygame.font.Font(None, 22)
        font_small = pygame.font.Font(None, 18)
        font_button = pygame.font.Font(None, 20)


levels = [
    [
        (0, 0, "right"),
        (0, 2, "down"),
        (1, 2, "down"),
        (2, 4, "left"),
        (4, 1, "up")
    ],
    [
        (0, 1, "down"),
        (1, 1, "down"),
        (2, 3, "left"),
        (2, 4, "left"),
        (4, 0, "right"),
        (4, 3, "up")
    ],
    [
        (0, 0, "down"),
        (1, 0, "down"),
        (2, 0, "right"),
        (2, 2, "right"),
        (2, 4, "up"),
        (3, 4, "up"),
        (4, 2, "left"),
        (4, 3, "left")
    ]
]


current_level = 0
arrows = []
mistakes = 3

collision_cell = None
animation = None

star_explosion = None

game_state = "start"


def load_level(level_index):
    global arrows
    global mistakes
    global collision_cell
    global animation
    global star_explosion

    arrows = [list(item) for item in levels[level_index]]

    mistakes = 3

    collision_cell = None

    animation = None

    star_explosion = None


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
    row, col, direction = arrow

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


def draw_arrow(
        surface,
        x,
        y,
        direction,
        color=ARROW_COLOR,
        scale=1.0):

    shaft = int(30 * scale)
    head = int(18 * scale)
    width = max(2, int(7 * scale))

    if direction == "up":

        pygame.draw.line(
            surface,
            color,
            (x, y + shaft // 2),
            (x, y - shaft // 2),
            width
        )

        pygame.draw.polygon(
            surface,
            color,
            [
                (x, y - shaft // 2 - head),
                (x - head, y - shaft // 2),
                (x + head, y - shaft // 2)
            ]
        )

    elif direction == "down":

        pygame.draw.line(
            surface,
            color,
            (x, y - shaft // 2),
            (x, y + shaft // 2),
            width
        )

        pygame.draw.polygon(
            surface,
            color,
            [
                (x, y + shaft // 2 + head),
                (x - head, y + shaft // 2),
                (x + head, y + shaft // 2)
            ]
        )

    elif direction == "left":

        pygame.draw.line(
            surface,
            color,
            (x + shaft // 2, y),
            (x - shaft // 2, y),
            width
        )

        pygame.draw.polygon(
            surface,
            color,
            [
                (x - shaft // 2 - head, y),
                (x - shaft // 2, y - head),
                (x - shaft // 2, y + head)
            ]
        )

    elif direction == "right":

        pygame.draw.line(
            surface,
            color,
            (x - shaft // 2, y),
            (x + shaft // 2, y),
            width
        )

        pygame.draw.polygon(
            surface,
            color,
            [
                (x + shaft // 2 + head, y),
                (x + shaft // 2, y - head),
                (x + shaft // 2, y + head)
            ]
        )


def draw_board():

    board_rect = pygame.Rect(
        BOARD_X,
        BOARD_Y,
        BOARD_SIZE,
        BOARD_SIZE
    )

    pygame.draw.rect(
        screen,
        BOARD_BG,
        board_rect,
        border_radius=18
    )

    pygame.draw.rect(
        screen,
        (232, 226, 215),
        board_rect,
        width=3,
        border_radius=18
    )

    for i in range(1, GRID_SIZE):

        x = BOARD_X + i * CELL_SIZE
        y = BOARD_Y + i * CELL_SIZE

        pygame.draw.line(
            screen,
            GRID_COLOR,
            (x, BOARD_Y),
            (x, BOARD_Y + BOARD_SIZE),
            2
        )

        pygame.draw.line(
            screen,
            GRID_COLOR,
            (BOARD_X, y),
            (BOARD_X + BOARD_SIZE, y),
            2
        )


def draw_arrows():

    for row, col, direction in arrows:

        x, y = get_arrow_position(
            row,
            col
        )

        color = ARROW_COLOR

        if collision_cell is not None:

            if (
                row == collision_cell[0]
                and
                col == collision_cell[1]
            ):
                color = RED

        draw_arrow(
            screen,
            x,
            y,
            direction,
            color
        )


def draw_animation_arrow():

    if animation is None:
        return

    x = animation["x"]
    y = animation["y"]

    direction = animation["direction"]

    color = animation["color"]

    draw_arrow(
        screen,
        int(x),
        int(y),
        direction,
        color
    )


def finish_fly_animation():

    global animation
    global current_level
    global game_state

    animation = None

    if len(arrows) == 0:

        if current_level < len(levels) - 1:

            current_level += 1

            load_level(
                current_level
            )

        else:

            game_state = "win"


def move_fly_animation():

    global animation

    if animation is None:
        return

    dx = (
        animation["target_x"]
        -
        animation["x"]
    )

    dy = (
        animation["target_y"]
        -
        animation["y"]
    )

    distance = math.sqrt(
        dx * dx + dy * dy
    )

    if distance <= animation["speed"]:

        animation["x"] = animation["target_x"]
        animation["y"] = animation["target_y"]

        finish_fly_animation()

        return

    animation["x"] += (
        dx / distance
        *
        animation["speed"]
    )

    animation["y"] += (
        dy / distance
        *
        animation["speed"]
    )


def start_star_explosion(star_index):

    global star_explosion

    star_x = 730 + star_index * 38
    star_y = 55

    star_explosion = {
        "x": star_x,
        "y": star_y,
        "timer": 0,
        "duration": 28
    }


def update_star_explosion():

    global star_explosion

    if star_explosion is None:
        return

    star_explosion["timer"] += 1

    if (
        star_explosion["timer"]
        >=
        star_explosion["duration"]
    ):
        star_explosion = None


def draw_star_explosion():

    if star_explosion is None:
        return

    x = star_explosion["x"]
    y = star_explosion["y"]

    timer = star_explosion["timer"]
    duration = star_explosion["duration"]

    progress = timer / duration

    alpha = int(
        255
        *
        (1 - progress)
    )

    radius = int(
        5
        +
        progress * 22
    )

    explosion_surface = pygame.Surface(
        (100, 100),
        pygame.SRCALPHA
    )

    center = (50, 50)

    for i in range(10):

        angle = (
            i
            *
            math.pi
            *
            2
            /
            10
        )

        length = (
            10
            +
            progress * 25
        )

        start_x = (
            50
            +
            math.cos(angle)
            *
            5
        )

        start_y = (
            50
            +
            math.sin(angle)
            *
            5
        )

        end_x = (
            50
            +
            math.cos(angle)
            *
            length
        )

        end_y = (
            50
            +
            math.sin(angle)
            *
            length
        )

        pygame.draw.line(
            explosion_surface,
            (
                255,
                210,
                60,
                alpha
            ),
            (
                int(start_x),
                int(start_y)
            ),
            (
                int(end_x),
                int(end_y)
            ),
            3
        )

    pygame.draw.circle(
        explosion_surface,
        (
            255,
            225,
            80,
            alpha
        ),
        center,
        radius
    )

    pygame.draw.circle(
        explosion_surface,
        (
            255,
            245,
            170,
            alpha
        ),
        center,
        max(2, radius // 2)
    )

    screen.blit(
        explosion_surface,
        (
            x - 50,
            y - 50
        )
    )


def update_collision_animation():

    global animation
    global mistakes
    global collision_cell
    global game_state

    if animation is None:
        return

    if animation["type"] != "collision":
        return

    phase = animation.get(
        "phase",
        "move"
    )

    if phase == "move":

        dx = (
            animation["target_x"]
            -
            animation["x"]
        )

        dy = (
            animation["target_y"]
            -
            animation["y"]
        )

        distance = math.sqrt(
            dx * dx
            +
            dy * dy
        )

        if distance <= animation["speed"]:

            animation["x"] = animation["target_x"]
            animation["y"] = animation["target_y"]

            animation["phase"] = "red"

            animation["timer"] = 0

        else:

            animation["x"] += (
                dx / distance
                *
                animation["speed"]
            )

            animation["y"] += (
                dy / distance
                *
                animation["speed"]
            )

    elif phase == "red":

        animation["timer"] += 1

        if animation["timer"] >= 24:

            animation["phase"] = "return"

    elif phase == "return":

        dx = (
            animation["start_x"]
            -
            animation["x"]
        )

        dy = (
            animation["start_y"]
            -
            animation["y"]
        )

        distance = math.sqrt(
            dx * dx
            +
            dy * dy
        )

        if distance <= animation["speed"]:

            animation["x"] = animation["start_x"]
            animation["y"] = animation["start_y"]

            arrows.append(
                animation["arrow"]
            )

            animation = None

            collision_cell = None

            mistakes -= 1

            lost_star_index = mistakes

            start_star_explosion(
                lost_star_index
            )

            if mistakes <= 0:

                game_state = "fail"

        else:

            animation["x"] += (
                dx / distance
                *
                animation["speed"]
            )

            animation["y"] += (
                dy / distance
                *
                animation["speed"]
            )


def draw_button(rect, text):

    mouse_pos = pygame.mouse.get_pos()

    if rect.collidepoint(mouse_pos):

        color = BUTTON_HOVER

    else:

        color = BUTTON_COLOR

    pygame.draw.rect(
        screen,
        color,
        rect,
        border_radius=12
    )

    text_surface = font_button.render(
        text,
        True,
        WHITE
    )

    text_rect = text_surface.get_rect(
        center=rect.center
    )

    screen.blit(
        text_surface,
        text_rect
    )


def draw_star(
        surface,
        center_x,
        center_y,
        radius,
        alpha,
        scale):

    size = int(
        radius * scale
    )

    glow_surface = pygame.Surface(
        (size * 5, size * 5),
        pygame.SRCALPHA
    )

    glow_center = (
        glow_surface.get_width() // 2,
        glow_surface.get_height() // 2
    )

    glow_alpha = int(
        alpha * 0.30
    )

    for extra in range(
            size * 2,
            0,
            -2):

        current_alpha = int(
            glow_alpha
            *
            (
                1
                -
                extra
                /
                (size * 2)
            )
        )

        if current_alpha > 0:

            pygame.draw.circle(
                glow_surface,
                (
                    255,
                    215,
                    70,
                    current_alpha
                ),
                glow_center,
                size + extra
            )

    surface.blit(
        glow_surface,
        (
            center_x
            -
            glow_surface.get_width() // 2,

            center_y
            -
            glow_surface.get_height() // 2
        )
    )

    star_points = []

    for i in range(10):

        angle = (
            -math.pi / 2
            +
            i
            *
            math.pi
            /
            5
        )

        if i % 2 == 0:

            r = size

        else:

            r = size * 0.43

        px = (
            center_x
            +
            math.cos(angle)
            *
            r
        )

        py = (
            center_y
            +
            math.sin(angle)
            *
            r
        )

        star_points.append(
            (
                int(px),
                int(py)
            )
        )

    star_surface = pygame.Surface(
        (size * 3, size * 3),
        pygame.SRCALPHA
    )

    shifted_points = []

    offset_x = size * 1.5
    offset_y = size * 1.5

    for px, py in star_points:

        shifted_points.append(
            (
                int(
                    px
                    -
                    center_x
                    +
                    offset_x
                ),
                int(
                    py
                    -
                    center_y
                    +
                    offset_y
                )
            )
        )

    pygame.draw.polygon(
        star_surface,
        (
            255,
            215,
            70,
            int(alpha)
        ),
        shifted_points
    )

    pygame.draw.polygon(
        star_surface,
        (
            255,
            240,
            150,
            int(alpha)
        ),
        shifted_points,
        width=max(
            1,
            int(size * 0.08)
        )
    )

    surface.blit(
        star_surface,
        (
            int(
                center_x
                -
                star_surface.get_width()
                /
                2
            ),
            int(
                center_y
                -
                star_surface.get_height()
                /
                2
            )
        )
    )


def draw_mistakes():

    current_time = pygame.time.get_ticks()

    cycle = 800

    progress = (
        current_time
        %
        cycle
    ) / cycle

    wave = (
        math.sin(
            progress
            *
            math.pi
            *
            2
        )
        +
        1
    ) / 2

    alpha = (
        178
        +
        int(77 * wave)
    )

    scale = (
        1.0
        +
        0.1 * wave
    )

    star_y = 55

    for i in range(mistakes):

        x = 730 + i * 38

        draw_star(
            screen,
            x,
            star_y,
            12,
            alpha,
            scale
        )

    draw_star_explosion()


def draw_top_bar():

    level_text = font_normal.render(
        f"第{current_level + 1}/{len(levels)}关",
        True,
        TEXT_COLOR
    )

    arrow_text = font_normal.render(
        f"箭头 {len(arrows)}",
        True,
        TEXT_COLOR
    )

    level_rect = level_text.get_rect()

    arrow_rect = arrow_text.get_rect()

    level_rect.midright = (
        575,
        55
    )

    arrow_rect.midleft = (
        610,
        55
    )

    screen.blit(
        level_text,
        level_rect
    )

    screen.blit(
        arrow_text,
        arrow_rect
    )

    draw_mistakes()


def draw_game_screen():

    screen.fill(BG)

    title = font_title.render(
        "一箭又一箭",
        True,
        TEXT_COLOR
    )

    title_rect = title.get_rect(
        center=(350, 55)
    )

    screen.blit(
        title,
        title_rect
    )

    draw_top_bar()

    draw_board()

    draw_arrows()

    draw_animation_arrow()

    hint = font_small.render(
        "点击箭头，让它沿方向飞出",
        True,
        SUB_TEXT
    )

    hint_rect = hint.get_rect(
        center=(450, 675)
    )

    screen.blit(
        hint,
        hint_rect
    )

    restart_rect = pygame.Rect(
        35,
        620,
        125,
        45
    )

    draw_button(
        restart_rect,
        "重新开始"
    )

    warning = font_small.render(
        f"剩余失误：{mistakes}",
        True,
        SUB_TEXT
    )

    warning_rect = warning.get_rect(
        center=(760, 675)
    )

    screen.blit(
        warning,
        warning_rect
    )


def draw_start_screen():

    screen.fill(BG)

    title = font_title.render(
        "一箭又一箭",
        True,
        TEXT_COLOR
    )

    title_rect = title.get_rect(
        center=(450, 230)
    )

    screen.blit(
        title,
        title_rect
    )

    subtitle = font_normal.render(
        "沿着箭头方向，让箭头飞出棋盘",
        True,
        SUB_TEXT
    )

    subtitle_rect = subtitle.get_rect(
        center=(450, 300)
    )

    screen.blit(
        subtitle,
        subtitle_rect
    )

    start_rect = pygame.Rect(
        350,
        380,
        200,
        60
    )

    draw_button(
        start_rect,
        "开始游戏"
    )


def draw_fail_screen():

    screen.fill(BG)

    title = font_title.render(
        "挑战失败",
        True,
        RED
    )

    title_rect = title.get_rect(
        center=(450, 250)
    )

    screen.blit(
        title,
        title_rect
    )

    text = font_normal.render(
        "失误次数已经用完",
        True,
        SUB_TEXT
    )

    text_rect = text.get_rect(
        center=(450, 320)
    )

    screen.blit(
        text,
        text_rect
    )

    restart_rect = pygame.Rect(
        350,
        390,
        200,
        60
    )

    draw_button(
        restart_rect,
        "重新挑战"
    )


def draw_win_screen():

    screen.fill(BG)

    title = font_title.render(
        "恭喜通关！",
        True,
        BUTTON_COLOR
    )

    title_rect = title.get_rect(
        center=(450, 250)
    )

    screen.blit(
        title,
        title_rect
    )

    text = font_normal.render(
        "所有箭头都成功飞出了棋盘",
        True,
        SUB_TEXT
    )

    text_rect = text.get_rect(
        center=(450, 320)
    )

    screen.blit(
        text,
        text_rect
    )

    restart_rect = pygame.Rect(
        350,
        390,
        200,
        60
    )

    draw_button(
        restart_rect,
        "再玩一次"
    )


load_level(current_level)

running = True

while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:

            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:

            mouse_x, mouse_y = event.pos

            if game_state == "start":

                start_rect = pygame.Rect(
                    350,
                    380,
                    200,
                    60
                )

                if start_rect.collidepoint(
                        mouse_x,
                        mouse_y):

                    current_level = 0

                    load_level(
                        current_level
                    )

                    game_state = "game"

            elif game_state == "game":

                restart_rect = pygame.Rect(
                    35,
                    620,
                    125,
                    45
                )

                if restart_rect.collidepoint(
                        mouse_x,
                        mouse_y):

                    load_level(
                        current_level
                    )

                elif animation is None:

                    if (
                        BOARD_X
                        <= mouse_x
                        <
                        BOARD_X + BOARD_SIZE

                        and

                        BOARD_Y
                        <= mouse_y
                        <
                        BOARD_Y + BOARD_SIZE
                    ):

                        col = (
                            mouse_x
                            -
                            BOARD_X
                        ) // CELL_SIZE

                        row = (
                            mouse_y
                            -
                            BOARD_Y
                        ) // CELL_SIZE

                        clicked_arrow = find_arrow(
                            row,
                            col
                        )

                        if clicked_arrow:

                            blocker = get_blocking_arrow(
                                clicked_arrow
                            )

                            start_x, start_y = get_arrow_position(
                                row,
                                col
                            )

                            if blocker is None:

                                arrows.remove(
                                    clicked_arrow
                                )

                                direction = clicked_arrow[2]

                                if direction == "up":

                                    target_x = start_x

                                    target_y = (
                                        BOARD_Y
                                        -
                                        80
                                    )

                                elif direction == "down":

                                    target_x = start_x

                                    target_y = (
                                        BOARD_Y
                                        +
                                        BOARD_SIZE
                                        +
                                        80
                                    )

                                elif direction == "left":

                                    target_x = (
                                        BOARD_X
                                        -
                                        80
                                    )

                                    target_y = start_y

                                else:

                                    target_x = (
                                        BOARD_X
                                        +
                                        BOARD_SIZE
                                        +
                                        80
                                    )

                                    target_y = start_y

                                animation = {
                                    "type": "fly",

                                    "x": start_x,
                                    "y": start_y,

                                    "target_x": target_x,
                                    "target_y": target_y,

                                    "direction": direction,

                                    "color": ARROW_COLOR,

                                    "speed": 15
                                }

                            else:

                                blocker_x, blocker_y = get_arrow_position(
                                    blocker[0],
                                    blocker[1]
                                )

                                direction = clicked_arrow[2]

                                if direction == "up":

                                    target_x = start_x

                                    target_y = (
                                        blocker_y
                                        +
                                        38
                                    )

                                elif direction == "down":

                                    target_x = start_x

                                    target_y = (
                                        blocker_y
                                        -
                                        38
                                    )

                                elif direction == "left":

                                    target_x = (
                                        blocker_x
                                        +
                                        38
                                    )

                                    target_y = start_y

                                else:

                                    target_x = (
                                        blocker_x
                                        -
                                        38
                                    )

                                    target_y = start_y

                                arrows.remove(
                                    clicked_arrow
                                )

                                collision_cell = (
                                    clicked_arrow[0],
                                    clicked_arrow[1]
                                )

                                animation = {
                                    "type": "collision",

                                    "phase": "move",

                                    "timer": 0,

                                    "x": start_x,
                                    "y": start_y,

                                    "start_x": start_x,
                                    "start_y": start_y,

                                    "target_x": target_x,
                                    "target_y": target_y,

                                    "direction": direction,

                                    "color": ARROW_COLOR,

                                    "arrow": clicked_arrow,

                                    "speed": 10
                                }

            elif game_state == "fail":

                restart_rect = pygame.Rect(
                    350,
                    390,
                    200,
                    60
                )

                if restart_rect.collidepoint(
                        mouse_x,
                        mouse_y):

                    current_level = 0

                    load_level(
                        current_level
                    )

                    game_state = "game"

            elif game_state == "win":

                restart_rect = pygame.Rect(
                    350,
                    390,
                    200,
                    60
                )

                if restart_rect.collidepoint(
                        mouse_x,
                        mouse_y):

                    current_level = 0

                    load_level(
                        current_level
                    )

                    game_state = "game"


    if game_state == "game":

        if (
            animation is not None
            and
            animation["type"] == "collision"
        ):

            update_collision_animation()

        elif (
            animation is not None
            and
            animation["type"] == "fly"
        ):

            move_fly_animation()

        update_star_explosion()


    if game_state == "start":

        draw_start_screen()

    elif game_state == "game":

        draw_game_screen()

    elif game_state == "fail":

        draw_fail_screen()

    elif game_state == "win":

        draw_win_screen()


    pygame.display.flip()

    clock.tick(60)


pygame.quit()

sys.exit()