import asyncio
import pathlib
from collections import defaultdict
from random import uniform
from typing import Any, Callable, Iterator, cast

import pygame
from pygame.typing import ColorLike, Point, RectLike

from gamelibs import (
    animation,
    game_state,
    gui2d,
    interfaces,
    particles,
    platformer,
    hoverboarding,
    sprite,
    topdown,
    util_draw,
    visual_fx,
    hardware,
)

CAMERA_SPEED = 128


class Parallax(interfaces.Background):
    def __init__(
        self,
        level: interfaces.Level,
        anim: interfaces.Animation,
        rect: RectLike = ((0, 0), util_draw.RESOLUTION),
        item_size: tuple[int, int] = (64, 64),
        scroll_speed: tuple[float, float] = (1, 1),
        anchor_bottom: bool = False,
        loop_x: bool = True,
        loop_y: bool = True,
    ) -> None:
        self.level = level
        self.anim = anim
        self.image = anim.image
        self._rect = pygame.FRect(rect)
        self.scroll_speed = pygame.Vector2(scroll_speed)
        self.item_size = pygame.Vector2(item_size)
        self.anchor_bottom = anchor_bottom
        self.loop_x = loop_x
        self.loop_y = loop_y

    @property
    def rect(self) -> pygame.FRect:
        return self._rect

    def lock(self) -> None:
        pass

    def unlock(self) -> None:
        pass

    def update(self, dt: float) -> None:
        self.anim.update(dt)
        self.image = self.anim.image

    @classmethod
    def load(cls, level: interfaces.Level, name: str) -> Iterator["Parallax"]:
        # load background data
        data = hardware.loader.get_json("backgrounds.json")
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
        source_surface = hardware.loader.get_surface(background_data["source"])
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
                item_size = tuple(layer["frames"][0][2:])
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
                scroll_speed=(layer["scroll_x"], layer["scroll_y"]),
                anchor_bottom=anchor_bottom,
                loop_x=layer["loop_x"],
                loop_y=layer["loop_y"],
            )

    def draw(self, surface: pygame.Surface, offset: Point) -> None:
        offset = pygame.Vector2(offset)
        if (not self.loop_y) and self.anchor_bottom:
            offset.y += self.level.map_rect.height - self.item_size.y
        offset = offset.elementwise() * self.scroll_speed
        if self.loop_x:
            offset.x = offset.x % self.item_size.x - self.item_size.x
        if self.loop_y:
            offset.y = offset.y % self.item_size.y - self.item_size.y
        surface.blit(self.image, self.rect.move(offset))


class Level(game_state.GameState, interfaces.Level):
    AXIS_X = 1
    AXIS_Y = 2

    TERRAIN_CLEAR = 0
    TERRAIN_GROUND = 1
    TERRAIN_GROUND2 = 2

    TERRAIN_MOUNTAIN = 1

    sprite_classes: dict[interfaces.MapType, dict[str, type | None]] = {
        interfaces.MapType.TOPDOWN: {
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
            "Spapple": topdown.immobile.Spapple,
            "Spikefruit": topdown.immobile.Spikefruit,
            "WaspberryBush": topdown.immobile.WaspberryBush,
            "Waspberry": topdown.immobile.Waspberry,
        },
        interfaces.MapType.HOUSE: {
            "Emerald": platformer.immobile.Emerald,  # same for both perspectives
            "Furniture": topdown.immobile.Furniture,
        },
        interfaces.MapType.PLATFORMER: {
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
        interfaces.MapType.HOVERBOARD: {
            "Drone": hoverboarding.Drone,
            "DeadPlayer": hoverboarding.DeadPlayer,
            "Rock": hoverboarding.Rock,
            "Stump": hoverboarding.Stump,
            "Player": topdown.mobile.Player,
        },
    }

    def __init__(
        self,
        game: interfaces.Game,
        name: interfaces.FileID,
        player_pos: Point = (0, 0),
        player_facing: interfaces.Direction | None = None,
        map_size: Point = (256, 256),
        map_type: interfaces.MapType = interfaces.MapType.TOPDOWN,
        soundtrack: interfaces.FileID | None = None,
        entrance: interfaces.MapEntranceType = interfaces.MapEntranceType.NORMAL,
    ) -> None:
        super().__init__(game)
        self._map_rect = pygame.Rect((0, 0), map_size)
        self._name = name
        self.backgrounds: list[interfaces.Background] = []
        self.groups: dict[str, set[interfaces.Sprite]] = defaultdict(set)
        self.rects: dict[str, list[interfaces.MiscRect]] = defaultdict(list)
        self.soundtrack = soundtrack
        rect = pygame.FRect(0, 0, 16, 16)
        small_rect = pygame.FRect(0, 0, 5, 5)
        rect.center = player_pos
        if map_type == interfaces.MapType.PLATFORMER:
            self.player = platformer.player.Player(
                cast(interfaces.PlatformerLevel, self), rect
            )
            self.iball = topdown.mobile.Iball(self, small_rect)
        elif map_type in {interfaces.MapType.HOUSE, interfaces.MapType.TOPDOWN}:
            self.player = topdown.mobile.Player(self, rect, entrance=entrance)
            self.iball = topdown.mobile.Iball(self, small_rect)
        elif map_type == interfaces.MapType.HOVERBOARD:
            rect.size = (32, 32)
            self.player = hoverboarding.Player(
                cast(interfaces.HoverboardLevel, self), rect
            )
            self.iball = topdown.mobile.Iball(self, small_rect)
        else:
            print("AAAAHAHH")
            raise
        self._map_type = map_type
        self.entity_layer = 0
        if player_facing and isinstance(self.player, topdown.mobile.Player):
            self.player.last_facing = player_facing
        self.sprites: set[interfaces.Sprite] = set()
        self.to_add: set[interfaces.Sprite] = set()
        self.gui: list[interfaces.GUISprite] = [
            gui2d.HeartMeter(self, (2, 2, 16 * 9, 9)),
            gui2d.EmeraldMeter(self, (2, 11, 0, 0)),
        ]
        self.dialog = None
        self.dialog_answer = None
        self.dialog_lock = asyncio.Lock()
        self.dialog_event = asyncio.Event()
        self.viewport_rect = pygame.FRect(util_draw.SCREEN_RECT)
        self.effects: list[interfaces.GlobalEffect] = []
        self.locked = False

        self.shake_magnitude = 0
        self.shake_delta = 0
        self.shake_axes = 0
        self.speed = 0  # used for hoverboard levels
        self.dt_multiplier = 1
        self.particle_manager = particles.ParticleManager()

        self.add_sprite(self.player)
        self.add_sprite(self.iball)
        self.update(0)
        self.get_game().delayed_callback(
            0, lambda: self.get_game().run_cutscene("level_begin")
        )
        surface = hardware.loader.create_surface((16, 16))
        surface.fill("blue")

    def attach(self, base: str, follower: str="player") -> None:
        print(base, self.get_group(base))
        print(follower, self.get_group(follower))
        next(iter(self.get_group(follower))).attach(next(iter(self.get_group(base))))

    def add_particle(self, surface: pygame.Surface, rect: RectLike, velocity: Point, duration: float) -> int:
        return self.particle_manager.add_particle(
            surface,
            rect,
            velocity,
            duration
        )

    def time_phase(self, mult: float) -> None:
        self.dt_mult = mult

    @property
    def map_rect(self) -> pygame.Rect:
        return self._map_rect

    @property
    def map_type(self) -> interfaces.MapType:
        return self._map_type

    @property
    def name(self) -> interfaces.FileID:
        return self._name

    def shake(
        self,
        magnitude: float = 5,
        delta: float = 8,
        axis: interfaces.Axis = interfaces.Axis.X | interfaces.Axis.Y,
    ) -> None:
        self.shake_magnitude += magnitude
        self.shake_delta += delta
        self.shake_axes = axis

    async def attempt_map_cutscene(self) -> Any:
        try:
            hardware.loader.get_cutscene(self.name)
        except FileNotFoundError:
            return False
        return await self.get_game().run_sub_cutscene(self.name, {})

    def lock(self, group: str | None=None) -> None:
        if group is None:
            self.locked = True
            for sprite in self.sprites:
                sprite.lock()
            for background in self.backgrounds:
                background.lock()
        else:
            for sprite in self.get_group(group):
                sprite.lock()

    def unlock(self, group: str | None=None) -> None:
        if group is None:
            self.locked = False
            for sprite in self.sprites:
                sprite.unlock()
            for background in self.backgrounds:
                background.unlock()
        else:
            for sprite in self.get_group(group):
                sprite.unlock()

    def message(self, message: str, group: str="player") -> None:
        for sprite in self.groups[group]:
            sprite.message(message)

    def add_effect(self, effect: interfaces.GlobalEffect) -> None:
        self.effects.append(effect)

    def clear_effects(self) -> None:
        self.effects.clear()

    def spawn(
        self,
        sprite_name: str,
        rect: RectLike,
        z: int | None = None,
        **custom_fields: Any
    ) -> interfaces.Sprite | None:
        if z is None:
            z = self.entity_layer
        sprite_cls = self.sprite_classes[self.map_type].get(sprite_name, None)
        if sprite_cls is not None:
            new_sprite = sprite_cls(self, rect, z, **custom_fields)
            self.add_sprite(new_sprite)
            return new_sprite

    def add_sprite(self, sprite: interfaces.Sprite) -> None:
        self.to_add.add(sprite)

    def add_sprite_internal(self, sprite: interfaces.Sprite) -> None:
        self.sprites.add(sprite)
        for group in sprite.groups:
            if group == "static-collision":
                self.rects["collision"].append(sprite.collision_rect)  # type: ignore
                if hasattr(sprite, "extra_collision_rects"):
                    self.rects["collision"].extend(sprite.extra_collision_rects)  # type: ignore
                continue
            if group == "vertical-collision":
                self.rects["platform"].append(sprite.collision_rect)  # type: ignore
                if hasattr(sprite, "extra_collision_rects"):
                    self.rects["platform"].extend(sprite.extra_collision_rects)  # type: ignore
            self.groups[group].add(sprite)

    def finish_dialog(self, answer: str | None) -> None:
        assert self.dialog is not None, "Dialog is not running"
        self.gui.remove(self.dialog)
        self.dialog = None
        self.dialog_answer = answer
        self.dialog_event.set()

    async def run_dialog(self, *terms: str, face: str | None = None) -> None | str:
        async with self.dialog_lock:
            self.dialog = gui2d.Dialog(
                self,
                gui2d.dialog_rect(face is not None),
                terms[0],
                list(terms[1:]),
                self.finish_dialog,
            )
            self.gui.append(self.dialog)
            await self.dialog_event.wait()
            self.dialog_event.clear()
            answer = self.dialog_answer
            self.dialog_answer = None
            return answer

    async def fade(
        self, effect_type: str, *args: str | float
    ) -> interfaces.GlobalEffect:
        """ "
        Args:
        "fadein_circle", x, y
        "fadeout_cirlce", x, y
        "fadeout_paint", r, g, b
        "fadein_paint", r, g, b
        "paint", r, g, b[, duration]
        """

        def get_color() -> ColorLike:
            if len(arg_list):
                item1 = arg_list.pop(0)
                print(item1)
                if isinstance(item1, str):
                    return item1
                else:
                    return int(item1), int(arg_list.pop(0)), int(arg_list.pop(0))
            else:
                return "black"

        def get_pos() -> pygame.Vector2:
            if len(arg_list):
                assert isinstance(
                    arg_list[0], (int, float)
                ), "Position must be a number"
                assert isinstance(
                    arg_list[1], (int, float)
                ), "Position must be a number"
                return self.world_to_screen((arg_list.pop(0), arg_list.pop(0)))  # type: ignore
            return self.world_to_screen(self.player.pos)

        def get_number() -> float:
            if len(arg_list):
                assert isinstance(arg_list[0], (int, float)), "Arg must be a number"
                return arg_list.pop(0)  # type: ignore
            return 0

        arg_list = list(args)
        finish_event = asyncio.Event()
        effects: dict[str, Callable[[], interfaces.GlobalEffect]] = {
            "fadein_circle": lambda: visual_fx.CircleTransitionIn(
                util_draw.RESOLUTION, get_pos(), 400, on_done=finish_event.set
            ),
            "fadeout_circle": lambda: visual_fx.CircleTransitionOut(
                util_draw.RESOLUTION, get_pos(), 400, on_done=finish_event.set
            ),
            "fadein_paint": lambda: visual_fx.ColorTransitionIn(
                get_color(), on_done=finish_event.set
            ),
            "fadeout_paint": lambda: visual_fx.ColorTransitionOut(
                get_color(), on_done=finish_event.set
            ),
            "paint": lambda: visual_fx.Fill(
                get_color(), get_number(), on_done=finish_event.set
            ),
        }
        effect = effects[effect_type]()
        self.add_effect(effect)
        await finish_event.wait()
        return effect  # only useful if you don't terminate

    def get_x(self, group: str = "player") -> float:
        if group not in self.groups:
            exit()
        return next(iter(self.get_group(group))).pos.x

    def get_y(self, group: str = "player") -> float:
        if group not in self.groups:
            exit()
        return next(iter(self.get_group(group))).pos.y

    def get_z(self, group: str = "player") -> int:
        if group not in self.groups:
            exit()
        return next(iter(self.get_group(group))).z

    def get_facing(self, group: str = "player") -> interfaces.Direction:
        return next(iter(self.get_group(group))).facing  # type: ignore

    def get_group(self, group_name: str) -> set[interfaces.Sprite]:
        return self.groups[group_name]

    def get_player(self) -> interfaces.Player:
        return self.player

    def get_rects(self, rect_name: str) -> list[interfaces.MiscRect]:
        return self.rects[rect_name]

    def show(self, group: str = "player") -> None:
        for sprite in self.get_group(group):
            sprite.show()

    def hide(self, group: str = "player") -> None:
        for sprite in self.get_group(group):
            sprite.hide()

    @classmethod
    def load(
        cls,
        game: interfaces.Game,
        name: interfaces.FileID,
        direction: interfaces.Direction | None = None,
        position: Point | None = None,
        entrance: interfaces.MapEntranceType = interfaces.MapEntranceType.NORMAL,
    ) -> "Level":
        # basic metadata
        folder = pathlib.Path("ldtk/simplified", name)
        data = hardware.loader.get_json(str(folder / "data"), for_map=True)
        size = data["width"], data["height"]
        map_type = data["customFields"]["Maptype"]
        soundtrack = data["customFields"]["Soundtrack"]
        map_rect = pygame.Rect((0, 0), size)
        # level initialization
        player_position: list[int] = data["customFields"]["start"]
        position = (
            [int(position[0]), int(position[1])] if position else player_position.copy()
        )
        if map_type == interfaces.MapType.PLATFORMER:
            if direction == "left":
                player_position = [size[0] - 8, player_position[1]]
            if direction == "right":
                player_position = [8, player_position[1]]
        elif map_type == interfaces.MapType.HOVERBOARD:
            pass
        elif entrance == interfaces.MapEntranceType.NORMAL:
            if direction == interfaces.Direction.DOWN:
                player_position = [position[0], 8]
            if direction == "up":
                player_position = [position[0], size[1] - 8]
            if direction == "right":
                player_position = [8, position[1]]
            if direction == "left":
                player_position = [size[0] - 8, position[1]]
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
        if map_type == interfaces.MapType.HOVERBOARD:
            level.backgrounds.append(
                hoverboarding.ScrollingBackground(
                    cast(interfaces.HoverboardLevel, level)
                )
            )
        # tile layers
        entity_layer = data["customFields"]["entity_layer"]
        level.entity_layer = entity_layer
        for layer_ind, layer in enumerate(data["layers"]):
            level.add_sprite(
                sprite.Sprite(
                    level,
                    hardware.loader.get_surface(folder / layer),
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
            hardware.loader.get_csv(str(folder / "Ground"), for_map=True)
        ):
            for col, value in enumerate(line):
                value = int(value)
                rect = pygame.FRect(col * 16, row * 16, 16, 16)
                if map_type == interfaces.MapType.PLATFORMER:
                    if value == cls.TERRAIN_GROUND:
                        level.rects["collision"].append(rect)
                    if value == cls.TERRAIN_GROUND2:
                        level.rects["platform"].append(rect)
                elif map_type in {interfaces.MapType.TOPDOWN, interfaces.MapType.HOUSE}:
                    if value == cls.TERRAIN_CLEAR:
                        level.rects[background_type].append(rect)
                    if value in {cls.TERRAIN_GROUND, cls.TERRAIN_GROUND2}:
                        level.rects["ground"].append(rect)
        if map_type == interfaces.MapType.TOPDOWN:
            for row, line in enumerate(
                hardware.loader.get_csv(str(folder / "Elevation"), for_map=True)
            ):
                for col, value in enumerate(line):
                    value = int(value)
                    rect = pygame.FRect(col * 16, row * 16, 16, 16)
                    if value == cls.TERRAIN_MOUNTAIN:
                        level.rects["mountain"].append(rect)

        level.player.z = entity_layer
        level.iball.z = entity_layer + 1
        level.iball.move_to(level.player.head_rect.center)
        return level

    def world_to_screen(self, pos: Point) -> pygame.Vector2:
        return pygame.Vector2(pos) - self.viewport_rect.topleft

    def screen_to_world(self, pos: Point) -> pygame.Vector2:
        return pygame.Vector2(pos) + self.viewport_rect.topleft

    def update(self, dt: float) -> bool:
        # adjusts dt if needed
        dt *= self.dt_multiplier
        self.dt_multiplier = 1
        # adds new sprites to the list
        for sprite in self.to_add:
            self.add_sprite_internal(sprite)
        self.to_add.clear()
        # removes dead sprites from the list
        self.sprites = {sprite for sprite in self.sprites if sprite.update(dt)}
        for group in self.groups.values():
            group &= self.sprites
        dest = self.player.pos
        self.viewport_rect.center = self.viewport_rect.center + pygame.Vector2(
            dest - self.viewport_rect.center
        ).clamp_magnitude(CAMERA_SPEED)
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
        # update particles
        self.particle_manager.update(dt)
        return super().update(dt) and True

    def draw(self) -> None:
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
            self.game.window_surface.blit(
                sprite.to_draw,
                rect,
            )
        # draw particles
        self.particle_manager.draw(self.game.window_surface, (-int(self.viewport_rect.left), -int(self.viewport_rect.top)))
        # draw visual effects
        for effect in self.effects:
            effect.draw(self.game.window_surface)
        # draw gui
        for sprite in self.gui:
            sprite.draw(self.game.window_surface)
