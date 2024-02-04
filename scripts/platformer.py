import functools
import pathlib
from collections import defaultdict, namedtuple

import pygame
import pygame._sdl2 as sdl2


from scripts import game_state, sprite, util_draw

GRAVITY = pygame.Vector2(0, 1)  # TODO: sideways gravity?????
WALK_SPEED = 64
JUMP_SPEED = 260
LERP_SPEED = 0.15

Parallax = namedtuple(
    "Parallax",
    ("image", "rect", "mult", "loop_x", "loop_y"),
    defaults=(pygame.FRect((0, 0), util_draw.RESOLUTION), (1, 1), True, True),
)


class PhysicsSprite(sprite.Sprite):
    def __init__(self, level, image=None, rect=(0, 0, 16, 16), src_rect=None, z=0, weight=10):
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

    def update(self, dt):
        # physics
        old_rect = self.collision_rect.copy()
        self.velocity += GRAVITY * self.weight
        vel = self.velocity * dt
        self.rect.x += vel.x
        self.on_ground = False
        # bottom of the map
        if self.collision_rect.bottom > self.level.map_rect.bottom:
            self.dead = True
            return False
        if vel.x < 0:
            for collided in sorted(self.level.collision_rects, key=lambda rect: -rect.x):
                if self.collision_rect.colliderect(collided):
                    self.rect.x += collided.right - self.collision_rect.left
                    self.velocity.x = 0
                    break
        else:
            for collided in sorted(self.level.collision_rects, key=lambda rect: rect.x):
                if self.collision_rect.colliderect(collided):
                    self.rect.x += collided.left - self.collision_rect.right
                    self.velocity.x = 0
                    break
        self.rect.y += vel.y
        if vel.y < 0:
            for collided in sorted(self.level.collision_rects, key=lambda rect: -rect.y):
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
                    if old_rect.bottom <= collided.top and self.collision_rect.colliderect(collided):
                        self.rect.y += collided.top - self.collision_rect.bottom
                        self.velocity.y = 0
                        self.on_ground = True
                        self.on_downer = True
                        break
        self.velocity.x = 0
        self.ducking = False
        return True


class CollisionSprite(sprite.Sprite):
    def __init__(self, level, image=None, rect=(0, 0, 16, 16), src_rect=None, z=0):
        if image is None:
            image = util_draw.square_image(level.game.renderer, "blue")
        super().__init__(level, image=image, rect=rect, src_rect=src_rect, z=z)
        # self.level.groups["collision"].add(self)
        self.level.collision_rects.add(self.collision_rect)

    def update(self, dt):
        pass  # No physics on a static sprite

    @property
    def collision_rect(self):
        return self.rect.copy()


class Player(PhysicsSprite):
    def __init__(self, level, rect=(0, 0, 16, 16)):
        super().__init__(level, rect=rect, image=util_draw.square_image(level.game.renderer))

    def walk_left(self):
        self.velocity.x -= WALK_SPEED

    def walk_right(self):
        self.velocity.x += WALK_SPEED

    def jump(self):
        if self.on_ground:
            self.velocity.y = -JUMP_SPEED
            self.on_ground = False
            self.on_downer = False

    def unjump(self):
        self.velocity.y = max(0, self.velocity.y)

    def duck(self):
        self.ducking = True


class Level(game_state.GameState):
    sprite_classes = {
        "Coin2": None,
    }

    def __init__(self, game, player_pos=(0, 0), map_size=(256, 256)):
        super().__init__(game)
        self.backgrounds = []
        self.groups = defaultdict(set)
        self.player = Player(self)
        self.player.rect.center = player_pos
        self.sprites = [self.player]
        self.collision_rects = []
        self.down_rects = []
        self.map_rect = pygame.Rect((0, 0), map_size)
        self.viewport_rect = pygame.FRect(self.game.screen_rect)

    def add_sprite(self, sprite):
        self.sprites.append(sprite)

    @classmethod
    @functools.cache
    def load(cls, game, name):
        # basic metadata
        folder = pathlib.Path("ldtk/simplified", name)
        data = game.loader.get_json(folder / "data.json")
        size = data["width"], data["height"]
        map_rect = pygame.Rect((0, 0), size)
        # level initialization
        level = cls(game, player_pos=data["customFields"]["start"], map_size=size)
        level.bg_color = data["bgColor"]
        # background creation
        background_source = data["customFields"]["Background"]
        images = game.loader.get_spritesheet(background_source, (256, 256))
        multipliers = zip(
            data["customFields"]["BackgroundXMult"],
            data["customFields"]["BackgroundYMult"],
        )
        for image, multiplier in zip(images, multipliers):
            level.backgrounds.append(
                Parallax(
                    image,
                    mult=multiplier,
                    loop_x=data["customFields"]["LoopX"],
                    loop_y=data["customFields"]["LoopY"],
                )
            )
        # layer and entity creation
        entity_layer = data["customFields"]["entity_layer"]
        for layer_ind, layer in enumerate(data["layers"]):
            level.add_sprite(
                sprite.Sprite(
                    level,
                    game.loader.get_texture(folder / layer),
                    pygame.FRect(map_rect),
                    z=layer_ind + entity_layer,
                )
            )
        for key, value in data["entities"].items():
            sprite_cls = cls.sprite_classes[key]
            if sprite_cls is None:
                continue
            # TODO: Sprite creation
            ...
        # collision data creation
        for row, line in enumerate(game.loader.get_csv(folder / "Collision.csv")):
            for col, value in enumerate(line):
                value = int(value)
                if value == 1:
                    rect = pygame.FRect(col * 16, row * 16, 16, 16)
                    level.collision_rects.append(rect)
                if value == 2:
                    rect = pygame.FRect(col * 16, row * 16, 16, 16)
                    level.down_rects.append(rect)
        level.player.z = entity_layer
        return level

    def update(self, dt):
        super().update(dt)
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.player.walk_left()
        if keys[pygame.K_RIGHT]:
            self.player.walk_right()
        if not keys[pygame.K_UP]:
            self.player.unjump()
        if keys[pygame.K_DOWN]:
            self.player.duck()
        # removes dead sprites from the list
        self.sprites = [sprite for sprite in self.sprites if sprite.update(dt)]
        self.viewport_rect.center = pygame.Vector2(self.viewport_rect.center).lerp(self.player.pos, LERP_SPEED)
        self.viewport_rect.clamp_ip(self.map_rect)

    def handle_event(self, event):
        match event:
            case pygame.Event(type=pygame.KEYDOWN, key=pygame.K_UP):
                self.player.jump()

    def draw(self):
        super().draw()
        for background in self.backgrounds:
            offset = (-pygame.Vector2(self.viewport_rect.topleft)).elementwise() * background.mult
            offset.y += self.map_rect.height - background.rect.height
            if background.loop_x:
                offset.x = (offset.x % util_draw.RESOLUTION[0]) - background.rect.width
                while offset.x < util_draw.RESOLUTION[0]:
                    background.image.draw(None, background.rect.move(offset))
                    offset.x += background.rect.width
        for sprite in sorted(self.sprites, key=lambda sprite: sprite.z):
            sprite.image.draw(sprite.src_rect, sprite.rect.move(-pygame.Vector2(self.viewport_rect.topleft)))
        #    sprite.image.draw(sprite.src_rect, sprite.rect.move(-pygame.Vector2(self.viewport_rect.topleft)))
