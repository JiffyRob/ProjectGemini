# TODO: This type hinting is terrible.
# Why did I even bother with this...?

from functools import partial
from math import ceil, sin
from typing import Any, Callable, Sequence
from enum import Enum, auto

import pygame
from pygame.typing import RectLike

from gamelibs import (
    animation,
    game_state,
    sprite,
    timer,
    env,
    util_draw,
    interfaces,
    hardware,
)


def nine_slice(
    images: Sequence[pygame.Surface], size: tuple[int, int]
) -> pygame.Surface:
    image = hardware.loader.create_surface(size)
    rect = pygame.Rect(0, 0, *size)
    rects = [image.get_rect() for image in images]
    middle_rect = rect.copy()
    middle_rect.height -= rects[0].height + rects[6].height
    middle_rect.width -= rects[0].width + rects[2].width
    middle_rect.center = rect.center
    image.blit(images[0], (0, 0))
    image.blit(
        pygame.transform.scale(images[1], (middle_rect.width, rects[1].height)),
        (middle_rect.left, 0),
    )
    image.blit(images[2], (middle_rect.right, 0))
    image.blit(
        pygame.transform.scale(images[3], (rects[3].width, middle_rect.height)),
        (0, middle_rect.top),
    )
    image.blit(pygame.transform.scale(images[4], middle_rect.size), middle_rect.topleft)
    image.blit(
        pygame.transform.scale(images[5], (rects[5].width, middle_rect.height)),
        middle_rect.topright,
    )
    image.blit(images[6], (0, middle_rect.bottom))
    image.blit(
        pygame.transform.scale(images[7], (middle_rect.width, rects[7].height)),
        middle_rect.bottomleft,
    )
    image.blit(images[8], middle_rect.bottomright)
    return image


def three_slice(images: Sequence[pygame.Surface], width: int) -> pygame.Surface:
    if width < images[0].get_width() + images[2].get_width():
        return images[1]
    image = hardware.loader.create_surface((width, images[0].get_height()))
    image.blit(images[0], (0, 0))
    image.blit(
        pygame.transform.scale(
            images[1],
            (
                width - images[0].get_width() - images[1].get_width(),
                images[1].get_height(),
            ),
        ),
        (images[0].get_width(), 0),
    )
    image.blit(images[2], (width - images[2].get_width(), 0))
    return image


class Background(sprite.GUISprite):
    def __init__(self, level: interfaces.Level, rect: RectLike, z: int = 0) -> None:
        rect = pygame.Rect(rect)
        super().__init__(
            level,
            nine_slice(
                [
                    hardware.loader.get_surface("gui.png", i)
                    for i in (
                        (80, 80, 16, 16),
                        (96, 80, 16, 16),
                        (112, 80, 16, 16),
                        (80, 96, 16, 16),
                        (96, 96, 16, 16),
                        (112, 96, 16, 16),
                        (80, 112, 16, 16),
                        (96, 112, 16, 16),
                        (112, 112, 16, 16),
                    )
                ],
                rect.size,
            ),
            rect,
            z,
        )


class Button(sprite.GUISprite):
    class State(Enum):
        NORMAL = auto()
        DISABLED = auto()
        SELECTED = auto()

    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike,
        top_image: pygame.Surface,
        on_click: Callable[[], Any] = lambda: None,
        z: int = 0,
    ) -> None:
        rect = pygame.Rect(rect)
        self.image_dict: dict[Button.State, pygame.Surface] = {
            self.State.NORMAL: three_slice(
                [
                    hardware.loader.get_surface("gui.png", i)
                    for i in (
                        (16, 64, 16, 16),
                        (32, 64, 16, 16),
                        (48, 64, 16, 16),
                    )
                ],
                rect.width,
            ),
            self.State.SELECTED: three_slice(
                [
                    hardware.loader.get_surface("gui.png", i)
                    for i in (
                        (16, 48, 16, 16),
                        (32, 48, 16, 16),
                        (48, 48, 16, 16),
                    )
                ],
                rect.width,
            ),
            self.State.DISABLED: three_slice(
                [
                    hardware.loader.get_surface("gui.png", i)
                    for i in ((16, 80, 16, 16), (32, 80, 16, 16), (48, 80, 16, 16))
                ],
                rect.width,
            ),
        }
        self.top_image = top_image
        self.top_image_rect = self.top_image.get_rect(center=rect.center)
        self.state = self.State.NORMAL
        self.click = on_click
        super().__init__(level, None, rect, z)

    def select(self) -> None:
        self.state = self.State.SELECTED

    def deselect(self) -> None:
        self.state = self.State.NORMAL

    def disable(self) -> None:
        self.state = self.State.DISABLED

    def enable(self) -> None:
        self.state = self.State.NORMAL

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.image_dict[self.state], self.rect)
        surface.blit(self.top_image, self.top_image.get_rect(center=self.rect.center))


class ToggleSwitch(sprite.GUISprite):
    class State(Enum):
        DISABLED = auto()
        NORMAL = auto()
        SELECTED = auto()

    FRAME_DELAY = 0.06

    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike,
        z: int = 0,
        on_toggle: Callable[[Any], Any] = lambda value: None,
        start_on: bool = False,
    ) -> None:
        frames = hardware.loader.get_spritesheet("switch", (16, 8))
        length = 10
        self.anim_dict: dict[ToggleSwitch.State, tuple[pygame.Surface, ...]] = {
            self.State.DISABLED: frames[:length],
            self.State.NORMAL: frames[length : length * 2],
            self.State.SELECTED: frames[length * 2 : length * 3],
        }
        self.age = 0
        self.state = self.State.NORMAL
        self.frame: int
        if start_on:
            self.on = True
            self.frame = length - 1
        else:
            self.on = False
            self.frame = 0
        self.on_toggle = on_toggle
        super().__init__(level, None, rect, z)

    def click(self) -> None:
        self.on_toggle(self.on)
        self.on = not self.on

    def update(self, dt: float) -> bool:
        self.age += dt
        if self.age > self.FRAME_DELAY:
            if self.on:
                self.frame += 1
            else:
                self.frame -= 1
            self.age = 0
        frames = self.anim_dict[self.state]
        self.frame = int(pygame.math.clamp(self.frame, 0, len(frames) - 1))
        return super().update(dt)

    def select(self) -> None:
        self.state = self.State.SELECTED

    def deselect(self) -> None:
        self.state = self.State.NORMAL

    def disable(self) -> None:
        self.state = self.State.DISABLED

    def enable(self) -> None:
        self.state = self.State.NORMAL

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.anim_dict[self.state][self.frame], self.rect)


class Selector(sprite.GUISprite):
    class State(Enum):
        DISABLED = auto()
        NORMAL = auto()
        SELECTED = auto()

    COLORS = {
        State.DISABLED: "#4c505b",
        State.NORMAL: "#777e86",
        State.SELECTED: "#cbcbcb",
    }

    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike,
        values: Sequence[Any],
        z: int = 0,
        on_toggle: Callable[[Any], Any] = lambda value: None,
        initial_value: Any = None,
    ) -> None:
        super().__init__(level, None, rect, z)
        self.values = values
        if initial_value is None:
            self.index = 0
        else:
            self.index = values.index(initial_value)
        self.state = self.State.NORMAL
        self.on_toggle = on_toggle

    def click(self) -> None:
        self.index += 1
        self.index %= len(self.values)
        self.on_toggle(self.values[self.index])

    def select(self) -> None:
        self.state = self.State.SELECTED

    def deselect(self) -> None:
        self.state = self.State.NORMAL

    def disable(self) -> None:
        self.state = self.State.DISABLED

    def enable(self) -> None:
        self.state = self.State.NORMAL

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, self.COLORS[self.state], self.rect)
        text = hardware.loader.font.render(
            str(self.values[self.index]), int(self.rect.width - 4)
        )
        text_rect = text.get_rect()
        text_rect.center = self.rect.center
        surface.blit(text, text_rect)


class Label(sprite.GUISprite):
    def __init__(
        self, level: interfaces.Level, rect: RectLike, text: str, z: int = 0
    ) -> None:
        rect = pygame.Rect(rect)
        surface = hardware.loader.create_surface(rect.size)
        text_surf = hardware.loader.font.render(text, rect.width)
        text_rect = text_surf.get_rect()
        text_rect.midleft = pygame.Rect((0, 0), rect.size).midleft
        surface.blit(text_surf, text_rect)
        super().__init__(level, surface, rect, z)


class Setting(sprite.GUISprite):
    class State:
        DISABLED = auto()
        NORMAL = auto()
        SELECTED = auto()

    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike,
        name: str,
        start_value: Any = None,
        on_switch: Callable[[Any], Any] = lambda value: print(value),
        z: int = 0,
    ) -> None:
        super().__init__(level, None, rect, z)
        rect = pygame.Rect(rect)
        label_rect = rect.copy()
        label_rect.width //= 2
        self.label = Label(level, label_rect, name)
        self.type: type = type(start_value)
        if self.type == bool:
            switch_rect = rect.copy()
            switch_rect.size = (16, 8)
            switch_rect.right = rect.right
            switch_rect.centery = rect.centery
            self.toggler = ToggleSwitch(
                level, switch_rect, z, on_switch, not start_value
            )
        elif self.type == interfaces.ScaleMode:
            switch_rect = rect.copy()
            switch_rect.size = (128, self.rect.height)
            switch_rect.right = rect.right
            self.toggler = Selector(
                level,
                switch_rect,
                list(interfaces.ScaleMode),
                z,
                on_switch,
                start_value,
            )
        elif self.type == interfaces.GraphicsSetting:
            switch_rect = rect.copy()
            switch_rect.size = (128, self.rect.height)
            switch_rect.right = rect.right
            self.toggler = Selector(
                level,
                switch_rect,
                list(interfaces.GraphicsSetting),
                z,
                on_switch,
                start_value,
            )
        elif self.type == interfaces.FrameCap:
            switch_rect = rect.copy()
            switch_rect.size = (128, self.rect.height)
            switch_rect.right = rect.right
            self.toggler = Selector(
                level, switch_rect, list(interfaces.FrameCap), z, on_switch, start_value
            )
        else:
            raise TypeError(
                "Setting is of unsupported type.  See interfaces.GameSetting fields for up-to-date list."
            )

        self.state = self.State.NORMAL

    def update(self, dt: float) -> bool:
        self.label.update(dt)
        self.toggler.update(dt)
        return super().update(dt)

    def click(self) -> None:
        self.toggler.click()

    def select(self) -> None:
        self.toggler.select()
        self.state = self.State.SELECTED

    def deselect(self) -> None:
        self.toggler.deselect()
        self.state = self.State.NORMAL

    def disable(self) -> None:
        self.toggler.disable()
        self.state = self.State.DISABLED

    def enable(self) -> None:
        self.toggler.enable()
        self.state = self.State.NORMAL

    def draw(self, surface: pygame.Surface) -> None:
        self.label.draw(surface)
        self.toggler.draw(surface)


class KnifeIndicator(sprite.GUISprite):
    STATE_GREEN = 0
    STATE_RED = 1

    def __init__(
        self,
        level: interfaces.Level,
        button_dict: dict[tuple[int | None, int | None], Button],
        start_pos: tuple[int, int] = (0, 0),
        z: int = 0,
    ) -> None:
        button_coords = list(button_dict.keys())
        button_xs = [i[0] for i in button_coords if i[0] is not None]
        button_ys = [i[1] for i in button_coords if i[1] is not None]
        self.button_dict = button_dict
        self.button_bounds = pygame.Rect(
            min(button_xs), min(button_ys), max(button_xs), max(button_ys)
        ).inflate(5, 5)
        self.anim = animation.Animation(
            [
                hardware.loader.get_surface("gui.png", i)
                for i in (
                    (0, 48, 16, 16),
                    (0, 64, 16, 16),
                    (0, 80, 16, 16),
                    (0, 96, 16, 16),
                )
            ]
        )
        self.red_anim = animation.Animation(
            [
                hardware.loader.get_surface("gui.png", i)
                for i in (
                    (16, 96, 16, 16),
                    (32, 96, 16, 16),
                    (48, 96, 16, 16),
                    (64, 96, 16, 16),
                )
            ]
        )
        self.state = self.STATE_GREEN
        self.age = 0
        self.button_coord: tuple[int | None, int | None] = (start_pos[0], start_pos[1])
        self.last_coord: tuple[int | None, int | None] = (start_pos[0], start_pos[1])
        self.last_x: int = start_pos[0]
        self.last_y: int = start_pos[1]
        self.button.select()
        self.motion_cooldown = timer.Timer(150)
        super().__init__(
            level,
            None,
            z=z,
        )

    @property
    def button(self) -> Button:
        return self.button_dict[self.button_coord]

    def search(
        self, direction: interfaces.Direction
    ) -> tuple[int, int] | tuple[int, None] | tuple[None, int] | None:
        current_x = self.last_x
        current_y = self.last_y
        delta_x, delta_y = direction.to_tuple()
        while self.button_bounds.collidepoint(current_x, current_y):
            current_x += delta_x
            current_y += delta_y
            current_coord = (current_x, current_y)
            if (
                current_coord in self.button_dict
                and self.button_dict[current_coord].state
                == self.button_dict[current_coord].State.NORMAL
            ):
                return current_coord
            x_only_coord = (current_coord[0], None)
            y_only_coord = (None, current_coord[1])
            if (
                x_only_coord in self.button_dict
                and self.button_dict[x_only_coord].state
                == self.button_dict[x_only_coord].State.NORMAL
            ):
                return x_only_coord
            if (
                y_only_coord in self.button_dict
                and self.button_dict[y_only_coord].state
                == self.button_dict[y_only_coord].State.NORMAL
            ):
                return y_only_coord
        return None

    def move(self, direction: interfaces.Direction) -> None:
        if not self.motion_cooldown.done():
            return
        new_coord = self.search(direction)
        if new_coord is None:
            return
        self.last_coord = self.button_coord
        self.button_coord = new_coord
        if new_coord[0] is not None:
            self.last_x = new_coord[0]
        if new_coord[1] is not None:
            self.last_y = new_coord[1]
        self.rect.midright = self.button.rect.midleft
        self.button_dict[self.last_coord].deselect()
        self.button.select()
        self.motion_cooldown.reset()

    def update(self, dt: float) -> bool:
        pressed = hardware.input_queue.held
        if "up" in pressed:
            self.move(interfaces.Direction.UP)
        if "down" in pressed:
            self.move(interfaces.Direction.DOWN)
        if "left" in pressed:
            self.move(interfaces.Direction.LEFT)
        if "right" in pressed:
            self.move(interfaces.Direction.RIGHT)

        if "interact" in hardware.input_queue.just_pressed:
            self.button.click()
        self.age += dt
        self.rect.midright = self.button.rect.midleft
        self.anim.update(dt)
        self.red_anim.update(dt)
        self.motion_cooldown.update()
        return True

    def draw(self, surface: pygame.Surface) -> None:
        anim = self.anim
        if self.state == self.STATE_RED:
            anim = self.red_anim
        surface.blit(anim.image, self.rect.move(sin(self.age * 5) * 2, 0))

    def make_red(self) -> None:
        self.state = self.STATE_RED

    def make_green(self) -> None:
        self.state = self.STATE_GREEN


class TextButton(Button):
    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike,
        text: str,
        on_click: Callable[[], Any] = lambda: None,
    ) -> None:
        super().__init__(
            level,
            rect,
            hardware.loader.font.render(text),
            on_click=on_click,
        )
        self.text = text

    def draw(self, surface: pygame.Surface) -> None:
        surface.blit(self.top_image, self.top_image.get_rect(midleft=self.rect.midleft))


class TextInput(sprite.GUISprite):
    def __init__(
        self, level: interfaces.Level, rect: RectLike, z: int = 0, max_chars: int = 16
    ) -> None:
        super().__init__(level, None, rect, z)
        self.text: list[str] = ["_"] * max_chars
        self.cursor_position: int = 0
        self.age: float = 0

    def update(self, dt: float) -> bool:
        self.age += dt
        return super().update(dt)

    def draw(self, surface: pygame.Surface) -> None:
        text_copy = self.text.copy()
        if self.age % 1 < 0.5:
            text_copy[self.cursor_position] = "|"
        text = hardware.loader.font.render("".join(text_copy))
        surface.blit(text, text.get_rect(center=self.rect.center))

    def input_character(self, char: str) -> None:
        if char == "\b":
            self.cursor_position -= 1
            self.text[self.cursor_position] = "_"
        else:
            if char == "_":
                char = " "
            self.text[self.cursor_position] = char
            self.cursor_position += 1
        self.cursor_position = int(
            pygame.math.clamp(self.cursor_position, 0, len(self.text) - 1)
        )


class Save(TextButton):
    def __init__(
        self,
        level: interfaces.Level,
        rect: RectLike,
        index: int,
        name: str,
        path: interfaces.FileID,
    ) -> None:
        self.name = name
        self.path = path
        super().__init__(
            level,
            rect,
            f"{index}. {name}",
            self.load,
        )

    def get_level(self) -> "MainMenu":  # type: ignore
        return super().get_level()  # type: ignore

    def load(self) -> None:
        if self.get_level().delete_mode:
            if self.name:
                self.get_game().push_state(
                    DeleteConfirmationMenu(self.get_game(), self.name, self.path)
                )
            self.get_level().delete_mode_toggle()
            return
        if self.name:
            self.get_game().load_save(self.path)
        else:
            self.get_game().push_state(NameInputMenu(self.get_game()))


class Image(sprite.GUISprite):
    pass


class MainMenu(game_state.GameState):
    def __init__(self, game: interfaces.Game) -> None:
        super().__init__(game, "black")
        self.delete_mode = False

        backdrop = pygame.transform.scale(
            hardware.loader.get_surface("background.png"), util_draw.SCREEN_RECT.size
        )

        background_rect = util_draw.SCREEN_RECT.inflate(-16, -16)
        title1 = hardware.loader.get_surface("gui.png", (0, 0, 80, 16))
        title1_rect = pygame.Rect(20, background_rect.top + 10, *title1.get_size())

        title2 = hardware.loader.get_surface("gui.png", (0, 16, 128, 32))
        title2_rect = pygame.Rect(0, title1_rect.bottom, *title2.get_size())
        title2_rect.centerx = background_rect.centerx

        button_rect = pygame.Rect(0, 0, 150, 8)
        button_rect.top = title2_rect.bottom + 3
        button_rect.centerx = background_rect.centerx
        button_dict = {}

        save_names = hardware.loader.get_save_names(5)
        print(save_names)

        self.gui: list[interfaces.GUISprite] = [  # type: ignore
            Image(self, backdrop, util_draw.SCREEN_RECT),  # type: ignore
            Background(self, background_rect, -1),  # type: ignore
            Image(
                self,  # type: ignore
                title1,
                title1_rect,
            ),
            Image(
                self,  # type: ignore
                title2,
                title2_rect,
            ),
        ]
        i = 0
        for i, (save_name, save_path) in enumerate(save_names):
            button = Save(self, button_rect, i + 1, save_name, save_path)  # type: ignore
            self.gui.append(button)  # type: ignore
            button_dict[(0, i)] = button
            button_rect.top = button_rect.bottom + 3

        button_rect.height = 16
        button_rect.width -= 25
        button_rect.x += 25
        delete_button = Button(
            self,  # type: ignore
            button_rect,
            hardware.loader.font.render("Delete Data"),
            self.delete_mode_toggle,
        )
        i += 1
        button_dict[(0, i)] = delete_button
        self.gui.append(delete_button)

        button_rect.top = button_rect.bottom + 3

        settings_button = Button(
            self,  # type: ignore
            button_rect,
            hardware.loader.font.render("Settings"),
            self.open_settings,
        )
        i += 1
        button_dict[(0, i)] = settings_button
        self.gui.append(settings_button)

        button_rect.top = button_rect.bottom + 3

        if not env.PYGBAG:
            exit_button = Button(
                self,  # type: ignore
                button_rect,
                hardware.loader.font.render("Exit Game"),
                self.game.exit,
            )
            self.gui.append(exit_button)
            button_dict[(0, i + 2)] = exit_button

        self.knife = KnifeIndicator(self, button_dict=button_dict)  # type: ignore
        self.gui.append(self.knife)

        # TODO: better place for this...?
        self.game.play_soundtrack("CelestialHymn")

    def delete_mode_toggle(self) -> None:
        self.delete_mode = not self.delete_mode
        if self.delete_mode:
            self.knife.make_red()
        else:
            self.knife.make_green()

    def update(self, dt: float) -> bool:
        self.gui = [sprite for sprite in self.gui if sprite.update(dt)]
        if "quit" in hardware.input_queue.just_pressed:
            self.game.exit()
        return super().update(dt)

    def draw(self) -> None:
        super().draw()
        for sprite in self.gui:
            sprite.draw(self.game.window_surface)

    def start(self) -> None:
        self.pop()

    def quit(self) -> None:
        self.game.quit()

    def open_settings(self) -> None:
        self.get_game().push_state(SettingsMenu(self.game))


class NameInputMenu(game_state.GameState):
    MAX_CHARS = 16

    def __init__(self, game: interfaces.Game) -> None:
        super().__init__(game, "black")
        background_rect = util_draw.SCREEN_RECT.inflate(-16, -16)
        self.gui: list[interfaces.GUISprite] = [  # type: ignore
            Image(
                self,  # type: ignore
                pygame.transform.scale(
                    hardware.loader.get_surface("background.png"),
                    util_draw.SCREEN_RECT.size,
                ),
                util_draw.SCREEN_RECT,
            ),
            Background(self, background_rect, -1),  # type: ignore
        ]

        per_row = 14
        letters = "abcdefghijklmnopqrstuvwxyz_'ABCDEFGHIJKLMNOPQRSTUVWXYZ-\b"
        letter_size = (10, 16)
        keyboard_rect = pygame.Rect(
            0,
            0,
            letter_size[0] * per_row,
            ceil(len(letters) / per_row) * letter_size[1],
        )
        keyboard_rect.bottom = background_rect.bottom - 20
        keyboard_rect.centerx = background_rect.centerx
        letter_rect = pygame.Rect(keyboard_rect.topleft, letter_size)

        button_x = 0
        button_y = 0
        button_dict: dict[tuple[int | None, int | None], Button] = {}

        for letter in letters:
            button = TextButton(
                self, letter_rect, letter, partial(self.click_letter, letter)  # type: ignore
            )
            self.gui.append(button)
            button_dict[(button_x, button_y)] = button
            letter_rect.left = letter_rect.right
            button_x += 1
            if letter_rect.right > keyboard_rect.right:
                letter_rect.top = letter_rect.bottom
                letter_rect.left = keyboard_rect.left
                button_x = 0
                button_y += 1

        button_rect = pygame.Rect(
            (0, keyboard_rect.bottom), hardware.loader.font.size("ABCD")
        )
        button_rect.centerx = keyboard_rect.centerx
        cancel_button = TextButton(self, button_rect, "Back", self.cancel)  # type: ignore
        self.gui.append(cancel_button)
        button_dict[(None, button_y + 1)] = cancel_button

        button_rect.bottom = keyboard_rect.top
        confirm_button = TextButton(self, button_rect, "Done", self.confirm_name)  # type: ignore
        self.gui.append(confirm_button)
        button_dict[(None, -1)] = confirm_button

        self.gui.append(KnifeIndicator(self, button_dict, (0, 0), 1))  # type: ignore

        start_text = "_" * self.MAX_CHARS
        name_rect = pygame.Rect((0, 0), hardware.loader.font.size(start_text))
        name_rect.bottom = button_rect.top - 10
        name_rect.centerx = background_rect.centerx
        self.input = TextInput(self, name_rect)  # type: ignore
        self.gui.append(self.input)

    def update(self, dt: float) -> bool:
        self.gui = [sprite for sprite in self.gui if sprite.update(dt)]
        if "quit" in hardware.input_queue.just_pressed:
            self.game.quit()
        return super().update(dt)

    def draw(self) -> None:
        super().draw()
        for sprite in self.gui:
            sprite.draw(self.game.window_surface)

    def click_letter(self, letter: str) -> None:
        self.input.input_character(letter)

    def confirm_name(self) -> None:
        hardware.save.load(None)
        save_name = "".join(self.input.text).replace("_", "")
        if save_name:
            path = hardware.save.new(save_name)
            self.game.load_save(path)

    def cancel(self) -> None:
        self.pop()


class DeleteConfirmationMenu(game_state.GameState):
    def __init__(self, game: interfaces.Game, save_name: str, save_path: interfaces.FileID) -> None:
        self.save_name = save_name
        self.save_path = save_path
        super().__init__(game, (0, 0, 0, 0))
        background_rect = pygame.Rect(0, 0, 256, 48)
        background_rect.center = util_draw.SCREEN_RECT.center
        button1_rect = pygame.Rect(
            background_rect.left + 32,
            background_rect.top + 8,
            background_rect.width - 64,
            16,
        )
        button2_rect = pygame.Rect(
            background_rect.left + 32,
            background_rect.top + 24,
            background_rect.width - 64,
            16,
        )
        button_dict: dict[tuple[int | None, int | None], Button] = {
            (0, 0): Button(
                self,  # type: ignore
                button1_rect,
                hardware.loader.font.render(f"Keep '{save_name}'"),
                self.keep,
            ),
            (0, 1): Button(
                self,  # type: ignore
                button2_rect,
                hardware.loader.font.render(f"Delete '{save_name}'"),
                self.delete,
            ),
        }
        self.gui: list[interfaces.GUISprite] = [  # type: ignore
            Image(
                self,  # type: ignore
                pygame.transform.scale(
                    hardware.loader.get_surface("background.png"),
                    util_draw.SCREEN_RECT.size,
                ),
                util_draw.SCREEN_RECT,
            ),
            Background(self, background_rect, -1),  # type: ignore
            *button_dict.values(),
            KnifeIndicator(self, button_dict),  # type: ignore
        ]

    def update(self, dt: float) -> bool:
        self.gui = [sprite for sprite in self.gui if sprite.update(dt)]
        if "quit" in hardware.input_queue.just_pressed:
            self.game.quit()
        return super().update(dt)

    def draw(self) -> None:
        super().draw()
        for sprite in self.gui:
            sprite.draw(self.game.window_surface)

    def keep(self) -> None:
        self.pop()

    def delete(self) -> None:
        hardware.save.delete(self.save_path)
        print(hardware.loader.get_save_names())
        self.get_game().quit()  # runs back into main menu


class SettingsMenu(game_state.GameState):
    def __init__(self, game: interfaces.Game) -> None:
        super().__init__(game, "black")
        background_rect = util_draw.SCREEN_RECT.inflate(-16, -16)
        button_dict: dict[tuple[int | None, int | None], Button] = {}
        self.gui: list[interfaces.GUISprite] = []
        y = 0
        z = 1
        for name, value in hardware.settings.fields():
            rect = pygame.Rect(32, y * 20 + 48, background_rect.width - 32 - 8, 16)
            element = Setting(
                self,  # type: ignore
                rect,
                name,
                value,
                partial(self.game.switch_setting, name),
                z,
            )
            self.gui.append(element)
            button_dict[(0, y)] = element  # type: ignore
            y += 1

        rect = pygame.Rect(32, y * 20 + 48, 128, 16)
        rect.centerx = background_rect.centerx
        back_button: Button = Button(
            self, rect, hardware.loader.font.render("OK"), self.pop, 1  # type: ignore
        )
        button_dict[(0, y)] = back_button

        self.gui.extend(
            [
                Image(
                    self,  # type: ignore
                    pygame.transform.scale(
                        hardware.loader.get_surface("background.png"),
                        util_draw.SCREEN_RECT.size,
                    ),
                    util_draw.SCREEN_RECT,
                ),
                Background(self, background_rect, -1),  # type: ignore
                *button_dict.values(),
                KnifeIndicator(self, button_dict),  # type: ignore
                back_button,
            ]
        )

    def pop(self):
        print("pop!")
        super().pop()

    def on_pop(self) -> None:
        hardware.loader.save_settings(hardware.settings)

    def update(self, dt: float) -> bool:
        self.gui = [sprite for sprite in self.gui if sprite.update(dt)]
        if "quit" in hardware.input_queue.just_pressed:
            self.game.quit()
        return super().update(dt)

    def draw(self) -> None:
        super().draw()
        for sprite in self.gui:
            sprite.draw(self.game.window_surface)


class ItemMenu(game_state.GameState): ...  # TODO
