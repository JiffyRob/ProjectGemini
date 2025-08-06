from typing import Any
import pygame
from pygame.typing import RectLike

from gamelibs import sprite, timer, visual_fx, interfaces, hardware
from gamelibs.animation import Animation, NoLoopAnimation, SingleAnimation
from gamelibs.platformer import mobile

ACCEL_SPEED = 6
DECCEL_SPEED = 6
WALK_SPEED = 84
JUMP_SPEED = 240
WALLJUMP_X_SPEED = 64
WALLJUMP_Y_SPEED = 400


class Player(mobile.PhysicsSprite, interfaces.PlatformerPlayer):
    groups = {"player", *mobile.PhysicsSprite.groups}

    def __init__(
        self,
        level: interfaces.PlatformerLevel,
        rect: RectLike = (0, 0, 16, 16),
        z: int = 0,
        **custom_fields: Any
    ) -> None:
        super().__init__(level, rect=rect, image=None, z=z)
        images = hardware.loader.get_spritesheet("me.png")
        self.anim_dict: dict[str, interfaces.Animation] = {
            "walk": Animation(images[8:12]),
            "idle": Animation((images[9],)),
            "jump": Animation((images[12],)),
            "pound": NoLoopAnimation((images[12:20]), 0.03),
            "pound-recover": NoLoopAnimation((images[20:28]), 0.1),
            "skid": SingleAnimation(images[28]),
        }
        self.state = "jump"
        self.jump_forced = False
        self.jump_cause: interfaces.JumpCause | None = None
        self.image = self.anim_dict[self.state].image
        self.facing_left = False
        self.pain_timer = timer.Timer(1000)
        self.pain_timer.finish()
        self.on_wall = False
        self.from_wall = False
        self.time_from_wall: float = 0
        self.time_on_wall: float = 0
        self.wall_direction = None

    @property
    def skidding(self) -> bool:
        return self.time_on_wall >= 0.2 and not self.on_ground

    @property
    def facing(self) -> interfaces.Direction:
        if self.facing_left:
            return interfaces.Direction.LEFT
        return interfaces.Direction.RIGHT

    @property
    def head_rect(self) -> interfaces.MiscRect:
        return pygame.FRect(self.rect.left, self.rect.top, self.rect.width, 8)

    @property
    def below_rect(self) -> pygame.FRect:
        return pygame.FRect(self.rect.left, self.rect.bottom, self.rect.width, 3)

    @property
    def name(self) -> str:
        return hardware.save.loaded_path

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

    def on_xy_collision(self, direction: interfaces.Direction) -> None:
        if direction == interfaces.Direction.LEFT:
            self.on_wall = True
            self.wall_direction = interfaces.Direction.LEFT
        if direction == interfaces.Direction.RIGHT:
            self.on_wall = True
            self.wall_direction = interfaces.Direction.RIGHT
        self.from_wall = False

    def on_fallout(self) -> None:
        self.health = 0

    def swap_state(self, new: str) -> None:
        if self.state != new:
            self.state = new
            self.anim_dict[self.state].restart()
            self.image = self.anim_dict[self.state].image

    def update(self, dt: float) -> bool:  # type: ignore
        if not self.locked:
            held_input = hardware.input_queue.held
            just_input = hardware.input_queue.just_pressed
            if (
                self.state == "jump"
                and "duck" in just_input
                and self.jump_cause == interfaces.JumpCause.NORMAL
            ):
                self.knife_pound()
            if self.state in {"idle", "walk", "jump", "skid"}:
                if "left" in held_input and not self.from_wall:
                    self.walk_left()
                if "right" in held_input and not self.from_wall:
                    self.walk_right()
                if (
                    not "left" in held_input
                    and not "right" in held_input
                    and self.on_ground
                ):
                    self.decelerate()
            else:
                self.velocity.x = 0
            self.velocity.x = pygame.math.clamp(
                self.velocity.x, -WALK_SPEED, WALK_SPEED
            )
            if "jump" in held_input:
                self.jump(just=("jump" in just_input))
            elif self.jump_cause == interfaces.JumpCause.NORMAL:
                self.velocity.y = max(self.velocity.y, self.velocity.y * 0.7)
            if "duck" in held_input:
                self.duck()
            if "quit" in hardware.input_queue.just_pressed:
                self.get_game().run_cutscene("quit")
            if "interact" in just_input:
                if self.facing_left:
                    interaction_rect = self.rect.move(-8, 0)
                else:
                    interaction_rect = self.rect.move(8, 0)
                # TODO: new getter for every sprite type?
                for sprite in self.get_level().get_group("interactable"):
                    if interaction_rect.colliderect(sprite.collision_rect):  # type: ignore
                        sprite.interact()  # type: ignore
                        break
        if self.state == "pound":
            hit = self.on_ground
            if not hit and not self.ducking:
                for sprite in self.get_level().get_group("time-reversable"):
                    if (
                        sprite.time_reverse_collision_rect.colliderect(self.below_rect)  # type: ignore
                        or self.on_ground
                    ):
                        sprite.reverse_time()  # type: ignore
                        sprite.collision_rect.update(sprite.time_reverse_collision_rect)  # type: ignore
                        self.velocity.y *= 0
                        hit = True
            if hit:
                self.swap_state("pound-recover")
                self.get_level().shake(axis=interfaces.Axis.Y)
                hardware.input_queue.rumble(0.5, 0.5, 250)
        elif not self.on_ground:
            if self.skidding:
                self.swap_state("skid")
                self.velocity.y *= 0.9
            else:
                self.swap_state("jump")
        elif self.velocity.x and self.state != "pound-recover":
            self.swap_state("walk")
        elif self.state != "pound-recover":
            self.swap_state("idle")
        if self.state == "pound-recover" and self.anim_dict[self.state].done():
            self.swap_state("idle")
        if self.velocity.x:
            self.facing_left = self.velocity.x < 0
        if self.velocity.y > 0 and self.state == "pound":
            self.get_level().time_phase(self.velocity.y / 64)
        self.anim_dict[self.state].update(dt)
        self.anim_dict[self.state].flip_x = self.facing_left
        self.image = self.anim_dict[self.state].image
        # push player into walls so they collide
        if self.on_wall:
            if self.wall_direction == interfaces.Direction.LEFT:
                self.velocity.x -= ACCEL_SPEED / 3
            if self.wall_direction == interfaces.Direction.RIGHT:
                self.velocity.x += ACCEL_SPEED / 3
        if self.from_wall:
            self.time_from_wall += dt
            if self.time_from_wall >= 0.5:
                self.from_wall = False
        if not self.from_wall:
            self.time_from_wall = 0
        self.on_wall = False
        super().update(dt, physics=self.health > 0)
        if self.on_ground:
            self.on_wall = False
        if not self.on_wall:
            self.time_on_wall = 0
            self.wall_direction = None
        else:
            self.time_on_wall += dt
        return True

    def hurt(self, amount: int) -> None:
        if self.pain_timer.done() and self.health > 0:
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

    def pay(self, emeralds: int) -> None:
        self.emeralds = min(999, self.emeralds + emeralds)

    def charge(self, emeralds: int) -> None:
        self.emeralds = max(0, self.emeralds - emeralds)

    def knife_pound(self) -> None:
        self.velocity *= 0
        self.velocity.y = 10
        self.swap_state("pound")
        self.jump(interfaces.JumpCause.KNIFE)

    def walk_left(self) -> None:
        self.velocity.x -= ACCEL_SPEED

    def walk_right(self) -> None:
        self.velocity.x += ACCEL_SPEED

    def decelerate(self) -> None:
        if self.velocity.x:
            self.velocity.x -= (
                self.velocity.x
                / abs(self.velocity.x)
                * min(DECCEL_SPEED, abs(self.velocity.x))
            )

    def jump(
        self,
        cause: interfaces.JumpCause = interfaces.JumpCause.NORMAL,
        just: bool = False,
    ) -> None:
        forced = cause in {
            interfaces.JumpCause.KNIFE,
            interfaces.JumpCause.PAIN,
            interfaces.JumpCause.BOOSTED,
        }
        if forced or (self.on_ground and self.state in {"idle", "walk"}):
            self.from_wall = False
            amp: float = {
                interfaces.JumpCause.NORMAL: 1.0,
                interfaces.JumpCause.PAIN: 1.1,
                interfaces.JumpCause.BOOSTED: 1.5,
                interfaces.JumpCause.KNIFE: 0.3,
            }.get(cause, 1)
            self.velocity.y = -JUMP_SPEED * amp
            self.on_ground = False
            self.on_downer = False
            self.jump_cause = cause
        elif (
            cause in {interfaces.JumpCause.NORMAL, interfaces.JumpCause.PAIN}
            and self.skidding
            and just
        ):
            if self.wall_direction == interfaces.Direction.RIGHT:
                self.velocity.update(-WALLJUMP_X_SPEED, -WALLJUMP_Y_SPEED)
            if self.wall_direction == interfaces.Direction.LEFT:
                self.velocity.update(WALLJUMP_X_SPEED, -WALLJUMP_Y_SPEED)
            self.on_wall = False
            self.from_wall = True

    def duck(self) -> None:
        self.ducking = True


class DeadPlayer(sprite.Sprite):
    def __init__(
        self, level: interfaces.Level, rect: RectLike, z: int = 0, **_: Any
    ) -> None:
        image = hardware.loader.get_spritesheet("me.png")[29]
        super().__init__(level, image, rect, z)
        self.rect.center = self.get_player().pos
        self.velocity = pygame.Vector2(0, -300)

    def update(self, dt: float) -> bool:
        vel = self.velocity * dt + 0.5 * mobile.GRAVITY * 10 * dt**2
        self.velocity += mobile.GRAVITY * 10 * dt
        self.rect.move_ip(*vel)
        return super().update(dt)
