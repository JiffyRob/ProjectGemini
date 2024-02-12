from itertools import cycle

import pygame

from scripts import sprite

GRAVITY = pygame.Vector2(0, 50)  # TODO: sideways gravity?????
WALK_SPEED = 64
JUMP_SPEED = 240


class PhysicsSprite(sprite.Sprite):
    def __init__(
        self, level, image=None, rect=(0, 0, 16, 16), src_rect=None, z=0, weight=10
    ):
        super().__init__(level, image=image, rect=rect, src_rect=src_rect, z=z)
        self.weight = weight
        self.velocity = pygame.Vector2()
        self.desired_velocity = pygame.Vector2()
        self.on_ground = False
        self.on_downer = False
        self.ducking = False

    @property
    def collision_rect(self):
        return self.rect.copy()

    def on_xy_collision(self):
        pass

    def update(self, dt):
        # physics
        old_rect = self.collision_rect.copy()
        vel = self.velocity * dt + .5 * GRAVITY * self.weight * dt ** 2
        self.velocity += GRAVITY * self.weight * dt
        self.rect.x += vel.x
        self.on_ground = False
        # bottom of the map
        if self.collision_rect.bottom > self.level.map_rect.bottom:
            self.dead = True
            return False
        if vel.x < 0:
            for collided in sorted(
                self.level.collision_rects, key=lambda rect: -rect.x
            ):
                if self.collision_rect.colliderect(collided):
                    self.on_xy_collision()
                    self.rect.x += collided.right - self.collision_rect.left
                    self.velocity.x = 0
                    break
        else:
            for collided in sorted(self.level.collision_rects, key=lambda rect: rect.x):
                if self.collision_rect.colliderect(collided):
                    self.on_xy_collision()
                    self.rect.x += collided.left - self.collision_rect.right
                    self.velocity.x = 0
                    break
        self.rect.y += vel.y
        if vel.y < 0:
            for collided in sorted(
                self.level.collision_rects, key=lambda rect: -rect.y
            ):
                if self.collision_rect.colliderect(collided):
                    self.rect.y += collided.bottom - self.collision_rect.top
                    self.velocity.y = 0
                    break
        else:
            for collided in sorted(self.level.collision_rects, key=lambda rect: rect.y):
                if self.collision_rect.colliderect(collided):
                    self.rect.y += collided.top - self.collision_rect.bottom
                    self.velocity.y = 0
                    self.on_ground = True
                    break
            if not self.ducking:
                for collided in sorted(self.level.down_rects, key=lambda rect: rect.y):
                    if (
                        old_rect.bottom <= collided.top
                        and self.collision_rect.colliderect(collided)
                    ):
                        self.rect.y += collided.top - self.collision_rect.bottom
                        self.velocity.y = 0
                        self.on_ground = True
                        self.on_downer = True
                        break
        self.velocity.x = 0
        self.ducking = False
        return True


class BoingerBeetle(PhysicsSprite):
    def __init__(self, level, rect=(0, 0, 16, 16)):
        super().__init__(level, rect=rect, weight=3)
        self.anim_speed = 0.2
        self.anim_time = 0
        self.anim = cycle(
            self.level.game.loader.get_spritesheet("platformer-sprites.png")[8:12]
        )
        self.hit_image = self.level.game.loader.get_spritesheet("platformer-sprites.png")[12]
        self.facing_left = True
        self.image = next(self.anim)

    @property
    def collision_rect(self):
        return self.rect.inflate(-4, -10).move(0, 5)

    def on_xy_collision(self):
        self.facing_left = not self.facing_left

    def update(self, dt):
        self.velocity.x = WALK_SPEED * .3 * (-1 + self.facing_left * 2)
        if not super().update(dt):
            return False
        self.anim_time += dt
        if self.collision_rect.colliderect(self.level.player.collision_rect) and self.level.player.velocity.y > 0:
            self.image = self.hit_image
            self.anim_time = 0
            self.level.player.jump(True, 1.5)
        if self.anim_time >= self.anim_speed:
            self.anim_time = 0
            self.image = next(self.anim)
        self.image.flip_x = self.facing_left
        return True


class Player(PhysicsSprite):
    def __init__(self, level, rect=(0, 0, 16, 16)):
        super().__init__(level, rect=rect, image=None)
        images = level.game.loader.get_spritesheet("me-Sheet.png")
        self.anim_dict = {
            "walk": cycle(images[8:12]),
            "idle": cycle((images[9],)),
            "jump": cycle((images[12],)),
        }
        self.anim_speed = 0.2
        self.anim_time = 0
        self.state = "jump"
        self.jump_forced = False
        self.image = next(self.anim_dict[self.state])

    def swap_state(self, new):
        if self.state != new:
            self.state = new
            self.anim_time = 0
            self.image = next(self.anim_dict[self.state])

    def update(self, dt):
        if self.state == "jump":
            if self.on_ground:
                print("jump swap")
                self.swap_state("idle")
        elif self.velocity.x:
            self.swap_state("walk")
            self.image.flip_x = self.velocity.x < 0
        else:
            self.swap_state("idle")
        self.anim_time += dt
        if self.anim_time > self.anim_speed:
            self.image = next(self.anim_dict[self.state])
            self.anim_time = 0
            if self.velocity.x:
                self.image.flip_x = self.velocity.x < 0
        return super().update(dt)

    def walk_left(self):
        self.velocity.x -= WALK_SPEED

    def walk_right(self):
        self.velocity.x += WALK_SPEED

    def unwalk(self):
        pass

    def jump(self, pain=False, amp=1):
        if self.on_ground or pain:
            self.velocity.y = -JUMP_SPEED * amp
            self.on_ground = False
            self.on_downer = False
            self.jump_forced = pain

    def unjump(self):
        if not self.jump_forced:
            self.velocity.y = max(0, self.velocity.y)

    def duck(self):
        self.ducking = True
