import json

import pygame

AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0,
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,
    tuple(sorted([(-1, 0), (0, 1)])): 2,
    tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 3,
    tuple(sorted([(-1, 0), (0, -1)])): 4,
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 5,
    tuple(sorted([(1, 0), (0, -1)])): 6,
    tuple(sorted([(1, 0), (0, -1), (0, 1)])): 7,
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 8,
}
NEIGHBOR_OFFSETS = [
    (-1, 0),
    (-1, -1),
    (0, -1),
    (1, -1),
    (1, 0),
    (0, 0),
    (-1, 1),
    (0, 1),
    (1, 1),
]
PHYSICS_TILES = {"grass", "stone", "ice"}
AUTOTILE_TYPES = {"grass", "stone", "ice"}
COLLIDER_TYLES = {"colliders"}


class Tilemap:
    def __init__(self, game, tile_size=16):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = []

    def extract(self, id_pairs, keep=False):
        matches = []
        to_delete = []  # List to hold keys to be deleted

        for tile in self.offgrid_tiles.copy():
            if (tile["type"], tile["variant"]) in id_pairs:
                matches.append(tile.copy())
                if not keep:
                    self.offgrid_tiles.remove(tile)

        for loc in list(self.tilemap.keys()):  # Iterate over a copy of the keys
            tile = self.tilemap[loc]
            if (tile["type"], tile["variant"]) in id_pairs:
                matches.append(tile.copy())
                matches[-1]["pos"] = matches[-1]["pos"].copy()
                matches[-1]["pos"][0] *= self.tile_size
                matches[-1]["pos"][1] *= self.tile_size
                if not keep:
                    to_delete.append(loc)  # Add loc to the list of items to delete

        # Now that the iteration is over, delete the keys
        for loc in to_delete:
            del self.tilemap[loc]

        return matches

    def tiles_around(self, pos):
        tiles = []
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in NEIGHBOR_OFFSETS:
            check_loc = (
                str(tile_loc[0] + offset[0]) + ";" + str(tile_loc[1] + offset[1])
            )
            if check_loc in self.tilemap:
                tiles.append(self.tilemap[check_loc])
        return tiles

    def save(self, path, background_index=0):
        f = open(path, "w")
        json.dump(
            {
                "tilemap": self.tilemap,
                "tile_size": self.tile_size,
                "offgrid": self.offgrid_tiles,
                "background_index": background_index,
            },
            f,
        )
        f.close()
        print(path + " saved")

    def load(self, path):
        f = open(path, "r")
        map_data = json.load(f)
        f.close()

        self.tilemap = map_data["tilemap"]
        self.tile_size = map_data["tile_size"]
        self.offgrid_tiles = map_data["offgrid"]
        print(path + " loaded")
        background_index = map_data.get("background_index", 0)
        return background_index

    def solid_check(self, pos):
        tile_loc = (
            str(int(pos[0] // self.tile_size))
            + ";"
            + str(int(pos[1] // self.tile_size))
        )
        if tile_loc in self.tilemap:
            if self.tilemap[tile_loc]["type"] in PHYSICS_TILES:
                return self.tilemap[tile_loc]

    def physics_rects_around(self, pos):
        rects = []
        for tile in self.tiles_around(pos):
            if tile["type"] in PHYSICS_TILES:
                rects.append(
                    pygame.Rect(
                        tile["pos"][0] * self.tile_size,
                        tile["pos"][1] * self.tile_size,
                        self.tile_size,
                        self.tile_size,
                    )
                )
            if tile["type"] in COLLIDER_TYLES:
                self.game.new_background = (
                    "background_cave" if tile["variant"] == 1 else "background"
                )
                self.game.background = (
                    "background" if tile["variant"] == 1 else "background_cave"
                )
        return rects

    def autotile(self):
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            neighbors = set()
            for shift in [(1, 0), (-1, 0), (0, -1), (0, 1)]:
                check_loc = (
                    str(tile["pos"][0] + shift[0])
                    + ";"
                    + str(tile["pos"][1] + shift[1])
                )
                if check_loc in self.tilemap:
                    if self.tilemap[check_loc]["type"] == tile["type"]:
                        neighbors.add(shift)
            neighbors = tuple(sorted(neighbors))
            if (tile["type"] in AUTOTILE_TYPES) and (neighbors in AUTOTILE_MAP):
                tile["variant"] = AUTOTILE_MAP[neighbors]

    def render(self, surf, offset=(0, 0), scale=1.0):
        for tile in self.offgrid_tiles:
            tile_img = self.game.assets[tile["type"]][tile["variant"]]
            scaled_tile_img = pygame.transform.scale(
                tile_img,
                (
                    int(tile_img.get_width() * scale),
                    int(tile_img.get_height() * scale),
                ),
            )
            surf.blit(
                scaled_tile_img,
                (
                    (tile["pos"][0] - offset[0]) * scale,
                    (tile["pos"][1] - offset[1]) * scale,
                ),
            )

        for x in range(
            int(offset[0] // self.tile_size),
            int((offset[0] + surf.get_width() / scale) // self.tile_size + 1),
        ):
            for y in range(
                int(offset[1] // self.tile_size),
                int((offset[1] + surf.get_height() / scale) // self.tile_size + 1),
            ):
                loc = str(x) + ";" + str(y)
                if loc in self.tilemap:
                    tile = self.tilemap[loc]
                    tile_img = self.game.assets[tile["type"]][tile["variant"]]
                    scaled_tile_img = pygame.transform.scale(
                        tile_img,
                        (
                            int(tile_img.get_width() * scale),
                            int(tile_img.get_height() * scale),
                        ),
                    )
                    surf.blit(
                        scaled_tile_img,
                        (
                            (x * self.tile_size - offset[0]) * scale,
                            (y * self.tile_size - offset[1]) * scale,
                        ),
                    )

    def render_whole(self, surf, scale=1.0, offset=(0, 0)):
        scaler = 3
        init_offset = (50, 50)

        for tile in self.offgrid_tiles:
            tile_img = self.game.assets[tile["type"]][tile["variant"]]
            scaled_tile_img = pygame.transform.scale(
                tile_img,
                (
                    int(tile_img.get_width() * (scale / scaler)),
                    int(tile_img.get_height() * (scale / scaler)),
                ),
            )
            surf.blit(
                scaled_tile_img,
                (
                    tile["pos"][0] * (scale / scaler) + init_offset[0],
                    tile["pos"][1] * (scale / scaler) + init_offset[1],
                ),
            )

        for loc in self.tilemap:
            x, y = map(int, loc.split(";"))
            tile = self.tilemap[loc]
            tile_img = self.game.assets[tile["type"]][tile["variant"]]
            scaled_tile_img = pygame.transform.scale(
                tile_img,
                (
                    int(tile_img.get_width() * (scale / scaler)),
                    int(tile_img.get_height() * (scale / scaler)),
                ),
            )
            surf.blit(
                scaled_tile_img,
                (
                    x * self.tile_size * (scale / scaler) + init_offset[0],
                    y * self.tile_size * (scale / scaler) + init_offset[1],
                ),
            )

        offs = (offset[0] / (scaler * 2), offset[1] / (scaler * 2))
        rect_width = 2
        rect_height = 2
        pygame.draw.rect(
            surf,
            (255, 0, 0),
            pygame.Rect(
                offs[0] + init_offset[0] + 30,
                offs[1] + init_offset[1] + 15,
                rect_width,
                rect_height,
            ),
        )
