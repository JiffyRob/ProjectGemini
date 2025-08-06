import random
from math import sin
from collections import deque
from typing import Any, cast

import pygame
from pygame.typing import RectLike, Point

from gamelibs import (
    sprite,
    util_draw,
    timer,
    projectile,
    visual_fx,
    easings,
    interfaces,
    hardware,
)
from gamelibs.animation import Animation, SingleAnimation, NoLoopAnimation


class ScrollingBackground(sprite.Sprite, interfaces.Background):
    STATE_GROUND = 0
    STATE_WATER = 1
    STATE_SLOWDOWN = 2

    def __init__(
        self,
        level: interfaces.HoverboardLevel,
        rect: RectLike = (
            (
                0,
                0,
            ),
            util_draw.RESOLUTION,
        ),
        z: int = 0,
    ) -> None:
        tileset = hardware.loader.get_surface("tileset.png")
        self.land_tile = tileset.subsurface((112, 176, 16, 16))
        self.land_sea_transition = tileset.subsurface((128, 176, 16, 16))
        self.sea_land_transition = tileset.subsurface((96, 176, 16, 16))
        self.sea_tile = hardware.loader.get_spritesheet("liquid.png")[4]
        self.state = self.STATE_WATER
        self.swap_cooldown = timer.Timer(10000)
        self.spawn_cooldown = timer.Timer(100)
        self.speedup_time = 5000
        self.speedup_timer = timer.Timer(5000)
        self.slowdown_timer = timer.Timer(70000)
        self.stop_timer = timer.Timer(75000)
        self.x_offset: float = 0
        self.images: deque[pygame.Surface] = deque()
        self.rect = pygame.FRect(rect)
        self.land_rock_chance = 150 // 6
        self.sea_rock_chance = 100 // 6
        self.stump_chance = 150 // 6
        self.locked = False
        self.finished = False
        self.age = 0

        super().__init__(level, self.get_next_image(), rect, z)

    def get_level(self) -> interfaces.HoverboardLevel:
        return self.get_level()

    def get_player(self) -> interfaces.HoverboardPlayer:
        return self.get_player()

    def lock(self) -> None:
        self.locked = True

    def unlock(self) -> None:
        self.locked = False

    def get_next_image(self) -> pygame.Surface:
        if self.state == self.STATE_SLOWDOWN:
            return util_draw.repeat_surface(self.sea_tile, (16, self.rect.height))
        if self.swap_cooldown.done():
            self.swap_cooldown.reset()
            if self.state == self.STATE_GROUND:
                self.state = self.STATE_WATER
                return util_draw.repeat_surface(
                    self.land_sea_transition, (16, self.rect.height)
                )
            else:
                self.state = self.STATE_GROUND
                return util_draw.repeat_surface(
                    self.sea_land_transition, (16, self.rect.height)
                )
        elif self.state == self.STATE_GROUND:
            return util_draw.repeat_surface(self.land_tile, (16, self.rect.height))
        else:
            return util_draw.repeat_surface(self.sea_tile, (16, self.rect.height))

    def update(self, dt: float) -> None:  # type: ignore[override]
        if not self.locked:
            self.age += dt
            self.x_offset -= self.get_level().speed * dt
            self.swap_cooldown.update()
            self.spawn_cooldown.update()
            self.slowdown_timer.update()
            self.speedup_timer.update()
            if (
                self.state == self.STATE_GROUND
                and 0.05 < self.swap_cooldown.percent_complete() < 0.95
                and self.spawn_cooldown.done()
            ):
                if not random.randint(0, self.land_rock_chance):
                    self.get_level().spawn(
                        "Rock",
                        (
                            util_draw.RESOLUTION[0] + 8,
                            random.randint(0, util_draw.RESOLUTION[1]),
                            16,
                            16,
                        ),
                        z=8,
                    )
                if not random.randint(0, self.stump_chance):
                    self.get_level().spawn(
                        "Stump",
                        (
                            util_draw.RESOLUTION[0] + 8,
                            random.randint(0, util_draw.RESOLUTION[1]),
                            16,
                            16,
                        ),
                        z=8,
                    )
                self.spawn_cooldown.reset()
            elif (
                self.state == self.STATE_WATER
                and 0.05 < self.swap_cooldown.percent_complete() < 0.95
                and self.spawn_cooldown.done()
            ):
                if not random.randint(0, self.sea_rock_chance):
                    self.get_level().spawn(
                        "Rock",
                        (
                            util_draw.RESOLUTION[0] + 8,
                            random.randint(0, util_draw.RESOLUTION[1]),
                            16,
                            16,
                        ),
                        z=8,
                    )
                self.spawn_cooldown.reset()
            if not self.speedup_timer.done():
                self.get_level().speed = 200 * easings.in_out_quad(
                    self.age / self.speedup_time * 1000
                )
            if self.slowdown_timer.done():
                self.get_level().speed = 200 * (
                    1
                    - easings.in_out_quad(
                        (self.age * 1000 - self.slowdown_timer.wait) / self.speedup_time
                    )
                )
                self.state = self.STATE_SLOWDOWN
                self.get_level().message("drones", "leave")
            if self.stop_timer.done():
                self.get_level().speed = 0
                if not self.finished:
                    self.get_player().exit()
                    self.finished = True

    def draw(self, surface: pygame.Surface, offset: Point) -> None:
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


class Player(sprite.Sprite, interfaces.HoverboardPlayer):
    groups = {"interactable", "player"}

    BANK_SPEED = 82
    ACCEL_SPEED = 48

    MIN_Y = 32
    MAX_Y = util_draw.RESOLUTION[1] - 32
    MIN_X = 32
    MAX_X = util_draw.RESOLUTION[0] - 32

    def __init__(
        self,
        level: interfaces.HoverboardLevel,
        rect: RectLike = (0, 0, 32, 32),
        z: int = 0,
    ) -> None:
        frames = hardware.loader.get_spritesheet("hoverboard.png", (32, 32))
        self.anim_dict = {
            "entering-right": Animation(frames[4:8], 0.1),
            "empty-right": Animation(frames[:4], 0.1),
            "idle-right": Animation(frames[4:8], 0.1),
            "lookback-left": Animation(frames[8:12], 0.1),
            "exiting-right": Animation(frames[4:8], 0.1),
        }
        self.state = "entering"
        self._facing = interfaces.Direction.RIGHT
        self.pain_timer = timer.Timer(1000)
        super().__init__(
            level, self.anim_dict[f"{self.state}-{self.facing}"].image, rect, z
        )
        self.rect.right = 0

    def interact(self) -> interfaces.InteractionResult:
        return interfaces.InteractionResult.FAILED

    @property
    def facing(self) -> interfaces.Direction:
        return self._facing

    @property
    def health(self) -> int:
        return hardware.save.get_state("health")

    @health.setter
    def health(self, value: int) -> None:
        hardware.save.set_state("health", value)

    @property
    def max_health(self) -> int:
        return hardware.save.get_state("max_health")

    @max_health.setter
    def max_health(self, value: int) -> None:
        hardware.save.set_state("max_health", value)

    @property
    def emeralds(self) -> int:
        return hardware.save.get_state("emeralds")

    @emeralds.setter
    def emeralds(self, value: int) -> None:
        hardware.save.set_state("emeralds", value)

    @property
    def collision_rect(self) -> pygame.Rect:
        return pygame.Rect(self.rect.left + 8, self.rect.top + 14, 12, 11)

    @property
    def head_rect(self) -> pygame.Rect:
        rect = pygame.Rect(12, 9, 8, 8)
        rect.x += self.rect.x
        rect.y += self.rect.y
        return rect

    def get_inventory(self, name: str) -> int:
        return hardware.save.get_state("inventory").get(name, 0)

    def acquire(self, thing: str, count: int = 1) -> bool:
        # TODO: this mutability looks not right
        hardware.save.get_state("inventory")[thing] = self.get_inventory(thing) + count
        return True  # TODO: return whether acquisition was successful

    def pay(self, emeralds: int) -> None:
        self.emeralds = min(999, self.emeralds + emeralds)

    def charge(self, emeralds: int) -> None:
        self.emeralds = max(0, self.emeralds - emeralds)

    def hurt(self, amount: int) -> None:
        if self.pain_timer.done():
            self.effects.append(visual_fx.Blink(speed=0.1, count=6))
            self.health = max(0, self.health - amount)
            self.pain_timer.reset()
            if self.health > 0:
                hardware.input_queue.rumble(1, 1, 500)
            else:
                hardware.input_queue.rumble(1, 1, 1000)
                self.get_game().run_cutscene("death")

    def heal(self, amount: int) -> None:
        self.health = min(self.max_health, self.health + amount)

    def exit(self) -> None:
        self.state = "exiting"

    def dismount(self) -> None:
        self.state = "empty"
        rect = pygame.Rect(0, 0, 16, 16)
        rect.midbottom = self.rect.midbottom
        player = self.get_level().spawn("Player", rect, self.z)
        self.get_level().set_player(cast(interfaces.Player, player))

    def update(self, dt: float) -> bool:
        if not self.locked:
            if self.state == "entering":
                self.rect.left += 64 * dt
                if self.rect.left > 32:
                    self.state = "idle"
            elif self.state == "exiting":
                self.rect.left += 64 * dt
                if self.rect.left > self.get_level().map_rect.right:
                    long_name = f"{self.get_level().name}_right"
                    x = long_name.count("right") - long_name.count("left")
                    y = long_name.count("down") - long_name.count("up")
                    short_name = str(self.get_level().name).split("_")[0]
                    if x < 0:
                        short_name += "_left" * abs(x)
                    if x > 0:
                        short_name += "_right" * x
                    if y < 0:
                        short_name += "_up" * abs(y)
                    if y > 0:
                        short_name += "_down" * y
                    self.get_game().switch_level(
                        short_name,
                        direction=interfaces.Direction.RIGHT,
                        position=self.pos,
                        entrance=interfaces.MapEntranceType.HOVERBOARD,
                    )
            elif self.state != "empty":
                held_input = hardware.input_queue.held
                just_input = hardware.input_queue.just_pressed
                self.state = "idle"
                self._facing = interfaces.Direction.RIGHT
                if "quit" in just_input:
                    self.get_game().run_cutscene("quit")
                if "down" in held_input:
                    self.rect.y = min(self.MAX_Y, self.rect.y + self.BANK_SPEED * dt)
                if "up" in held_input:
                    self.rect.y = max(self.MIN_Y, self.rect.y - self.BANK_SPEED * dt)
                if "right" in held_input:
                    self.rect.x = min(self.MAX_X, self.rect.x + self.ACCEL_SPEED * dt)
                if "left" in held_input:
                    self.rect.x = max(self.MIN_Y, self.rect.x - self.ACCEL_SPEED * dt)
                    self.state = "lookback"
                    self._facing = interfaces.Direction.LEFT
                if (
                    self.collision_rect.collidelist(
                        self.get_level().get_rects("collision")
                    )
                    != -1
                ):
                    self.hurt(3)
        if self.state == "exiting":
            self._facing = interfaces.Direction.RIGHT
        anim = self.anim_dict[f"{self.state}-{self.facing}"]
        anim.update(dt)
        self.image = anim.image
        return super().update(dt)


class DeadPlayer(sprite.Sprite):
    def __init__(
        self,
        level: interfaces.HoverboardLevel,
        rect: RectLike = (0, 0, 16, 16),
        z: int = 0,
        **_: Any,
    ) -> None:
        self.anim = NoLoopAnimation(
            hardware.loader.get_spritesheet("me.png")[30:35], 0.1
        )
        super().__init__(level, self.anim.image, rect, z)

    def get_level(self) -> interfaces.HoverboardLevel:
        return super().get_level()  # type: ignore

    def update(self, dt: float) -> bool:
        self.anim.update(dt)
        self.image = self.anim.image
        self.rect.x -= self.get_level().speed * dt
        if not super().update(dt) or self.rect.right < 0:
            return False
        return True


class Drone(sprite.Sprite):
    groups = {"drones", "hurtable"}

    SPEED = 32
    FALL_SPEED = 48
    MAX_HEALTH = 2

    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike = (0, 0, 10, 10),
        z: int = 0,
        **_: Any,
    ) -> None:
        frames = hardware.loader.get_spritesheet("drone.png", (10, 10))
        self.images = {
            "ascent": SingleAnimation(frames[0]),
            "descent": SingleAnimation(frames[0]),
            "idle": SingleAnimation(frames[0]),
            "shoot": SingleAnimation(frames[1]),
        }
        self.state = "descent"
        self.true_pos: pygame.Vector2 = pygame.Vector2(pygame.Rect(rect).center)
        self.dest = pygame.Vector2(pygame.FRect(rect).center)
        self.age = 0
        self.shoot_cooldown = timer.Timer(1200)
        self.pos_cycle = timer.Timer(random.randint(0, 5000))
        self.shoot_start = pygame.Vector2(7, 4)
        self.facing_left = False
        self.distance = 16
        self.offset = 16
        self.new_pos()
        self.health = self.MAX_HEALTH
        self.pain_cooldown = timer.Timer(200)
        super().__init__(level, self.images[self.state].image, rect, z)
        self.true_pos.x = self.dest.x - self.get_level().map_rect.width

    def get_level(self) -> interfaces.HoverboardLevel:
        return super().get_level()  # type: ignore

    def hurt(self, amount: int) -> None:
        if self.pain_cooldown.done():
            self.pain_cooldown.reset()
            self.health -= amount
            if self.health <= 0:
                self.health = 0
                self.dead = True
            else:
                self.effects.append(
                    visual_fx.Blink(color=(205, 36, 36), speed=0.1, count=1)
                )
            print("OW!")

    @property
    def collision_rect(self) -> interfaces.MiscRect:
        return self.rect.inflate(-2, -2)

    def message(self, message: str) -> None:
        if message == "leave":
            self.leave()

    def leave(self) -> None:
        self.state = "ascent"
        self.dest = pygame.Vector2(-32, self.pos.y + self.offset)

    def new_pos(self) -> None:
        self.distance = random.randint(-84, -48)
        self.offset = random.randint(-64, 64)
        self.pos_cycle = timer.Timer(2500)

    def update(self, dt: float) -> bool:
        if not self.locked:
            if self.state == "descent":
                motion = self.dest - self.true_pos
                motion.clamp_magnitude_ip(self.FALL_SPEED * dt)
                self.true_pos += motion
                if self.true_pos.distance_squared_to(self.dest) < 4:
                    self.state = "idle"
            elif self.state == "ascent":
                motion = self.dest - self.true_pos
                motion.clamp_magnitude_ip(self.FALL_SPEED * dt)
                self.true_pos += motion
                if self.true_pos.distance_squared_to(self.dest) < 4:
                    return False
            else:
                self.age += dt
                desired_position = pygame.Vector2(
                    self.get_player().pos.x + self.distance,
                    self.get_player().pos.y + self.offset,
                )
                dist = (desired_position - self.true_pos).length_squared()
                if dist > 64:
                    motion = desired_position - self.true_pos
                    motion.scale_to_length(self.SPEED * dt)
                    self.true_pos += motion
                    if dist < 128:
                        self.state = "shoot"
                    else:
                        self.state = "idle"
                elif self.shoot_cooldown.done():
                    direction = interfaces.Direction.RIGHT
                    if self.facing_left:
                        direction = interfaces.Direction.LEFT
                    self.get_level().add_sprite(
                        projectile.Laser(
                            self.get_level(),
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
        self.facing_left = self.true_pos.x > self.get_player().pos.x
        self.rect.center = self.true_pos
        self.rect.y += 3 * sin(self.age * 5)
        self.images[self.state].flip_x = self.facing_left
        self.images[self.state].update(dt)
        self.image = self.images[self.state].image
        return super().update(dt)


class Rock(sprite.Sprite):
    groups = {"static-collision"}

    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike = (0, 0, 16, 16),
        z: int = 0,
        **_: Any,
    ) -> None:
        image = hardware.loader.get_surface("tileset.png").subsurface(64, 192, 16, 16)
        super().__init__(level, image, rect, z)

    def get_level(self) -> interfaces.HoverboardLevel:
        return super().get_level()  # type: ignore

    @property
    def collision_rect(self) -> interfaces.MiscRect:
        return self.rect

    def update(self, dt: float) -> bool:
        if not self.locked:
            self.rect.left -= self.get_level().speed * dt
            if self.rect.right < 0:
                return False
        return super().update(dt)


class Stump(sprite.Sprite):
    groups = {"static-collision"}

    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike = (0, 0, 16, 16),
        z: int = 0,
        **_: Any,
    ) -> None:
        image = hardware.loader.get_surface("tileset.png").subsurface(16, 256, 32, 32)
        super().__init__(level, image, rect, z)

    def get_level(self) -> interfaces.HoverboardLevel:
        return super().get_level()  # type: ignore

    @property
    def collision_rect(self) -> interfaces.MiscRect:
        return self.rect

    def update(self, dt: float) -> bool:
        if not self.locked:
            self.rect.left -= self.get_level().speed * dt
            if self.rect.right < 0:
                return False
        return super().update(dt)
