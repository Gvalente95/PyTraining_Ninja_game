import random


class Cloud:
    def __init__(self, pos, img, speed, depth):
        self.pos = list(pos)
        self.img = img
        self.speed = speed
        self.depth = depth

    def update(self):
        self.pos[0] += self.speed

    def render(self, surf, offset=(0, 0)):
        render_pos = (
            self.pos[0] - offset[0] * self.depth,
            self.pos[1] - offset[1] * self.depth,
        )
        surf.blit(
            self.img,
            (
                render_pos[0] % (surf.get_width() + self.img.get_width()) - self.img.get_width(),
                render_pos[1] % (surf.get_height() + self.img.get_height()) - self.img.get_height(),
            ),
        )


class Clouds:
    def __init__(self, tilemap, cloud_images, count=16):
        self.clouds = []
        extracted_clouds = tilemap.extract([("clouds", 0)])
        y_pos = []

        for cloud in extracted_clouds:
            y_pos.append(cloud["pos"][1])

        y_pos_index = 0
        for i in range(count):
            depth = random.random() * 0.6 + 0.2
            adjusted_y = y_pos[y_pos_index] / depth - 500
            self.clouds.append(
                Cloud(
                    (random.random() * 99999, adjusted_y),
                    random.choice(cloud_images),
                    random.random() * 0.05 + 0.05,
                    depth,
                )
            )
            y_pos_index += 1
            if y_pos_index >= len(y_pos) - 1:
                y_pos_index = 0

        self.clouds.sort(key=lambda x: x.depth)

    def update(self):
        for cloud in self.clouds:
            cloud.update()

    def render(self, surf, offset=(0, 0)):
        for cloud in self.clouds:
            cloud.render(surf, offset=offset)
