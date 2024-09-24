import pygame  # type: ignore
import sys
import os

from scripts.utils import load_images
from scripts.tilemap import Tilemap
from game import Game

RENDER_SCALE = 2.0


class Editor:
    def __init__(self):
        pygame.init()

        self.font = pygame.font.Font(None, 20)

        pygame.display.set_caption("editor: -1")
        self.screen = pygame.display.set_mode((640, 480))
        self.display = pygame.Surface((320, 240))

        self.clock = pygame.time.Clock()

        self.assets = {
            "colliders": load_images("tiles/colliders"),
            "decor": load_images("tiles/decor"),
            "grass": load_images("tiles/grass"),
            "large_decor": load_images("tiles/large_decor"),
            "stone": load_images("tiles/stone"),
            "spawners": load_images("tiles/spawners"),
            "water": load_images("tiles/water"),
            "ice": load_images("tiles/ice"),
        }
        self.backgrounds = load_images("backgrounds")

        self.movement = [False, False, False, False]
        self.speed = 2
        self.level = -1

        self.tilemap = Tilemap(self, tile_size=16)

        try:
            self.tilemap.load("map.json")
        except FileNotFoundError:
            print("map not found")
            pass

        self.scroll = [0, 0]

        self.tile_list = list(self.assets)
        self.tile_group = 0
        self.tile_variant = 0

        self.clicking = False
        self.right_clicking = False
        self.shift = False
        self.ongrid = True
        self.copying = False
        self.background_scroll = 0

        self.minimap_scale = 0.4
        self.minimap_size = (
            int(320 * self.minimap_scale),
            int(240 * self.minimap_scale),
        )
        self.minimap_surface = pygame.Surface(self.minimap_size)

    def draw_minimap(self):
        self.minimap_surface.fill((50, 50, 50))
        self.minimap_surface.set_alpha(200)
        self.tilemap.render_whole(
            self.minimap_surface, scale=self.minimap_scale, offset=self.scroll
        )
        minimap_x = self.screen.get_width() - self.minimap_size[0] - 10
        minimap_y = self.screen.get_height() - self.minimap_size[1] - 10
        self.screen.blit(self.minimap_surface, (minimap_x, minimap_y))

    def run(self):
        while True:

            if self.shift:
                self.speed = max(self.speed + 0.05, 4)
            else:
                self.speed = 2
            self.display.fill((0, 0, 0))
            self.display.blit(self.backgrounds[self.background_scroll], (0, 0))
            self.scroll[0] += (self.movement[1] - self.movement[0]) * self.speed
            self.scroll[1] += (self.movement[3] - self.movement[2]) * self.speed

            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.tilemap.render(self.display, offset=render_scroll)

            current_tile_img = self.assets[self.tile_list[self.tile_group]][
                self.tile_variant
            ].copy()
            current_tile_img.set_alpha(150)

            mpos = pygame.mouse.get_pos()
            mpos = (mpos[0] / RENDER_SCALE, mpos[1] / RENDER_SCALE)

            tile_pos = (
                int((mpos[0] + self.scroll[0]) // self.tilemap.tile_size),
                int((mpos[1] + self.scroll[1]) // self.tilemap.tile_size),
            )
            if self.ongrid:
                self.display.blit(
                    current_tile_img,
                    (
                        tile_pos[0] * self.tilemap.tile_size - self.scroll[0],
                        tile_pos[1] * self.tilemap.tile_size - self.scroll[1],
                    ),
                )
            else:
                self.display.blit(current_tile_img, mpos)

            if self.clicking and self.ongrid:
                self.tilemap.tilemap[str(tile_pos[0]) + ";" + str(tile_pos[1])] = {
                    "type": self.tile_list[self.tile_group],
                    "variant": self.tile_variant,
                    "pos": tile_pos,
                }
            if self.right_clicking:
                tile_loc = str(tile_pos[0]) + ";" + str(tile_pos[1])
                if tile_loc in self.tilemap.tilemap:
                    del self.tilemap.tilemap[tile_loc]
                for tile in self.tilemap.offgrid_tiles.copy():
                    tile_img = self.assets[tile["type"]][tile["variant"]]
                    tile_r = pygame.Rect(
                        tile["pos"][0] - self.scroll[0],
                        tile["pos"][1] - self.scroll[1],
                        tile_img.get_width(),
                        tile_img.get_height(),
                    )
                    if tile_r.collidepoint(mpos):
                        self.tilemap.offgrid_tiles.remove(tile)

            if self.copying:
                tile_loc = str(tile_pos[0]) + ";" + str(tile_pos[1])
                selected_tile = None
                if tile_loc in self.tilemap.tilemap:
                    selected_tile = self.tilemap.tilemap[tile_loc]
                if not selected_tile:
                    for tile in self.tilemap.offgrid_tiles:
                        tile_img = self.assets[tile["type"]][tile["variant"]]
                        tile_r = pygame.Rect(
                            tile["pos"][0] - self.scroll[0],
                            tile["pos"][1] - self.scroll[1],
                            tile_img.get_width(),
                            tile_img.get_height(),
                        )
                        if tile_r.collidepoint(mpos):
                            selected_tile = tile
                            break
                if selected_tile:
                    self.tile_group = self.tile_list.index(selected_tile["type"])
                    self.tile_variant = selected_tile["variant"]
                    self.copying = False

            self.display.blit(current_tile_img, (5, 5))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.clicking = True
                        if not self.ongrid:
                            self.tilemap.offgrid_tiles.append(
                                {
                                    "type": self.tile_list[self.tile_group],
                                    "variant": self.tile_variant,
                                    "pos": (
                                        mpos[0] + self.scroll[0],
                                        mpos[1] + self.scroll[1],
                                    ),
                                }
                            )
                    if event.button == 3:
                        self.right_clicking = True
                    if self.shift:
                        if event.button == 4:
                            self.tile_variant = (self.tile_variant - 1) % len(
                                self.assets[self.tile_list[self.tile_group]]
                            )
                        if event.button == 5:
                            self.tile_variant = (self.tile_variant + 1) % len(
                                self.assets[self.tile_list[self.tile_group]]
                            )
                    else:
                        if event.button == 4:
                            self.tile_group = (self.tile_group - 1) % len(
                                self.tile_list
                            )
                            self.tile_variant = 0
                        if event.button == 5:
                            self.tile_group = (self.tile_group + 1) % len(
                                self.tile_list
                            )
                            self.tile_variant = 0
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False
                    if event.button == 3:
                        self.right_clicking = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_LEFT:
                        self.background_scroll -= 1
                        if self.background_scroll < 0:
                            self.background_scroll = len(self.backgrounds) - 1
                    if event.key == pygame.K_RIGHT:
                        self.background_scroll += 1
                        if self.background_scroll > len(self.backgrounds) - 1:
                            self.background_scroll = 0
                    if event.key == pygame.K_q:
                        pygame.quit()
                        sys.exit()
                    if event.key == pygame.K_UP or event.key == pygame.K_DOWN:
                        self.level += 1 if event.key == pygame.K_UP else -1
                        if self.level > len(os.listdir("data/maps")) - 1:
                            self.level = -1
                        if self.level < -1:
                            self.level = len(os.listdir("data/maps")) - 1
                        if self.level == -1:
                            self.tilemap.load("map.json")
                            pygame.display.set_caption("editor: map.json")
                        else:
                            try:
                                self.tilemap.load(
                                    "data/maps/" + str(self.level) + ".json"
                                )
                                pygame.display.set_caption(
                                    "editor: " + str(self.level) + ".json"
                                )
                                self.scroll = [0, 0]
                            except FileNotFoundError:
                                print(
                                    "data/maps/"
                                    + str(key_to_number(self.level))
                                    + ".json"
                                    + " not found"
                                )
                                pass
                    if event.key == pygame.K_SPACE:
                        game = Game(self.level)
                        game.run()
                    if event.key == pygame.K_i:
                        self.copying = True
                    if event.key == pygame.K_a:
                        self.movement[0] = True
                    if event.key == pygame.K_d:
                        self.movement[1] = True
                    if event.key == pygame.K_w:
                        self.movement[2] = True
                    if event.key == pygame.K_s:
                        self.movement[3] = True
                    if event.key == pygame.K_g:
                        self.ongrid = not self.ongrid
                    if event.key == pygame.K_t:
                        self.tilemap.autotile()
                    if event.key == pygame.K_LSHIFT:
                        self.shift = True
                    if event.key == pygame.K_o:
                        if self.level != -1:
                            self.tilemap.save(
                                "data/maps/" + str(self.level) + ".json",
                                self.background_scroll,
                            )
                        else:
                            self.tilemap.save(
                                "map.json",
                                self.background_scroll,
                            )
                        self.display_msg("ADD TO GAME?", [pygame.K_q, pygame.K_SPACE])
                if event.type == pygame.KEYUP:
                    if event.key == pygame.K_a:
                        self.movement[0] = False
                    if event.key == pygame.K_d:
                        self.movement[1] = False
                    if event.key == pygame.K_w:
                        self.movement[2] = False
                    if event.key == pygame.K_s:
                        self.movement[3] = False
                    if event.key == pygame.K_LSHIFT:
                        self.shift = False

            self.screen.blit(
                pygame.transform.scale(self.display, self.screen.get_size()), (0, 0)
            )
            self.draw_minimap()

            pygame.display.update()

            self.clock.tick(60)

    def display_msg(self, txt, escape_key):
        font = pygame.font.Font(None, 20)
        text_surface = font.render(txt, True, (255, 255, 255))
        text_rect = text_surface.get_rect()
        text_rect.center = (
            self.screen.get_width() / 2,
            self.screen.get_height() / 2,
        )
        self.screen.blit(text_surface, text_rect)
        pygame.display.update()

        for x in range(4):
            self.movement[x] = 0

        while True:
            self.screen.blit(
                pygame.transform.scale(self.display, self.screen.get_size()), (0, 0)
            )
            for event in pygame.event.get():
                if event.type == pygame.QUIT:  # Corrected to pygame.QUIT
                    pygame.quit()
                    sys.exit()

                if event.type == pygame.KEYDOWN:
                    if escape_key == any or event.key in escape_key:
                        return event.key


def key_to_number(key):
    if pygame.K_0 <= key <= pygame.K_9:
        return key - pygame.K_0
    else:
        return None


Editor().run()
