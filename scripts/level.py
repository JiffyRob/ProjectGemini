import pathlib
from collections import defaultdict, namedtuple

import pygame

from scripts import game_state, gui2d, platformer, sprite, topdown, util_draw

Parallax = namedtuple(
    "Parallax",
    ("image", "rect", "mult", "loop_x", "loop_y"),
    defaults=(pygame.FRect((0, 0), util_draw.RESOLUTION), (1, 1), True, True),
)

LERP_SPEED = 0.15


class Level(game_state.GameState):
    sprite_classes = (
        # topdown
        {
            "Emerald": platformer.immobile.Emerald,  # same for both perspectives
            "Ship": topdown.immobile.Ship,
            "BrokenShip": topdown.immobile.BrokenShip,
        },
        # platformer
        {
            "Emerald": platformer.immobile.Emerald,
            "BustedParts": platformer.immobile.BustedParts,
            "BoingerBeetle": platformer.mobile.BoingerBeetle,
            "RedShroom": platformer.immobile.Prop,
            "BrownShroom": platformer.immobile.BrownShroom,
            "Player": platformer.mobile.Player,
        },
    )

    def __init__(
        self,
        game,
        name=None,
        player_pos=(0, 0),
        map_size=(256, 256),
        is_platformer=False,
    ):
        super().__init__(game)
        self.name = name
        self.backgrounds = []
        self.groups = defaultdict(set)
        if is_platformer:
            self.player = platformer.mobile.Player(self)
        else:
            self.player = topdown.mobile.Player(self)
        self.player.rect.center = player_pos
        self.sprites = {self.player}
        self.collision_rects = []
        self.down_rects = []
        self.gui = [
            gui2d.HeartMeter(self, (2, 2, 16 * 9, 9)),
            gui2d.EmeraldMeter(self, (2, 11, 0, 0)),
        ]
        self.dialog = None
        self.on_dialog_finish = lambda answer: None
        self.map_rect = pygame.Rect((0, 0), map_size)
        self.viewport_rect = pygame.FRect(self.game.screen_rect)

    def add_sprite(self, sprite):
        self.sprites.add(sprite)
        for group in sprite.groups:
            if group == "static-collision":
                self.collision_rects.append(sprite.collision_rect)
                continue
            self.groups[group].add(sprite)

    def start_dialog(self, text, *answers, face=None, on_finish=lambda answer: None):
        self.dialog = gui2d.Dialog(
            self, gui2d.dialog_rect(face is not None), text, answers, self.finish_dialog
        )
        self.gui.append(self.dialog)
        self.on_dialog_finish = on_finish

    def finish_dialog(self, answer):
        self.gui.remove(self.dialog)
        self.dialog = None
        self.on_dialog_finish(answer)
        self.on_dialog_finish = lambda answer: None

    @classmethod
    def load(cls, game, name):
        # basic metadata
        folder = pathlib.Path("ldtk/simplified", name)
        data = game.loader.get_json(folder / "data.json")
        size = data["width"], data["height"]
        is_platformer = data["customFields"]["platformer"]
        map_rect = pygame.Rect((0, 0), size)
        # level initialization
        level = cls(
            game,
            name=name,
            player_pos=data["customFields"]["start"],
            map_size=size,
            is_platformer=is_platformer,
        )
        # background creation
        level.bgcolor = data["bgColor"]
        background_source = data["customFields"]["Background"]
        if background_source is not None:
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
                    z=layer_ind * 3 + 1,
                )
            )
        for key, value in data["entities"].items():
            sprite_cls = cls.sprite_classes[is_platformer][key]
            if sprite_cls is None:
                continue
            for entity in value:
                level.add_sprite(
                    sprite_cls(
                        level,
                        (entity["x"], entity["y"], entity["width"], entity["height"]),
                        z=entity_layer,
                    )
                )
        level.player.z = entity_layer
        # collision data creation
        for row, line in enumerate(game.loader.get_csv(folder / "Collision.csv")):
            for col, value in enumerate(line):
                value = int(value)
                if value == 0 and not is_platformer:
                    rect = pygame.FRect(col * 16, row * 16, 16, 16)
                    level.collision_rects.append(rect)
                if value == 1 and is_platformer:
                    rect = pygame.FRect(col * 16, row * 16, 16, 16)
                    level.collision_rects.append(rect)
                if value == 2 and is_platformer:
                    rect = pygame.FRect(col * 16, row * 16, 16, 16)
                    level.down_rects.append(rect)
        level.player.z = entity_layer
        return level

    def update(self, dt):
        # removes dead sprites from the list
        self.sprites = {sprite for sprite in self.sprites if sprite.update(dt)}
        for group in self.groups.values():
            group &= self.sprites
        self.viewport_rect.center = pygame.Vector2(self.viewport_rect.center).lerp(
            self.player.pos, LERP_SPEED
        )
        self.viewport_rect.clamp_ip(self.map_rect)
        # if player died, end game
        if self.player not in self.sprites:
            print("player dead.  Exiting.")
            return False
        # update gui
        for sprite in self.gui:
            sprite.update(dt)
        return super().update(dt) and True

    def draw(self):
        super().draw()
        for background in self.backgrounds:
            offset = (
                -pygame.Vector2(self.viewport_rect.topleft)
            ).elementwise() * background.mult
            if background.loop_x:
                offset.x = (offset.x % util_draw.RESOLUTION[0]) - background.rect.width
                while offset.x < util_draw.RESOLUTION[0]:
                    self.game.window_surface.blit(
                        background.image, background.rect.move(offset)
                    )
                    offset.x += background.rect.width
        for sprite in sorted(self.sprites, key=lambda sprite: sprite.z):
            if sprite.image is not None:
                self.game.window_surface.blit(
                    sprite.image,
                    sprite.rect.move(
                        (-int(self.viewport_rect.left), -int(self.viewport_rect.top))
                    ),
                )
        for sprite in self.gui:
            sprite.draw(self.game.window_surface)
