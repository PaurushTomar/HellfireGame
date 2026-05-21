import random
import pygame
import os
import sys
import base64
import math

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

pygame.init()

# ── MOBILE: safe audio init ────────────────────────────────────────────────────
try:
    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.mixer.init()
    audio_available = True
except Exception:
    audio_available = False

# Colors
white    = (255, 255, 255)
black    = (0,   0,   0  )
red      = (255, 0,   0  )
yellow   = (255, 255, 0  )
orange   = (255, 165, 0  )
DARK_RED = (150, 0,   0  )

# ── FIX: Force landscape BEFORE reading display info ──────────────────────────
# On Android, pygame.display.set_mode must be called first to trigger
# landscape orientation. We call it with FULLSCREEN + SCALED flags.
# SCALED lets pygame handle any resolution mismatch automatically.
os.environ['SDL_ORIENTATIONS'] = 'landscape'  # hint to Android SDL layer

# ── FIX: Use a fixed logical resolution of 800x480 (standard landscape) ───────
# Instead of scaling from the physical screen size (which caused compression),
# we design the game at 800x480 and let pygame/SDL scale it to fit any screen.
# This is the correct approach for cross-device compatibility.
LOGICAL_W = 800
LOGICAL_H = 480

# ── MOBILE: FULLSCREEN + SCALED — pygame scales logical size to fit screen ─────
# SCALED flag is key: it maintains aspect ratio and handles all screen sizes.
window = pygame.display.set_mode(
    (LOGICAL_W, LOGICAL_H),
    pygame.FULLSCREEN | pygame.SCALED
)
pygame.display.set_caption("HellFire")

try:
    icon = pygame.image.load(resource_path("resources/icon.jpg"))
    pygame.display.set_icon(icon)
except Exception:
    pass

# ── FIX: Scale ratios now based on logical size vs original 600x400 ────────────
# This gives correct proportions without depending on physical screen pixels.
SCALE_X = LOGICAL_W / 600   # = 1.333
SCALE_Y = LOGICAL_H / 400   # = 1.2

# screen_width/height now refer to logical canvas size
screen_width  = LOGICAL_W
screen_height = LOGICAL_H

# ── Load all assets once at startup ───────────────────────────────────────────
background = pygame.image.load(resource_path("resources/background.png"))
background = pygame.transform.scale(background, (screen_width, screen_height))

wlcm_img = pygame.image.load(resource_path("resources/homedragon.png"))
wlcm_img = pygame.transform.scale(wlcm_img, (screen_width // 2, screen_height // 2))

dino_img = pygame.image.load(resource_path("resources/dino.png"))
dino_img = pygame.transform.scale(dino_img, (int(80 * SCALE_X), int(80 * SCALE_Y)))

rock_img = pygame.image.load(resource_path("resources/rock.png"))
rock_img = pygame.transform.scale(rock_img, (int(80 * SCALE_X), int(100 * SCALE_Y)))

dragon_img = pygame.image.load(resource_path("resources/enmydragon.png"))
dragon_img = pygame.transform.scale(dragon_img, (int(100 * SCALE_X), int(80 * SCALE_Y)))

land_img = pygame.image.load(resource_path("resources/land.png"))
land_img = pygame.transform.scale(land_img, (screen_width, int(150 * SCALE_Y)))

# ── MOBILE: audio wrapped safely ──────────────────────────────────────────────
if audio_available:
    try:
        intro_music    = resource_path("resources/introsound.mp3")
        jump_sound     = pygame.mixer.Sound(resource_path("resources/jump.mp3"))
        gameover_sound = pygame.mixer.Sound(resource_path("resources/gameover.mp3"))
        achieve_sound  = pygame.mixer.Sound(resource_path("resources/achievement.mp3"))
        pygame.mixer.music.set_volume(0.8)
    except Exception:
        audio_available = False

clock = pygame.time.Clock()
fps   = 60

# ── MOBILE: touch zones — bottom 20% of logical screen, split left/right ──────
btn_height = int(screen_height * 0.20)
btn_y      = screen_height - btn_height
jump_btn   = pygame.Rect(0,                btn_y, screen_width // 2, btn_height)
fall_btn   = pygame.Rect(screen_width // 2, btn_y, screen_width // 2, btn_height)

# ── FIX: Android-safe font loading ────────────────────────────────────────────
# comicsansms and other named fonts don't exist on Android.
# pygame.font.Font(None, size) uses pygame's built-in default font — always works.
# We wrap it so the rest of the code stays clean.
def get_font(size):
    scaled = max(8, int(size * min(SCALE_X, SCALE_Y)))
    try:
        return pygame.font.Font(resource_path("resources/font.ttf"), scaled)
    except Exception:
        return pygame.font.Font(None, scaled)  
        # fallback if file missing
def draw_touch_buttons():
    """Semi-transparent tap zones at the bottom."""
    overlay = pygame.Surface((screen_width // 2, btn_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 80))
    window.blit(overlay, (0,                btn_y))
    window.blit(overlay, (screen_width // 2, btn_y))

    font_btn   = get_font(22)
    jump_label = font_btn.render("TAP  [L]  JUMP", True, (255, 255, 100))
    fall_label = font_btn.render("TAP  [R]  DIVE", True, (255, 200, 100))

    window.blit(jump_label, (
        jump_btn.centerx - jump_label.get_width() // 2,
        btn_y + btn_height // 2 - jump_label.get_height() // 2
    ))
    window.blit(fall_label, (
        fall_btn.centerx - fall_label.get_width() // 2,
        btn_y + btn_height // 2 - fall_label.get_height() // 2
    ))
    pygame.draw.line(window, (200, 200, 200),
                     (screen_width // 2, btn_y),
                     (screen_width // 2, screen_height), 2)

def text_screen(text, size, color, x, y):
    font = get_font(size)
    window.blit(font.render(text, True, DARK_RED), (x + 2, y + 2))
    window.blit(font.render(text, True, color),    (x,     y    ))

# ── HIGH SCORE: Android-safe path ─────────────────────────────────────────────
_android_private = os.environ.get('ANDROID_PRIVATE')
hiscore_path = os.path.join(
    _android_private if _android_private else os.path.expanduser("~"),
    "dragon_hiscore.dat"
)
SECRET_KEY = 1234

def save_hiscore(score):
    try:
        with open(hiscore_path, "wb") as f:
            f.write(base64.b64encode(str(score + SECRET_KEY).encode()))
    except Exception:
        pass

def load_hiscore():
    try:
        if not os.path.exists(hiscore_path):
            save_hiscore(0)
            return 0
        with open(hiscore_path, "rb") as f:
            return int(base64.b64decode(f.read()).decode()) - SECRET_KEY
    except Exception:
        return 0


def reset_game_state():
    """
    Fresh state dict for every new game.
    Speeds, timers, lists all reset — difficulty always starts from zero.
    """
    return {
        "game_over"            : False,
        "iteration"            : 0,
        "score"                : 0,
        "tree_speed"           : 4.0 * SCALE_X,   # reset to start speed
        "land_speed"           : 4.0 * SCALE_X,
        "rock_spawn_timer"     : 0,
        "rock_spawn_interval"  : random.randint(60, 120),
        "dragon_spawn_timer"   : 0,
        "dragon_spawn_interval": random.randint(300, 500),
        "rock_list"            : [],
        "dragon_list"          : [],
        "dino_y"               : int(230 * SCALE_Y),
        "is_jumping"           : False,
        "velocity_y"           : 0,
        # ── FIX: gravity uses SCALE_Y=1.2, so jump feels like original ─────────
        "gravity"              : 0.6 * SCALE_Y,
        "land_tiles"           : [[0, False], [screen_width, True]],
        "active_touches"       : {},
    }


def welcome():
    window.fill(white)
    window.blit(background, (0, 0))
    window.blit(wlcm_img, (screen_width // 2 - screen_width // 4,
                            screen_height // 3 - screen_height // 6))

    # ── FIX: use get_font() instead of SysFont directly ───────────────────────
    title_font = get_font(55)
    title_x    = int(180 * SCALE_X)
    window.blit(title_font.render("HELLFIRE", True, DARK_RED), (title_x + 2, 12))
    window.blit(title_font.render("HELLFIRE", True, orange),   (title_x,     10))

    # ── MOBILE: "Tap anywhere to play" instead of "Press Enter" ───────────────
    text_screen("Tap anywhere to play",    35, yellow,
                int(screen_width * 0.25),  screen_height - int(80 * SCALE_Y))
    text_screen("Made by ~ Paurush Tomar", 16, yellow,
                screen_width - int(260 * SCALE_X), screen_height - int(30 * SCALE_Y))

    if audio_available:
        try:
            pygame.mixer.music.load(intro_music)
            pygame.mixer.music.play()
        except Exception:
            pass

    pygame.display.update()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_AC_BACK:
                    pygame.quit(); sys.exit()
                if event.key == pygame.K_RETURN:
                    if audio_available: pygame.mixer.music.stop()
                    gameloop(); return
            if event.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
                if audio_available: pygame.mixer.music.stop()
                gameloop(); return
        pygame.display.update()


def gameloop():
    ground_y      = int(230 * SCALE_Y)
    dino_x        = int(100 * SCALE_X)
    dino_width    = int(80  * SCALE_X)
    dino_height   = int(80  * SCALE_Y)
    land_y        = ground_y + int(20 * SCALE_Y)
    # ── FIX: jump velocity tuned to SCALE_Y=1.2 so jump height feels normal ───
    jump_velocity = -13 * SCALE_Y
    max_speed     = 25  * SCALE_X

    hiscore = load_hiscore()

    # Outer loop — each iteration is one full game session (no recursion)
    while True:
        s = reset_game_state()
        restart_requested = False

        # Inner loop — one frame per tick
        while not restart_requested:

            # ── Events ────────────────────────────────────────────────────────
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_AC_BACK:
                        pygame.quit(); sys.exit()
                    if not s["game_over"]:
                        if event.key in (pygame.K_UP, pygame.K_SPACE) and not s["is_jumping"]:
                            if audio_available:
                                jump_sound.set_volume(0.8); jump_sound.play()
                            s["is_jumping"] = True
                            s["velocity_y"] = jump_velocity
                            s["gravity"]    = 0.6 * SCALE_Y
                        if event.key == pygame.K_DOWN:
                            s["gravity"] = 1.4 * SCALE_Y
                    else:
                        if event.key == pygame.K_SPACE:
                            restart_requested = True

                # ── MOBILE: finger touch ───────────────────────────────────────
                if event.type == pygame.FINGERDOWN:
                    # ── FIX: SCALED mode changes how touch coords map ──────────
                    # With pygame.SCALED, finger coords (0.0-1.0) must be
                    # multiplied by LOGICAL size, not physical screen size.
                    fx = int(event.x * screen_width)
                    fy = int(event.y * screen_height)

                    if s["game_over"]:
                        restart_requested = True
                    else:
                        if jump_btn.collidepoint(fx, fy) and not s["is_jumping"]:
                            if audio_available:
                                jump_sound.set_volume(0.8); jump_sound.play()
                            s["is_jumping"] = True
                            s["velocity_y"] = jump_velocity
                            s["gravity"]    = 0.6 * SCALE_Y
                            s["active_touches"][event.finger_id] = 'jump'
                        elif fall_btn.collidepoint(fx, fy):
                            s["gravity"] = 1.8 * SCALE_Y
                            s["active_touches"][event.finger_id] = 'fall'

                if event.type == pygame.FINGERUP:
                    zone = s["active_touches"].pop(event.finger_id, None)
                    if zone == 'fall' and not s["is_jumping"]:
                        s["gravity"] = 0.6 * SCALE_Y

                # ── Mouse (PC testing) ─────────────────────────────────────────
                if event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    if s["game_over"]:
                        restart_requested = True
                    else:
                        if jump_btn.collidepoint(mx, my) and not s["is_jumping"]:
                            if audio_available:
                                jump_sound.set_volume(0.8); jump_sound.play()
                            s["is_jumping"] = True
                            s["velocity_y"] = jump_velocity
                            s["gravity"]    = 0.6 * SCALE_Y
                        elif fall_btn.collidepoint(mx, my):
                            s["gravity"] = 1.8 * SCALE_Y

            if restart_requested:
                break

            # ── GAME OVER SCREEN ───────────────────────────────────────────────
            if s["game_over"]:
                window.blit(background, (0, 0))
                text_screen("Game Over", 100, red,
                            int(screen_width * 0.16), int(screen_height * 0.25))
                text_screen(f"Score: {s['score']}   High Score: {hiscore}", 28, white,
                            int(screen_width * 0.28), int(screen_height * 0.62))
                # ── MOBILE: "Tap to play again" instead of "Press Space" ───────
                text_screen("Tap to play again", 30, yellow,
                            int(screen_width * 0.34), int(screen_height * 0.85))
                if s["score"] >= hiscore:
                    hiscore = s["score"]
                    save_hiscore(hiscore)
                pygame.display.update()
                clock.tick(fps)
                continue

            # ── PHYSICS ───────────────────────────────────────────────────────
            if s["is_jumping"]:
                s["dino_y"]     += s["velocity_y"]
                s["velocity_y"] += s["gravity"]
                if s["dino_y"] >= ground_y:
                    s["dino_y"]     = ground_y
                    s["is_jumping"] = False
                    s["velocity_y"] = 0
                    s["gravity"]    = 0.6 * SCALE_Y

            # ── LAND ──────────────────────────────────────────────────────────
            for tile in s["land_tiles"]:
                tile[0] -= s["land_speed"]
            if s["land_tiles"][0][0] + screen_width <= 0:
                last_x    = s["land_tiles"][-1][0]
                last_flip = s["land_tiles"][-1][1]
                s["land_tiles"].append([last_x + screen_width, not last_flip])
                s["land_tiles"].pop(0)

            # ── SPAWN ROCKS ───────────────────────────────────────────────────
            s["rock_spawn_timer"] += 1.0
            if s["rock_spawn_timer"] > s["rock_spawn_interval"]:
                new_rx = screen_width + random.randint(0, int(100 * SCALE_X))
                if not any(abs(new_rx - d[0]) < int(300 * SCALE_X) for d in s["dragon_list"]):
                    s["rock_list"].append([new_rx, int(220 * SCALE_Y)])
                s["rock_spawn_timer"]    = 0
                s["rock_spawn_interval"] = random.randint(60, 120)

            # ── SPAWN DRAGONS ─────────────────────────────────────────────────
            s["dragon_spawn_timer"] += 1.8
            if s["dragon_spawn_timer"] > s["dragon_spawn_interval"]:
                new_dx = screen_width + random.randint(0, int(200 * SCALE_X))
                if not any(abs(new_dx - r[0]) < int(200 * SCALE_X) for r in s["rock_list"]):
                    s["dragon_list"].append([new_dx, int(150 * SCALE_Y)])
                s["dragon_spawn_timer"]    = 0
                s["dragon_spawn_interval"] = random.randint(300, 500)

            # ── MOVE OBSTACLES ────────────────────────────────────────────────
            for rock in s["rock_list"]:
                rock[0] -= s["tree_speed"]
            s["rock_list"] = [r for r in s["rock_list"] if r[0] + int(80 * SCALE_X) > 0]

            for idx, dragon in enumerate(s["dragon_list"]):
                dragon[0] -= s["tree_speed"] + SCALE_X
                dragon[1]  = int(150 * SCALE_Y) + math.sin(
                    pygame.time.get_ticks() / 200 + idx) * 5

            # ── COLLISION ─────────────────────────────────────────────────────
            dino_hitbox = pygame.Rect(
                dino_x + int(10 * SCALE_X), s["dino_y"] + int(10 * SCALE_Y),
                dino_width  - int(20 * SCALE_X),
                dino_height - int(30 * SCALE_Y)
            )
            for rock in s["rock_list"]:
                if dino_hitbox.colliderect(pygame.Rect(
                    rock[0] + int(15 * SCALE_X), rock[1] + int(20 * SCALE_Y),
                    int(45 * SCALE_X), int(70 * SCALE_Y)
                )):
                    if audio_available:
                        gameover_sound.set_volume(0.3); gameover_sound.play()
                    s["game_over"] = True

            for dragon in s["dragon_list"]:
                if dino_hitbox.colliderect(pygame.Rect(
                    dragon[0] + int(10 * SCALE_X), dragon[1] + int(20 * SCALE_Y),
                    int(80 * SCALE_X), int(50 * SCALE_Y)
                )):
                    if audio_available:
                        gameover_sound.set_volume(0.3); gameover_sound.play()
                    s["game_over"] = True

            # ── DRAW ──────────────────────────────────────────────────────────
            window.blit(background, (0, 0))

            for x, flip in s["land_tiles"]:
                window.blit(pygame.transform.flip(land_img, flip, False), (x, land_y))

            dino_wave = math.sin(pygame.time.get_ticks() / 200) * 3
            if not s["is_jumping"]:
                window.blit(dino_img, (dino_x, s["dino_y"] + dino_wave))
            else:
                window.blit(dino_img, (dino_x, s["dino_y"]))

            for rock   in s["rock_list"]:
                window.blit(rock_img,   (rock[0],   rock[1]))
            for dragon in s["dragon_list"]:
                window.blit(dragon_img, (dragon[0], dragon[1]))

            # ── MOBILE: draw tap zones ─────────────────────────────────────────
            draw_touch_buttons()

            # ── SCORE & SPEED ─────────────────────────────────────────────────
            s["iteration"] += 1
            s["score"]      = s["iteration"] // 10

            if s["score"] > 0 and s["score"] % 100 == 0:
                if audio_available:
                    achieve_sound.set_volume(0.3); achieve_sound.play()

            s["tree_speed"] = min(s["tree_speed"] + 0.009 * SCALE_X, max_speed)
            s["land_speed"] = min(s["land_speed"] + 0.009 * SCALE_X, max_speed)

            if s["score"] > hiscore:
                hiscore = s["score"]

            text_screen(f"Score: {s['score']}  High Score: {hiscore}",
                        28, black, int(10 * SCALE_X), int(10 * SCALE_Y))

            pygame.display.update()
            clock.tick(fps)


# ── Entry point ────────────────────────────────────────────────────────────────
welcome()
pygame.quit()
sys.exit()