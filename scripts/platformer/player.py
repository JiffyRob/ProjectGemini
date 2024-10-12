import pygame

from scripts import sprite, timer, visual_fx
from scripts.animation import Animation, NoLoopAnimation, SingleAnimation
from scripts.platformer import mobile

ACCEL_SPEED = 6
DECCEL_SPEED = 6
WALK_SPEED = 84
JUMP_SPEED = 240
WALLJUMP_X_SPEED = 64
WALLJUMP_Y_SPEED = 400


class Player(mobile.PhysicsSprite):
    JUMP_PAIN = 0
    JUMP_NORMAL = 2
    JUMP_BOOSTED = 3
    JUMP_KNIFE = 1

    def __init__(self, level, rect=(0, 0, 16, 16), z=0, **custom_fields):
        super().__init__(level, rect=rect, image=None, z=z)
        images = level.game.loader.get_spritesheet("me.png")
        self.anim_dict = {
            "walk": Animation(images[8:12]),
            "idle": Animation((images[9],)),
            "jump": Animation((images[12],)),
            "pound": NoLoopAnimation((images[12:20]), 0.03),
            "pound-recover": NoLoopAnimation((images[20:28]), 0.1),
            "skid": SingleAnimation(images[28]),
        }
        self.state = "jump"
        self.jump_forced = False
        self.jump_cause = None
        self.image = self.anim_dict[self.state].image
        self.facing_left = False
        self.pain_timer = timer.Timer(1000)
        self.pain_timer.finish()
        self.on_wall = False
        self.from_wall = False
        self.time_from_wall = 0
        self.time_on_wall = 0
        self.wall_direction = None

    @property
    def skidding(self):
        return self.time_on_wall >= 0.2 and not self.on_ground

    @property
    def below_rect(self):
        return pygame.FRect(self.rect.left, self.rect.bottom, self.rect.width, 3)

    @property
    def name(self):
        return self.level.game.save.loaded_path

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

    def on_xy_collision(self, direction):
        if direction == self.DIRECTION_LEFT:
            self.on_wall = True
            self.wall_direction = self.DIRECTION_LEFT
        if direction == self.DIRECTION_RIGHT:
            self.on_wall = True
            self.wall_direction = self.DIRECTION_RIGHT
        self.from_wall = False

    def on_fallout(self):
        self.health = 0

    def swap_state(self, new):
        if self.state != new:
            self.state = new
            self.anim_dict[self.state].restart()
            self.image = self.anim_dict[self.state].image

    def update(self, dt):
        if not self.locked:
            held_input = self.level.game.input_queue.held
            just_input = self.level.game.input_queue.just_pressed
            if (
                self.state == "jump"
                and "duck" in just_input
                and self.jump_cause == self.JUMP_NORMAL
            ):
                self.knife_pound()
            if self.state in {"idle", "walk", "jump", "skid"}:
                if held_input["left"] and not self.from_wall:
                    self.walk_left()
                if held_input["right"] and not self.from_wall:
                    self.walk_right()
                if (
                    not held_input["left"]
                    and not held_input["right"]
                    and self.on_ground
                ):
                    self.decelerate()
            else:
                self.velocity.x = 0
            self.velocity.x = pygame.math.clamp(
                self.velocity.x, -WALK_SPEED, WALK_SPEED
            )
            if held_input["jump"]:
                self.jump(just=("jump" in just_input))
            elif self.jump_cause == self.JUMP_NORMAL:
                self.velocity.y = max(self.velocity.y, self.velocity.y * 0.7)
            if held_input["duck"]:
                self.duck()
            if "quit" in self.level.game.input_queue.just_pressed:
                self.level.run_cutscene("quit")
            if "interact" in just_input:
                if self.facing_left:
                    interaction_rect = self.rect.move(-8, 0)
                else:
                    interaction_rect = self.rect.move(8, 0)
                for sprite in self.level.groups["interactable"]:
                    if interaction_rect.colliderect(sprite.collision_rect):
                        sprite.interact()
                        break
        if self.state == "pound":
            hit = self.on_ground
            if not hit and not self.ducking:
                for sprite in self.level.groups["time-reversable"]:
                    if (
                        sprite.time_reverse_collision_rect.colliderect(self.below_rect)
                        or self.on_ground
                    ):
                        sprite.reverse_time()
                        sprite.collision_rect.update(sprite.time_reverse_collision_rect)
                        self.velocity.y *= 0
                        hit = True
            if hit:
                self.swap_state("pound-recover")
                self.level.shake(axes=self.level.AXIS_Y)
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
            self.level.game.time_phase(self.velocity.y / 64)
        self.anim_dict[self.state].update(dt)
        self.anim_dict[self.state].flip_x = self.facing_left
        self.image = self.anim_dict[self.state].image
        # push player into walls so they collide
        if self.on_wall:
            if self.wall_direction == self.DIRECTION_LEFT:
                self.velocity.x -= ACCEL_SPEED / 3
            if self.wall_direction == self.DIRECTION_RIGHT:
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

    def hurt(self, amount, deliverer=None, knockback=5):
        if self.pain_timer.done():
            self.effects.append(visual_fx.Blink(speed=0.1, count=6))
            self.health = max(0, self.health - amount)
            self.pain_timer.reset()
            if deliverer is not None:
                motion = (self.pos - deliverer.pos).scale_to_length(knockback)
                self.rect.x += motion.x
                self.rect.y += motion.y

    def heal(self, amount):
        self.health = min(self.health_capacity, self.health + amount)

    def pay(self, emeralds):
        self.emeralds = min(999, self.emeralds + emeralds)

    def charge(self, emeralds):
        self.emeralds = max(0, self.emeralds - emeralds)

    def knife_pound(self):
        self.velocity *= 0
        self.velocity.y = 10
        self.swap_state("pound")
        self.jump(self.JUMP_KNIFE)

    def walk_left(self):
        self.velocity.x -= ACCEL_SPEED

    def walk_right(self):
        self.velocity.x += ACCEL_SPEED

    def decelerate(self):
        if self.velocity.x:
            self.velocity.x -= (
                self.velocity.x
                / abs(self.velocity.x)
                * min(DECCEL_SPEED, abs(self.velocity.x))
            )

    def jump(self, cause=JUMP_NORMAL, just=False):
        forced = cause in {self.JUMP_KNIFE, self.JUMP_PAIN, self.JUMP_BOOSTED}
        if forced or (self.on_ground and self.state in {"idle", "walk"}):
            self.from_wall = False
            amp = {
                self.JUMP_NORMAL: 1,
                self.JUMP_PAIN: 1.1,
                self.JUMP_BOOSTED: 1.5,
                self.JUMP_KNIFE: 0.3,
            }[cause]
            self.velocity.y = -JUMP_SPEED * amp
            self.on_ground = False
            self.on_downer = False
            self.jump_cause = cause
        elif cause in {self.JUMP_NORMAL, self.JUMP_PAIN} and self.skidding and just:
            if self.wall_direction == self.DIRECTION_RIGHT:
                self.velocity.update(-WALLJUMP_X_SPEED, -WALLJUMP_Y_SPEED)
            if self.wall_direction == self.DIRECTION_LEFT:
                self.velocity.update(WALLJUMP_X_SPEED, -WALLJUMP_Y_SPEED)
            self.on_wall = False
            self.from_wall = True

    def duck(self):
        self.ducking = True


class DeadPlayer(sprite.Sprite):
    def __init__(self, level, rect, z=0, **custom_fields):
        image = level.game.loader.get_spritesheet("me.png")[29]
        super().__init__(level, image, rect, z)
        self.rect.center = self.level.player.pos
        self.velocity = pygame.Vector2(0, -300)

    def update(self, dt):
        vel = self.velocity * dt + 0.5 * mobile.GRAVITY * 10 * dt ** 2
        self.velocity += mobile.GRAVITY * 10 * dt
        self.rect.move_ip(*vel)
        return super().update(dt)