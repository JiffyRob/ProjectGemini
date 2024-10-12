import random
from math import sin
from collections import deque

import pygame

from scripts import sprite, util_draw, timer, projectile, visual_fx
from scripts.animation import Animation, SingleAnimation

BOARD_SPEED = 256


class ScrollingBackground(sprite.Sprite):
    STATE_GROUND = 0
    STATE_WATER = 1

    def __init__(self, level, rect=((0, 0,), util_draw.RESOLUTION), z=0):
        tileset = level.game.loader.get_surface("tileset.png")
        self.land_tile = tileset.subsurface((112, 176, 16, 16))
        self.land_sea_transition = tileset.subsurface((128, 176, 16, 16))
        self.sea_land_transition = tileset.subsurface((96, 176, 16, 16))
        self.sea_tile = level.game.loader.get_spritesheet("liquid.png")[0]
        self.state = self.STATE_GROUND
        self.swap_cooldown = timer.Timer(1000)
        self.x_offset = 0
        self.images = deque()
        self.rect = pygame.FRect(rect)
        self.rock_chance = 100
        self.locked = False
        super().__init__(level, self.get_next_image(), rect, z)

    def lock(self):
        self.locked = True

    def unlock(self):
        self.locked = False

    def get_next_image(self):
        if self.swap_cooldown.done():
            self.swap_cooldown.reset()
            if self.state == self.STATE_GROUND:
                self.state = self.STATE_WATER
                return util_draw.repeat_surface(self.land_sea_transition, (16, self.rect.height))
            else:
                self.state = self.STATE_GROUND
                return util_draw.repeat_surface(self.sea_land_transition, (16, self.rect.height))
        elif self.state == self.STATE_GROUND:
            return util_draw.repeat_surface(self.land_tile, (16, self.rect.height))
        else:
            return util_draw.repeat_surface(self.sea_tile, (16, self.rect.height))

    def update(self, dt):
        if not self.locked:
            self.x_offset -= BOARD_SPEED * dt
            self.swap_cooldown.update()
            if not random.randint(0, self.rock_chance):
                self.level.spawn("Rock", (util_draw.RESOLUTION[0] + 8, random.randint(0, util_draw.RESOLUTION[1]), 16, 16), z=8)

    def draw(self, surface, offset):
        if self.x_offset < 0:
            for _ in range(int(self.x_offset / 16)):
                self.images.popleft()
                self.x_offset += 16
        x = self.x_offset
        # draw images in the deque
        for image in self.images:
            surface.blit(image, (x, 0))
            x += image.get_width()
        # add images to the deque and draw them if the deque is too short
        while x < self.rect.width:
            image = self.get_next_image()
            self.images.append(image)
            surface.blit(image, (x, 0))
            x += image.get_width()


class Player(sprite.Sprite):
    BANK_SPEED = 64
    ACCEL_SPEED = 32

    MIN_Y = 32
    MAX_Y = util_draw.RESOLUTION[1] - 32
    MIN_X = 32
    MAX_X = util_draw.RESOLUTION[0] - 32

    def __init__(self, level, rect=(0, 0, 32, 32), z=0):
        frames = level.game.loader.get_spritesheet("hoverboard.png", (32, 32))
        self.anim_dict = {
            "idle-right": Animation(frames[4:8], 0.1),
            "lookback-right": Animation(frames[8:12], 0.1),
        }
        self.state = "idle"
        self.facing = "right"
        self.pain_timer = timer.Timer(1000)
        super().__init__(level, self.anim_dict[f"{self.state}-{self.facing}"].image, rect, z)

    @property
    def health(self):
        return self.level.game.save.health

    @health.setter
    def health(self, value):
        self.level.game.save.health = value

    @property
    def health_capacity(self):
        return self.level.game.save.health_capacity

    @health_capacity.setter
    def health_capacity(self, value):
        self.level.game.save.health_capacity = value

    @property
    def emeralds(self):
        return self.level.game.save.emeralds

    @emeralds.setter
    def emeralds(self, value):
        self.level.game.save.emeralds = value

    @property
    def collision_rect(self):
        return pygame.Rect(self.rect.left + 5, self.rect.top + 13, 19, 13)

    def hurt(self, amount):
        if self.pain_timer.done():
            self.effects.append(visual_fx.Blink(speed=0.1, count=6))
            self.health = max(0, self.health - amount)
            self.pain_timer.reset()

    def update(self, dt):
        if not self.locked:
            held_input = self.level.game.input_queue.held
            just_input = self.level.game.input_queue.just_pressed
            self.state = "idle"
            if "quit" in just_input:
                self.level.run_cutscene("quit")
            if held_input["down"]:
                self.rect.y = min(self.MAX_Y, self.rect.y + self.BANK_SPEED * dt)
            if held_input["up"]:
                self.rect.y = max(self.MIN_Y, self.rect.y - self.BANK_SPEED * dt)
            if held_input["right"]:
                self.rect.x = min(self.MAX_X, self.rect.x + self.ACCEL_SPEED * dt)
            if held_input["left"]:
                self.rect.x = max(self.MIN_Y, self.rect.x - self.ACCEL_SPEED * dt)
                self.state = "lookback"
            if self.collision_rect.collidelist(self.level.collision_rects) != -1:
                print("OW!", self.level.collision_rects)
                self.hurt(10)
        anim = self.anim_dict[f"{self.state}-{self.facing}"]
        anim.update(dt)
        self.image = anim.image
        return super().update(dt)


class DeadPlayer(sprite.Sprite):
    def __init__(self, level, rect=(0, 0, 32, 32), z=0, **custom_fields):
        frames = level.game.loader.get_spritesheet("hoverboard.png", (32, 32))
        self.image = frames[4]
        super().__init__(level, frames[4], rect, z)

    def update(self, dt):
        self.rect.x -= BOARD_SPEED * dt
        if not super().update(dt) or self.rect.right < 0:
            return False
        return True


class Drone(sprite.Sprite):
    SPEED = 32
    FALL_SPEED = 48

    def __init__(self, level, rect=(0, 0, 10, 10), z=0, **custom_fields):
        frames = level.game.loader.get_spritesheet("drone.png", (10, 10))
        self.images = {
            "descent": SingleAnimation(frames[0]),
            "idle": SingleAnimation(frames[0]),
            "shoot": SingleAnimation(frames[1]),
        }
        self.state = "descent"
        self.true_pos = pygame.Vector2(pygame.Rect(rect).center)
        self.dest = pygame.Vector2(pygame.FRect(rect).center)
        self.age = 0
        self.shoot_cooldown = timer.Timer(1200)
        self.pos_cycle = timer.Timer(random.randint(0, 5000))
        self.shoot_start = pygame.Vector2(7, 4)
        self.facing_left = False
        self.distance = 16
        self.offset = 16
        self.new_pos()
        super().__init__(level, self.images[self.state], rect, z)
        self.true_pos.x = self.dest.x - self.level.map_rect.width

    def new_pos(self):
        self.distance = random.randint(-112, -48)
        self.offset = random.randint(-48, 48)
        self.pos_cycle = timer.Timer(2500)

    def update(self, dt):
        if not self.locked:
            if self.state == "descent":
                motion = self.dest - self.true_pos
                motion.clamp_magnitude_ip(self.FALL_SPEED * dt)
                self.true_pos += motion
                print(self.true_pos)
                if self.true_pos.distance_squared_to(self.dest) < 4:
                    print("idle")
                    self.state = "idle"
            else:
                self.age += dt
                desired_position = pygame.Vector2(self.level.player.pos.x + self.distance, self.level.player.pos.y + self.offset)
                dist = (desired_position - self.true_pos).length_squared()
                if dist > 16:
                    motion = desired_position - self.true_pos
                    motion.scale_to_length(self.SPEED * dt)
                    self.true_pos += motion
                    if dist < 64:
                        self.state = "shoot"
                    else:
                        self.state = "idle"
                elif self.shoot_cooldown.done():
                    direction = pygame.Vector2(100, 0)
                    if self.facing_left:
                        direction.x *= -1
                    self.level.add_sprite(
                        projectile.Laser(
                            self.level,
                            pygame.Rect(self.rect.topleft + self.shoot_start, (4, 1)),
                            self.z,
                            direction,
                        )
                    )
                    self.new_pos()
                    self.shoot_cooldown.reset()
                    self.state = "idle"
                if self.pos_cycle.done():
                    self.new_pos()
        self.shoot_cooldown.update()
        self.pos_cycle.update()
        self.facing_left = self.true_pos.x > self.level.player.pos.x
        self.rect.center = self.true_pos
        self.rect.y += 3 * sin(self.age * 5)
        self.images[self.state].flip_x = self.facing_left
        self.images[self.state].update(dt)
        self.image = self.images[self.state].image
        return super().update(dt)


class Rock(sprite.Sprite):
    groups = {"static-collision"}

    def __init__(self, level, rect=(0, 0, 16, 16), z=0, **custom_fields):
        image = level.game.loader.get_surface("tileset.png").subsurface(64, 192, 16, 16)
        super().__init__(level, image, rect, z)

    @property
    def collision_rect(self):
        return self.rect

    def update(self, dt):
        if not self.locked:
            self.rect.left -= BOARD_SPEED * dt
            if self.rect.right < 0:
                return False
        return super().update(dt)



class Stump(sprite.Sprite):
    ...