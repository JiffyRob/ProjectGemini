from queue import Queue

import pygame

from scripts import sprite, util_draw
from scripts.animation import Animation

WALK_SPEED = 64
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
        super().__init__(level, rect=rect, image=None, z=z)
        images = level.game.loader.get_spritesheet("me.png")
        self.anim_dict = {
            "walk-up": Animation(images[4:8]),
            "idle-up": Animation((images[5],)),
            "walk-right": Animation(images[8:12]),
            "idle-right": Animation((images[9],)),
            "walk-down": Animation(images[0:4]),
            "idle-down": Animation((images[1],)),
            "walk-left": Animation(images[8:12], flip_x=True),
            "idle-left": Animation((images[9],), flip_x=True),
        }
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
        if not self.level.is_house:
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
            self.level.switch_level(short_name, direction=directions[0], position=self.pos)
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
    frontier = Queue()
    frontier.put(tuple(start))
    reached = set()
    reached.add(tuple(start))
    while True:
        current = frontier.get()
        for next in neighbors(current):
            if next not in reached:
                frontier.put(next)
                reached.add(next)
        yield current
