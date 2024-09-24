import pygame  # type: ignore
import sys
import random
import math
import time
import os

from scripts.utils import load_image, load_images, Animation
from scripts.entities import PhysicsEntity, Player, Enemy, Destroyable
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark


class Game:
    def __init__(self, is_test=0):
        pygame.init()

        pygame.display.set_caption("ninja game")
        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((320, 240), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((320, 240))

        self.clock = pygame.time.Clock()

        self.movement = [False, False]

        self.assets = {
            "colliders": load_images("tiles/colliders"),
            "decor": load_images("tiles/decor"),
            "grass": load_images("tiles/grass"),
            "large_decor": load_images("tiles/large_decor"),
            "stone": load_images("tiles/stone"),
            "water": load_images("tiles/water"),
            "ice": load_images("tiles/ice"),
            "player": load_image("entities/player.png"),
            "spawners": load_images("tiles/spawners"),
            "destroyable": load_image("entities/destroyable.png"),
            "backgrounds": load_images("backgrounds"),
            "clouds": load_images("clouds"),
            "destroyable/idle": Animation(
                load_images("entities/destroyable/idle"), img_dur=6
            ),
            "destroyable/destroy": Animation(
                load_images("entities/destroyable/destroy"), img_dur=6
            ),
            "enemy/idle": Animation(load_images("entities/enemy/idle"), img_dur=6),
            "enemy/run": Animation(load_images("entities/enemy/run"), img_dur=4),
            "player/idle": Animation(load_images("entities/player/idle"), img_dur=6),
            "player/run": Animation(load_images("entities/player/run"), img_dur=4),
            "player/jump": Animation(
                load_images("entities/player/jump"), img_dur=4, loop=False
            ),
            "player/slide": Animation(load_images("entities/player/slide")),
            "player/wall_slide": Animation(load_images("entities/player/wall_slide")),
            "player/deflect": Animation(load_images("entities/player/deflect")),
            "player/powJump": Animation(load_images("entities/player/powJump")),
            "player/attack": Animation(
                load_images("entities/player/attack"), img_dur=1, loop=False
            ),
            "player/push": Animation(
                load_images("entities/player/push"), img_dur=4, loop=True
            ),
            "particle/leaf": Animation(
                load_images("particles/leaf"), img_dur=20, loop=False
            ),
            "particle/particle": Animation(
                load_images("particles/particle"), img_dur=6, loop=False
            ),
            "gun": load_image("gun.png"),
            "projectile": load_image("projectile.png"),
            "def_projectile": load_image("def_projectile.png"),
        }

        self.sfx = {
            "jump": pygame.mixer.Sound("data/sfx/jump.wav"),
            "dash": pygame.mixer.Sound("data/sfx/dash.wav"),
            "hit": pygame.mixer.Sound("data/sfx/hit.wav"),
            "shoot": pygame.mixer.Sound("data/sfx/shoot.wav"),
            "ambience": pygame.mixer.Sound("data/sfx/ambience.wav"),
            "slash": pygame.mixer.Sound("data/sfx/slash.mp3"),
            "parry": pygame.mixer.Sound("data/sfx/parry.mp3"),
        }

        self.sfx["jump"].set_volume(0.4)
        self.sfx["ambience"].set_volume(0.2)
        self.sfx["dash"].set_volume(0.4)
        self.sfx["hit"].set_volume(0.8)
        self.sfx["shoot"].set_volume(0.3)
        self.sfx["ambience"].set_volume(0.7)
        self.sfx["slash"].set_volume(0.4)
        self.sfx["parry"].set_volume(0.4)

        self.clouds = Clouds(self.assets["clouds"], count=16)

        self.player = Player(self, (50, 50), (8, 15))

        self.tilemap = Tilemap(self, tile_size=16)

        self.level = is_test
        self.is_test = is_test
        self.load_level(self.level)
        self.screenshake = 0
        self.has_paried = 0

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
        print(str(self.background))
        print("LEVEL LOADED: data/maps/" + str(map_id) + ".json")

        self.leaf_spawners = []
        for tree in self.tilemap.extract([("large_decor", 2)], keep=True):
            self.leaf_spawners.append(
                pygame.Rect(4 + tree["pos"][0], 4 + tree["pos"][1], 23, 13)
            )

        self.enemies = []
        self.destroyable = []

        for spawner in self.tilemap.extract(
            [("spawners", 0), ("spawners", 1), ("spawners", 2)]
        ):
            if spawner["variant"] == 0:
                self.player.pos = spawner["pos"]
                self.player.air_time = 0
            elif spawner["variant"] == 1:
                self.enemies.append(Enemy(self, spawner["pos"], (8, 15)))
            else:
                self.destroyable.append(Destroyable(self, spawner["pos"], (8, 15)))

        self.projectiles = []
        self.particles = []
        self.sparks = []

        self.scroll = [0, 0]
        self.dead = 0
        self.transition = -30
        self.bg = self.assets["backgrounds"][self.background].copy()
        self.timer = 0

    def run(self):
        pygame.mixer.music.load("data/music.wav")
        pygame.mixer.music.set_volume(0.5)
        pygame.mixer.music.play(-1)

        self.sfx["ambience"].play(-1)

        running = 1
        while running:
            self.display.fill((0, 0, 0, 0))
            self.display_2.blit(self.bg, (0, 0))

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
                self.dead += 1
                if self.dead >= 10:
                    self.transition = min(30, self.transition + 1)
                if self.dead > 40:
                    self.load_level(self.level)

            self.scroll[0] += (
                self.player.rect().centerx
                - self.display.get_width() / 2
                - self.scroll[0]
            ) / 20
            self.scroll[1] += (
                self.player.rect().centery
                - self.display.get_height() / 2
                - self.scroll[1]
            ) / 20
            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

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

            self.tilemap.render(self.display, offset=self.scroll)

            for dstr in self.destroyable.copy():
                kill = dstr.update(self.tilemap, (0, 0))
                dstr.render(self.display, offset=render_scroll)
                if kill:
                    self.destroyable.remove(dstr)
            for enemy in self.enemies.copy():
                kill = enemy.update(self.tilemap, (0, 0))
                enemy.render(self.display, offset=render_scroll)
                if kill:
                    self.enemies.remove(enemy)

            if not self.dead:
                self.player.update(
                    self.tilemap, (self.movement[1] - self.movement[0], 0)
                )
                self.player.render(self.display, offset=render_scroll)

            # [x,y], direction, timer, is_redirected]
            for projectile in self.projectiles.copy():
                removed = 0
                projectile[0][0] += projectile[1] * 1.5
                projectile[2] += 1
                if self.tilemap.solid_check(projectile[0]):
                    removed = 1
                    for i in range(4):
                        self.sparks.append(
                            Spark(
                                projectile[0],
                                random.random()
                                - 0.5
                                + (math.pi if projectile[1] > 0 else 0),
                                2 + random.random(),
                            )
                        )

                elif projectile[2] > 360:
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

                    if self.player.attacking >= 10:
                        self.player.pos = projectile[0]
                        self.player.attacking = 10
                    else:
                        for enemy in self.enemies:
                            if enemy.rect().collidepoint(projectile[0]):
                                removed = 1
                                enemy.alive = 0
                elif abs(self.player.dashing) < 50 and self.player.attacking != 10:
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
                else:
                    img = self.assets[
                        "def_projectile" if projectile[3] else "projectile"
                    ]
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
            display_silhouette = display_mask.to_surface(
                setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0)
            )
            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.display_2.blit(display_silhouette, offset)
            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type == "leaf":
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if kill:
                    self.particles.remove(particle)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if self.dead:
                    break
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.player.attack()
                    if event.key == pygame.K_a or event.key == pygame.K_d:
                        is_left = event.key == pygame.K_a
                        if self.player.attack():
                            self.player.flip = is_left
                            self.player.pos[0] += -1 if is_left else 1

                    if event.key == pygame.K_q:
                        running = 0
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = True
                    if event.key == pygame.K_RIGHT:
                        self.movement[1] = True
                    if event.key == pygame.K_UP:
                        if self.player.jump():
                            self.sfx["jump"].play()
                    if event.key == pygame.K_DOWN:
                        if self.player.action == "jump":
                            self.player.power_jump()
                    if event.key == pygame.K_x:
                        self.player.dash()
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_LEFT:
                        self.movement[0] = False
                    if event.key == pygame.K_RIGHT:
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
            screenshake_offset = (
                random.random() * self.screenshake - self.screenshake / 2
            )
            self.display_2.blit(self.display, (0, 0))

            self.screen.blit(
                pygame.transform.scale(self.display_2, self.screen.get_size()),
                (screenshake_offset, screenshake_offset),
            )
            pygame.display.update()
            self.clock.tick(60)
        pygame.mixer.stop()
        pygame.mixer.music.stop()


def auto_run():
    Game().run()


if __name__ == "__main__":
    auto_run()
