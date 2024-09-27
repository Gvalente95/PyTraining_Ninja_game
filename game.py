import pygame  # type: ignore
import sys
import random
import math
import time
import os

from scripts.utils import load_image, load_images, display_msg, Animation, keys, colors
from scripts.entities import Player, Enemy, Box, Bird, Mob, Demo
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds, Cloud
from scripts.particle import Particle
from scripts.spark import Spark

scrn_mult = 2
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480


class Game:
    def __init__(self, is_test=0):
        pygame.init()

        pygame.display.set_caption("ninja game")
        if is_test:
            SCREEN_WIDTH, SCREEN_HEIGHT = pygame.display.get_surface().get_size()
        if is_test != -1:
            scr_w, scr_h = pygame.display.get_surface().get_size()
        else:
            scr_w = SCREEN_WIDTH
            scr_h = SCREEN_HEIGHT
        self.screen = pygame.display.set_mode((scr_w, scr_h), pygame.RESIZABLE)
        self.display = pygame.Surface((scr_w / 2, scr_h / 2), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((scr_w / 2, scr_h / 2))

        self.clock = pygame.time.Clock()

        self.movement = [False, False]

        self.assets = {
            "colliders": load_images("tiles/colliders"),
            "decor": load_images("tiles/decor"),
            "grass": load_images("tiles/grass"),
            "herb": load_images("tiles/herb"),
            "large_decor": load_images("tiles/large_decor"),
            "stone": load_images("tiles/stone"),
            "water": load_images("tiles/water"),
            "ice": load_images("tiles/ice"),
            "player": load_image("entities/player.png"),
            "demo": load_images("tiles/demo"),
            "spawners": load_images("tiles/spawners", color_key=(255, 255, 255)),
            "box": load_image("entities/box.png"),
            "backgrounds": load_images("backgrounds"),
            "clouds": load_images("clouds"),
            "demo_surf/idle": Animation(load_images("demo/surf/idle"), img_dur=6),
            "demo_hold/idle": Animation(load_images("demo/hold/idle"), img_dur=6),
            "box/idle": Animation(load_images("entities/box/idle"), img_dur=6),
            "box/destroy": Animation(load_images("entities/box/destroy"), img_dur=6),
            "enemy/idle": Animation(load_images("entities/enemy/idle"), img_dur=6),
            "enemy/run": Animation(load_images("entities/enemy/run"), img_dur=4),
            "player/idle": Animation(load_images("entities/player/idle"), img_dur=6),
            "player/hold": Animation(load_images("entities/player/hold"), img_dur=6),
            "player/run": Animation(load_images("entities/player/run"), img_dur=4),
            "player/jump": Animation(load_images("entities/player/jump"), img_dur=4, loop=False),
            "player/slide": Animation(load_images("entities/player/slide")),
            "player/wall_slide": Animation(load_images("entities/player/wall_slide")),
            "player/deflect": Animation(load_images("entities/player/deflect")),
            "player/powJump": Animation(load_images("entities/player/powJump")),
            "player/attack": Animation(load_images("entities/player/attack"), img_dur=1, loop=False),
            "player/swim": Animation(load_images("entities/player/swim"), img_dur=4),
            "player/push": Animation(load_images("entities/player/push"), img_dur=4, loop=True),
            "particle/leaf": Animation(load_images("particles/leaf"), img_dur=20, loop=False),
            "particle/particle": Animation(load_images("particles/particle"), img_dur=6, loop=False),
            "gun": load_image("gun.png"),
            "projectile": load_image("projectile.png"),
            "def_projectile": load_image("def_projectile.png"),
            "bird/fly": Animation(load_images("entities/bird/fly"), img_dur=1),
            "bird/fly_b": Animation(load_images("entities/bird/fly_b"), img_dur=1),
            "bird/idle": Animation(load_images("entities/bird/idle")),
            "mob/idle": Animation(load_images("entities/mob/idle", color_key=(20, 20, 20))),
            "mob/run": Animation(load_images("entities/mob/run", color_key=(20, 20, 20))),
        }
        time.sleep(1)

        self.sfx = {
            "jump": pygame.mixer.Sound("data/sfx/jump.wav"),
            "dash": pygame.mixer.Sound("data/sfx/dash.wav"),
            "hit": pygame.mixer.Sound("data/sfx/hit.wav"),
            "clonk": pygame.mixer.Sound("data/sfx/clonk.wav"),
            "shoot": pygame.mixer.Sound("data/sfx/shoot.wav"),
            "wind": pygame.mixer.Sound("data/sfx/wind.wav"),
            "ambience": pygame.mixer.Sound("data/sfx/ambience.wav"),
            "slash": pygame.mixer.Sound("data/sfx/slash.mp3"),
            "parry": pygame.mixer.Sound("data/sfx/parry.mp3"),
            "flight": pygame.mixer.Sound("data/sfx/flight.wav"),
            "thump": pygame.mixer.Sound("data/sfx/thump.mp3"),
        }
        self.flight_sfx_pool = [pygame.mixer.Sound("data/sfx/flight.wav") for _ in range(200)]  # Create a pool of sounds

        self.sfx["clonk"].set_volume(1)
        self.sfx["jump"].set_volume(0.4)
        self.sfx["wind"].set_volume(0.4)
        self.sfx["ambience"].set_volume(0.2)
        self.sfx["dash"].set_volume(0.4)
        self.sfx["hit"].set_volume(0.8)
        self.sfx["shoot"].set_volume(0.3)
        self.sfx["ambience"].set_volume(0.7)
        self.sfx["slash"].set_volume(0.4)
        self.sfx["parry"].set_volume(0.4)
        self.sfx["flight"].set_volume(0.4)
        self.sfx["thump"].set_volume(5)

        self.player = Player(self, (50, 50), (8, 15))

        self.tilemap = Tilemap(self, tile_size=16)

        self.level = is_test
        self.is_test = is_test
        self.input = 0
        self.last_input = 0
        self.last_pressed_input = 0
        self.screenshake = 0
        self.has_paried = 0
        self.shift = 0
        self.player.alive = 1
        self.fly_audio_index = 0
        self.menu = 0
        self.load_level(self.level)
        self.clouds = Clouds(self.tilemap, self.assets["clouds"])

    def load_level(self, map_id):
        self.movement[0] = 0
        self.movement[1] = 0
        label = "MAP TEST" if self.is_test else "ninja game Lv" + str(map_id)
        pygame.display.set_caption(label)
        self.background = 0

        if self.is_test == -1:
            self.background = self.tilemap.load("map.json")
        else:
            self.background = self.tilemap.load("data/maps/" + str(map_id) + ".json")
        print("LEVEL LOADED: data/maps/" + str(map_id) + ".json")

        self.leaf_spawners = []
        for tree in self.tilemap.extract([("large_decor", 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree["pos"][0], 4 + tree["pos"][1], 23, 13))

        self.birds = []
        self.mobs = []
        self.enemies = []
        self.boxes = []
        self.demo_boards = []

        for spawner in self.tilemap.extract(
            [
                ("spawners", 0),
                ("spawners", 1),
                ("spawners", 2),
                ("spawners", 3),
                ("spawners", 4),
            ]
        ):
            if spawner["variant"] == 0:
                self.player.pos = spawner["pos"]
                self.player.air_time = 0
            elif spawner["variant"] == 1:
                self.enemies.append(Enemy(self, spawner["pos"], (8, 15)))
            elif spawner["variant"] == 2:
                self.boxes.append(Box(self, spawner["pos"], (10, 10)))
            elif spawner["variant"] == 3:
                self.birds.append(Bird(self, spawner["pos"], (18, 12), index=self.fly_audio_index))
                self.fly_audio_index = self.fly_audio_index + 1
                if self.fly_audio_index > len(self.flight_sfx_pool) - 1:
                    self.fly_audio_index = 0
            elif spawner["variant"] == 4:
                self.mobs.append(Mob(self, spawner["pos"], (20, 16)))

        for demo in self.tilemap.extract(
            [
                ("demo", 0),
                ("demo", 1),
            ]
        ):
            self.demo_boards.append(Demo(self, demo["pos"], (20, 16)))

        self.projectiles = []
        self.particles = []
        self.sparks = []
        self.scroll = [0, 0]
        self.dead = 0
        self.transition = -30
        self.bg = self.assets["backgrounds"][self.background].copy().convert_alpha()
        self.timer = 0

    def run(self):
        pygame.mixer.music.load("data/music.wav")
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)

        self.sfx["ambience"].play(-1)

        running = 1
        while running:

            self.display.fill((0, 0, 0, 0))
            SCREEN_WIDTH, SCREEN_HEIGHT = self.display_2.get_size()

            self.display_2.blit(pygame.transform.scale(self.bg, (SCREEN_WIDTH, SCREEN_HEIGHT)), (0, 0))

            self.player.pushing = 0

            self.screenshake = max(0, self.screenshake - 1)

            if not len(self.enemies):
                self.transition += 1
                if self.transition > 30:
                    self.level = min(self.level + 1, len(os.listdir("data/maps")) - 1)
                    self.load_level(self.level)
            if self.transition < 0:
                self.transition += 1

            if self.has_paried:
                time.sleep(0.2)
                self.has_paried = 0

            if self.dead:
                self.player.is_holding = 0
                self.player.bul_surf = 0
                self.player.is_swiming = 0
                self.dead += 1
                if self.dead >= 10:
                    self.transition = min(30, self.transition + 1)
                if self.dead > 40:
                    self.load_level(self.level)

            self.scroll[0] += (self.player.rect().centerx - self.display.get_width() / 2 - self.scroll[0]) / 20
            self.scroll[1] += (self.player.rect().centery - self.display.get_height() / 2 - self.scroll[1]) / 20
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            for demo in self.demo_boards:
                demo.update(self.tilemap, (0, 0))
                demo.render(self.display, offset=render_scroll)

            for rect in self.leaf_spawners:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (
                        rect.x + random.random() * rect.width,
                        rect.y + random.random() * rect.height,
                    )
                    self.particles.append(
                        Particle(
                            self,
                            "leaf",
                            pos,
                            velocity=[-0, 1, 0.3],
                            frame=random.randint(0, 20),
                        )
                    )

            self.clouds.update()
            self.clouds.render(self.display_2, offset=render_scroll)

            self.tilemap.render(self.display, offset=self.scroll, include="all", exclude="herb")

            x = 0
            for dstr in self.boxes.copy():
                x += 1
                kill = dstr.update(self.tilemap, (0, 0))
                dstr.render(self.display, offset=render_scroll)
                if kill:
                    self.boxes.remove(dstr)
            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, offset=render_scroll)
                if kill:
                    self.enemies.remove(enemy)

            if not self.dead:
                if self.shift > 0:
                    self.shift = min(self.shift + 0.3, 2.5)
                mov_x = self.movement[0] * max(self.shift, 1)
                mov_y = self.movement[1] * max(self.shift, 1)

                self.player.update(self.tilemap, (mov_y - mov_x, 0))
                self.player.render(self.display, offset=(render_scroll[0], render_scroll[1] - 1))

            # [x,y], direction, timer, is_redirected]
            for projectile in self.projectiles.copy():
                removed = 0
                is_surf_proj = projectile[3] and self.player.bul_surf
                projectile[0][0] += projectile[1] * 1.5
                projectile[2] += 1
                if self.tilemap.solid_check(projectile[0]):
                    removed = 1
                    for i in range(4):
                        self.sparks.append(
                            Spark(
                                projectile[0],
                                random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0),
                                2 + random.random(),
                            )
                        )

                elif projectile[2] > 360 and not is_surf_proj:
                    removed = 1
                elif projectile[3] > 0:
                    for i in range(2):
                        angle = random.random() * math.pi * 2
                        speed = random.random() * 0.5 + 0.5
                        pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                        self.particles.append(
                            Particle(
                                self,
                                "particle",
                                (projectile[0][0], projectile[0][1]),
                                velocity=pvelocity,
                                frame=random.randint(0, 7),
                            )
                        )
                    if self.player.deflecting:
                        self.player.bul_surf += 1
                        projectile[2] = 0
                    if self.player.bul_surf:
                        if self.input != 0 and self.input != keys["surf"]:
                            self.player.bul_surf = 0
                            removed = 1
                        else:
                            end_pos = (projectile[0][0], projectile[0][1] - 15)
                            if abs(self.player.pos[0] - projectile[0][0]) > 5:
                                self.player.pos[0] -= (self.player.pos[0] - end_pos[0]) * 0.2
                                self.player.pos[1] -= (self.player.pos[1] - end_pos[1]) * 0.2

                                self.particles.append(Particle(self, "particle", self.player.rect().center, velocity=(0.3, 0.3), frame=random.randint(0, 7)))
                                self.player.is_swiming = 1

                                if abs(self.player.pos[0] - projectile[0][0]) < 15:
                                    self.player.pos = list(projectile[0])
                                    self.player.pos[0] = projectile[0][0]
                                    self.player.pos[1] = projectile[0][1] - 15
                            else:
                                self.player.is_swiming = 0
                                self.player.pos = list(projectile[0])
                                self.player.pos[0] = projectile[0][0]
                                self.player.pos[1] = projectile[0][1] - 15

                            self.player.attacking = 0
                            self.player.bul_surf += 1
                    else:
                        for enemy in self.enemies:
                            if enemy.rect().collidepoint(projectile[0]):
                                removed = 1
                                enemy.alive = 0
                elif abs(self.player.dashing) < 50 and self.player.bul_surf < 11 and self.player.attacking != 10:
                    if self.player.rect().collidepoint(projectile[0]):
                        if self.player.attacking:
                            projectile[1] *= -1
                            projectile[0][0] += 5
                            self.sfx["parry"].play()
                            self.has_paried = 1
                            projectile[3] = 1
                        else:
                            self.sfx["hit"].play()
                            removed = 1
                            self.dead += 1
                            self.screenshake = max(16, self.screenshake)
                        for i in range(5 if projectile[3] else 30):
                            angle = random.random() * math.pi * 2
                            speed = random.random() * 5
                            self.sparks.append(
                                Spark(
                                    self.player.rect().center,
                                    angle,
                                    2 + random.random(),
                                )
                            )
                            self.particles.append(
                                Particle(
                                    self,
                                    "particle",
                                    projectile[0],
                                    velocity=[
                                        math.cos(angle + math.pi) * speed * 0.5,
                                        math.sin(angle + math.pi) * speed * 0.5,
                                    ],
                                    frame=random.randint(0, 7),
                                )
                            )
                if removed:
                    self.projectiles.remove(projectile)
                    if projectile == self.player.pos and self.player.bul_surf > 10:
                        self.player.bul_surf = 0

                else:
                    img = self.assets["def_projectile" if projectile[3] else "projectile"]
                    self.display.blit(
                        img,
                        (
                            projectile[0][0] - img.get_width() / 2 - render_scroll[0],
                            projectile[0][1] - img.get_height() / 2 - render_scroll[1],
                        ),
                    )

            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)

            display_mask = pygame.mask.from_surface(self.display)
            display_silhouette = display_mask.to_surface(setcolor=(0, 0, 0, 80), unsetcolor=(0, 0, 0, 0))

            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.display_2.blit(display_silhouette, offset)
            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type == "leaf":
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if kill:
                    self.particles.remove(particle)

            self.player.deflecting = 0
            self.player.bul_surf = max(self.player.bul_surf - 1, 0)
            self.tilemap.render(self.display, offset=self.scroll, include="herb", exclude="all")

            for event in pygame.event.get():
                pressed = pygame.key.get_pressed()
                self.last_pressed_input = 0

                for action, key in keys.items():
                    if pressed[key]:
                        self.last_pressed_input = key
                        break
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    self.last_input = self.input
                    self.last_pressed_input = self.last_input
                    self.input = event.key

                    if event.key == keys["quit"]:
                        running = 0
                    if self.dead:
                        break
                    if event.key == keys["attack"]:
                        self.player.attack()

                    if event.key == pygame.K_LSHIFT:
                        self.shift = 0.1
                    if event.key == keys["surf"]:
                        self.player.deflecting = 1
                    if event.key == keys["menu"]:
                        self.menu = not self.menu
                    if event.key == keys["mv_left"]:
                        self.movement[0] = True
                    if event.key == keys["mv_right"]:
                        self.movement[1] = True
                    if event.key == keys["jump"]:
                        if self.player.jump():
                            self.sfx["jump"].play()
                    if event.key == keys["mv_down"]:
                        if self.player.action == "jump":
                            self.player.power_jump()
                    if event.key == keys["dash"]:
                        self.player.dash()
                if event.type == pygame.VIDEORESIZE:
                    SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h
                    self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                    self.display = pygame.Surface((SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2), pygame.SRCALPHA)
                    self.display_2 = pygame.Surface((SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))
                if self.dead:
                    break
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LSHIFT:
                        self.shift = 0
                    if event.key == keys["mv_left"]:
                        self.movement[0] = False
                    if event.key == keys["mv_right"]:
                        self.movement[1] = False

            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(
                    transition_surf,
                    (255, 255, 255),
                    (
                        self.display.get_width() // 2,
                        self.display.get_height() // 2,
                    ),
                    (30 - abs(self.transition)) * 8,
                )
                transition_surf.set_colorkey((255, 255, 255))
                self.display.blit(transition_surf, (0, 0))
            screenshake_offset = random.random() * self.screenshake - self.screenshake / 2
            self.display_2.blit(self.display, (0, 0))

            for bird in self.birds.copy():
                kill = bird.update(self.tilemap, (0, 0))
                bird.render(self.display_2, offset=render_scroll)
                if kill:
                    self.birds.remove(bird)

            for mob in self.mobs.copy():
                kill = mob.update(self.tilemap, (0, 0))
                mob.render(self.display_2, offset=render_scroll)

            self.screen.blit(
                pygame.transform.scale(self.display_2, self.screen.get_size()),
                (screenshake_offset, screenshake_offset),
            )
            pygame.display.update()
            self.clock.tick(60)
            if self.menu:
                in_menu(self)
            self.menu = 0

        pygame.mixer.stop()
        pygame.mixer.music.stop()


def in_menu(self):
    run = 1

    self.sfx["ambience"].stop()
    width = 640 - (640 / 3)
    height = 480 - (480 / 3)

    menu_display = pygame.Surface((width, height), pygame.SRCALPHA)
    menu_display.fill(colors["DARK_GRAY"])

    button_rect = pygame.Rect(50, 50, 100, 50)
    pygame.draw.rect(menu_display, colors["RED"], button_rect)

    center_x = (640 - width) / 2
    center_y = (480 - height) / 2

    while run:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == keys["quit"]:
                    run = 0
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                if button_rect.collidepoint(mouse_x - center_x, mouse_y - center_y):
                    print("Button clicked!")

        self.screen.blit(pygame.transform.scale(menu_display, menu_display.get_size()), (center_x, center_y))
        pygame.display.update()

    self.sfx["ambience"].play()


def play_music(file_name):
    pygame.mixer.music.load("data/" + file_name)
    pygame.mixer.music.set_volume(0.5)
    pygame.mixer.music.play(-1)


def auto_run():
    Game().run()


if __name__ == "__main__":
    auto_run()
