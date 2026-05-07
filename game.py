# ================================================================
#  MAZE GIRL  -  Updated with Fire Traps & Stone Collectibles!
# ================================================================
#
#  HOW TO INSTALL AND RUN:
#    Step 1:  pip install pygame
#    Step 2:  python cute_updated.py
#
#  NEW FEATURES:
#    🔥 FIRE TRAPS  → stepping on fire drains energy (-20) and score (-100)
#    🪨 STONES      → collecting stones gives bonus score (+150) and energy (+10)
#    ❤️ ENERGY BAR  → shown in the panel; game over if energy hits 0!
#
#  CONTROLS:
#    Arrow keys  or  W A S D  =  Move the girl
#    H key                    =  Show a hint
#    ESC key                  =  Go back to the menu
# ================================================================

import pygame
import random
import sys
import time
import math
import heapq

pygame.init()

info     = pygame.display.Info()
SCREEN_W = info.current_w  - 10
SCREEN_H = info.current_h  - 48
screen   = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.RESIZABLE)
pygame.display.set_caption("MAZE GAME - Fire & Stones Edition")

PANEL_W = 270
FPS     = 60

# ── Colours ─────────────────────────────────────────────────────
WHITE      = (255, 255, 255)
DARK_BG    = (240, 245, 255)
WALL_COL   = ( 70,  90, 140)
WALL_SHINE = (120, 150, 200)
FLOOR_A    = (255, 255, 255)
FLOOR_B    = (245, 248, 255)
GOLD       = (220, 160,   0)
GOLD_DIM   = (170, 120,   0)
GREEN      = ( 40, 180,  80)
RED        = (210,  55,  55)
PANEL_BG   = (225, 230, 245)
PURPLE     = ( 90,  80, 200)
PINK       = (230,  80, 140)
SKIN       = (255, 200, 160)
HAIR_COL   = ( 78,  40,  10)
DRESS_COL  = (215,  78, 158)
SHOE_COL   = ( 55,  38,  18)
HINT_COL   = (255, 200,   0)
ORANGE     = (255, 130,   0)
STONE_COL  = (140, 140, 160)
ENERGY_COL = ( 80, 210,  80)
ENERGY_LOW = (255,  80,  80)


# ================================================================
#  MAZE BUILDING
# ================================================================

class Cell:
    def __init__(self):
        self.walls   = [True, True, True, True]
        self.visited = False


class Maze:
    DIRECTIONS = [
        (-1,  0,  0,  1),
        ( 1,  0,  1,  0),
        ( 0,  1,  2,  3),
        ( 0, -1,  3,  2),
    ]

    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.grid = [[Cell() for _ in range(cols)] for _ in range(rows)]
        self._build_maze(0, 0)
        self.grid[0][0].walls[0] = False
        self.grid[rows - 1][cols - 1].walls[1] = False

    def _build_maze(self, start_r, start_c):
        stack = [(start_r, start_c)]
        self.grid[start_r][start_c].visited = True
        directions = list(range(4))

        while stack:
            r, c = stack[-1]
            random.shuffle(directions)
            found_neighbour = False

            for d in directions:
                dr, dc, my_wall, nb_wall = self.DIRECTIONS[d]
                nr = r + dr
                nc = c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    if not self.grid[nr][nc].visited:
                        self.grid[r][c].walls[my_wall]   = False
                        self.grid[nr][nc].walls[nb_wall] = False
                        self.grid[nr][nc].visited = True
                        stack.append((nr, nc))
                        found_neighbour = True
                        break

            if not found_neighbour:
                stack.pop()

    def open_path(self, r, c, wall_index):
        return not self.grid[r][c].walls[wall_index]

    def find_solution(self, start_r, start_c, end_r, end_c):
        """DFS – used for the hint overlay (H key).

        Explores the maze depth-first using an explicit stack.
        Finds *a* valid path to the exit (not necessarily the shortest).
        The hint trail may be longer/windier, keeping the game challenging.
        """
        visited = {(start_r, start_c): None}   # cell → came_from
        stack   = [(start_r, start_c)]

        while stack:
            r, c = stack.pop()

            if r == end_r and c == end_c:
                path = []
                node = (r, c)
                while node is not None:
                    path.append(node)
                    node = visited[node]
                path.reverse()
                return path

            for dr, dc, wall, _ in self.DIRECTIONS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    if self.open_path(r, c, wall) and (nr, nc) not in visited:
                        visited[(nr, nc)] = (r, c)
                        stack.append((nr, nc))

        return []

    def find_solution_astar(self, start_r, start_c, end_r, end_c,
                            fire_cells=None, stone_cells=None,
                            collected_stones=None):
        """A* pathfinding.

        Heuristic  : Manhattan distance to exit.
        Cost model :
          • Moving onto a fire cell  → +50 penalty  (prefer to avoid)
          • Moving onto an uncollected stone → -10 reward (prefer to collect)
          • Every step costs 1 base unit.
        Returns the full path as a list of (row, col) tuples, or [].
        """
        fire_cells       = fire_cells       or set()
        stone_cells      = stone_cells      or set()
        collected_stones = collected_stones or set()

        def h(r, c):
            return abs(r - end_r) + abs(c - end_c)

        def step_cost(nr, nc):
            cost = 1
            if (nr, nc) in fire_cells:
                cost += 50          # avoid fire
            if (nr, nc) in stone_cells and (nr, nc) not in collected_stones:
                cost -= 10          # prefer uncollected stones
            return max(1, cost)     # cost must stay positive

        # heap entry: (f_score, g_score, row, col)
        start = (h(start_r, start_c), 0, start_r, start_c)
        heap  = [start]
        came_from = {(start_r, start_c): None}
        g_score   = {(start_r, start_c): 0}

        while heap:
            f, g, r, c = heapq.heappop(heap)

            if r == end_r and c == end_c:
                path = []
                node = (r, c)
                while node is not None:
                    path.append(node)
                    node = came_from[node]
                path.reverse()
                return path

            if g > g_score.get((r, c), float('inf')):
                continue        # stale entry

            for dr, dc, wall, _ in self.DIRECTIONS:
                nr, nc = r + dr, c + dc
                if 0 <= nr < self.rows and 0 <= nc < self.cols:
                    if self.open_path(r, c, wall):
                        new_g = g + step_cost(nr, nc)
                        if new_g < g_score.get((nr, nc), float('inf')):
                            g_score[(nr, nc)] = new_g
                            came_from[(nr, nc)] = (r, c)
                            heapq.heappush(heap, (new_g + h(nr, nc), new_g, nr, nc))

        return []


# ================================================================
#  DRAW MAZE IMAGE
# ================================================================

def build_maze_image(maze, cell):
    img_w   = maze.cols * cell + 8
    img_h   = maze.rows * cell + 8
    surface = pygame.Surface((img_w, img_h), pygame.SRCALPHA)
    wall_t  = max(3, cell // 13)

    for r in range(maze.rows):
        for c in range(maze.cols):
            x     = c * cell
            y     = r * cell
            color = FLOOR_A if (r + c) % 2 == 0 else FLOOR_B
            pygame.draw.rect(surface, color, (x + 1, y + 1, cell - 2, cell - 2))

    for r in range(maze.rows):
        for c in range(maze.cols):
            x = c * cell
            y = r * cell
            w = maze.grid[r][c].walls

            if w[0]:
                pygame.draw.rect(surface, WALL_COL,   (x, y, cell, wall_t))
                pygame.draw.rect(surface, WALL_SHINE, (x, y, cell, 1))
            if w[1]:
                pygame.draw.rect(surface, WALL_COL, (x, y + cell - wall_t, cell, wall_t))
            if w[3]:
                pygame.draw.rect(surface, WALL_COL,   (x, y, wall_t, cell))
                pygame.draw.rect(surface, WALL_SHINE, (x, y, 1, cell))
            if w[2]:
                pygame.draw.rect(surface, WALL_COL, (x + cell - wall_t, y, wall_t, cell))

    return surface


# ================================================================
#  DRAW FIRE TRAP  🔥
#  Animated flickering flames drawn with circles + polygons
# ================================================================

def draw_fire(surface, cx, cy, size, tick):
    """Draw an animated fire at (cx, cy)."""
    s = max(8, size // 3)
    t = tick * 0.12

    # Base glow
    for radius in range(s + 4, 2, -3):
        alpha = int(60 * (1 - radius / (s + 4)))
        glow  = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (255, 80, 0, alpha), (radius, radius), radius)
        surface.blit(glow, (cx - radius, cy - radius + s // 2))

    # Flame tongues (3 flames side by side)
    offsets = [(-s // 2, 0), (0, -s // 4), (s // 2, 0)]
    colors  = [(255, 60, 0), (255, 140, 0), (255, 220, 50)]

    for i, (ox, _) in enumerate(offsets):
        wave = int(math.sin(t + i * 1.2) * (s // 3))
        h    = s + wave
        pts  = [
            (cx + ox,          cy + s // 2),           # base left
            (cx + ox + s // 2, cy + s // 2),           # base right
            (cx + ox + s // 4, cy - h // 2),           # tip
        ]
        if len(pts) >= 3:
            flame_surf = pygame.Surface((size, size + s), pygame.SRCALPHA)
            # Draw in local coords shifted
            local_pts = [(p[0] - (cx - size // 2), p[1] - (cy - size // 2)) for p in pts]
            if all(0 <= lp[0] <= size and 0 <= lp[1] <= size + s for lp in local_pts):
                pygame.draw.polygon(flame_surf, (*colors[i], 210), local_pts)
                surface.blit(flame_surf, (cx - size // 2, cy - size // 2))

    # Simple direct flame drawing (reliable fallback)
    for i, ox in enumerate([-s//3, 0, s//3]):
        wave = int(math.sin(t + i * 1.5) * 3)
        col  = colors[i]
        pygame.draw.ellipse(surface, col,
                            (cx + ox - s//4, cy - s//2 + wave, s//2, s + 4))

    # Inner bright core
    pygame.draw.ellipse(surface, (255, 240, 100),
                        (cx - s//4, cy - s//6, s//2, s//2))


# ================================================================
#  DRAW STONE COLLECTIBLE  🪨
#  A glowing gem-like rock
# ================================================================

def draw_stone(surface, cx, cy, size, tick):
    """Draw a sparkling stone gem at (cx, cy)."""
    s = max(8, size // 3)
    t = tick * 0.07

    # Outer glow
    pulse = int(math.sin(t) * 3)
    for radius in range(s + 6 + pulse, 2, -3):
        alpha = int(50 * (1 - radius / (s + 10)))
        glow  = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, (180, 180, 220, alpha), (radius, radius), radius)
        surface.blit(glow, (cx - radius, cy - radius))

    # Stone body (hexagon-ish polygon)
    r = s
    pts = [
        (cx,          cy - r),        # top
        (cx + r,      cy - r // 2),   # top-right
        (cx + r,      cy + r // 2),   # bottom-right
        (cx,          cy + r),        # bottom
        (cx - r,      cy + r // 2),   # bottom-left
        (cx - r,      cy - r // 2),   # top-left
    ]
    pygame.draw.polygon(surface, STONE_COL, pts)
    pygame.draw.polygon(surface, (200, 200, 220), pts, 2)

    # Highlight facet
    hi_pts = [pts[0], pts[1], (cx + r // 2, cy - r // 4), (cx, cy)]
    pygame.draw.polygon(surface, (210, 215, 240), hi_pts)

    # Sparkle star
    sparkle_alpha = int(180 + math.sin(t * 2) * 75)
    spark_r = max(3, s // 4)
    spark_surf = pygame.Surface((spark_r * 4, spark_r * 4), pygame.SRCALPHA)
    sx, sy = spark_r * 2, spark_r * 2
    for angle in range(0, 360, 90):
        rad = math.radians(angle)
        ex  = sx + int(math.cos(rad) * spark_r)
        ey  = sy + int(math.sin(rad) * spark_r)
        pygame.draw.line(spark_surf, (255, 255, 255, sparkle_alpha), (sx, sy), (ex, ey), 2)
    surface.blit(spark_surf, (cx - spark_r * 2, cy - r - spark_r * 2))


# ================================================================
#  DRAW THE GIRL CHARACTER
# ================================================================

def draw_girl(surface, cx, cy, size, tick):
    total  = size
    head_r = int(total * 0.28)
    head_cy = cy - int(total * 0.38)
    body_top    = head_cy + head_r - 2
    body_bottom = cy + int(total * 0.18)
    body_h      = body_bottom - body_top
    body_w      = int(head_r * 1.3)
    leg_h  = int(total * 0.20)
    leg_w  = max(5, int(head_r * 0.32))

    pygame.draw.ellipse(surface, (180, 185, 200),
                        (cx - head_r, cy + int(total*0.18), head_r*2, 6))
    pygame.draw.ellipse(surface, SHOE_COL,
                        (cx - body_w//2 - 2, body_bottom + leg_h - 5, leg_w + 4, 7))
    pygame.draw.ellipse(surface, SHOE_COL,
                        (cx + body_w//2 - leg_w - 2, body_bottom + leg_h - 5, leg_w + 4, 7))
    pygame.draw.rect(surface, SKIN,
                     (cx - body_w//2, body_bottom, leg_w, leg_h), border_radius=4)
    pygame.draw.rect(surface, SKIN,
                     (cx + body_w//2 - leg_w, body_bottom, leg_w, leg_h), border_radius=4)
    pygame.draw.polygon(surface, DRESS_COL, [
        (cx - body_w//2 - 5, body_bottom + 4),
        (cx + body_w//2 + 5, body_bottom + 4),
        (cx + body_w//2 - 2, body_top + 4),
        (cx - body_w//2 + 2, body_top + 4),
    ])
    pygame.draw.arc(surface, (240, 160, 210),
                    (cx - body_w//2 + 2, body_top + 2, body_w - 4, 10), 0, math.pi, 3)

    arm_len = int(head_r * 0.7)
    pygame.draw.line(surface, SKIN,
                     (cx - body_w//2 + 2, body_top + 6),
                     (cx - body_w//2 - arm_len, body_top + arm_len + 2), 5)
    pygame.draw.circle(surface, SKIN,
                       (cx - body_w//2 - arm_len, body_top + arm_len + 2), 4)
    pygame.draw.line(surface, SKIN,
                     (cx + body_w//2 - 2, body_top + 6),
                     (cx + body_w//2 + arm_len, body_top + arm_len + 2), 5)
    pygame.draw.circle(surface, SKIN,
                       (cx + body_w//2 + arm_len, body_top + arm_len + 2), 4)

    pygame.draw.circle(surface, SKIN, (cx, head_cy), head_r)
    pygame.draw.ellipse(surface, HAIR_COL,
                        (cx - head_r - 3, head_cy - head_r - 4,
                         (head_r + 3) * 2, int(head_r * 1.2)))
    pygame.draw.arc(surface, HAIR_COL,
                    (cx - head_r, head_cy - head_r//2, head_r*2, head_r),
                    0, math.pi, int(head_r * 0.35))
    pygame.draw.ellipse(surface, HAIR_COL,
                        (cx - head_r - 5, head_cy - 4, 10, int(head_r * 0.9)))
    pygame.draw.ellipse(surface, HAIR_COL,
                        (cx + head_r - 5, head_cy - 4, 10, int(head_r * 0.9)))
    pygame.draw.ellipse(surface, HAIR_COL,
                        (cx + head_r - 4, head_cy - head_r + 4,
                         int(head_r * 0.55), int(head_r * 0.9)))

    eye_y  = head_cy + head_r // 8
    eye_rx = max(4, head_r // 3)
    eye_ry = max(5, int(head_r * 0.42))
    eye_ox = max(5, head_r // 2 - 1)
    pygame.draw.ellipse(surface, (255,255,255),
                        (cx - eye_ox - eye_rx, eye_y - eye_ry, eye_rx*2, eye_ry*2))
    pygame.draw.ellipse(surface, (255,255,255),
                        (cx + eye_ox - eye_rx, eye_y - eye_ry, eye_rx*2, eye_ry*2))
    pygame.draw.ellipse(surface, (60,30,100),
                        (cx - eye_ox - eye_rx//2, eye_y - eye_ry//2 + 1,
                         eye_rx, int(eye_ry * 0.9)))
    pygame.draw.ellipse(surface, (60,30,100),
                        (cx + eye_ox - eye_rx//2, eye_y - eye_ry//2 + 1,
                         eye_rx, int(eye_ry * 0.9)))
    pygame.draw.circle(surface, (255,255,255),
                       (cx - eye_ox - 1, eye_y - eye_ry//3), max(2, eye_rx//3))
    pygame.draw.circle(surface, (255,255,255),
                       (cx + eye_ox - 1, eye_y - eye_ry//3), max(2, eye_rx//3))

    cheek_y = eye_y + eye_ry + 2
    cheek_x = max(8, head_r // 2)
    cheek_surf = pygame.Surface((14, 8), pygame.SRCALPHA)
    pygame.draw.ellipse(cheek_surf, (255,160,160,130), (0,0,14,8))
    surface.blit(cheek_surf, (cx - cheek_x - 7, cheek_y))
    surface.blit(cheek_surf, (cx + cheek_x - 7, cheek_y))
    pygame.draw.arc(surface, (200,80,120),
                    (cx - 6, cheek_y + 4, 12, 7), math.pi, 2*math.pi, 2)

    bow_cx = cx + head_r - 4
    bow_cy = head_cy - head_r + 4
    bow_sz = max(6, head_r // 2)
    pygame.draw.polygon(surface, PINK, [
        (bow_cx, bow_cy),
        (bow_cx - bow_sz, bow_cy - bow_sz + 2),
        (bow_cx - bow_sz, bow_cy + bow_sz - 2)])
    pygame.draw.polygon(surface, PINK, [
        (bow_cx, bow_cy),
        (bow_cx + bow_sz, bow_cy - bow_sz + 2),
        (bow_cx + bow_sz, bow_cy + bow_sz - 2)])
    pygame.draw.circle(surface, (255,180,210), (bow_cx, bow_cy), max(3, bow_sz//2))


# ================================================================
#  DRAW WAVING FLAG
# ================================================================

def draw_flag(surface, cx, cy, size, tick):
    pole_h = size
    pygame.draw.line(surface, (180, 160, 100), (cx, cy), (cx, cy - pole_h), 3)

    t      = tick * 0.05
    fw     = size - 4
    fh     = (size - 4)//2
    steps  = 8

    top_pts = []
    bot_pts = []
    for i in range(steps + 1):
        x    = cx + i * fw // steps
        wave = int(math.sin(t + i * 0.5) * 4)
        top_pts.append((x, cy - pole_h + i * fh // (steps * 2) + wave))
        bot_pts.append((x, cy - pole_h + fh - i * fh // (steps * 2) + wave))

    flag_shape = top_pts + list(reversed(bot_pts))
    if len(flag_shape) >= 3:
        pygame.draw.polygon(surface, GOLD,    flag_shape)
        pygame.draw.polygon(surface, GOLD_DIM, flag_shape, 1)

    star_x = cx + fw // 2
    star_y = cy - pole_h + fh // 2 + int(math.sin(t + 2) * 2)
    pygame.draw.circle(surface, WHITE, (star_x, star_y), 4)


# ================================================================
#  LEVEL SELECT SCREEN
# ================================================================

def level_select_screen():
    clock   = pygame.time.Clock()
    f_title = pygame.font.SysFont("comicsansms", 64, bold=True)
    f_card  = pygame.font.SysFont("comicsansms", 40, bold=True)
    f_desc  = pygame.font.SysFont("comicsansms", 26)
    f_hint  = pygame.font.SysFont("comicsansms", 22)
    f_ctrl  = pygame.font.SysFont("comicsansms", 20)

    levels   = [
        ("Easy",  8,  8,  GREEN),
        ("Hard", 14, 14,  RED),
    ]
    selected = 0
    tick     = 0

    while True:
        tick += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_UP, pygame.K_w):
                    selected = (selected - 1) % len(levels)
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    selected = (selected + 1) % len(levels)
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    name, rows, cols, _ = levels[selected]
                    return rows, cols, name

        screen.fill(DARK_BG)

        title = f_title.render("* MAZE GAME *", True, GOLD)
        screen.blit(title, title.get_rect(center=(SCREEN_W // 2, 70)))

        # Fire & stone legend
        legend = f_desc.render("🔥 Avoid fire  (-energy & score)          🪨 Collect stones  (+score & energy)", True, (100, 80, 160))
        screen.blit(legend, legend.get_rect(center=(SCREEN_W // 2, 135)))

        hint_txt = f_hint.render("Use  UP / DOWN  arrow keys  to choose   then press  ENTER", True, (80, 90, 160))
        screen.blit(hint_txt, hint_txt.get_rect(center=(SCREEN_W // 2, 172)))

        card_w  = 520
        card_h  = 110
        card_x  = SCREEN_W // 2 - card_w // 2
        start_y = 210

        for i, (name, rows, cols, color) in enumerate(levels):
            cy = start_y + i * (card_h + 20)

            if i == selected:
                glow = pygame.Surface((card_w + 24, card_h + 24), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*color, 55), (0, 0, card_w + 24, card_h + 24), border_radius=18)
                screen.blit(glow, (card_x - 12, cy - 12))
                pygame.draw.rect(screen, color, (card_x, cy, card_w, card_h), border_radius=14)
                text_col = (18, 10, 35)
            else:
                pygame.draw.rect(screen, (38, 28, 68), (card_x, cy, card_w, card_h), border_radius=14)
                text_col = WHITE

            screen.blit(f_card.render(name, True, text_col),
                        (card_x + 24, cy + card_h // 2 - 20))

            if i == selected:
                draw_girl(screen, card_x + card_w - 44, cy + card_h // 2, 60, tick)

        ctrl_lines = ["CONTROLS:  Arrow keys / WASD = Move    H = A* Hint (optimal)    SPACE = A* Autoplay    ESC = Menu"]
        for i, line in enumerate(ctrl_lines):
            cs = f_ctrl.render(line, True, (120, 100, 160))
            screen.blit(cs, cs.get_rect(center=(SCREEN_W // 2, SCREEN_H - 45 + i * 26)))

        pygame.display.flip()
        clock.tick(FPS)


# ================================================================
#  WIN SCREEN
# ================================================================

def win_screen(level_name, elapsed_time, score, stones_collected):
    clock   = pygame.time.Clock()
    f_big   = pygame.font.SysFont("comicsansms", 72, bold=True)
    f_med   = pygame.font.SysFont("comicsansms", 42, bold=True)
    f_small = pygame.font.SysFont("comicsansms", 28)
    f_hint  = pygame.font.SysFont("comicsansms", 24)
    tick    = 0

    # Format time nicely
    minutes = int(elapsed_time // 60)
    seconds = elapsed_time % 60
    if minutes > 0:
        time_str = f"{minutes}m {seconds:.1f}s"
    else:
        time_str = f"{seconds:.1f} seconds"

    while True:
        tick += 1

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  return "restart"
                if event.key == pygame.K_m:  return "menu"
                if event.key == pygame.K_q:
                    pygame.quit()
                    sys.exit()

        screen.fill(DARK_BG)

        t = f_big.render("You Won!", True, GOLD)
        screen.blit(t, t.get_rect(center=(SCREEN_W // 2, 80)))

        draw_girl(screen, SCREEN_W // 2, 240, 120, tick)

        stats = [
            (f"Level  :   {level_name}",                  WHITE),
            (f"Time   :   {time_str}",                    GOLD),
            (f"Stones :   {stones_collected} collected",  STONE_COL),
            (f"Score  :   {score}  points",               PURPLE),
        ]
        for i, (text, col) in enumerate(stats):
            s2 = f_med.render(text, True, col)
            screen.blit(s2, s2.get_rect(center=(SCREEN_W // 2, 360 + i * 56)))

        hints = "[R]  Play Again           [M]  Main Menu           [Q]  Quit"
        hs = f_hint.render(hints, True, (160, 140, 210))
        screen.blit(hs, hs.get_rect(center=(SCREEN_W // 2, SCREEN_H - 48)))

        pygame.display.flip()
        clock.tick(FPS)


# ================================================================
#  GAME OVER SCREEN  (energy ran out)
# ================================================================

def game_over_screen(elapsed_time):
    clock   = pygame.time.Clock()
    f_big   = pygame.font.SysFont("comicsansms", 68, bold=True)
    f_med   = pygame.font.SysFont("comicsansms", 36, bold=True)
    f_hint  = pygame.font.SysFont("comicsansms", 32)

    # Format time nicely
    minutes = int(elapsed_time // 60)
    seconds = elapsed_time % 60
    if minutes > 0:
        time_str = f"{minutes}m {seconds:.1f}s"
    else:
        time_str = f"{seconds:.1f}s"

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:  return "restart"
                if event.key == pygame.K_m:  return "menu"

        screen.fill((30, 10, 10))

        msg  = f_big.render("No Energy Left! 🔥", True, RED)
        time_msg = f_med.render(f"You survived for {time_str}", True, GOLD)
        hint = f_hint.render("[R]  Try Again          [M]  Menu", True, WHITE)
        
        screen.blit(msg,  msg.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 - 60)))
        screen.blit(time_msg, time_msg.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 20)))
        screen.blit(hint, hint.get_rect(center=(SCREEN_W // 2, SCREEN_H // 2 + 90)))

        pygame.display.flip()
        clock.tick(FPS)


# ================================================================
#  SPAWN FIRE AND STONE POSITIONS
#  Randomly placed on walkable cells, avoiding start & exit
# ================================================================

def spawn_hazards(maze, rows, cols, n_fires, n_stones):
    """Return sets of (row, col) for fire traps and stone gems."""
    forbidden = {(0, 0), (rows - 1, cols - 1)}   # never on start or exit
    all_cells = [(r, c) for r in range(rows) for c in range(cols)
                 if (r, c) not in forbidden]
    random.shuffle(all_cells)

    fires  = set()
    stones = set()

    for cell in all_cells:
        if len(fires) < n_fires:
            fires.add(cell)
        elif len(stones) < n_stones:
            stones.add(cell)
        else:
            break

    return fires, stones


# ================================================================
#  DRAW ENERGY BAR  (shown in the right panel)
# ================================================================

def draw_energy_bar(surface, x, y, w, h, energy, max_energy):
    """Draw a horizontal energy bar with label."""
    pygame.draw.rect(surface, (180, 190, 210), (x, y, w, h), border_radius=6)   # background
    fill_w = int(w * energy / max_energy)
    col    = ENERGY_COL if energy > max_energy * 0.3 else ENERGY_LOW
    if fill_w > 0:
        pygame.draw.rect(surface, col, (x, y, fill_w, h), border_radius=6)
    pygame.draw.rect(surface, (100, 110, 140), (x, y, w, h), 2, border_radius=6)  # border


# ================================================================
#  POPUP NOTIFICATION  (shows +150 / -100 etc. floating up)
# ================================================================

class FloatingText:
    def __init__(self, text, x, y, color):
        self.text  = text
        self.x     = x
        self.y     = float(y)
        self.color = color
        self.alpha = 255
        self.font  = pygame.font.SysFont("comicsansms", 26, bold=True)

    def update(self):
        self.y    -= 1.5
        self.alpha = max(0, self.alpha - 6)

    def draw(self, surface):
        if self.alpha <= 0:
            return
        surf = self.font.render(self.text, True, self.color)
        surf.set_alpha(self.alpha)
        surface.blit(surf, (self.x - surf.get_width() // 2, int(self.y)))

    @property
    def dead(self):
        return self.alpha <= 0


# ================================================================
#  MAIN GAME
# ================================================================

def play_game(rows, cols, level_name):
    # ---- Level settings ----
    if level_name == "Easy":
        n_fires    = 3
        n_stones   = 5
    else:
        n_fires    = 7
        n_stones   = 9

    MAX_ENERGY    = 100
    energy        = MAX_ENERGY
    FIRE_DAMAGE   = 20    # energy lost per fire step
    STONE_ENERGY  = 10    # energy gained per stone
    STONE_SCORE   = 150   # score added per stone collected
    FIRE_PENALTY  = 100   # score subtracted per fire stepped on

    score = 0             # THE ONLY score: +150 per stone, -100 per fire

    # ---- Build maze ----
    maze = Maze(rows, cols)

    # ---- Spawn fires and stones ----
    fire_cells, stone_cells = spawn_hazards(maze, rows, cols, n_fires, n_stones)
    collected_stones = set()
    stepped_fires    = set()   # fires we are currently standing on (prevent repeated damage)

    # ---- Cell size ----
    play_area_w   = SCREEN_W - PANEL_W
    max_by_width  = (play_area_w  - 40) // cols
    max_by_height = (SCREEN_H     - 40) // rows
    cell = max(22, min(max_by_width, max_by_height, 130))

    maze_pixel_w = cols * cell
    maze_pixel_h = rows * cell
    offset_x = max(10, (play_area_w  - maze_pixel_w) // 2)
    offset_y = max(10, (SCREEN_H     - maze_pixel_h) // 2)

    need_camera = (maze_pixel_w > play_area_w - 20) or (maze_pixel_h > SCREEN_H - 40)
    cam_x = 0
    cam_y = 0

    maze_image = build_maze_image(maze, cell)

    # ---- State ----
    hint_path    = []
    show_hint    = False
    player_row   = 0
    player_col   = 0
    exit_row     = rows - 1
    exit_col     = cols - 1

    # ---- Autoplay (A*) state ----
    autoplay          = False        # toggled with SPACE
    astar_path        = []           # full A* path from current pos to exit
    astar_step_idx    = 0            # next step index in astar_path
    AUTOPLAY_DELAY    = 12           # frames between each auto-move (lower = faster)
    autoplay_timer    = 0

    draw_x  = float(offset_x + player_col * cell + cell // 2)
    draw_y  = float(offset_y + player_row * cell + cell // 2)
    target_x = draw_x
    target_y  = draw_y

    floating_texts = []   # list of FloatingText objects

    f_hud   = pygame.font.SysFont("comicsansms", 28, bold=True)
    f_small = pygame.font.SysFont("comicsansms", 20)
    f_big   = pygame.font.SysFont("comicsansms", 56, bold=True)

    key_map = {
        pygame.K_UP:    (-1,  0,  0),
        pygame.K_DOWN:  ( 1,  0,  1),
        pygame.K_RIGHT: ( 0,  1,  2),
        pygame.K_LEFT:  ( 0, -1,  3),
        pygame.K_w:     (-1,  0,  0),
        pygame.K_s:     ( 1,  0,  1),
        pygame.K_d:     ( 0,  1,  2),
        pygame.K_a:     ( 0, -1,  3),
    }

    clock      = pygame.time.Clock()
    start_time = time.time()  # Track game start time
    tick       = 0

    # ============================================================
    #  GAME LOOP
    # ============================================================
    while True:
        tick     += 1

        # ---- Handle input ----
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"

                if event.key == pygame.K_h:
                    show_hint = not show_hint
                    if show_hint and not hint_path:
                        hint_path = maze.find_solution_astar(
                            player_row, player_col, exit_row, exit_col,
                            fire_cells, stone_cells, collected_stones)

                # ── AUTOPLAY TOGGLE (SPACE) ───────────────────────
                if event.key == pygame.K_SPACE:
                    autoplay = not autoplay
                    if autoplay:
                        # Compute fresh A* path from current position
                        astar_path     = maze.find_solution_astar(
                            player_row, player_col, exit_row, exit_col,
                            fire_cells, stone_cells, collected_stones)
                        astar_step_idx = 1   # index 0 is current cell
                        autoplay_timer = 0
                    else:
                        astar_path     = []
                        astar_step_idx = 0

                if event.key in key_map:
                    dr, dc, wall = key_map[event.key]
                    if maze.open_path(player_row, player_col, wall):
                        player_row += dr
                        player_col += dc
                        target_x    = offset_x + player_col * cell + cell // 2
                        target_y    = offset_y + player_row * cell + cell // 2
                        if show_hint:
                            hint_path = maze.find_solution_astar(
                                player_row, player_col, exit_row, exit_col,
                                fire_cells, stone_cells, collected_stones)

                        pos = (player_row, player_col)

                        # ── STONE COLLECTION ─────────────────────────
                        if pos in stone_cells and pos not in collected_stones:
                            collected_stones.add(pos)
                            energy = min(MAX_ENERGY, energy + STONE_ENERGY)
                            score += STONE_SCORE
                            px2 = int(offset_x + player_col * cell + cell // 2)
                            py2 = int(offset_y + player_row * cell + cell // 2)
                            floating_texts.append(
                                FloatingText(f"+{STONE_SCORE} 🪨", px2, py2 - 10, (100, 210, 100)))
                            floating_texts.append(
                                FloatingText(f"+{STONE_ENERGY} ⚡", px2, py2 - 36, (80, 200, 255)))

                        # ── FIRE DAMAGE ───────────────────────────────
                        if pos in fire_cells:
                            if pos not in stepped_fires:
                                stepped_fires.add(pos)
                                energy = max(0, energy - FIRE_DAMAGE)
                                score  = max(0, score - FIRE_PENALTY)
                                px2 = int(offset_x + player_col * cell + cell // 2)
                                py2 = int(offset_y + player_row * cell + cell // 2)
                                floating_texts.append(
                                    FloatingText(f"-{FIRE_PENALTY} 🔥", px2, py2 - 10, (255, 80, 0)))
                                floating_texts.append(
                                    FloatingText(f"-{FIRE_DAMAGE} ⚡", px2, py2 - 36, (255, 160, 0)))
                        else:
                            stepped_fires.discard((player_row - dr, player_col - dc))

        # ---- Autoplay movement (A*) ----
        if autoplay and energy > 0:
            autoplay_timer += 1
            if autoplay_timer >= AUTOPLAY_DELAY:
                autoplay_timer = 0
                if astar_step_idx < len(astar_path):
                    nr, nc = astar_path[astar_step_idx]
                    astar_step_idx += 1
                    player_row = nr
                    player_col = nc
                    target_x   = offset_x + player_col * cell + cell // 2
                    target_y   = offset_y + player_row * cell + cell // 2

                    if show_hint:
                        hint_path = maze.find_solution_astar(
                            player_row, player_col, exit_row, exit_col,
                            fire_cells, stone_cells, collected_stones)

                    pos = (player_row, player_col)

                    # Stone collection
                    if pos in stone_cells and pos not in collected_stones:
                        collected_stones.add(pos)
                        energy = min(MAX_ENERGY, energy + STONE_ENERGY)
                        score += STONE_SCORE
                        px2 = int(offset_x + player_col * cell + cell // 2)
                        py2 = int(offset_y + player_row * cell + cell // 2)
                        floating_texts.append(
                            FloatingText(f"+{STONE_SCORE} stone", px2, py2 - 10, (100, 210, 100)))
                        floating_texts.append(
                            FloatingText(f"+{STONE_ENERGY} energy", px2, py2 - 36, (80, 200, 255)))
                        # Recompute path (stone collected changes cost model)
                        astar_path = maze.find_solution_astar(
                            player_row, player_col, exit_row, exit_col,
                            fire_cells, stone_cells, collected_stones)
                        astar_step_idx = 1

                    # Fire damage
                    if pos in fire_cells:
                        if pos not in stepped_fires:
                            stepped_fires.add(pos)
                            energy = max(0, energy - FIRE_DAMAGE)
                            score  = max(0, score - FIRE_PENALTY)
                            px2 = int(offset_x + player_col * cell + cell // 2)
                            py2 = int(offset_y + player_row * cell + cell // 2)
                            floating_texts.append(
                                FloatingText(f"-{FIRE_PENALTY} fire", px2, py2 - 10, (255, 80, 0)))
                            floating_texts.append(
                                FloatingText(f"-{FIRE_DAMAGE} energy", px2, py2 - 36, (255, 160, 0)))
                    else:
                        dr = player_row - (astar_path[astar_step_idx - 2][0] if astar_step_idx >= 2 else player_row)
                        dc = player_col - (astar_path[astar_step_idx - 2][1] if astar_step_idx >= 2 else player_col)
                        stepped_fires.discard((player_row - dr, player_col - dc))
                else:
                    # Path finished; recompute in case we need to continue
                    astar_path = maze.find_solution_astar(
                        player_row, player_col, exit_row, exit_col,
                        fire_cells, stone_cells, collected_stones)
                    astar_step_idx = 1

        # ---- Smooth movement ----
        draw_x += (target_x - draw_x) * 0.25
        draw_y += (target_y - draw_y) * 0.25

        # ---- Camera ----
        if need_camera:
            view_w = play_area_w - 20
            view_h = SCREEN_H    - 40
            cam_x  = max(0, min(int(draw_x) - view_w // 2, maze_pixel_w - view_w))
            cam_y  = max(0, min(int(draw_y) - view_h // 2, maze_pixel_h - view_h))

        # ---- Update floating texts ----
        for ft in floating_texts:
            ft.update()
        floating_texts = [ft for ft in floating_texts if not ft.dead]

        # ================================================================
        #  DRAWING
        # ================================================================
        screen.fill(DARK_BG)

        if need_camera:
            screen.set_clip(pygame.Rect(10, 10, play_area_w - 20, SCREEN_H - 20))
            ox = 10 - cam_x
            oy = 10 - cam_y
        else:
            ox = offset_x
            oy = offset_y

        # 1. Maze image
        screen.blit(maze_image, (ox, oy))

        # 2. Fire traps
        fire_sz = max(10, cell // 2)
        for (fr, fc) in fire_cells:
            fx = ox + fc * cell + cell // 2
            fy = oy + fr * cell + cell // 2
            # Animated red floor glow under fire
            glow_surf = pygame.Surface((cell - 4, cell - 4), pygame.SRCALPHA)
            glow_surf.fill((255, 60, 0, 55))
            screen.blit(glow_surf, (ox + fc * cell + 2, oy + fr * cell + 2))
            draw_fire(screen, fx, fy, fire_sz, tick)

        # 3. Stone collectibles (only uncollected ones)
        stone_sz = max(10, cell // 2)
        for (sr, sc) in stone_cells:
            if (sr, sc) not in collected_stones:
                sx = ox + sc * cell + cell // 2
                sy = oy + sr * cell + cell // 2
                draw_stone(screen, sx, sy, stone_sz, tick)

        # 4. Hint path (A* optimal) — gold trail
        if show_hint and hint_path:
            for (hr, hc) in hint_path[1:]:
                hx = ox + hc * cell + 2
                hy = oy + hr * cell + 2
                hint_surf = pygame.Surface((cell - 4, cell - 4), pygame.SRCALPHA)
                hint_surf.fill((220, 160, 0, 120))   # gold for A* optimal hint
                screen.blit(hint_surf, (hx, hy))
            if len(hint_path) >= 2:
                nr, nc = hint_path[1]
                ax = ox + nc * cell + cell // 2
                ay = oy + nr * cell + cell // 2
                pygame.draw.circle(screen, (255, 210, 60), (ax, ay), cell // 5)

        # 4b. A* autoplay path visualisation
        if autoplay and astar_path:
            for idx, (ar, ac) in enumerate(astar_path[astar_step_idx:], start=0):
                ax2 = ox + ac * cell + 2
                ay2 = oy + ar * cell + 2
                # Gradient: bright cyan near the player, fades toward exit
                progress = idx / max(1, len(astar_path) - astar_step_idx)
                alpha    = int(140 * (1 - progress * 0.7))
                astar_surf = pygame.Surface((cell - 4, cell - 4), pygame.SRCALPHA)
                astar_surf.fill((0, 210, 255, alpha))
                screen.blit(astar_surf, (ax2, ay2))
            # Draw a small arrow dot on the very next cell
            if astar_step_idx < len(astar_path):
                nr2, nc2 = astar_path[astar_step_idx]
                pygame.draw.circle(screen,
                                   (0, 255, 200),
                                   (ox + nc2 * cell + cell // 2,
                                    oy + nr2 * cell + cell // 2),
                                   max(4, cell // 5))

        # 5. Exit flag glow
        fx = ox + exit_col * cell + cell // 2
        fy = oy + exit_row * cell + cell // 2
        for radius in range(30, 5, -5):
            alpha = int(70 * (1 - (radius / 30) ** 2))
            glow  = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow, (*GOLD, alpha), (radius, radius), radius)
            screen.blit(glow, (fx - radius, fy - radius))

        # 6. Flag
        draw_flag(screen, fx, fy + cell // 3, cell - 6, tick)

        # 7. Start dot
        pygame.draw.circle(screen, GREEN, (ox + cell // 2, oy + cell // 2), 8)

        # 8. Girl
        girl_x = int(ox + player_col * cell + cell // 2)
        girl_y = int(oy + player_row * cell + cell // 2)
        draw_girl(screen, girl_x, girl_y, cell - 4, tick)

        # 9. Floating score/energy texts
        for ft in floating_texts:
            ft.draw(screen)

        if need_camera:
            screen.set_clip(None)

        # ================================================================
        #  RIGHT-SIDE PANEL
        # ================================================================
        px = SCREEN_W - PANEL_W
        pygame.draw.rect(screen, PANEL_BG, (px, 0, PANEL_W, SCREEN_H))
        pygame.draw.line(screen, (180, 190, 215), (px, 0), (px, SCREEN_H), 2)

        # Level badge
        badge_col = GREEN if level_name == "Easy" else RED
        pygame.draw.rect(screen, badge_col, (px + 10, 14, PANEL_W - 22, 52), border_radius=10)
        lbl = f_hud.render(level_name, True, (15, 10, 30))
        screen.blit(lbl, lbl.get_rect(center=(px + PANEL_W // 2, 40)))

        # ── ENERGY BAR ───────────────────────────────────────────
        ebar_y = 100
        screen.blit(f_small.render("ENERGY", True, (80, 90, 140)), (px + 14, ebar_y))
        draw_energy_bar(screen, px + 14, ebar_y + 24, PANEL_W - 28, 22, energy, MAX_ENERGY)
        en_col = ENERGY_COL if energy > MAX_ENERGY * 0.3 else ENERGY_LOW
        en_txt = f_small.render(f"{energy}/{MAX_ENERGY}", True, en_col)
        screen.blit(en_txt, en_txt.get_rect(center=(px + PANEL_W // 2, ebar_y + 60)))

        def draw_stat(label, value, y, value_col=WHITE):
            screen.blit(f_small.render(label, True, (80, 90, 140)), (px + 14, y))
            screen.blit(f_hud.render(str(value), True, value_col),  (px + 14, y + 26))

        # Score = stones × 150  −  fires stepped × 100  (nothing else)
        draw_stat("SCORE",  score,                       160, GOLD)

        # Stone counter
        screen.blit(f_small.render("STONES", True, (80, 90, 140)), (px + 14, 230))
        stone_val = f_hud.render(f"{len(collected_stones)}/{len(stone_cells)}", True, STONE_COL)
        screen.blit(stone_val, (px + 14, 256))

        # Hint / ESC reminder
        h_hint = f_small.render("H=A* hint  SPC=A* auto  ESC=menu", True, (80, 90, 140))
        screen.blit(h_hint, (px + 14, SCREEN_H - 54))

        # Autoplay indicator badge
        if autoplay:
            auto_badge = pygame.Surface((PANEL_W - 28, 30), pygame.SRCALPHA)
            auto_badge.fill((0, 200, 255, 60))
            screen.blit(auto_badge, (px + 14, SCREEN_H - 90))
            auto_lbl = f_small.render("A* AUTOPLAY  ON", True, (0, 220, 255))       
            screen.blit(auto_lbl, auto_lbl.get_rect(center=(px + PANEL_W // 2, SCREEN_H - 75)))

        # ================================================================
        #  OVERLAYS
        # ================================================================

        # Calculate elapsed time for game over screen
        elapsed_time = time.time() - start_time

        # ── NO ENERGY ─────────────────────────────────────────────────
        if energy <= 0:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((80, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            # Show game over screen with time
            pygame.display.flip()
            clock.tick(FPS)
            
            # Wait for key press and return result
            return ("game_over", elapsed_time)

        pygame.display.flip()
        clock.tick(FPS)

        # ── WIN CHECK ─────────────────────────────────────────────────
        if player_row == exit_row and player_col == exit_col:
            return ("win", elapsed_time, score, len(collected_stones))


# ================================================================
#  MAIN
# ================================================================

def main():
    while True:
        rows, cols, level_name = level_select_screen()

        while True:
            result = play_game(rows, cols, level_name)

            if result == "menu":
                break

            if result == "restart":
                continue

            if isinstance(result, tuple):
                if result[0] == "win":
                    _, elapsed_time, score, stones = result
                    action = win_screen(level_name, elapsed_time, score, stones)
                    if action == "menu":
                        break
                    if action == "restart":
                        continue
                
                elif result[0] == "game_over":
                    _, elapsed_time = result
                    action = game_over_screen(elapsed_time)
                    if action == "menu":
                        break
                    if action == "restart":
                        continue


if __name__ == "__main__":
    main()