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
pygame.mixer.init()
# Colors
white = (255, 255, 255)
black = (0, 0, 0)
red = (255, 0, 0)
yellow = (255, 255, 0)
orange = (255,165,0)
DARK_RED = (150, 0, 0)

# Screen setup
screen_width = 600
screen_height = 400
window = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("HellFire")
icon = pygame.image.load(resource_path("resources/icon.jpg"))
pygame.display.set_icon(icon)

# font = pygame.font.SysFont('mistral', 40, bold=True)


# Load and scale background
background = pygame.image.load(resource_path("resources/background.png"))
background = pygame.transform.scale(background, (screen_width, screen_height))
# Getting welcome screen image
wlcm_img = pygame.image.load(resource_path("resources/homedragon.png"))
wlcm_img = pygame.transform.scale(wlcm_img, (screen_width//2, screen_height//2))
# Load sounds
intro_music = resource_path("resources/introsound.mp3")
jump_sound = pygame.mixer.Sound(resource_path("resources/jump.mp3"))
gameover_sound = pygame.mixer.Sound(resource_path("resources/gameover.mp3"))
achieve_sound = pygame.mixer.Sound(resource_path("resources/achievement.mp3"))
pygame.mixer.music.set_volume(0.8) 



# Clock
clock = pygame.time.Clock()
fps = 60

def text_screen(text, size, color, x, y):
    screen_text = pygame.font.SysFont('comicsansms', size, bold=True).render(text, True, color)
    text_shadow = pygame.font.SysFont('comicsansms', size, bold=True).render(text, True, DARK_RED)
    window.blit(text_shadow, (x+2, y+2))
    window.blit(screen_text, [x, y])

def welcome():
    window.fill(white)
    window.blit(background, (0, 0))
    window.blit(wlcm_img, (screen_width//2 - screen_width//4, screen_height//3 - screen_height//6))
    #Game title
    window.blit(pygame.font.SysFont('Bradley Hand ITC', 60, bold=True).render("HELLFIRE", True, DARK_RED), (150+2, 10+2))
    window.blit(pygame.font.SysFont('Bradley Hand ITC', 60, bold=True).render("HELLFIRE", True, orange), [150, 10])
    # text_screen("HELLFIRE", 60, orange, screen_width//8.5, 10)
    text_screen("Press Enter to play", 40, yellow, screen_width//5, screen_height - 120)
    text_screen("Made by ~ Paurush Tomar", 20, yellow, screen_width-280, screen_height-40)
    pygame.mixer.music.load(intro_music)
    pygame.mixer.music.play()
    pygame.display.update()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    pygame.mixer.music.stop()
                    gameloop()

        pygame.display.update()


def gameloop():
    game_over = False
    iteration = 0
    score = 0
    ground_y = 230
    dino_x = 100
    dino_y = ground_y
    dino_width = 80
    dino_height = 80

    dino_img = pygame.image.load(resource_path("resources/dino.png"))
    dino_img = pygame.transform.scale(dino_img, (dino_width, dino_height))

    rock_img = pygame.image.load(resource_path("resources/rock.png"))
    rock_img = pygame.transform.scale(rock_img, (80, 100))
    rock_list = []
    rock_spawn_timer = 0
    rock_spawn_interval = random.randint(60, 120)

    tree_y = 220
    tree_speed = 4

    dragon_list = []
    dragon_spawn_timer = 0
    dragon_spawn_interval = random.randint(300, 500)
    dragon_img = pygame.image.load(resource_path("resources/enmydragon.png"))
    dragon_img = pygame.transform.scale(dragon_img, (100, 80))

    tile_width = screen_width
    tile_height = 150
    land_img = pygame.image.load(resource_path("resources/land.png"))
    land_img = pygame.transform.scale(land_img, (tile_width, tile_height))
    land_y = ground_y + 20
    land_tiles = [[0, False], [tile_width, True]]
    land_speed = 4

    is_jumping = False
    jump_velocity = -15
    gravity = 0.6
    velocity_y = 0

    # High score file
    hiscore_path = os.path.join(os.path.expanduser("~"), "dragon_hiscore.dat")

    secret_key = 1234

    def save_hiscore(hiscore):
        real_score = hiscore + secret_key
        with open(hiscore_path, "wb") as f:
            f.write(base64.b64encode(str(real_score).encode()))

    def load_hiscore():
        try:
            if (not os.path.exists(hiscore_path)):
                with open(hiscore_path, "wb") as f:
                    f.write(base64.b64encode(str(0).encode()))
            with open(hiscore_path, "rb") as f:
                data = f.read()
                real_score = int(base64.b64decode(data).decode())
                return real_score - secret_key
        except:
            return 0  # if file not found
    exit_game = False
    hiscore = load_hiscore()
    while not exit_game:
        events = pygame.event.get()  # 🚨 Read all events once

        for event in events:
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if not game_over:
                    if (event.key == pygame.K_UP or event.key == pygame.K_SPACE) and not is_jumping:
                        jump_sound.set_volume(0.8)  
                        jump_sound.play()
                        is_jumping = True
                        velocity_y = jump_velocity
                        gravity = 0.6
                    if (event.key == pygame.K_DOWN):
                        gravity = 1.4   
                else: 
                    # when game over
                    if event.key == pygame.K_SPACE:
                        pygame.mixer.music.stop()
                        game_over = False
                        rock_list.clear()

                        gameloop()
            
        if game_over:
            text_screen("Game Over", 50, red, 180, 80)
            text_screen("Press Space bar to continue", 30, yellow, 110, 320)
            if score>=int(hiscore):
                save_hiscore(hiscore)
            pygame.display.update()
            clock.tick(fps)
            continue  # 
        else:
            # Apply gravity
            if is_jumping:
                dino_y += velocity_y
                velocity_y += gravity
                if dino_y >= ground_y:
                    dino_y = ground_y
                    is_jumping = False
                    velocity_y = 0
                
            # Move land
            for tile in land_tiles:
                tile[0] -= land_speed
            if land_tiles[0][0] + tile_width <= 0:
                last_x = land_tiles[-1][0]
                last_flip = land_tiles[-1][1]
                land_tiles.append([last_x + tile_width, not last_flip])
                land_tiles.pop(0)

            # Spawn rocks
            rock_spawn_timer += 0.7
            if rock_spawn_timer > rock_spawn_interval:
                new_rock_x = screen_width + random.randint(0, 100)
                if not any(abs(new_rock_x - dragon[0]) < 300 for dragon in dragon_list):
                    rock_list.append([new_rock_x, tree_y])
                rock_spawn_timer = 0
                rock_spawn_interval = random.randint(60, 120)

            # Spawn dragons
            dragon_spawn_timer += 1.5
            if dragon_spawn_timer > dragon_spawn_interval:
                new_dragon_x = screen_width + random.randint(0, 200)
                new_dragon_y = random.randint(50, 150)
                if not any((abs(new_dragon_x - rock[0]) < 200 or abs(new_dragon_y - rock[0]) < 50) for rock in rock_list):
                    dragon_y = 150
                    dragon_list.append([new_dragon_x, dragon_y])
                dragon_spawn_timer = 0
                dragon_spawn_interval = random.randint(300, 500)

            # Move rocks and dragons
            for rock in rock_list:
                rock[0] -= tree_speed
            rock_list = [rock for rock in rock_list if rock[0] + 80 > 0]

            for idx, dragon in enumerate(dragon_list):
                dragon[0] -= tree_speed + 1
                # Add waving effect
                dragon_wave = math.sin(pygame.time.get_ticks() / 200 + idx) * 5  # 5 pixels up/down
                dragon[1] = 150 + dragon_wave  # dragon's base y position + wave

            # Collision detection
            dino_hitbox = pygame.Rect(dino_x + 10, dino_y + 10, dino_width - 20, dino_height - 30)
            for rock in rock_list:
                rock_hitbox = pygame.Rect(rock[0] + 15, rock[1] + 20, 80 - 35, 100 - 30)
                if dino_hitbox.colliderect(rock_hitbox):
                    gameover_sound.set_volume(0.3)  
                    gameover_sound.play()
                    game_over = True

            for dragon in dragon_list:
                dragon_hitbox = pygame.Rect(dragon[0] + 10, dragon[1] + 20, 80, 50)
                if dino_hitbox.colliderect(dragon_hitbox):
                    gameover_sound.set_volume(0.3)
                    gameover_sound.play()
                    game_over = True

            window.blit(background, (0, 0))

            for x, flip in land_tiles:
                tile_img = pygame.transform.flip(land_img, flip, False)
                window.blit(tile_img, (x, land_y))

            # Dino's waving effect
            dino_wave = math.sin(pygame.time.get_ticks() / 200) * 3  # Small wave effect (3 pixels)

            # Only add the waving effect if the dino isn't jumping
            if not is_jumping:
                window.blit(dino_img, (dino_x, dino_y + dino_wave))
            else:
                window.blit(dino_img, (dino_x, dino_y))  # Normal jump without wave
            for rock in rock_list:
                window.blit(rock_img, (rock[0], rock[1]))
            for dragon in dragon_list:
                window.blit(dragon_img, (dragon[0], dragon[1]))

            iteration += 1
            score = iteration
            score = iteration//10
            if (score%100 == 0):
                achieve_sound.set_volume(0.3)  
                achieve_sound.play()
                rock_spawn_timer += 0.01
                dragon_spawn_timer += 0.001
            if tree_speed>= 10:
                tree_speed = 10
                land_speed = 10
            tree_speed += 0.001
            land_speed += 0.001
            
            if score>int(hiscore):
                hiscore = score
            text_screen(f"Score: {score}  High Score: {hiscore}", 30, black, 10, 10)

            pygame.display.update()
            clock.tick(fps)

# Start
welcome()
pygame.quit()
sys.exit()

