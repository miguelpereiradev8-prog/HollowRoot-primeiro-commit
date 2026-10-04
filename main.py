import pygame
import json
import os
from PIL import Image, ImageSequence

pygame.init()

# ============================================================
# CONFIGURAÇÃO
# ============================================================

WIDTH = 1200
HEIGHT = 720
FPS = 60

TILE_SIZE = 32

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Hollowroot Engine")

clock = pygame.time.Clock()

# ============================================================
# CORES
# ============================================================

BG = (18, 15, 22)
GRID = (35, 32, 42)

BLOCK_COLOR = (75, 55, 40)
BLOCK_BORDER = (110, 80, 55)

EDITOR_COLOR = (100, 180, 255)

WHITE = (255, 255, 255)

# ============================================================
# ESTADO
# ============================================================

editor_mode = True

blocks = []

camera_x = 0.0
camera_y = 0.0

# ============================================================
# ARRASTAR CÂMERA COM SCROLL
# ============================================================

camera_dragging = False

last_mouse_x = 0
last_mouse_y = 0

# ============================================================
# PLAYER
# ============================================================

player = pygame.Rect(
    300,
    200,
    32,
    48
)

velocity_x = 0.0
velocity_y = 0.0

MOVE_SPEED = 5.0

# ============================================================
# FÍSICA
# ============================================================

GRAVITY = 0.65
MAX_FALL_SPEED = 16.0

JUMP_FORCE = -15.5

# Quanto o pulo é cortado ao soltar Z
JUMP_CUT = 0.45

on_ground = False

# ============================================================
# DIREÇÃO DO VEX
# ============================================================

facing_right = True

# ============================================================
# DASH
# ============================================================

dash_active = False
dash_timer = 0

DASH_SPEED = 16.0
DASH_TIME = 8

dash_direction = 1

# ============================================================
# ANIMAÇÃO
# ============================================================

idle_frames = []
run_frames = []

idle_frame = 0
run_frame = 0

idle_timer = 0
run_timer = 0

IDLE_SPEED = 0.12
RUN_SPEED = 0.08


# ============================================================
# CARREGAR GIF
# ============================================================

def load_gif(path, size):

    frames = []

    if not os.path.exists(path):

        print("GIF nao encontrado:", path)

        return frames

    try:

        gif = Image.open(path)

        for frame in ImageSequence.Iterator(gif):

            frame = frame.convert("RGBA")

            frame = frame.resize(
                size,
                Image.Resampling.NEAREST
            )

            frame_data = frame.tobytes()

            surface = pygame.image.fromstring(
                frame_data,
                size,
                "RGBA"
            ).convert_alpha()

            frames.append(surface)

        gif.close()

        print(
            "GIF carregado:",
            path,
            "| frames:",
            len(frames)
        )

    except Exception as error:

        print(
            "Erro ao carregar GIF:",
            path,
            error
        )

    return frames


# ============================================================
# CARREGAR SPRITES
# ============================================================

idle_frames = load_gif(
    os.path.join(
        "assets",
        "playeVexidle.gif"
    ),
    (32, 48)
)

run_frames = load_gif(
    os.path.join(
        "assets",
        "playeVexrun.gif"
    ),
    (32, 48)
)


# ============================================================
# MAPA
# ============================================================

MAP_FILE = "world.json"


def save_world():

    data = []

    for block in blocks:

        data.append({
            "x": block.x,
            "y": block.y,
            "w": block.width,
            "h": block.height
        })

    try:

        with open(
            MAP_FILE,
            "w",
            encoding="utf-8"
        ) as file:

            json.dump(
                data,
                file,
                indent=4
            )

        print("Mapa salvo!")

    except Exception as error:

        print("Erro ao salvar:", error)


def load_world():

    global blocks

    if not os.path.exists(MAP_FILE):

        print("world.json nao existe.")

        return

    try:

        with open(
            MAP_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(file)

        blocks.clear()

        for item in data:

            blocks.append(
                pygame.Rect(
                    item["x"],
                    item["y"],
                    item["w"],
                    item["h"]
                )
            )

        print("Mapa carregado!")

    except Exception as error:

        print("Erro ao carregar:", error)


# ============================================================
# PULO
# ============================================================

def jump():

    global velocity_y

    if on_ground:

        velocity_y = JUMP_FORCE


# ============================================================
# DASH
# ============================================================

def start_dash():

    global dash_active
    global dash_timer
    global dash_direction
    global velocity_y
    global facing_right

    if dash_active:

        return

    keyboard = pygame.key.get_pressed()

    if keyboard[pygame.K_LEFT]:

        dash_direction = -1

        facing_right = False

    elif keyboard[pygame.K_RIGHT]:

        dash_direction = 1

        facing_right = True

    dash_active = True

    dash_timer = DASH_TIME

    velocity_y = 0


# ============================================================
# MOVIMENTO E COLISÃO
# ============================================================

def move_player():

    global velocity_y
    global on_ground

    # ========================================================
    # HORIZONTAL
    # ========================================================

    player.x += round(velocity_x)

    for block in blocks:

        if player.colliderect(block):

            if velocity_x > 0:

                player.right = block.left

            elif velocity_x < 0:

                player.left = block.right

    # ========================================================
    # VERTICAL
    # ========================================================

    player.y += round(velocity_y)

    on_ground = False

    for block in blocks:

        if player.colliderect(block):

            # Caindo
            if velocity_y > 0:

                player.bottom = block.top

                velocity_y = 0

                on_ground = True

            # Subindo
            elif velocity_y < 0:

                player.top = block.bottom

                velocity_y = 0


# ============================================================
# UPDATE DO PLAYER
# ============================================================

def update_player():

    global velocity_x
    global velocity_y
    global dash_active
    global dash_timer
    global facing_right

    keyboard = pygame.key.get_pressed()

    # ========================================================
    # DASH
    # ========================================================

    if dash_active:

        velocity_x = DASH_SPEED * dash_direction

        velocity_y = 0

        dash_timer -= 1

        if dash_timer <= 0:

            dash_timer = 0

            dash_active = False

    else:

        # ====================================================
        # MOVIMENTO NORMAL
        # ====================================================

        velocity_x = 0

        if keyboard[pygame.K_LEFT]:

            velocity_x = -MOVE_SPEED

            facing_right = False

        elif keyboard[pygame.K_RIGHT]:

            velocity_x = MOVE_SPEED

            facing_right = True

        # ====================================================
        # GRAVIDADE
        # ====================================================

        velocity_y += GRAVITY

        if velocity_y > MAX_FALL_SPEED:

            velocity_y = MAX_FALL_SPEED

        # ====================================================
        # PULO VARIÁVEL
        # ====================================================

        if not keyboard[pygame.K_z] and velocity_y < 0:

            velocity_y *= JUMP_CUT

    # ========================================================
    # APLICAR MOVIMENTO
    # ========================================================

    move_player()


# ============================================================
# ANIMAÇÃO
# ============================================================

def update_animation():

    global idle_frame
    global run_frame

    global idle_timer
    global run_timer

    moving = abs(velocity_x) > 0.1

    # ========================================================
    # IDLE
    # ========================================================

    if not moving:

        run_frame = 0
        run_timer = 0

        if len(idle_frames) > 0:

            idle_timer += 1

            if idle_timer >= IDLE_SPEED * FPS:

                idle_timer = 0

                idle_frame += 1

                if idle_frame >= len(idle_frames):

                    idle_frame = 0

    # ========================================================
    # RUN
    # ========================================================

    else:

        idle_frame = 0
        idle_timer = 0

        if len(run_frames) > 0:

            run_timer += 1

            if run_timer >= RUN_SPEED * FPS:

                run_timer = 0

                run_frame += 1

                if run_frame >= len(run_frames):

                    run_frame = 0


# ============================================================
# DESENHAR VEX
# ============================================================

def draw_player():

    moving = abs(velocity_x) > 0.1

    sprite = None

    # ========================================================
    # RUN
    # ========================================================

    if moving and len(run_frames) > 0:

        sprite = run_frames[run_frame]

    # ========================================================
    # IDLE
    # ========================================================

    elif len(idle_frames) > 0:

        sprite = idle_frames[idle_frame]

    # ========================================================
    # FALLBACK
    # ========================================================

    if sprite is None:

        rect = pygame.Rect(
            player.x - int(camera_x),
            player.y - int(camera_y),
            player.width,
            player.height
        )

        pygame.draw.rect(
            screen,
            (240, 210, 45),
            rect
        )

        return

    # ========================================================
    # VIRAR VEX
    # ========================================================

    if not facing_right:

        sprite = pygame.transform.flip(
            sprite,
            True,
            False
        )

    # ========================================================
    # DESENHAR
    # ========================================================

    screen.blit(
        sprite,
        (
            player.x - int(camera_x),
            player.y - int(camera_y)
        )
    )


# ============================================================
# EDITOR
# ============================================================

def editor_update():

    mouse_x, mouse_y = pygame.mouse.get_pos()

    # ========================================================
    # TELA -> MUNDO
    # ========================================================

    world_x = mouse_x + camera_x
    world_y = mouse_y + camera_y

    # ========================================================
    # GRID
    # ========================================================

    grid_x = (
        world_x // TILE_SIZE
    ) * TILE_SIZE

    grid_y = (
        world_y // TILE_SIZE
    ) * TILE_SIZE

    mouse_buttons = pygame.mouse.get_pressed()

    # ========================================================
    # COLOCAR BLOCO
    # ========================================================

    if mouse_buttons[0]:

        new_block = pygame.Rect(
            grid_x,
            grid_y,
            TILE_SIZE,
            TILE_SIZE
        )

        if new_block not in blocks:

            blocks.append(new_block)

    # ========================================================
    # APAGAR BLOCO
    # ========================================================

    if mouse_buttons[2]:

        for block in blocks:

            if block.collidepoint(
                world_x,
                world_y
            ):

                blocks.remove(block)

                break


# ============================================================
# CÂMERA
# ============================================================

def update_camera():

    global camera_x
    global camera_y

    # ========================================================
    # EDITOR
    # ========================================================

    # No editor a câmera fica onde o usuário arrastou.
    if editor_mode:

        return

    # ========================================================
    # JOGO
    # ========================================================

    target_x = (
        player.centerx
        - WIDTH // 2
    )

    target_y = (
        player.centery
        - HEIGHT // 2
    )

    camera_x += (
        target_x - camera_x
    ) * 0.10

    camera_y += (
        target_y - camera_y
    ) * 0.10


# ============================================================
# GRID
# ============================================================

def draw_grid():

    start_x = -(
        int(camera_x) % TILE_SIZE
    )

    start_y = -(
        int(camera_y) % TILE_SIZE
    )

    # Verticais

    for x in range(
        start_x,
        WIDTH,
        TILE_SIZE
    ):

        pygame.draw.line(
            screen,
            GRID,
            (x, 0),
            (x, HEIGHT)
        )

    # Horizontais

    for y in range(
        start_y,
        HEIGHT,
        TILE_SIZE
    ):

        pygame.draw.line(
            screen,
            GRID,
            (0, y),
            (WIDTH, y)
        )


# ============================================================
# MUNDO
# ============================================================

def draw_world():

    for block in blocks:

        rect = pygame.Rect(
            block.x - int(camera_x),
            block.y - int(camera_y),
            block.width,
            block.height
        )

        pygame.draw.rect(
            screen,
            BLOCK_COLOR,
            rect
        )

        pygame.draw.rect(
            screen,
            BLOCK_BORDER,
            rect,
            2
        )


# ============================================================
# CURSOR DO EDITOR
# ============================================================

def draw_editor_cursor():

    mouse_x, mouse_y = pygame.mouse.get_pos()

    world_x = mouse_x + camera_x
    world_y = mouse_y + camera_y

    grid_x = (
        world_x // TILE_SIZE
    ) * TILE_SIZE

    grid_y = (
        world_y // TILE_SIZE
    ) * TILE_SIZE

    preview = pygame.Rect(
        grid_x - int(camera_x),
        grid_y - int(camera_y),
        TILE_SIZE,
        TILE_SIZE
    )

    pygame.draw.rect(
        screen,
        EDITOR_COLOR,
        preview,
        2
    )


# ============================================================
# UI
# ============================================================

def draw_ui():

    font = pygame.font.SysFont(
        "Arial",
        20
    )

    if editor_mode:

        message = (
            "EDITOR | H: jogar | "
            "S: salvar | L: carregar | "
            "LMB: bloco | RMB: apagar | "
            "MMB: arrastar camera"
        )

    else:

        message = (
            "JOGO | H: editor | "
            "Setas: mover | Z: pular | C: dash"
        )

    text = font.render(
        message,
        True,
        WHITE
    )

    screen.blit(
        text,
        (15, 15)
    )


# ============================================================
# LOOP PRINCIPAL
# ============================================================

running = True

while running:

    clock.tick(FPS)

    # ========================================================
    # EVENTOS
    # ========================================================

    for event in pygame.event.get():

        # ====================================================
        # FECHAR
        # ====================================================

        if event.type == pygame.QUIT:

            running = False

        # ====================================================
        # TECLAS
        # ====================================================

        if event.type == pygame.KEYDOWN:

            # ------------------------------------------------
            # Z = PULO
            # ------------------------------------------------

            if event.key == pygame.K_z:

                if not editor_mode:

                    jump()

            # ------------------------------------------------
            # C = DASH
            # ------------------------------------------------

            elif event.key == pygame.K_c:

                if not editor_mode:

                    start_dash()

            # ------------------------------------------------
            # H = EDITOR / JOGO
            # ------------------------------------------------

            elif event.key == pygame.K_h:

                editor_mode = not editor_mode

                if editor_mode:

                    velocity_x = 0
                    velocity_y = 0

                    dash_active = False
                    dash_timer = 0

                print(
                    "EDITOR"
                    if editor_mode
                    else "JOGO"
                )

            # ------------------------------------------------
            # S = SALVAR
            # ------------------------------------------------

            elif event.key == pygame.K_s:

                save_world()

            # ------------------------------------------------
            # L = CARREGAR
            # ------------------------------------------------

            elif event.key == pygame.K_l:

                load_world()

        # ====================================================
        # BOTÃO DO MOUSE PRESSIONADO
        # ====================================================

        if event.type == pygame.MOUSEBUTTONDOWN:

            # Botão do meio / scroll
            if event.button == 2 and editor_mode:

                camera_dragging = True

                last_mouse_x = event.pos[0]
                last_mouse_y = event.pos[1]

        # ====================================================
        # BOTÃO DO MOUSE SOLTO
        # ====================================================

        if event.type == pygame.MOUSEBUTTONUP:

            if event.button == 2:

                camera_dragging = False

        # ====================================================
        # MOUSE SE MOVENDO
        # ====================================================

        if event.type == pygame.MOUSEMOTION:

            if camera_dragging and editor_mode:

                mouse_x = event.pos[0]
                mouse_y = event.pos[1]

                dx = mouse_x - last_mouse_x
                dy = mouse_y - last_mouse_y

                camera_x -= dx
                camera_y -= dy

                last_mouse_x = mouse_x
                last_mouse_y = mouse_y

    # ========================================================
    # UPDATE
    # ========================================================

    if editor_mode:

        editor_update()

    else:

        update_player()

        update_animation()

    # ========================================================
    # CÂMERA
    # ========================================================

    update_camera()

    # ========================================================
    # RENDER
    # ========================================================

    screen.fill(BG)

    draw_grid()

    draw_world()

    if editor_mode:

        draw_editor_cursor()

    else:

        draw_player()

    draw_ui()

    pygame.display.flip()


pygame.quit()