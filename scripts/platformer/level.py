import functools
import pathlib
from collections import defaultdict, namedtuple

import pygame

from scripts import game_state, sprite, util_draw
from scripts.platformer import immobile, mobile

Parallax = namedtuple(
    "Parallax",
    ("image", "rect", "mult", "loop_x", "loop_y"),
    defaults=(pygame.FRect((0, 0), util_draw.RESOLUTION), (1, 1), True, True),
)

LERP_SPEED = 0.15


class Level(game_state.GameState):
    sprite_classes = {
        "Emerald": immobile.Emerald,
        "BustedParts": immobile.BustedParts,
        "BoingerBeetle": mobile.BoingerBeetle,
        "RedShroom": immobile.Prop,
        "BrownShroom": immobile.BrownShroom,
    }

    def __init__(self, game, player_pos=(0, 0), map_size=(256, 256)):
        super().__init__(game)
        self.backgrounds = []
        self.groups = defaultdict(set)
        self.player = mobile.Player(self)
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
        images = game.loader.get_spritesheet(background_source, (64, 64))
        multipliers = zip(
            data["customFields"]["BackgroundXMult"],
            data["customFields"]["BackgroundYMult"],
        )
        for image, multiplier in zip(images, multipliers):
            level.backgrounds.append(
                Parallax(
                    pygame.transform.scale(image, (256, 256)),
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
                    game.loader.get_surface(folder / layer),
                    pygame.FRect(map_rect),
                    z=layer_ind,
                )
            )
        for key, value in data["entities"].items():
            sprite_cls = cls.sprite_classes[key]
            if sprite_cls is None:
                continue
            for entity in value:
                level.add_sprite(
                    sprite_cls(
                        level,
                        (entity["x"], entity["y"], entity["width"], entity["height"]),
                    )
                )
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
        elif keys[pygame.K_RIGHT]:
            self.player.walk_right()
        else:
            self.player.unwalk()
        if keys[pygame.K_DOWN]:
            self.player.duck()
        if keys[pygame.K_UP]:
            self.player.jump()
        if keys[pygame.K_SPACE]:
            self.game.time_phase(-1)
        # removes dead sprites from the list
        self.sprites = [sprite for sprite in self.sprites if sprite.update(dt)]
        self.viewport_rect.center = pygame.Vector2(self.viewport_rect.center).lerp(self.player.pos, LERP_SPEED)
        self.viewport_rect.clamp_ip(self.map_rect)

    def draw(self):
        super().draw()
        for background in self.backgrounds:
            offset = (-pygame.Vector2(self.viewport_rect.topleft)).elementwise() * background.mult
            if background.loop_x:
                offset.x = (offset.x % util_draw.RESOLUTION[0]) - background.rect.width
                while offset.x < util_draw.RESOLUTION[0]:
                    self.game.window_surface.blit(background.image, background.rect.move(offset))
                    offset.x += background.rect.width
        for sprite in sorted(self.sprites, key=lambda sprite: sprite.z):
            if sprite.image is not None:
                self.game.window_surface.blit(
                    sprite.image,
                    sprite.rect.move((-int(self.viewport_rect.left), -int(self.viewport_rect.top))),
                )
