from math import sin
import random

import pygame

from scripts import sprite, projectile, timer
from scripts.animation import Animation, SingleAnimation, NoLoopAnimation

WALK_SPEED = 64
BOARD_SPEED = 96
FALL_SPEED = 128

REVERSE = {"up": "down", "down": "up", "left": "right", "right": "left"}


class PhysicsSprite(sprite.Sprite):
    def __init__(
        self, level, image=None, rect=(0, 0, 16, 16), z=0, weight=10, **custom_fields
    ):
        super().__init__(level, image=image, rect=rect, z=z)
        self.weight = weight
        self.velocity = pygame.Vector2()
        self.desired_velocity = pygame.Vector2()

    @property
    def collision_rect(self):
        return self.rect.copy()

    def on_xy_collision(self):
        pass

    def on_map_departure(self, directions):
        pass

    def update(self, dt):
        # physics
        vel = self.velocity * dt * (not self.locked)
        self.rect.clamp_ip(self.level.map_rect)
        self.rect.center += vel
        departure_directions = []
        iterator = search(self.pos)
        while self.collision_rect.collidelist(self.level.collision_rects) >= 0:
            self.rect.center = next(iterator)
        if self.rect.top < self.level.map_rect.top:
            departure_directions.append("up")
        if self.rect.bottom > self.level.map_rect.bottom:
            departure_directions.append("down")
        if self.rect.left < self.level.map_rect.left:
            departure_directions.append("left")
        if self.rect.right > self.level.map_rect.right:
            departure_directions.append("right")
        if departure_directions:
            self.on_map_departure(departure_directions)
        return super().update(dt)


class Player(PhysicsSprite):
    reverses = {
        "up": "down",
        "right": "left",
        "down": "up",
        "left": "right",
    }

    def __init__(self, level, rect=(0, 0, 16, 16), z=0, **custom_fields):
        self.dest = pygame.Vector2(pygame.Rect(rect).center)
        super().__init__(level, rect=rect, image=None, z=z)
        images = level.game.loader.get_spritesheet("me.png")
        board_images = level.game.loader.get_spritesheet("hoverboard.png", (32, 32))
        self.anim_dict = {
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
        self.last_facing = "right"
        self.image = self.anim_dict["idle-right"].image
        self.emeralds = 10

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
    def interaction_rect(self):
        return self.rect.move(
            {
                "up": (0, -8),
                "down": (0, 8),
                "left": (-8, 0),
                "right": (8, 0),
            }[self.facing]
        )

    @property
    def collision_rect(self):
        rect = pygame.FRect(0, 0, 14, 8)
        rect.midbottom = self.rect.midbottom
        return rect

    def on_map_departure(self, directions):
        if self.level.map_type != self.level.MAP_HOUSE:
            long_name = f"{self.level.name}_{directions[0]}"
            x = long_name.count("right") - long_name.count("left")
            y = long_name.count("down") - long_name.count("up")
            short_name = self.level.name.split("_")[0]
            if x < 0:
                short_name += "_left" * abs(x)
            if x > 0:
                short_name += "_right" * x
            if y < 0:
                short_name += "_up" * abs(y)
            if y > 0:
                short_name += "_down" * y
            self.level.switch_level(
                short_name, direction=directions[0], position=self.pos
            )
        else:
            self.level.run_cutscene("level_exit")

    @property
    def facing(self):
        if abs(self.desired_velocity.y) > abs(self.desired_velocity.x):
            if self.desired_velocity.y < 0:
                self.last_facing = "up"
            elif self.desired_velocity.y:
                self.last_facing = "down"
        if self.desired_velocity.x < 0:
            self.last_facing = "left"
        elif self.desired_velocity.x:
            self.last_facing = "right"
        return self.last_facing

    def swap_state(self, new):
        if self.state != new:
            self.state = new
            self.image = self.anim_dict[f"{self.state}-{self.facing}"].image

    def interact(self):
        for sprite in self.level.groups["interactable"]:
            if sprite.collision_rect.colliderect(self.interaction_rect):
                print("interact w/", sprite)
                sprite.interact()

    def update(self, dt):
        if "entrance" in self.state:
            if self.state == "entrance-board":
                self.rect.center += (self.dest - self.pos).clamp_magnitude(
                    BOARD_SPEED * dt
                )
                if self.pos.distance_squared_to(self.dest) <= 1:
                    self.level.spawn("Hoverboard", (self.rect.topleft, (32, 32)))
                    self.level.game.save.hoverboarded = True
                    self.rect.center = pygame.Rect(self.rect.topleft, (32, 32)).center
                    self.state = "idle-right"
            if self.state == "entrance-fall":
                self.rect.center += (self.dest - self.pos).clamp_magnitude(
                    FALL_SPEED * dt
                )
                if self.pos.distance_squared_to(self.dest) <= 1:
                    self.state = "idle-right"
                    self.level.shake()
            self.anim_dict[self.state].update(dt)
            self.image = self.anim_dict[self.state].image
            return sprite.Sprite.update(self, dt)
        self.desired_velocity *= 0
        if not self.locked:
            pressed = self.level.game.input_queue.just_pressed
            if "interact" in pressed:
                self.interact()
            if "quit" in pressed:
                self.level.run_cutscene("quit")
            held = self.level.game.input_queue.held
            if held["up"]:
                self.walk_up()
            if held["down"]:
                self.walk_down()
            if held["left"]:
                self.walk_left()
            if held["right"]:
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
        return super().update(dt) and self.health > 0

    def hurt(self, amount):
        self.health = max(0, self.health - amount)

    def heal(self, amount):
        self.health = min(self.health_capacity, self.health + amount)

    def pay(self, emeralds):
        self.emeralds = min(999, self.emeralds + emeralds)

    def charge(self, emeralds):
        self.emeralds = max(0, self.emeralds - emeralds)

    def walk_left(self):
        self.desired_velocity.x -= WALK_SPEED

    def walk_right(self):
        self.desired_velocity.x += WALK_SPEED

    def walk_up(self):
        self.desired_velocity.y -= WALK_SPEED

    def walk_down(self):
        self.desired_velocity.y += WALK_SPEED


class Drone(sprite.Sprite):
    SPEED = 32
    FALL_SPEED = 256

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
        self.true_pos.y = self.dest.y - self.level.map_rect.height

    def new_pos(self):
        self.distance = random.randint(16, 96)
        if random.randint(0, 1):
            self.distance *= -1
        self.offset = random.randint(-16, 16)
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
                desired_position = pygame.Vector2(
                    self.level.player.pos.x + self.distance,
                    self.level.player.pos.y + self.offset,
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


class DeadPlayer(sprite.Sprite):
    def __init__(self, level, rect=(0, 0, 16, 16), z=0, **custom_fields):
        self.anim = NoLoopAnimation(
            level.game.loader.get_spritesheet("me.png")[30:35], 0.1
        )
        super().__init__(level, self.anim.image, rect, z)

    def update(self, dt):
        self.anim.update(dt)
        self.image = self.anim.image
        return super().update(dt)


def search(start: tuple | pygame.Vector2):
    """yields positions in a grid of spacing 'dist', in order of rough proximity to 'start'"""

    def neighbors(position: tuple[int]):
        return (
            (position[0], position[1] - 1),
            (position[0] + 1, position[1]),
            (position[0], position[1] + 1),
            (position[0] - 1, position[1]),
        )

    # breadth first search (https://www.redblobgames.com/pathfinding/a-star/introduction.html)
    frontier = list()
    frontier.append(tuple(start))
    reached = set()
    reached.add(tuple(start))
    while True:
        current = frontier.pop(0)
        for next in neighbors(current):
            if next not in reached:
                frontier.append(next)
                reached.add(next)
        yield current
