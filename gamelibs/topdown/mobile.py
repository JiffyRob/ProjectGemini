from math import sin
import random
from typing import Any, Generator

import pygame
from pygame.typing import RectLike, Point

from gamelibs import sprite, projectile, timer, visual_fx, interfaces, hardware
from gamelibs.animation import Animation, SingleAnimation, NoLoopAnimation

WALK_SPEED = 64
BOARD_SPEED = 96
FALL_SPEED = 128


class PhysicsSprite(sprite.Sprite, interfaces.Collider, interfaces.Turner):
    collision_groups = {
        "collision",
        "water",
        "mountain",
        "saline",
        "lava",
        "purple",
        "chasm",
    }

    def __init__(
        self,
        level: interfaces.Level,
        image: pygame.Surface | None = None,
        rect: RectLike = (0, 0, 16, 16),
        z: int = 0,
        weight: float = 10,
        **_: Any,
    ) -> None:
        super().__init__(level, image=image, rect=rect, z=z)
        self.weight: float = weight
        self.velocity: pygame.Vector2 = pygame.Vector2()
        self.desired_velocity: pygame.Vector2 = pygame.Vector2()

    @property
    def collision_rect(self) -> interfaces.MiscRect:
        return self.rect.copy()

    def on_xy_collision(self) -> None:
        pass

    def on_map_departure(self, directions: list[interfaces.Direction]) -> None:
        pass

    def update(self, dt: float) -> bool:
        # physics
        vel = self.velocity * dt * (not self.locked)
        self.rect.clamp_ip(self.get_level().map_rect)
        self.rect.center += vel
        departure_directions: list[interfaces.Direction] = []
        iterator = search(self.pos)
        collision_rects: list[interfaces.MiscRect] = []
        for group in self.collision_groups:
            collision_rects.extend(self.get_level().get_rects(group))
        while self.collision_rect.collidelist(collision_rects) >= 0:
            self.rect.center = next(iterator)
        if self.rect.top < self.get_level().map_rect.top:
            departure_directions.append(interfaces.Direction.UP)
        if self.rect.bottom > self.get_level().map_rect.bottom:
            departure_directions.append(interfaces.Direction.DOWN)
        if self.rect.left < self.get_level().map_rect.left:
            departure_directions.append(interfaces.Direction.LEFT)
        if self.rect.right > self.get_level().map_rect.right:
            departure_directions.append(interfaces.Direction.RIGHT)
        if departure_directions:
            self.on_map_departure(departure_directions)
        return super().update(dt)


class Player(PhysicsSprite, interfaces.Player):
    groups = {"player", *PhysicsSprite.groups}

    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike = (0, 0, 16, 16),
        z: int = 0,
        **custom_fields: Any,
    ) -> None:
        self.dest = pygame.Vector2(pygame.Rect(rect).center)
        super().__init__(level, rect=rect, image=None, z=z)
        images = hardware.loader.get_spritesheet("me.png")
        board_images = hardware.loader.get_spritesheet("hoverboard.png", (32, 32))
        self.anim_dict: dict[str, interfaces.Animation] = {
            "entrance-board": Animation(board_images[4:8], 0.1),
            "entrance-fall": SingleAnimation(images[1]),
            "walk-up": Animation(images[4:8]),
            "idle-up": Animation((images[5],)),
            "walk-right": Animation(images[8:12]),
            "idle-right": Animation((images[9],)),
            "walk-down": Animation(images[0:4]),
            "idle-down": Animation((images[1],)),
            "walk-left": Animation(images[8:12], flip_x=True),
            "idle-left": Animation((images[9],), flip_x=True),
        }
        entrance = custom_fields.get("entrance", "normal")
        if entrance == "board":
            self.state = "entrance-board"
            self.rect.right = 0
        elif entrance == "fall":
            self.state = "entrance-fall"
            self.rect.bottom = 0
        else:
            self.state = "idle"
        self.last_facing = interfaces.Direction.RIGHT
        self.image = self.anim_dict["idle-right"].image
        self.pain_timer = timer.Timer(1000)
        self.pain_timer.finish()

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

    def get_inventory(self, name: str) -> int:
        return hardware.save.get_state("inventory").get(name, 0)

    def acquire(self, thing: str, count: int = 1) -> bool:
        # TODO: this mutability looks not right
        hardware.save.get_state("inventory")[thing] = self.get_inventory(thing) + count
        return True  # TODO: return whether acquisition was successful

    @property
    def interaction_rect(self) -> interfaces.MiscRect:
        return self.rect.move(self.facing.to_vector() * 8)

    @property
    def head_rect(self) -> interfaces.MiscRect:
        rect = pygame.Rect(8, 1, 8, 8)
        rect.x += self.rect.x
        rect.y += self.rect.y
        return rect

    @property
    def collision_rect(self) -> interfaces.MiscRect:
        rect = pygame.FRect(0, 0, 14, 8)
        rect.midbottom = self.rect.midbottom
        return rect

    def on_map_departure(self, directions: list[interfaces.Direction]) -> None:
        if self.get_level().map_type != interfaces.MapType.HOUSE:
            long_name = f"{self.get_level().name}_{directions[0]}"
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
                short_name, direction=directions[0], position=self.pos
            )
        else:
            self.get_level().run_cutscene("level_exit")

    @property
    def facing(self) -> interfaces.Direction:
        if abs(self.desired_velocity.y) > abs(self.desired_velocity.x):
            if self.desired_velocity.y < 0:
                self.last_facing = interfaces.Direction.UP
            elif self.desired_velocity.y:
                self.last_facing = interfaces.Direction.DOWN
        if self.desired_velocity.x < 0:
            self.last_facing = interfaces.Direction.LEFT
        elif self.desired_velocity.x:
            self.last_facing = interfaces.Direction.RIGHT
        return self.last_facing

    def swap_state(self, new: str) -> None:
        if self.state != new:
            self.state = new
            self.image = self.anim_dict[f"{self.state}-{self.facing}"].image

    def interact(self) -> interfaces.InteractionResult:
        for sprite in self.get_level().get_group("interactable"):
            if sprite.collision_rect.colliderect(self.interaction_rect):  # type: ignore
                print("interact w/", sprite)
                if sprite.interact() == interfaces.InteractionResult.NO_MORE:  # type: ignore
                    return interfaces.InteractionResult.MORE
        return interfaces.InteractionResult.FAILED

    def update(self, dt: float) -> bool:
        if "entrance" in self.state:
            if self.state == "entrance-board":
                self.rect.center += (self.dest - self.pos).clamp_magnitude(
                    BOARD_SPEED * dt
                )
                if self.pos.distance_squared_to(self.dest) <= 1:
                    self.get_level().spawn("Hoverboard", (self.rect.topleft, (32, 32)))
                    hardware.save.set_state("hoverboarded", True)
                    self.rect.center = pygame.Rect(self.rect.topleft, (32, 32)).center
                    self.state = "idle-right"
            if self.state == "entrance-fall":
                self.rect.center += (self.dest - self.pos).clamp_magnitude(
                    FALL_SPEED * dt
                )
                if self.pos.distance_squared_to(self.dest) <= 1:
                    self.state = "idle-right"
                    hardware.input_queue.rumble(0.5, 0.5, 1000)
                    self.get_level().shake()
            self.anim_dict[self.state].update(dt)
            self.image = self.anim_dict[self.state].image
            return sprite.Sprite.update(self, dt)
        self.desired_velocity *= 0
        if not self.locked:
            pressed = hardware.input_queue.just_pressed
            if "interact" in pressed:
                self.interact()
            if "quit" in pressed:
                self.get_level().run_cutscene("quit")
            held = hardware.input_queue.held
            if "up" in held:
                self.walk_up()
            if "down" in held:
                self.walk_down()
            if "left" in held:
                self.walk_left()
            if "right" in held:
                self.walk_right()
            self.desired_velocity.clamp_magnitude_ip(WALK_SPEED)
            self.velocity = self.desired_velocity
        if self.velocity and not self.locked:
            self.swap_state("walk")
        else:
            self.swap_state("idle")
        state = f"{self.state}-{self.facing}"
        self.anim_dict[state].update(dt)
        self.image = self.anim_dict[state].image
        return super().update(dt)

    def hurt(self, amount: int) -> None:
        if self.pain_timer.done():
            self.effects.append(visual_fx.Blink(speed=0.1, count=6))
            self.health = max(0, self.health - amount)
            self.pain_timer.reset()
            if self.health > 0:
                hardware.input_queue.rumble(1, 1, 500)
            else:
                hardware.input_queue.rumble(1, 1, 1000)
                self.get_level().run_cutscene("death")

    def heal(self, amount: int) -> None:
        self.health = min(self.max_health, self.health + amount)

    def pay(self, emeralds: int) -> None:
        self.emeralds = min(999, self.emeralds + emeralds)

    def charge(self, emeralds: int) -> None:
        self.emeralds = max(0, self.emeralds - emeralds)

    def walk_left(self) -> None:
        self.desired_velocity.x -= WALK_SPEED

    def walk_right(self) -> None:
        self.desired_velocity.x += WALK_SPEED

    def walk_up(self) -> None:
        self.desired_velocity.y -= WALK_SPEED

    def walk_down(self) -> None:
        self.desired_velocity.y += WALK_SPEED


class Iball(sprite.Sprite):
    SPEED = 32

    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike = (0, 0, 5, 5),
        z: int = 0,
        **_: Any,
    ):
        frames = hardware.loader.get_spritesheet("iball.png", (5, 5))
        self.frames = {
            "down": frames[0],
            "right": frames[1],
            "up": frames[2],
            "left": frames[3],
        }
        self.facing = "right"
        self.age = 0
        super().__init__(
            level,
            self.frames[self.facing],
            rect,
            z + 1,
        )
        self.true_pos = pygame.Vector2(self.rect.center)
        self.shoot_cooldown = timer.Timer(300)

    def nearest_in_rect(self, rect: interfaces.MiscRect) -> pygame.Vector2:
        x, y = self.true_pos
        return pygame.Vector2(
            pygame.math.clamp(x, rect.left, rect.right),
            pygame.math.clamp(y, rect.top, rect.bottom),
        )

    def update(self, dt: float) -> bool:
        if not self.locked:
            # motion handling
            self.age += dt
            desired_motion = (
                self.nearest_in_rect(self.get_player().head_rect) - self.true_pos
            )
            self.true_pos = pygame.Vector2(self.true_pos) + desired_motion * 4 * dt
            self.rect.center = self.true_pos
            self.rect.y += 3 * sin(self.age * 8)
            print(self.rect.size)

            # image handling
            self.facing = self.get_player().facing
            self.image = self.frames[self.facing]

            # input handling
            pressed = hardware.input_queue.just_pressed
            if "shoot" in pressed and self.shoot_cooldown.done():
                self.effects.append(visual_fx.Blink(speed=0.1, count=1))
                self.get_level().add_sprite(
                    projectile.MiniLaser(
                        self.get_level(),
                        pygame.Rect(self.rect.center, (2, 1)),
                        self.z,
                        self.facing,
                    )
                )
                self.shoot_cooldown.reset()

        self.shoot_cooldown.update()
        super().update(dt)
        return True


class Drone(sprite.Sprite):
    groups = {"hurtable"}
    SPEED = 32
    FALL_SPEED = 256
    MAX_HEALTH = 2

    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike = (0, 0, 10, 10),
        z: int = 0,
        **_: Any,
    ) -> None:
        frames = hardware.loader.get_spritesheet("drone.png", (10, 10))
        self.images: dict[str, interfaces.Animation] = {
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
        self.true_pos.y = self.dest.y - self.get_level().map_rect.height

    @property
    def collision_rect(self) -> pygame.FRect | pygame.Rect:
        return self.rect.inflate(-2, -2)

    def new_pos(self) -> None:
        self.distance = random.randint(16, 96)
        if random.randint(0, 1):
            self.distance *= -1
        self.offset = random.randint(-16, 16)
        self.pos_cycle = timer.Timer(2500)

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

    def update(self, dt: float) -> bool:
        if not self.locked:
            if self.state == "descent":
                motion = self.dest - self.true_pos
                motion.clamp_magnitude_ip(self.FALL_SPEED * dt)
                self.true_pos += motion
                if self.true_pos.distance_squared_to(self.dest) < 4:
                    self.state = "idle"
            else:
                self.age += dt
                desired_position = pygame.Vector2(
                    self.get_player().pos.x + self.distance,
                    self.get_player().pos.y + self.offset,
                )
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


class TumbleFish(sprite.Sprite):
    ROLL_SPEED = 96
    MOUNTAIN_ROLL_SPEED = 128

    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike = (0, 0, 16, 16),
        z: int = 0,
        **_: Any,
    ) -> None:
        frames = hardware.loader.get_spritesheet("topdown-sprites.png", (16, 16))
        self.eye_frames = {
            "up": frames[5],
            "down": frames[4],
            "left": frames[6],
            "right": frames[7],
        }
        self.base_frames: dict[str, interfaces.Animation] = {
            "idle": SingleAnimation(frames[8]),
            "prep": NoLoopAnimation(frames[8:10]),
            "rolling": Animation(frames[11:14]),
        }
        self.state = "idle"
        self.hit_chasm = False
        super().__init__(level, None, rect, z)

    def roll(self) -> None:
        self.state = "prep"
        self.rect.y -= 2

    def update(self, dt: float) -> bool:
        if self.state == "idle":
            self.image = self.base_frames["idle"].image.copy()
            direction = (
                pygame.Vector2(self.get_level().get_x(), self.get_level().get_y())
                - self.pos
            )
            self.image.blit(
                self.eye_frames[interfaces.Direction.from_vector(direction).name],
                (0, 0),
            )
            if abs(direction.x) < 16 and 0 < direction.y < 96:
                self.roll()
        elif self.state == "prep":
            if self.base_frames["prep"].done():
                self.state = "rolling"
            self.image = self.base_frames["prep"].image
            self.base_frames["prep"].update(dt)
        elif self.state == "rolling":
            speed = self.ROLL_SPEED
            if self.rect.collidelist(self.get_level().get_rects("mountain")) != -1:
                speed = self.MOUNTAIN_ROLL_SPEED
            self.rect.y += speed * dt
            self.image = self.base_frames["rolling"].image
            self.base_frames["rolling"].update(dt)
            if (
                self.hit_chasm
                and self.rect.collidelist(self.get_level().get_rects("ground")) == -1
            ):
                return False
            if (
                not self.hit_chasm
                and self.rect.collidelist(self.get_level().get_rects("chasm")) != -1
            ):
                self.hit_chasm = True
        if self.rect.colliderect(self.get_player().collision_rect):
            self.get_player().hurt(2)
        super().update(dt)
        return True


class DeadPlayer(sprite.Sprite):
    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike = (0, 0, 16, 16),
        z: int = 0,
        **_: Any,
    ) -> None:
        self.anim = NoLoopAnimation(
            hardware.loader.get_spritesheet("me.png")[30:35], 0.1
        )
        super().__init__(level, self.anim.image, rect, z)

    def update(self, dt: float) -> bool:
        self.anim.update(dt)
        self.image = self.anim.image
        return super().update(dt)


def search(start: Point) -> Generator[tuple[int, int]]:
    """yields positions in a grid of spacing 'dist', in order of rough proximity to 'start'"""

    def neighbors(
        position: tuple[int, int],
    ) -> tuple[tuple[int, int], tuple[int, int], tuple[int, int], tuple[int, int]]:
        return (
            (position[0], position[1] - 1),
            (position[0] + 1, position[1]),
            (position[0], position[1] + 1),
            (position[0] - 1, position[1]),
        )

    # breadth first search (https://www.redblobgames.com/pathfinding/a-star/introduction.html)
    frontier: list[tuple[int, int]] = list()
    start = (int(start[0]), int(start[1]))
    frontier.append(start)
    reached: set[tuple[int, int]] = set()
    reached.add(start)
    while True:
        current = frontier.pop(0)
        for next in neighbors(current):
            if next not in reached:
                frontier.append(next)
                reached.add(next)
        yield current
