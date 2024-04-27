import pygame

from scripts import sprite, util_draw
from scripts.animation import Animation

WALK_SPEED = 64


class PhysicsSprite(sprite.Sprite):
    def __init__(self, level, image=None, rect=(0, 0, 16, 16), z=0, weight=10, **custom_fields):
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
        self.rect.x += vel.x
        departure_directions = []
        if vel.x < 0:
            if self.rect.left < self.level.map_rect.left:
                self.rect.left = self.level.map_rect.left
                departure_directions.append("left")
            for collided in sorted(
                self.level.collision_rects, key=lambda rect: -rect.x
            ):
                if self.collision_rect.colliderect(collided):
                    self.on_xy_collision()
                    self.rect.x += collided.right - self.collision_rect.left
                    vel.x = 0
                    break
        else:
            if self.rect.right > self.level.map_rect.right:
                self.rect.right = self.level.map_rect.right
                departure_directions.append("right")
            for collided in sorted(self.level.collision_rects, key=lambda rect: rect.x):
                if self.collision_rect.colliderect(collided):
                    self.on_xy_collision()
                    self.rect.x += collided.left - self.collision_rect.right
                    vel.x = 0
                    break
        self.rect.y += vel.y
        if vel.y < 0:
            if self.rect.top < self.level.map_rect.top:
                self.rect.top = self.level.map_rect.top
                departure_directions.append("up")
            for collided in sorted(
                self.level.collision_rects, key=lambda rect: -rect.y
            ):
                if self.collision_rect.colliderect(collided):
                    self.rect.y += collided.bottom - self.collision_rect.top
                    vel.y = 0
                    break
        else:
            if self.rect.bottom > self.level.map_rect.bottom:
                self.rect.bottom = self.level.map_rect.bottom
                departure_directions.append("down")
            for collided in sorted(self.level.collision_rects, key=lambda rect: rect.y):
                if self.collision_rect.colliderect(collided):
                    self.rect.y += collided.top - self.collision_rect.bottom
                    vel.y = 0
                    break
        if departure_directions:
            self.on_map_departure(departure_directions)
        return True


class Player(PhysicsSprite):
    def __init__(self, level, rect=(0, 0, 16, 16), z=0, **custom_fields):
        super().__init__(level, rect=rect, image=None, z=z)
        images = level.game.loader.get_spritesheet("me-Sheet.png")
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

        self.health = 16
        self.health_capacity = 16
        self.emeralds = 10

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
            self.level.switch_level(f"{self.level.name}_{directions[0]}")
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

    def update(self, dt):
        self.desired_velocity *= 0
        if not self.locked:
            keys = pygame.key.get_pressed()
            if keys[pygame.K_UP]:
                self.walk_up()
            if keys[pygame.K_DOWN]:
                self.walk_down()
            if keys[pygame.K_LEFT]:
                self.walk_left()
            if keys[pygame.K_RIGHT]:
                self.walk_right()
            keys = pygame.key.get_just_pressed()
            if keys[pygame.K_SPACE]:
                for sprite in self.level.groups["interactable"]:
                    print(sprite.rect, self.interaction_rect)
                    if sprite.rect.colliderect(self.interaction_rect):
                        print("interact w/", sprite)
                        sprite.interact()
            self.desired_velocity.clamp_magnitude_ip(WALK_SPEED)
            self.velocity = self.desired_velocity
            if self.velocity:
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
