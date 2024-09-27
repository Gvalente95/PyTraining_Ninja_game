import pygame  # type: ignore
import sys
import os

from scripts.utils import load_images, display_msg, keys
from scripts.tilemap import Tilemap
from game import Game

RENDER_SCALE = 2.0
SCREEN_WIDTH = 640
SCREEN_HEIGHT = 480


class Editor:
    def __init__(self):
        pygame.init()

        self.font = pygame.font.Font(None, 20)

        pygame.display.set_caption("editor: -1")
        self.screen = pygame.display.set_mode((640, 480), pygame.RESIZABLE)
        self.display = pygame.Surface((320, 240))

        self.clock = pygame.time.Clock()

        self.assets = {
            "grass": load_images("tiles/grass"),
            "herb": load_images("tiles/herb"),
            "ice": load_images("tiles/ice"),
            "stone": load_images("tiles/stone"),
            "water": load_images("tiles/water"),
            "spawners": load_images("tiles/spawners"),
            "decor": load_images("tiles/decor"),
            "large_decor": load_images("tiles/large_decor"),
            "clouds": load_images("clouds"),
            "demo": load_images("tiles/demo", color_key=(1, 1, 1)),
            "colliders": load_images("tiles/colliders"),
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
        self.was_mod = 0

        self.clicking = 0
        self.right_clicking = False
        self.shift = False
        self.ongrid = True
        self.copying = False
        self.background_scroll = 0
        self.player = 0

        self.last_pressed_input = 0

        self.minimap_scale = 0.4
        self.minimap_size = (
            int(320 * self.minimap_scale),
            int(240 * self.minimap_scale),
        )
        self.minimap_surface = pygame.Surface(self.minimap_size)

        self.old_maps = []
        self.back_amount = 100
        self.back_count = 1
        self.z_count = 0
        self.tilemap.save(
            "saved_maps/" + "0;" + str(self.level) + ".json",
            self.background_scroll,
        )

    def draw_minimap(self):
        self.minimap_surface.fill((50, 50, 50))
        self.minimap_surface.set_alpha(200)
        self.tilemap.render_whole(self.minimap_surface, scale=self.minimap_scale, offset=self.scroll)
        minimap_x = self.screen.get_width() - self.minimap_size[0] - 10
        minimap_y = self.screen.get_height() - self.minimap_size[1] - 10
        self.screen.blit(self.minimap_surface, (minimap_x, minimap_y))

    def draw_clouds(self, pos, offset, depth, img, surf, altitude):
        render_pos = (
            pos[0] - offset[0] * depth,
            pos[1] - offset[1] * depth,
        )
        surf.blit(
            img,
            (
                render_pos[0],
                render_pos[1],
            ),
        )

    def run(self):
        while True:

            if self.was_mod >= 2 and self.back_count < self.back_amount:
                self.tilemap.save(
                    "saved_maps/" + str(self.back_count) + ";" + str(self.level) + ".json",
                    self.background_scroll,
                )
                self.back_count += 1
                self.was_mod = 0
                self.z_count += 1

            if self.was_mod:
                self.was_mod += 1

            if self.clicking:
                self.clicking += 2

            if self.shift:
                self.speed = min(self.speed + 1, 8)
            else:
                self.speed = 2
            screen_width, screen_height = self.screen.get_size()
            scaled_bg = pygame.transform.scale(self.backgrounds[self.background_scroll], (screen_width, screen_height))
            self.display.fill((0, 0, 0))
            self.display.blit(scaled_bg, (0, 0))
            self.scroll[0] += (self.movement[1] - self.movement[0]) * self.speed
            self.scroll[1] += (self.movement[3] - self.movement[2]) * self.speed

            render_scroll = (int(self.scroll[0]), int(self.scroll[1]))

            self.tilemap.render(self.display, offset=render_scroll)

            current_tile_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant].copy()
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
                self.was_mod = 1

            elif self.clicking >= 10:
                self.clicking = 1
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
                self.was_mod = 1

            if self.right_clicking:
                for tile in self.tilemap.offgrid_tiles.copy():
                    tile_img = self.assets[tile["type"]][tile["variant"]]
                    cur_img = self.assets[self.tile_list[self.tile_group]][self.tile_variant]
                    if self.shift and tile_img != cur_img:
                        continue
                    tile_r = pygame.Rect(
                        tile["pos"][0] - self.scroll[0],
                        tile["pos"][1] - self.scroll[1],
                        tile_img.get_width(),
                        tile_img.get_height(),
                    )
                    if tile_r.collidepoint(mpos):
                        self.tilemap.offgrid_tiles.remove(tile)
                        self.was_mod = 1

                tile_loc = str(tile_pos[0]) + ";" + str(tile_pos[1])
                if tile_loc in self.tilemap.tilemap:
                    tile = self.tilemap.tilemap[tile_loc]
                    tile_img = self.assets[tile["type"]][tile["variant"]]
                    if not self.shift or tile_img == cur_img:
                        del self.tilemap.tilemap[tile_loc]
                        self.was_mod = 1

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
                pressed = pygame.key.get_pressed()
                self.last_pressed_input = 0

                for action, key in keys.items():
                    if pressed[key]:
                        self.last_pressed_input = key
                        break
                if event.type == pygame.QUIT:
                    delete_saved_maps()
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.clicking = True
                    if event.button == 3:
                        self.right_clicking = True
                    if self.shift:
                        if event.button == 4:
                            self.tile_variant = (self.tile_variant - 1) % len(self.assets[self.tile_list[self.tile_group]])
                        if event.button == 5:
                            self.tile_variant = (self.tile_variant + 1) % len(self.assets[self.tile_list[self.tile_group]])
                    else:
                        if event.button == 4:
                            self.tile_group = (self.tile_group - 1) % len(self.tile_list)
                            self.tile_variant = 0
                        if event.button == 5:
                            self.tile_group = (self.tile_group + 1) % len(self.tile_list)
                            self.tile_variant = 0
                if event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.clicking = False
                    if event.button == 3:
                        self.right_clicking = False

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z:
                        if self.shift:
                            files = os.listdir("saved_maps")
                            self.z_count = min(len(files) - 1, self.z_count + 1)
                        else:
                            self.z_count = max(0, self.z_count - 1)

                        load_saved_map(self, self.z_count)
                        print(str(self.z_count))
                    if event.key == pygame.K_LEFT:
                        self.background_scroll -= 1
                        if self.background_scroll < 0:
                            self.background_scroll = len(self.backgrounds) - 1
                    if event.key == pygame.K_RIGHT:
                        self.background_scroll += 1
                        if self.background_scroll > len(self.backgrounds) - 1:
                            self.background_scroll = 0
                    if event.key == pygame.K_q:
                        delete_saved_maps()
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
                                bg_index = self.tilemap.load("data/maps/" + str(self.level) + ".json")
                                pygame.display.set_caption("editor: " + str(self.level) + ".json")
                                self.scroll = [0, 0]
                                self.background_scroll = bg_index
                            except FileNotFoundError:
                                print("data/maps/" + str(self.level) + ".json" + " not found")
                                pass
                    if event.key == pygame.K_SPACE:
                        game = Game(self.level)
                        game.run()
                        screen_width, screen_height = self.screen.get_size()
                        self.display = pygame.Surface((screen_width // 2, screen_height // 2), pygame.SRCALPHA)
                        self.display_2 = pygame.Surface((screen_width // 2, screen_height // 2))

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
                    if event.key == pygame.K_x:
                        if display_msg(self, "clear map?") == pygame.K_SPACE:
                            self.tilemap.offgrid_tiles.clear()
                            self.tilemap.tilemap.clear()
                    if event.key == pygame.K_t:
                        self.tilemap.autotile()
                    if event.key == pygame.K_LSHIFT:
                        self.shift = True
                    if event.key == pygame.K_o:
                        if display_msg(self, "ADD TO GAME?") == pygame.K_SPACE:
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
                if event.type == pygame.VIDEORESIZE:
                    SCREEN_WIDTH, SCREEN_HEIGHT = event.w, event.h
                    self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
                    self.display = pygame.Surface((SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2), pygame.SRCALPHA)
                    self.display_2 = pygame.Surface((SCREEN_WIDTH / 2, SCREEN_HEIGHT / 2))

            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            self.draw_minimap()

            pygame.display.update()

            self.clock.tick(60)


def load_saved_map(self, index=0):
    directory_path = "saved_maps"
    files = os.listdir(directory_path)

    # Generate the expected file name pattern based on the index
    expected_file_prefix = f"{index};"

    # Find the file that starts with the expected prefix
    try:
        file_name = next(file for file in files if file.startswith(expected_file_prefix))
        file_path = os.path.join(directory_path, file_name)
        self.tilemap.load(file_path)
        return 1
    except StopIteration:
        print(f"No file found for index {index}")
        return 0
    except Exception as e:
        print(f"Error: {e}")
        self.delete_saved_maps()
        pygame.quit()
        sys.exit()


def delete_saved_maps():
    directory_path = "saved_maps"
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)
        print(f"{file_path} has been deleted.")


Editor().run()
