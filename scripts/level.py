import pathlib
from collections import defaultdict
from random import uniform

import pygame

from scripts import (
    animation,
    game_state,
    gui2d,
    platformer,
    snekgemini,
    sprite,
    topdown,
    util_draw,
)

LERP_SPEED = 1


class Parallax:
    def __init__(
        self,
        level,
        anim=None,
        rect=((0, 0), util_draw.RESOLUTION),
        item_size=(64, 64),
        scroll_speed=(1, 1),
        anchor_bottom=False,
        loop_x=True,
        loop_y=True,
    ):
        self.level = level
        self.anim = anim
        self.image = anim.image
        self.rect = pygame.FRect(rect)
        self.scroll_speed = pygame.Vector2(scroll_speed)
        self.item_size = pygame.Vector2(item_size)
        self.anchor_bottom = anchor_bottom
        self.loop_x = loop_x
        self.loop_y = loop_y

    def update(self, dt):
        self.anim.update(dt)
        self.image = self.anim.image

    @classmethod
    def load(cls, level, name):
        # load background data
        data = level.game.loader.get_json("backgrounds.json")
        defaults = data.get("default", None)
        background_data = data.get(name, None)
        if (
            background_data is None
            or defaults is None
            or background_data.get("source", None) is None
        ):
            print("WARNING: Unable to load background data")
            return
        background_data = {**defaults, **background_data}
        # load background source
        source_surface = level.game.loader.get_surface(background_data["source"])
        # create layers
        for layer in background_data["layers"]:
            layer = {**defaults["layers"][0], **layer}
            mode = layer["mode"]
            anchor_bottom = False
            # size setting - some backgrounds loop indefinitely.  Draw slightly larger than the screen.
            if mode == "tile":
                size = pygame.Vector2(layer["frames"][0][2:]) + util_draw.RESOLUTION
                layer["loop_x"] = layer["loop_y"] = True
                layer["anchor_bottom"] = False
                frames = [
                    util_draw.repeat_surface(source_surface.subsurface(i), size)
                    for i in layer["frames"]
                ]
                item_size = pygame.Vector2(layer["frames"][0][2:])
            elif mode == "backdrop":
                size = pygame.Vector2(256, 256)
                if layer["loop_x"]:
                    size[0] += util_draw.RESOLUTION[0]
                if layer["loop_y"]:
                    size[1] += util_draw.RESOLUTION[1]
                elif layer["anchor_bottom"]:
                    anchor_bottom = True
                frames = [
                    util_draw.repeat_surface(
                        pygame.transform.scale(
                            source_surface.subsurface(i), (256, 256)
                        ),
                        size,
                    )
                    for i in layer["frames"]
                ]
                item_size = (256, 256)
            else:
                print("WARNING: layer has incorrect mode set.  Skipping.")
                continue
            # create and return Parallax layer with loaded information
            yield cls(
                level=level,
                anim=animation.Animation(frames, layer["anim_speed"]),
                rect=pygame.FRect((0, 0), size),
                item_size=item_size,
                scroll_speed=[layer["scroll_x"], layer["scroll_y"]],
                anchor_bottom=anchor_bottom,
                loop_x=layer["loop_x"],
                loop_y=layer["loop_y"],
            )

    def draw(self, surface, offset):
        if (not self.loop_y) and self.anchor_bottom:
            offset.y += self.level.map_rect.height - self.item_size.y
        offset = offset.elementwise() * self.scroll_speed
        if self.loop_x:
            offset.x = offset.x % self.item_size.x - self.item_size.x
        if self.loop_y:
            offset.y = offset.y % self.item_size.y - self.item_size.y
        surface.blit(self.image, self.rect.move(offset))


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
            "GunPlatform": platformer.puzzle.GunPlatform,
            "CrazyMushroom": platformer.immobile.CrazyMushroom,
            "Ship": platformer.mobile.Ship,
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
            self.is_platformer = True
        else:
            self.player = topdown.mobile.Player(self)
            self.is_platformer = False
        self.is_house = is_house
        self.entity_layer = 0
        self.player.rect.center = player_pos
        self.sprites = {self.player}
        self.to_add = set()
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

    def run_cutscene(self, cutscene_id, extra_constants=None, override=False):
        if self.script is None or override:
            self.script = snekgemini.cutscene(
                cutscene_id, level=self, extra_constants=extra_constants
            )
            self.script.cycle()

    def attempt_map_cutscene(self, override=True):
        if self.script is not None and not override:
            return False
        try:
            self.run_cutscene(self.name, override=True)
            return True
        except FileNotFoundError:
            print("No file found :/", self.name)
            return False

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

    def clear_effects(self):
        self.effects.clear()

    def spawn(self, sprite_name, rect, z=None, **custom_fields):
        if z is None:
            z = self.entity_layer
        self.add_sprite(
            self.sprite_classes[self.is_platformer][sprite_name](
                self, rect, z, **custom_fields
            )
        )

    def add_sprite(self, sprite):
        self.to_add.add(sprite)

    def add_sprite_internal(self, sprite):
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
        level.backgrounds.extend(
            Parallax.load(level, data["customFields"]["Background"])
        )
        # tile layers
        entity_layer = data["customFields"]["entity_layer"]
        level.entity_layer = entity_layer
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
        # adds new sprites to the list
        for sprite in self.to_add:
            self.add_sprite_internal(sprite)
        self.to_add.clear()
        # removes dead sprites from the list
        self.sprites = {sprite for sprite in self.sprites if sprite.update(dt)}
        for group in self.groups.values():
            group &= self.sprites
        self.viewport_rect.center = pygame.Vector2(self.viewport_rect.center).lerp(
            self.player.pos, LERP_SPEED
        )
        self.viewport_rect.clamp_ip(self.map_rect)
        # if player died, end game
        if self.player.health <= 0:
            self.run_cutscene("death")
        # update backgrounds
        for background in self.backgrounds:
            background.update(dt)
        # update gui
        for sprite in self.gui:
            sprite.update(dt)
        # update visual effects
        self.effects = [effect for effect in self.effects if effect.update(dt)]
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
        offset = -pygame.Vector2(self.viewport_rect.topleft)
        for background in self.backgrounds:
            background.draw(self.game.window_surface, offset.copy())
        # draw map + sprites
        for sprite in sorted(
            self.sprites, key=lambda sprite: sprite.z * 1000 + sprite.rect.centery
        ):
            rect = sprite.rect.move(
                (-int(self.viewport_rect.left), -int(self.viewport_rect.top))
                + shake_offset
            )
            if sprite.to_draw is not None:
                self.game.window_surface.blit(
                    sprite.to_draw,
                    rect,
                )
        # draw visual effects
        for effect in self.effects:
            effect.draw(self.game.window_surface)
        # draw gui
        for sprite in self.gui:
            sprite.draw(self.game.window_surface)
