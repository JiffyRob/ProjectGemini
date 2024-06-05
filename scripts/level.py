import pathlib
from collections import defaultdict, namedtuple
from random import uniform

import pygame

from scripts import (
    game_state,
    gui2d,
    platformer,
    snekgemini,
    sprite,
    topdown,
    util_draw,
)

Parallax = namedtuple(
    "Parallax",
    ("image", "rect", "mult", "loop_x", "loop_y"),
    defaults=(pygame.FRect((0, 0), util_draw.RESOLUTION), (1, 1), True, True),
)

LERP_SPEED = 1


class Level(game_state.GameState):
    AXIS_X = 1
    AXIS_Y = 2

    sprite_classes = (
        # topdown
        {
            "Emerald": platformer.immobile.Emerald,  # same for both perspectives
            "Ship": topdown.immobile.Ship,
            "BrokenShip": topdown.immobile.BrokenShip,
            "House": topdown.immobile.House,
            "Furniture": topdown.immobile.Furniture,
        },
        # platformer
        {
            "Emerald": platformer.immobile.Emerald,
            "BustedParts": platformer.immobile.BustedParts,
            "BoingerBeetle": platformer.mobile.BoingerBeetle,
            "RedShroom": platformer.immobile.Prop,
            "BrownShroom": platformer.immobile.BrownShroom,
            "Player": platformer.player.Player,
            "Battery": platformer.puzzle.Battery,
        },
    )

    def __init__(
        self,
        game,
        name=None,
        player_pos=(0, 0),
        map_size=(256, 256),
        is_platformer=False,
        is_house=False,
        soundtrack=None,
    ):
        super().__init__(game)
        self.name = name
        self.backgrounds = []
        self.groups = defaultdict(set)
        self.soundtrack = soundtrack
        if is_platformer:
            self.player = platformer.player.Player(self)
        else:
            self.player = topdown.mobile.Player(self)
        self.is_house = is_house
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
        self.effects = []
        self.script = None
        self.run_cutscene("level_begin")

        self.shake_magnitude = 0
        self.shake_delta = 0
        self.shake_axes = 0

    def shake(self, magnitude=5, delta=8, axes=AXIS_X | AXIS_Y):
        self.shake_magnitude += magnitude
        self.shake_delta += delta
        self.shake_axes = axes

    def run_cutscene(self, cutscene_id, extra_constants=None):
        self.script = snekgemini.cutscene(
            cutscene_id, level=self, extra_constants=extra_constants
        )
        self.script.cycle()

    def exit_level(self):
        self.run_cutscene("level_exit")

    def switch_level(self, dest):
        self.run_cutscene("level_switch", extra_constants={"NEXT_LEVEL": dest})

    def lock(self):
        for sprite in self.sprites:
            sprite.lock()

    def unlock(self):
        for sprite in self.sprites:
            sprite.unlock()

    def add_effect(self, effect):
        self.effects.append(effect)

    def add_sprite(self, sprite):
        self.sprites.add(sprite)
        for group in sprite.groups:
            if group == "static-collision":
                self.collision_rects.append(sprite.collision_rect)
                if hasattr(sprite, "extra_collision_rects"):
                    self.collision_rects.extend(sprite.extra_collision_rects)
                continue
            if group == "vertical-collision":
                self.down_rects.append(sprite.collision_rect)
                if hasattr(sprite, "extra_collision_rects"):
                    self.down_rects.extend(sprite.extra_collision_rects)
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
        data = game.loader.get_json(folder / "data.json", for_map=True)
        size = data["width"], data["height"]
        is_platformer = data["customFields"]["platformer"]
        is_house = data["customFields"]["house"]
        soundtrack = data["customFields"]["Soundtrack"]
        map_rect = pygame.Rect((0, 0), size)
        # level initialization
        level = cls(
            game,
            name=name,
            player_pos=data["customFields"]["start"],
            map_size=size,
            is_platformer=is_platformer,
            soundtrack=soundtrack,
            is_house=is_house,
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
        # tile layers
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
        # sprites
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
                        **entity["customFields"]
                    )
                )
        # collision data creation
        for row, line in enumerate(
            game.loader.get_csv(folder / "Collision.csv", for_map=True)
        ):
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

    def world_to_screen(self, pos):
        return pygame.Vector2(pos) - self.viewport_rect.topleft

    def screen_to_world(self, pos):
        return pygame.Vector2(pos) + self.viewport_rect.topleft

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
        # update visual effects
        self.effects = [effect.update(dt) for effect in self.effects if not effect.done]
        # update script
        if self.script is not None:
            self.script.cycle()
            if self.script.done():
                self.script = None
        self.shake_magnitude = max(self.shake_magnitude - self.shake_delta * dt, 0)
        if not self.shake_magnitude:
            self.shake_delta *= 0
        return super().update(dt) and True

    def draw(self):
        super().draw()
        # draw backgrounds
        shake_offset = pygame.Vector2(
            uniform(-self.shake_magnitude, self.shake_magnitude)
            * bool(self.shake_axes & self.AXIS_X),
            uniform(-self.shake_magnitude, self.shake_magnitude)
            * bool(self.shake_axes & self.AXIS_Y),
        )
        for background in self.backgrounds:
            offset = (
                -pygame.Vector2(self.viewport_rect.topleft) + shake_offset
            ).elementwise() * background.mult
            if background.loop_x:
                offset.x = (offset.x % util_draw.RESOLUTION[0]) - background.rect.width
                while offset.x < util_draw.RESOLUTION[0]:
                    self.game.window_surface.blit(
                        background.image, background.rect.move(offset)
                    )
                    offset.x += background.rect.width
        # draw map + sprites
        for sprite in sorted(
            self.sprites, key=lambda sprite: sprite.z * 1000 + sprite.rect.centery
        ):
            if sprite.image is not None:
                self.game.window_surface.blit(
                    sprite.image,
                    sprite.rect.move(
                        (-int(self.viewport_rect.left), -int(self.viewport_rect.top))
                        + shake_offset
                    ),
                )
        # draw visual effects
        for effect in self.effects:
            effect.draw(self.game.window_surface)
        # draw gui
        for sprite in self.gui:
            sprite.draw(self.game.window_surface)
