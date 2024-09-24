import math
import random
import pygame
import time

from scripts.particle import Particle
from scripts.spark import Spark


class PhysicsEntity:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos)
        self.size = size
        self.velocity = [0, 0]
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

    def update(self, tilemap, movement=(0, 0)):
        self.collisions = {"up": False, "down": False, "right": False, "left": False}

        frame_movement = (
            movement[0] + self.velocity[0],
            movement[1] + self.velocity[1],
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

        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True

        self.last_movement = movement

        self.velocity[1] = min(5, self.velocity[1] + 0.1)

        if self.collisions["down"] or self.collisions["up"]:
            self.velocity[1] = 0

        self.animation.update()

    def render(self, surf, offset=(0, 0)):
        surf.blit(
            pygame.transform.flip(self.animation.img(), self.flip, False),
            (
                self.pos[0] - offset[0] + self.anim_offset[0],
                self.pos[1] - offset[1] + self.anim_offset[1],
            ),
        )


class Enemy(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, "enemy", pos, size)

        self.walking = 0
        self.alive = 1

    def update(self, tilemap, movement=(0, 0)):
        if self.walking:
            if tilemap.solid_check(
                (self.rect().centerx + (-7 if self.flip else 7), self.pos[1] + 23)
            ):
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

        if abs(self.game.player.dashing) >= 50 or self.game.player.powJump > 0:
            if self.rect().colliderect(self.game.player.rect()):
                self.alive = 0

        if self.game.player.attacking == 15:
            if self.rect().colliderect(self.game.player.attack_rect()):
                self.alive = 0

        if self.alive <= 0:
            self.game.sfx["hit"].play()
            for i in range(15):
                angle = random.random() * math.pi * 2
                speed = random.random() * 5
                self.game.sparks.append(
                    Spark(self.rect().center, angle, 2 + random.random(), (150, 0, 0))
                )
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
                self.game.sparks.append(
                    Spark(self.rect().center, 0, 1 + random.random())
                )
                self.game.sparks.append(
                    Spark(self.rect().center, math.pi, 1 + random.random())
                )

            return True

    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)

        if self.flip:
            surf.blit(
                pygame.transform.flip(self.game.assets["gun"], True, False),
                (
                    self.rect().centerx
                    - 4
                    - self.game.assets["gun"].get_width()
                    - offset[0],
                    self.rect().centery - offset[1],
                ),
            )
        else:
            surf.blit(
                self.game.assets["gun"],
                (self.rect().centerx + 4 - offset[0], self.rect().centery - offset[1]),
            )


class Destroyable(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, "destroyable", pos, size)
        self.alive = 1

    def update(self, tilemap, movement=(0, 0)):

        super().update(tilemap, movement=movement)

        if self.collisions["right"] or self.collisions["left"]:
            return

        if not (self.collisions["right"] or self.collisions["left"]):
            for dst in self.game.destroyable:
                if dst != self and self.rect().colliderect(dst.rect()):
                    self.pos[0] += self.pos[0] - dst.pos[0]

        if self.game.player.attacking == 10:
            if self.rect().colliderect(self.game.player.attack_rect()):
                self.alive = 0

        if self.rect().colliderect(self.game.player.rect()):
            if abs(self.game.player.dashing) >= 50:
                self.alive = 0
            elif not self.collisions["right"] or self.collisions["left"]:
                self.pos[0] += -1 if self.game.player.flip else 1
                self.game.player.pushing = 1

        if self.alive <= 0:
            for i in range(15):
                angle = random.random() * math.pi * 2
                speed = random.random() * 2
                self.game.sparks.append(
                    Spark(self.rect().center, angle, 2, (139, 69, 19))
                )

            return True

    def render(self, surf, offset=(0, 0)):
        super().render(surf, offset=offset)


class Player(PhysicsEntity):
    def __init__(self, game, pos, size):
        super().__init__(game, "player", pos, size)
        self.air_time = 0
        self.jumps = 2
        self.wall_slide = 0
        self.dashing = 0
        self.deflecting = 0
        self.attacking = 0
        self.pushing = 0
        self.powJump = 0

    def attack_rect(self):
        return pygame.Rect(
            self.pos[0]
            + (-26 if self.flip else 8),  # Adjust the x position based on flip
            self.pos[1] - 5,  # y position
            self.size[0] + 30,  # width of the attack area
            self.size[1] + 30,  # height of the attack area
        )

    def update(self, tilemap, movement=(0, 0)):
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

        self.attacking = max(self.attacking - 1, 0)

        self.powJump = max(0, self.powJump - 1)
        if self.powJump and not self.collisions["down"]:
            self.velocity[0] = -0
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
            self.powJump = -1

        if self.attacking:
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
            attack_rect = self.attack_rect()
            """"
			pygame.draw.rect(
				self.game.display_2,
				(255, 0, 0),
				pygame.Rect(
					self.pos[0] - (self.game.scroll[0]) - (26 if self.flip else -8),
					self.pos[1] - (self.game.scroll[1]) - 5,
					30,
					30,
				),
				2,
			)"""
        self.air_time += 1

        if self.air_time > 180:
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

        if not self.wall_slide and not self.attacking:
            if self.air_time > 4:
                self.set_action("jump")
            elif movement[0] != 0:
                self.set_action("push" if self.pushing else "run")
            else:
                self.set_action("idle")

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

    def render(self, surf, offset=0):
        if abs(self.dashing) <= 50:
            super().render(surf, offset=offset)

    def attack(self):
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

        elif self.jumps:
            self.velocity[1] = -3
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
