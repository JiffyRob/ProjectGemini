import asyncio
import pathlib
from collections import defaultdict
from random import uniform

import pygame

from gamelibs import (
    animation,
    game_state,
    gui2d,
    platformer,
    hoverboarding,
    sprite,
    topdown,
    util_draw,
    visual_fx,
)

CAMERA_SPEED = 128


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

    def lock(self):
        pass

    def unlock(self):
        pass

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

    MAP_TOPDOWN = "TopDown"
    MAP_PLATFORMER = "Platformer"
    MAP_HOUSE = "House"
    MAP_HOVERBOARD = "Hoverboard"

    TERRAIN_CLEAR = 0
    TERRAIN_GROUND = 1
    TERRAIN_GROUND2 = 2

    TERRAIN_MOUNTAIN = 1

    sprite_classes = {
        MAP_TOPDOWN: {
            "Emerald": platformer.immobile.Emerald,  # same for both perspectives
            "Ship": topdown.immobile.Ship,
            "BrokenShip": topdown.immobile.BrokenShip,
            "House": topdown.immobile.House,
            "Furniture": topdown.immobile.Furniture,
            "Bush": topdown.immobile.Bush,
            "Smith": topdown.immobile.Smith,
            "Drone": topdown.mobile.Drone,
            "DeadPlayer": topdown.mobile.DeadPlayer,
            "Hoverboard": topdown.immobile.Hoverboard,
            "Tumblefish": topdown.mobile.TumbleFish,
        },
        MAP_HOUSE: {
            "Emerald": platformer.immobile.Emerald,  # same for both perspectives
            "Furniture": topdown.immobile.Furniture,
        },
        MAP_PLATFORMER: {
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
            "DeadPlayer": platformer.player.DeadPlayer,
        },
        MAP_HOVERBOARD: {
            "Drone": hoverboarding.Drone,
            "DeadPlayer": hoverboarding.DeadPlayer,
            "Rock": hoverboarding.Rock,
            "Stump": hoverboarding.Stump,
            "Player": topdown.mobile.Player,
        },
    }

    def __init__(
        self,
        game,
        name=None,
        player_pos=(0, 0),
        player_facing=None,
        map_size=(256, 256),
        map_type=MAP_TOPDOWN,
        soundtrack=None,
        entrance=None,
    ):
        super().__init__(game)
        self.name = name
        self.backgrounds = []
        self.groups = defaultdict(set)
        self.rects = defaultdict(list)
        self.soundtrack = soundtrack
        rect = pygame.FRect(0, 0, 16, 16)
        rect.center = player_pos
        if map_type == self.MAP_PLATFORMER:
            self.player = platformer.player.Player(self, rect)
        elif map_type in {self.MAP_HOUSE, self.MAP_TOPDOWN}:
            self.player = topdown.mobile.Player(self, rect, entrance=entrance)
        elif map_type == self.MAP_HOVERBOARD:
            self.player = hoverboarding.Player(self, rect)
        else:
            print("AAAAHAHH")
            raise
        self.map_type = map_type
        self.entity_layer = 0
        if player_facing is not None:
            self.player.last_facing = player_facing
        self.sprites = set()
        self.to_add = set()
        self.gui = [
            gui2d.HeartMeter(self, (2, 2, 16 * 9, 9)),
            gui2d.EmeraldMeter(self, (2, 11, 0, 0)),
        ]
        self.dialog = None
        self.dialog_answer = None
        self.dialog_lock = asyncio.Lock()
        self.dialog_event = asyncio.Event()
        self.map_rect = pygame.Rect((0, 0), map_size)
        self.viewport_rect = pygame.FRect(self.game.screen_rect)
        self.effects = []
        self.locked = False

        self.shake_magnitude = 0
        self.shake_delta = 0
        self.shake_axes = 0
        self.speed = 0  # used for hoverboard levels

        self.add_sprite(self.player)
        self.update(0)
        self.run_cutscene("level_begin")

    def shake(self, magnitude=5, delta=8, axes=AXIS_X | AXIS_Y):
        self.shake_magnitude += magnitude
        self.shake_delta += delta
        self.shake_axes = axes

    def run_cutscene(
        self, cutscene_id, api=None
    ):
        print("running cutscene")
        self.game.run_cutscene(cutscene_id, api)

    async def attempt_map_cutscene(self):
        try:
            self.game.loader.get_cutscene(self.name)
        except FileNotFoundError:
            return False
        return await self.game.run_sub_cutscene(self.name)

    def exit_level(self):
        self.run_cutscene("level_exit")

    def switch_level(self, dest, direction=None, position=None, entrance="normal"):
        self.run_cutscene(
            "level_switch",
            api={
                "NEXT_LEVEL": dest,
                "DIRECTION": direction,
                "POSITION": position,
                "ENTRANCE": entrance,
            },
        )

    def lock(self):
        self.locked = True
        for sprite in self.sprites:
            sprite.lock()
        for background in self.backgrounds:
            background.lock()

    def unlock(self):
        self.locked = False
        for sprite in self.sprites:
            sprite.unlock()
        for background in self.backgrounds:
            background.unlock()

    def message(self, group, message):
        for sprite in self.groups[group]:
            sprite.message(message)

    def add_effect(self, effect):
        self.effects.append(effect)

    def clear_effects(self):
        self.effects.clear()

    def spawn(self, sprite_name, rect, z=None, **custom_fields):
        if z is None:
            z = self.entity_layer
        new_sprite = self.sprite_classes[self.map_type][sprite_name](
            self, rect, z, **custom_fields
        )
        self.add_sprite(new_sprite)
        return new_sprite

    def add_sprite(self, sprite):
        self.to_add.add(sprite)

    def add_sprite_internal(self, sprite):
        self.sprites.add(sprite)
        for group in sprite.groups:
            if group == "static-collision":
                self.rects["collision"].append(sprite.collision_rect)
                if hasattr(sprite, "extra_collision_rects"):
                    self.rects["collision"].extend(sprite.extra_collision_rects)
                continue
            if group == "vertical-collision":
                self.rects["platform"].append(sprite.collision_rect)
                if hasattr(sprite, "extra_collision_rects"):
                    self.rects["platform"].extend(sprite.extra_collision_rects)
            self.groups[group].add(sprite)

    def finish_dialog(self, answer):
        self.gui.remove(self.dialog)
        self.dialog = None
        self.dialog_answer = answer
        self.dialog_event.set()

    async def run_dialog(self, *terms, face=None):
        async with self.dialog_lock:
            self.dialog = gui2d.Dialog(
                self, gui2d.dialog_rect(face is not None), terms[0], terms[1:], self.finish_dialog
            )
            self.gui.append(self.dialog)
            await self.dialog_event.wait()
            self.dialog_event.clear()
            answer = self.dialog_answer
            self.dialog_answer = None
            return answer

    async def fade(self, effect_type, *args):
        """"
        Args:
        "fadein_circle", x, y
        "fadeout_cirlce", x, y
        "fadeout_paint", r, g, b
        "fadein_paint", r, g, b
        "paint", r, g, b[, duration]
        """
        def get_color():
            if len(args):
                item1 = args.pop(0)
                print(item1)
                if isinstance(item1, str):
                    return item1
                else:
                    return item1, args.pop(0), args.pop(0)
            else:
                return "black"
        def get_pos():
            if len(args):
                return self.world_to_screen((args.pop(0), args.pop(0)))
            return self.world_to_screen(self.player.pos)
        def get_number():
            if len(args):
                return args.pop(0)
            return 0
        args = list(args)
        finish_event = asyncio.Event()
        effects = {
            "fadein_circle": lambda: visual_fx.CircleTransitionIn(util_draw.RESOLUTION, get_pos(), 400, on_done=finish_event.set),
            "fadeout_circle": lambda: visual_fx.CircleTransitionOut(util_draw.RESOLUTION, get_pos(), 400, on_done=finish_event.set),
            "fadein_paint": lambda: visual_fx.ColorTransitionIn(get_color(), on_done=finish_event.set),
            "fadeout_paint": lambda: visual_fx.ColorTransitionOut(get_color(), on_done=finish_event.set),
            "paint": lambda: visual_fx.Fill(get_color(), get_number(), on_done=finish_event.set),
        }
        effect = effects[effect_type]()
        self.add_effect(effect)
        await finish_event.wait()
        return effect  # only useful if you don't terminate

    def get_x(self, group="player"):
        if group not in self.groups:
            print(self.groups)
            exit()
        group = self.groups[group]
        return next(iter(group)).pos.x

    def get_y(self, group="player"):
        group = self.groups[group]
        return next(iter(group)).pos.y

    def get_z(self, group="player"):
        group = self.groups[group]
        return next(iter(group)).z

    def get_facing(self, group="player"):
        group = self.groups[group]
        return next(iter(group)).pos.y

    def get_group(self, group_name):
        return self.groups[group_name]

    def get_rects(self, rect_name):
        return self.rects[rect_name]

    def show(self, group="player"):
        group = self.groups[group]
        for sprite in group:
            sprite.show()

    def hide(self, group="player"):
        group = self.groups[group]
        for sprite in group:
            sprite.hide()

    @classmethod
    def load(cls, game, name, direction=None, position=None, entrance="normal"):
        # basic metadata
        folder = pathlib.Path("ldtk/simplified", name)
        data = game.loader.get_json(folder / "data.json", for_map=True)
        size = data["width"], data["height"]
        map_type = data["customFields"]["Maptype"]
        soundtrack = data["customFields"]["Soundtrack"]
        map_rect = pygame.Rect((0, 0), size)
        # level initialization
        player_position = data["customFields"]["start"]
        if map_type == cls.MAP_PLATFORMER:
            if direction == "left":
                player_position = (size[0] - 8, player_position[1])
            if direction == "right":
                print("right", player_position, position)
                player_position = (8, player_position[1])
        elif map_type == cls.MAP_HOVERBOARD:
            pass
        elif entrance == "normal":
            if direction == "down":
                player_position = (position[0], 8)
            if direction == "up":
                player_position = (position[0], size[1] - 8)
            if direction == "right":
                player_position = (8, position[1])
            if direction == "left":
                player_position = (size[0] - 8, position[1])
        level = cls(
            game,
            name=name,
            player_pos=player_position,
            player_facing=direction,
            map_size=size,
            map_type=map_type,
            soundtrack=soundtrack,
            entrance=entrance,
        )
        # background creation
        level.bgcolor = data["bgColor"]
        level.backgrounds.extend(
            Parallax.load(level, data["customFields"]["Background"])
        )
        if map_type == cls.MAP_HOVERBOARD:
            level.backgrounds.append(hoverboarding.ScrollingBackground(level))
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
            sprite_cls = cls.sprite_classes[map_type][key]
            if sprite_cls is None:
                continue
            for entity in value:
                level.add_sprite(
                    sprite_cls(
                        level,
                        (entity["x"], entity["y"], entity["width"], entity["height"]),
                        z=entity_layer,
                        **entity["customFields"],
                    )
                )
        # collision data creation
        background_type = data["customFields"]["Background"] or "chasm"
        for row, line in enumerate(
            game.loader.get_csv(folder / "Ground.csv", for_map=True)
        ):
            for col, value in enumerate(line):
                value = int(value)
                rect = pygame.FRect(col * 16, row * 16, 16, 16)
                if map_type == cls.MAP_PLATFORMER:
                    if value == cls.TERRAIN_GROUND:
                        level.rects["collision"].append(rect)
                    if value == cls.TERRAIN_GROUND2:
                        level.rects["platform"].append(rect)
                elif map_type in {cls.MAP_TOPDOWN, cls.MAP_HOUSE}:
                    if value == cls.TERRAIN_CLEAR:
                        level.rects[background_type].append(rect)
                    if value in {cls.TERRAIN_GROUND, cls.TERRAIN_GROUND2}:
                        level.rects["ground"].append(rect)
        if map_type == cls.MAP_TOPDOWN:
            for row, line in enumerate(
                    game.loader.get_csv(folder / "Elevation.csv", for_map=True)
            ):
                for col, value in enumerate(line):
                    value = int(value)
                    rect = pygame.FRect(col * 16, row * 16, 16, 16)
                    if value == cls.TERRAIN_MOUNTAIN:
                        level.rects["mountain"].append(rect)

            level.player.z = entity_layer
        print("rects", level.rects)
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
        dest = self.player.pos
        self.viewport_rect.center = self.viewport_rect.center + pygame.Vector2(dest - self.viewport_rect.center).clamp_magnitude(CAMERA_SPEED)
        self.viewport_rect.clamp_ip(self.map_rect)
        # update backgrounds
        for background in self.backgrounds:
            background.update(dt)
        # update gui
        for sprite in self.gui:
            sprite.update(dt)
        # update visual effects
        self.effects = [effect for effect in self.effects if effect.update(dt)]
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
