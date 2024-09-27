import math
import random
import pygame
import time

from scripts.particle import Particle
from scripts.spark import Spark
from game import keys


def get_movables(game, exclude_rect=None):
    rects = []
    for dstr in game.boxes.copy():
        if dstr.is_held:
            continue
        rect = dstr.rect()
        if exclude_rect is None or rect != exclude_rect:
            rects.append(rect)
    return rects


class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.in_water = 0
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
        self.force = [0, 0]
        self.collisions = {"up": False, "down": False, "left": False, "right": False}

        self.action = ""
        self.anim_offset = (-3, -3)
        self.flip = False
        self.set_action("idle")

        self.last_movement = [0, 0]

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])

    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + "/" + self.action].copy()

    def update(self, tilemap, movement=(0, 0), force=(0, 0)):
        self.collisions = {"up": False, "down": False, "right": False, "left": False}

        frame_movement = (
            movement[0] + self.velocity[0] + self.force[0],
            movement[1] + self.velocity[1] + self.force[1],
        )

        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions["right"] = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions["left"] = True
                self.pos[0] = entity_rect.x
        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions["down"] = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions["up"] = True
                self.pos[1] = entity_rect.y
        rects = get_movables(self.game, self.rect())
        for rect in rects:
            if self.rect().colliderect(rect):
                if rect.y > self.rect().y:
                    self.collisions["down"] = True

        in_water = tilemap.water_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1]))
        if in_water:
            self.in_water += 1
        else:
            self.in_water = 0

        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True

        self.last_movement = movement

        self.force = (self.force[0] + force[0], self.force[1] + force[1])

        if self.force[0] > 0 and self.collisions["down"] or self.in_water:
            self.force = (max(self.force[0] - (0.05 if self.in_water else 0.3), 0), self.force[1])
        elif self.force[0] < 0 and self.collisions["down"] or self.in_water:
            self.force = (min(self.force[0] + (0.05 if self.in_water else 0.3), 0), self.force[1])
        if self.force[1] > 0:
            self.force = (self.force[0], max(self.force[1] - 0.1, 0.1 if self.in_water else 0))
        elif self.force[1] < 0:
            self.force = (self.force[0], min(self.force[1] + 0.1, -0.1 if self.in_water else 0))
        if abs(self.force[0]) < 0.01:
            self.force = (0, self.force[1])
        if abs(self.force[1]) < 0.01:
            self.force = (self.force[0], 0)

        if self.in_water:
            self.force = (self.force[0], 0.1 if self.in_water < 50 else -0.09999)
            if self.in_water > 100:
                self.in_water = 1

        if self.in_water:
            self.velocity[1] = min(0.05 if self.in_water < 50 else -0.049, self.velocity[1] + 0.1)

        else:
            self.velocity[1] = min(5, self.velocity[1] + 0.1)

        if self.collisions["down"] or self.collisions["up"]:
            self.velocity[1] = 0

        self.animation.update()
        return self.collisions

    def render(self, surf, offset=(0, 0), alpha=255):
        if alpha != 255:
            self.animation.img().set_alpha(alpha)
        surf.blit(
            pygame.transform.flip(self.animation.img(), self.flip, False),
            (
                self.pos[0] - offset[0] + self.anim_offset[0],
                self.pos[1] - offset[1] + self.anim_offset[1],
            ),
        )
        # rect_collider = self.rect()
        # adjusted_rect = pygame.Rect(rect_collider.x - offset[0], rect_collider.y - offset[1], rect_collider.width, rect_collider.height)
        # pygame.draw.rect(surf, (255, 0, 0), adjusted_rect, 2)


class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, "enemy", pos, size)

        self.walking = 0
        self.alive = 1

    def update(self, tilemap, movement=(0, 0)):
        if self.walking:
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                if self.collisions["right"] or self.collisions["left"]:
                    self.flip = not self.flip
                else:
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
            else:
                self.flip = not self.flip
            self.walking = max(0, self.walking - 1)
            if not self.walking:
                dis = (
                    self.game.player.pos[0] - self.pos[0],
                    self.game.player.pos[1] - self.pos[1],
                )
                if abs(dis[1]) < 16:
                    if self.flip and dis[0] < 0:
                        self.game.sfx["shoot"].play()
                        self.game.projectiles.append(
                            [
                                [self.rect().centerx - 7, self.rect().centery],
                                -1.5,
                                0,
                                False,
                            ]
                        )
                        for i in range(4):
                            self.game.sparks.append(
                                Spark(
                                    self.game.projectiles[-1][0],
                                    random.random() - 0.5 + math.pi,
                                    2 + random.random(),
                                )
                            )
                    if not self.flip and dis[0] > 0:
                        self.game.projectiles.append(
                            [
                                [self.rect().centerx + 7, self.rect().centery],
                                1.5,
                                0,
                                False,
                            ]
                        )
                        for i in range(4):
                            self.game.sparks.append(
                                Spark(
                                    self.game.projectiles[-1][0],
                                    random.random() - 0.5,
                                    2 + random.random(),
                                )
                            )
        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)

        super().update(tilemap, movement=movement, force=(0 if self.alive else 2, 0))
        if movement[0] != 0:
            self.set_action("run")
        else:
            self.set_action("idle")

        if abs(self.game.player.dashing) >= 50 or self.game.player.powJump > 0:
            if self.rect().colliderect(self.game.player.rect()):
                self.alive = 0

        if self.game.player.powJump > 0:
            if self.rect().colliderect(self.game.player.jumpDown_rect()):
                self.alive = 0

        if self.game.player.attacking == 15:
            if self.rect().colliderect(self.game.player.attack_rect()):
                self.alive = 0

        if self.alive <= 0:
            self.game.sfx["hit"].play()
            for i in range(15):
                angle = random.random() * math.pi * 2
                speed = random.random() * 5
                self.game.sparks.append(Spark(self.rect().center, angle, 1 + random.random(), (255, 0, 0, 100)))
                self.game.particles.append(
                    Particle(
                        self.game,
                        "particle",
                        self.rect().center,
                        velocity=[
                            math.cos(angle + math.pi) * speed * 0.5,
                            math.sin(angle + math.pi) * speed * 0.5,
                        ],
                        frame=random.randint(0, 7),
                    )
                )
                self.game.sparks.append(Spark(self.rect().center, 0, 1 + random.random()))
                self.game.sparks.append(Spark(self.rect().center, math.pi, 1 + random.random()))

            return True

    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)

        if self.flip:
            surf.blit(
                pygame.transform.flip(self.game.assets["gun"], True, False),
                (
                    self.rect().centerx - 4 - self.game.assets["gun"].get_width() - offset[0],
                    self.rect().centery - offset[1],
                ),
            )
        else:
            surf.blit(
                self.game.assets["gun"],
                (self.rect().centerx + 4 - offset[0], self.rect().centery - offset[1]),
            )


class Box(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, "box", pos, size)
        self.audioPlayed = 0
        self.alive = 1
        self.is_held = 0
        self.collisions = {"up": False, "down": False, "right": False, "left": False}
        self.grab_offs = random.randint(-2, 2)

    def update(self, tilemap, movement=(0, 0)):
        force = (0, 0)
        rects = get_movables(self.game, self.rect())
        my_rect = self.rect()
        for rect in rects:
            if my_rect.colliderect(rect):
                if rect.y > my_rect.y:
                    self.velocity[1] = 0
                elif rect.y == my_rect.y:
                    movement = (1 if rect.x < self.rect().x else -1, 0)

        if self.rect().colliderect(self.game.player.attack_rect()):
            if self.game.player.attacking == 10:
                self.alive = 0
            elif not self.is_held and self.game.input == keys["grab"]:
                self.game.input = "."
                self.game.player.is_holding += 1
                self.is_held = self.game.player.is_holding
                if not self.is_held:
                    movement = (20 * (-1 if self.flip else 1), 0)

        if self.is_held:
            self.game.player.pushing = 1
            if self.game.dead:
                self.is_held = 0
                self.game.player.is_gabbing = 0
                force = (random.randint(-5, 5), 5)
            else:
                self.velocity[1] = 0
                self.velocity[0] = 0
                self.pos[0] = self.grab_offs + self.game.player.pos[0] + 11 * (-1 if self.game.player.flip else 1)
                self.pos[1] = self.game.player.pos[1] - 11 * (self.is_held - 1)
                if self.game.input == keys["throw"] and self.is_held == 1:
                    self.is_held = 0
                    self.game.player.is_holding -= 1
                    up = self.game.last_pressed_input == keys["mv_up"]
                    force = (0 if up else 1.1 * (-1 if self.game.player.flip else 1), -4 if up else -3)
                    self.game.input = "."
                    for box in self.game.boxes:
                        if box.is_held:
                            box.is_held -= 1

        if self.game.player.powJump:
            if self.rect().colliderect(self.game.player.jumpDown_rect()):
                self.alive = 0

        if self.rect().colliderect(self.game.player.rect()):
            if abs(self.game.player.dashing) >= 50:
                self.alive = 0
            elif not self.collisions["right"] or self.collisions["left"]:
                if self.rect().y - self.game.player.rect().y < 6 and abs(self.rect().x - self.game.player.rect().x) > 4:
                    if self.game.player.flip and self.game.player.rect().x - self.rect().x > 0:
                        movement = (-1, 0)
                        self.game.player.pushing = 1
                    elif not self.game.player.flip and self.game.player.rect().x - self.rect().x < 0:
                        movement = (1, 0)
                        self.game.player.pushing = 1

        if self.alive <= 0:
            for i in range(15):
                angle = random.random() * math.pi * 2
                self.game.sparks.append(Spark(self.rect().center, angle, 2, (139, 69, 19, 120)))
                self.game.sfx["clonk"].play()
            return True
        self.collisions = super().update(tilemap, movement=movement, force=force)

    def render(self, surf, offset=(0, 0)):
        adj_offset = (offset[0] - 2, offset[1] - 2)
        super().render(surf, offset=adj_offset)
        # rect_collider = self.rect()
        # adjusted_rect = pygame.Rect(rect_collider.x - offset[0] - 2, rect_collider.y - offset[1], rect_collider.width, rect_collider.height)
        # pygame.draw.rect(surf, (0, 255, 0), adjusted_rect, 2)


class Bird(PhysicsEntity):
    def __init__(self, game, pos, size, index=0):
        super().__init__(game, "bird", pos, size)
        self.walking = 0
        self.au_index = index
        self.flight = 0
        self.x_dir = 0
        self.y_dir = 0
        self.rotation_angle = 0
        self.alive = 1
        self.audio_played = 0
        self.set_action("idle")

    def rect(self):
        return pygame.Rect(
            self.pos[0],
            self.pos[1],
            self.size[0],
            self.size[1] - 4,
        )

    def update(self, tilemap, movement=(0, 0)):
        if self.audio_played:
            self.audio_played += 1
        if not self.alive:
            self.game.sfx["hit"].play()
            for i in range(15):
                angle = random.random() * math.pi * 2
                self.game.sparks.append(Spark(self.rect().center, angle, 1 + random.random(), (255, 0, 0, 100)))

            return True
        else:
            self.velocity[1] = 0

            dist = math.sqrt(sum((self.pos[i] - self.game.player.pos[i]) ** 2 for i in range(len(self.pos))))
            if abs(dist) < 20:
                if self.game.player.action == "attack":
                    self.alive = 0
                self.flight = 50
                if not self.audio_played:
                    self.game.flight_sfx_pool[self.au_index].play()
                    self.audio_played = 1

                # Initialize potential directions
                possible_x_dirs = [
                    -5,
                    -4,
                    -3,
                    -2,
                    -1,
                    1,
                    2,
                    3,
                    4,
                    5,
                ]
                possible_y_dirs = [-5, -4, -3, -2]
                if self.collisions["left"]:
                    possible_x_dirs = [d for d in possible_x_dirs if d > 0]
                if self.collisions["right"]:
                    possible_x_dirs = [d for d in possible_x_dirs if d < 0]
                if self.collisions["up"]:
                    possible_y_dirs = [d for d in possible_y_dirs if d > 0]
                if self.collisions["down"]:
                    possible_y_dirs = [d for d in possible_y_dirs if d < 0]
                if possible_x_dirs:
                    self.x_dir = random.choice(possible_x_dirs)
                else:
                    self.x_dir = 0
                if possible_y_dirs:
                    self.y_dir = random.choice(possible_y_dirs)
                else:
                    self.y_dir = 0
        if self.flight:
            self.flight -= 1
            self.rotation_angle = 0
            if self.y_dir > self.x_dir:
                self.set_action("fly")
            else:
                self.set_action("fly_b")
            self.velocity[0] = self.x_dir * 0.5
            self.velocity[1] = self.y_dir * 0.5
            if self.flight <= 30:
                self.check_landing()
        elif self.alive:
            self.check_landing()
            if not self.collisions["down"] and self.rotation_angle == 0:
                self.velocity[1] += 0.1

        super().update(tilemap, movement=movement)

    def render(self, surf, offset=(0, 0)):
        rotated_img = pygame.transform.rotate(self.animation.img(), self.rotation_angle)
        surf.blit(
            pygame.transform.flip(rotated_img, self.flip, False),
            (
                self.pos[0] - offset[0] + self.anim_offset[0],
                self.pos[1] - offset[1] + self.anim_offset[1],
            ),
        )

    def check_landing(self):
        if self.collisions["left"]:
            self.set_landing(-90)
        elif self.collisions["right"]:
            self.set_landing(90)
        elif self.collisions["up"]:
            self.set_landing(180)
        elif self.collisions["down"]:
            self.set_landing(0)

    def set_landing(self, rot_angle):
        self.velocity[0] = 0
        self.velocity[1] = 0
        self.rotation_angle = rot_angle
        self.set_action("idle")
        self.flight = 0
        self.audio_played = 0
        self.game.flight_sfx_pool[self.au_index].stop()


class Mob(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, "mob", pos, size)
        self.walking = 0
        self.alive = 1

    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1] - 4)

    def update(self, tilemap, movement=(0, 0)):
        if self.walking:
            if tilemap.solid_check((self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)):
                if self.collisions["right"] or self.collisions["left"]:
                    self.flip = not self.flip
                else:
                    movement = (movement[0] - 0.5 if self.flip else 0.5, movement[1])
            else:
                self.flip = not self.flip
            self.walking = max(0, self.walking - 1)
            if not self.walking:
                dis = (
                    self.game.player.pos[0] - self.pos[0],
                    self.game.player.pos[1] - self.pos[1],
                )
                if abs(dis[1]) < 16:
                    if self.flip and dis[0] < 0:
                        self.game.sfx["shoot"].play()
                        self.game.projectiles.append(
                            [
                                [self.rect().centerx - 7, self.rect().centery],
                                -1.5,
                                0,
                                False,
                            ]
                        )
                        for i in range(4):
                            self.game.sparks.append(
                                Spark(
                                    self.game.projectiles[-1][0],
                                    random.random() - 0.5 + math.pi,
                                    2 + random.random(),
                                )
                            )
                    if not self.flip and dis[0] > 0:
                        self.game.projectiles.append(
                            [
                                [self.rect().centerx + 7, self.rect().centery],
                                1.5,
                                0,
                                False,
                            ]
                        )
                        for i in range(4):
                            self.game.sparks.append(
                                Spark(
                                    self.game.projectiles[-1][0],
                                    random.random() - 0.5,
                                    2 + random.random(),
                                )
                            )
        elif random.random() < 0.01:
            self.walking = random.randint(30, 120)

        super().update(tilemap, movement=movement)
        if movement[0] != 0:
            self.set_action("run")
        else:
            self.set_action("idle")

    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)


class Demo(PhysicsEntity):
    def __init__(self, game, pos, size):
        self.action = "idle"
        self.set_action("idle")
        super().__init__(game, "demo_surf", pos, size)

    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)
        self.velocity[1] = 0
        self.set_action("idle")

    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)


class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, "player", pos, size)
        self.jumps = 2
        self.surf_audio_played = 0
        self.wall_slide = 0
        self.air_time = 0
        self.dashing = 0
        self.deflecting = 0
        self.attacking = 0
        self.pushing = 0
        self.powJump = 0
        self.is_swiming = 0
        self.bul_surf = 0
        self.is_holding_count = 0
        self.is_holding = 0
        self.start_width = self.size[0]

    def attack_rect(self):
        width = 10
        height = 6
        return pygame.Rect(
            int(self.pos[0]) + (-(width + 10) if self.flip else 8),  # Adjust the x position based on flip
            int(self.pos[1]) - height,  # y position
            self.size[0] + width,
            self.size[1] + height,
        )

    def jumpDown_rect(self):
        return pygame.Rect(
            self.pos[0] + (-26 if self.flip else 8) - 30,
            self.pos[1] - 5,
            self.size[0] + 60,  # width of the attack area
            self.size[1] + 30,  # height of the attack area
        )

    def update(self, tilemap, movement=(0, 0)):
        if self.is_holding_count != self.is_holding:
            self.game.sfx["clonk"].play()
            self.is_holding_count = self.is_holding
        if self.powJump >= 28:
            self.powJump -= 1
            if self.powJump == 27:
                self.game.sfx["dash"].play()
            return
        if self.powJump < 0:
            self.set_action("powJump")
            self.powJump -= 1
            if self.powJump < -30:
                self.powJump = 0
            return
        super().update(tilemap, movement=movement)

        if (self.bul_surf or self.is_swiming) and not self.surf_audio_played:
            self.game.sfx["wind"].play()
            self.surf_audio_played = 1

        if self.bul_surf:
            self.velocity[1] = 0
        elif self.surf_audio_played:
            self.game.sfx["wind"].stop()
            self.surf_audio_played = 0

        for box in self.game.boxes:
            if self.rect().y + self.rect().height - 4 < box.rect().y and self.rect().colliderect(box.rect()) and abs(self.rect().x - box.rect().x) < box.rect().width:
                self.collisions["down"] = 1
                self.velocity[1] = 0
                self.air_time = 0
                self.jumps = 2

        self.attacking = max(self.attacking - 1, 0)

        self.powJump = max(0, self.powJump - 1)
        if self.powJump and not self.collisions["down"]:
            self.velocity[0] = 0
            self.velocity[1] = 15
            for i in range(5):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(
                    Particle(
                        self.game,
                        "particle",
                        self.rect().center,
                        velocity=pvelocity,
                        frame=random.randint(0, 7),
                    )
                )
            return
        if self.powJump:
            for i in range(50):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(
                    Particle(
                        self.game,
                        "particle",
                        (
                            self.rect().center[0] + random.randint(-30, 30),
                            self.rect().center[1] + random.randint(-5, 5),
                        ),
                        velocity=pvelocity,
                        frame=random.randint(0, 1),
                    )
                )
            if self.collisions["down"]:
                self.game.sfx["slash"].play()
                self.powJump = 0
        if self.attacking:
            self.bul_surf = 0
            self.set_action("attack")
            if self.attacking == 10:
                self.game.sfx["slash"].play()
                for i in range(2):
                    self.game.sparks.append(
                        Spark(
                            (
                                (self.pos[0] + (-15 if self.flip else 15)),
                                self.pos[1] + 3,
                            ),
                            random.random() - 0.5 + (math.pi if self.flip else 0),
                            2 + random.random(),
                        )
                    )
        self.air_time += 1

        if self.pos[1] > 500:
            self.game.dead += 1

        if self.collisions["down"]:
            self.air_time = 0
            self.jumps = 2

        self.wall_slide = False
        if self.collisions["right"] or self.collisions["left"] and self.air_time > 4:
            self.dashing = 0
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 0.5)
            if self.collisions["right"]:
                self.flip = False
            else:
                self.flip = True
            self.set_action("wall_slide")
            self.air_time = min(40, self.air_time)

        if self.in_water:
            self.set_action("swim")
            if self.game.last_pressed_input == keys["mv_down"]:
                self.force = (self.force[0], 1)
            elif self.game.last_pressed_input == keys["mv_up"]:
                self.force = (self.force[0], -1)

        if self.is_swiming or self.in_water:
            self.set_action("swim")
            self.jumps = 2
            self.air_time = 0
        elif not self.wall_slide and not self.attacking:
            if self.air_time > 4:
                self.set_action("jump")
            elif movement[0] != 0:
                self.set_action("push" if self.pushing else "run")
            else:
                self.set_action("hold" if self.pushing else "idle")

        if abs(self.dashing) in {60, 50}:
            for i in range(30):
                angle = random.random() * math.pi * 2
                speed = random.random() * 0.5 + 0.5
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed]
                self.game.particles.append(
                    Particle(
                        self.game,
                        "particle",
                        self.rect().center,
                        velocity=pvelocity,
                        frame=random.randint(0, 7),
                    )
                )

        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)
        if abs(self.dashing) > 50:
            self.velocity[0] = abs(self.dashing) / self.dashing * 8
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
            pvelocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
            self.game.particles.append(
                Particle(
                    self.game,
                    "particle",
                    self.rect().center,
                    velocity=pvelocity,
                    frame=random.randint(0, 7),
                )
            )
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)
        if self.bul_surf:
            self.air_time = 5

    def render(self, surf, offset=0):
        if abs(self.dashing) <= 50:
            super().render(surf, offset=offset)
        # rect_collider = self.attack_rect()
        # adjusted_rect = pygame.Rect(rect_collider.x - offset[0], rect_collider.y - offset[1], rect_collider.width, rect_collider.height)
        # pygame.draw.rect(surf, (255, 0, 0), adjusted_rect, 2)

    def attack(self):
        if self.is_holding:
            return False
        if self.attacking <= 0:
            self.attacking += 15
            return True
        return False

    def jump(self):
        if self.wall_slide:
            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = 2
                self.velocity[1] = -2.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -2
                self.velocity[1] = -2.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True

        elif self.jumps and not self.in_water:
            self.velocity[1] = -1 * (2.5 if self.jumps == 2 else 2)
            self.jumps -= 1
            self.air_time = 5
            return True

    def dash(self):
        if not self.dashing:
            self.game.sfx["dash"].play()
            if self.flip:
                self.dashing = -60
            else:
                self.dashing = 60

    def power_jump(self):
        self.powJump = 30
