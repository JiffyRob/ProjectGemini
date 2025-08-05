from functools import partial
from math import ceil, sin

import pygame

from gamelibs import animation, game_state, loader, sprite, timer, env, util_draw


def nine_slice(images, size):
    image = loader.Loader.create_surface(size)
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


def three_slice(images, width):
    if width < images[0].get_width() + images[2].get_width():
        return images[1]
    image = loader.Loader.create_surface((width, images[0].get_height()))
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
    def __init__(self, level, rect, z=0):
        super().__init__(
            level,
            nine_slice(
                [
                    level.game.loader.get_image("gui.png", f"Border{i}")
                    for i in range(9)
                ],
                rect.size,
            ),
            rect,
            z,
        )


class Button(sprite.GUISprite):
    STATE_NORMAL = 0
    STATE_DISABLED = 1
    STATE_SELECTED = 2

    def __init__(self, level, rect, top_image, on_click=lambda: None, z=0):
        self.image_dict = {
            self.STATE_NORMAL: three_slice(
                [
                    level.game.loader.get_image("gui.png", f"ButtonNormal{i}")
                    for i in range(3)
                ],
                rect.width,
            ),
            self.STATE_SELECTED: three_slice(
                [
                    level.game.loader.get_image("gui.png", f"ButtonSelected{i}")
                    for i in range(3)
                ],
                rect.width,
            ),
            self.STATE_DISABLED: three_slice(
                [
                    level.game.loader.get_image("gui.png", f"ButtonDisabled{i}")
                    for i in range(3)
                ],
                rect.width,
            ),
        }
        self.top_image = top_image
        self.top_image_rect = self.top_image.get_rect(center=rect.center)
        self.state = self.STATE_NORMAL
        self.click = on_click
        super().__init__(level, None, rect, z)

    def select(self):
        self.state = self.STATE_SELECTED

    def deselect(self):
        self.state = self.STATE_NORMAL

    def disable(self):
        self.state = self.STATE_DISABLED

    def enable(self):
        self.state = self.STATE_NORMAL

    def draw(self, surface):
        surface.blit(self.image_dict[self.state], self.rect)
        surface.blit(self.top_image, self.top_image.get_rect(center=self.rect.center))


class ToggleSwitch(sprite.GUISprite):
    STATE_DISABLED = 0
    STATE_NORMAL = 1
    STATE_SELECTED = 2

    FRAME_DELAY = 0.06

    def __init__(self, level, rect, z=0, on_toggle=lambda value: None, start_on=False):
        frames = level.game.loader.get_spritesheet("switch", (16, 8))
        length = 10
        self.anim_dict = {
            self.STATE_DISABLED: frames[:length],
            self.STATE_NORMAL: frames[length : length * 2],
            self.STATE_SELECTED: frames[length * 2 : length * 3],
        }
        self.age = 0
        self.state = self.STATE_NORMAL
        if start_on:
            self.on = True
            self.frame = length - 1
        else:
            self.on = False
            self.frame = 0
        self.on_toggle = on_toggle
        super().__init__(level, None, rect, z)

    def click(self):
        self.on_toggle(self.on)
        self.on = not self.on

    def update(self, dt):
        self.age += dt
        if self.age > self.FRAME_DELAY:
            if self.on:
                self.frame += 1
            else:
                self.frame -= 1
            self.age = 0
        frames = self.anim_dict[self.state]
        self.frame = pygame.math.clamp(self.frame, 0, len(frames) - 1)
        return super().update(dt)

    def select(self):
        self.state = self.STATE_SELECTED

    def deselect(self):
        self.state = self.STATE_NORMAL

    def disable(self):
        self.state = self.STATE_DISABLED

    def enable(self):
        self.state = self.STATE_NORMAL

    def draw(self, surface):
        surface.blit(self.anim_dict[self.state][self.frame], self.rect)


class Selector(sprite.GUISprite):
    STATE_DISABLED = 0
    STATE_NORMAL = 1
    STATE_SELECTED = 2

    COLORS = {
        STATE_DISABLED: "#4c505b",
        STATE_NORMAL: "#777e86",
        STATE_SELECTED: "#cbcbcb",
    }

    def __init__(
        self, level, rect, values, z=0, on_toggle=lambda value: None, initial_value=None
    ):
        super().__init__(level, None, rect, z)
        self.values = values
        if initial_value is None:
            self.index = 0
        else:
            self.index = values.index(initial_value)
        self.state = self.STATE_NORMAL
        self.on_toggle = on_toggle

    def click(self):
        self.index += 1
        self.index %= len(self.values)
        self.on_toggle(self.values[self.index])

    def select(self):
        self.state = self.STATE_SELECTED

    def deselect(self):
        self.state = self.STATE_NORMAL

    def disable(self):
        self.state = self.STATE_DISABLED

    def enable(self):
        self.state = self.STATE_NORMAL

    def draw(self, surface):
        pygame.draw.rect(surface, self.COLORS[self.state], self.rect)
        text = self.level.game.loader.font.render(
            str(self.values[self.index]), self.rect.width - 4
        )
        text_rect = text.get_rect()
        text_rect.center = self.rect.center
        surface.blit(text, text_rect)


class Label(sprite.GUISprite):
    def __init__(self, level, rect, text, z=0):
        surface = level.game.loader.create_surface(rect.size)
        text = level.game.loader.font.render(text, rect.width)
        text_rect = text.get_rect()
        text_rect.midleft = pygame.Rect((0, 0), rect.size).midleft
        surface.blit(text, text_rect)
        super().__init__(level, surface, rect, z)


class Setting(sprite.GUISprite):
    TYPE_BOOL = 1
    TYPE_SCALEMODE = 2
    TYPE_GRAPHICS_PRESET = 3
    TYPE_FRAMECAP = 4

    STATE_DISABLED = 0
    STATE_NORMAL = 1
    STATE_SELECTED = 2

    def __init__(
        self,
        level,
        rect,
        name,
        setting_type,
        start_value,
        on_switch=lambda value: print(value),
        z=0,
    ):
        super().__init__(level, None, rect, z)
        label_rect = rect.copy()
        label_rect.width //= 2
        self.label = Label(level, label_rect, name)
        self.type = setting_type
        if self.type == self.TYPE_BOOL:
            switch_rect = rect.copy()
            switch_rect.size = (16, 8)
            switch_rect.right = rect.right
            switch_rect.centery = rect.centery
            self.toggler = ToggleSwitch(
                level, switch_rect, z, on_switch, not start_value
            )
        if self.type == self.TYPE_SCALEMODE:
            switch_rect = rect.copy()
            switch_rect.size = (128, self.rect.height)
            switch_rect.right = rect.right
            self.toggler = Selector(
                level, switch_rect, util_draw.SCALEMODES, z, on_switch, start_value
            )
        if self.type == self.TYPE_GRAPHICS_PRESET:
            switch_rect = rect.copy()
            switch_rect.size = (128, self.rect.height)
            switch_rect.right = rect.right
            self.toggler = Selector(
                level, switch_rect, util_draw.QUALITY_PRESETS, z, on_switch, start_value
            )
        if self.type == self.TYPE_FRAMECAP:
            switch_rect = rect.copy()
            switch_rect.size = (128, self.rect.height)
            switch_rect.right = rect.right
            self.toggler = Selector(
                level, switch_rect, util_draw.FRAMECAPS, z, on_switch, start_value
            )

        self.state = self.STATE_NORMAL

    def update(self, dt):
        self.label.update(dt)
        self.toggler.update(dt)
        return super().update(dt)

    def click(self):
        self.toggler.click()

    def select(self):
        self.toggler.select()
        self.state = self.STATE_SELECTED

    def deselect(self):
        self.toggler.deselect()
        self.state = self.STATE_NORMAL

    def disable(self):
        self.toggler.disable()
        self.state = self.STATE_DISABLED

    def enable(self):
        self.toggler.enable()
        self.state = self.STATE_NORMAL

    def draw(self, surface):
        self.label.draw(surface)
        self.toggler.draw(surface)


class KnifeIndicator(sprite.GUISprite):
    STATE_GREEN = 0
    STATE_RED = 1

    def __init__(self, level, button_dict, start_pos=(0, 0), z=0):
        button_coords = list(button_dict.keys())
        button_xs = [i[0] for i in button_coords if i[0] is not None]
        button_ys = [i[1] for i in button_coords if i[1] is not None]
        self.button_dict = button_dict
        self.button_bounds = pygame.Rect(
            min(button_xs), min(button_ys), max(button_xs), max(button_ys)
        ).inflate(5, 5)
        self.anim = animation.Animation(
            [level.game.loader.get_image("gui.png", f"Knife{i}") for i in range(4)]
        )
        self.red_anim = animation.Animation(
            [level.game.loader.get_image("gui.png", f"RedKnife{i}") for i in range(4)]
        )
        self.state = self.STATE_GREEN
        self.age = 0
        self.button_coord = start_pos
        self.last_coord = start_pos
        self.last_x = start_pos[0]
        self.last_y = start_pos[1]
        self.button.select()
        self.motion_cooldown = timer.Timer(150)
        super().__init__(
            level,
            None,
            z=z,
        )

    @property
    def button(self):
        return self.button_dict[self.button_coord]

    def search(self, direction):
        current_x = self.last_x
        current_y = self.last_y
        delta_x, delta_y = direction
        while self.button_bounds.collidepoint(current_x, current_y):
            current_x += delta_x
            current_y += delta_y
            current_coord = (current_x, current_y)
            if (
                current_coord in self.button_dict
                and self.button_dict[current_coord].state
                == self.button_dict[current_coord].STATE_NORMAL
            ):
                return current_coord
            x_only_coord = (current_coord[0], None)
            y_only_coord = (None, current_coord[1])
            if (
                x_only_coord in self.button_dict
                and self.button_dict[x_only_coord].state
                == self.button_dict[x_only_coord].STATE_NORMAL
            ):
                return x_only_coord
            if (
                y_only_coord in self.button_dict
                and self.button_dict[y_only_coord].state
                == self.button_dict[y_only_coord].STATE_NORMAL
            ):
                return y_only_coord
        return None

    def move(self, direction):
        if not self.motion_cooldown.done():
            return
        new_coord = self.search(direction)
        if new_coord is None:
            return None
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

    def update(self, dt):
        pressed = self.level.game.input_queue.held
        if pressed["up"]:
            self.move((0, -1))
        if pressed["down"]:
            self.move((0, 1))
        if pressed["left"]:
            self.move((-1, 0))
        if pressed["right"]:
            self.move((1, 0))

        if "interact" in self.level.game.input_queue.just_pressed:
            self.button.click()
        self.age += dt
        self.rect.midright = self.button.rect.midleft
        self.anim.update(dt)
        self.red_anim.update(dt)
        self.motion_cooldown.update()
        return True

    def draw(self, surface):
        anim = self.anim
        if self.state == self.STATE_RED:
            anim = self.red_anim
        surface.blit(anim.image, self.rect.move(sin(self.age * 5) * 2, 0))

    def make_red(self):
        self.state = self.STATE_RED

    def make_green(self):
        self.state = self.STATE_GREEN


class TextButton(Button):
    def __init__(self, level, rect, text, on_click=lambda: None):
        super().__init__(
            level,
            rect,
            level.game.loader.font.render(text),
            on_click=on_click,
        )
        self.text = text

    def draw(self, surface):
        surface.blit(self.top_image, self.top_image.get_rect(midleft=self.rect.midleft))


class TextInput(sprite.GUISprite):
    def __init__(self, level, rect, z=0, max_chars=16):
        super().__init__(level, None, rect, z)
        self.text = ["_"] * max_chars
        self.cursor_position = 0
        self.age = 0

    def update(self, dt):
        self.age += dt
        return super().update(dt)

    def draw(self, surface):
        text_copy = self.text.copy()
        if self.age % 1 < 0.5:
            text_copy[self.cursor_position] = "|"
        text = self.level.game.loader.font.render("".join(text_copy))
        surface.blit(text, text.get_rect(center=self.rect.center))

    def input_character(self, char):
        if char == "\b":
            self.cursor_position -= 1
            self.text[self.cursor_position] = "_"
        else:
            if char == "_":
                char = " "
            self.text[self.cursor_position] = char
            self.cursor_position += 1
        self.cursor_position = pygame.math.clamp(
            self.cursor_position, 0, len(self.text) - 1
        )


class Save(TextButton):
    def __init__(self, level, rect, index, name):
        self.name = name
        super().__init__(
            level,
            rect,
            f"{index}. {name}",
            self.load,
        )

    def load(self):
        if self.level.delete_mode:
            if self.name:
                self.level.game.stack.appendleft(
                    DeleteConfirmationMenu(self.level.game, self.name)
                )
            self.level.delete_mode_toggle()
            return
        if self.name:
            self.level.game.load_save(self.name)
        else:
            self.level.game.stack.appendleft(NameInputMenu(self.level.game))


class Image(sprite.GUISprite):
    pass


class MainMenu(game_state.GameState):
    def __init__(self, game):
        super().__init__(game, "black")
        self.delete_mode = False

        backdrop = pygame.transform.scale(
            game.loader.get_surface("background.png"), game.screen_rect.size
        )

        background_rect = game.screen_rect.inflate(-16, -16)
        title1 = game.loader.get_image("gui.png", "PROJECT")
        title1_rect = pygame.Rect(20, background_rect.top + 10, *title1.get_size())

        title2 = game.loader.get_image("gui.png", "GEMINI")
        title2_rect = pygame.Rect(0, title1_rect.bottom, *title2.get_size())
        title2_rect.centerx = background_rect.centerx

        button_rect = pygame.Rect(0, 0, 150, 8)
        button_rect.top = title2_rect.bottom + 3
        button_rect.centerx = background_rect.centerx
        button_dict = {}

        save_names = self.game.loader.get_save_names(5)

        self.gui = [
            Image(self, backdrop, game.screen_rect),
            Background(self, background_rect, -1),
            Image(
                self,
                title1,
                title1_rect,
            ),
            Image(
                self,
                title2,
                title2_rect,
            ),
        ]
        i = 0
        for i, save_name in enumerate(save_names):
            button = Save(self, button_rect, i + 1, save_name)
            self.gui.append(button)
            button_dict[(0, i)] = button
            button_rect.top = button_rect.bottom + 3

        button_rect.height = 16
        button_rect.width -= 25
        button_rect.x += 25
        delete_button = Button(
            self,
            button_rect,
            self.game.loader.font.render("Delete Data"),
            self.delete_mode_toggle,
        )
        i += 1
        button_dict[(0, i)] = delete_button
        self.gui.append(delete_button)

        button_rect.top = button_rect.bottom + 3

        settings_button = Button(
            self,
            button_rect,
            self.game.loader.font.render("Settings"),
            self.open_settings,
        )
        i += 1
        button_dict[(0, i)] = settings_button
        self.gui.append(settings_button)

        button_rect.top = button_rect.bottom + 3

        if not env.PYGBAG:
            exit_button = Button(
                self,
                button_rect,
                self.game.loader.font.render("Exit Game"),
                self.game.exit,
            )
            self.gui.append(exit_button)
            button_dict[(0, i + 2)] = exit_button

        self.knife = KnifeIndicator(self, button_dict=button_dict)
        self.gui.append(self.knife)

        # TODO: better place for this...?
        self.game.play_soundtrack("CelestialHymn")

    def delete_mode_toggle(self):
        self.delete_mode = not self.delete_mode
        if self.delete_mode:
            self.knife.make_red()
        else:
            self.knife.make_green()

    def update(self, dt):
        self.gui = [sprite for sprite in self.gui if sprite.update(dt)]
        if "quit" in self.game.input_queue.just_pressed:
            self.game.exit()
        return super().update(dt)

    def draw(self):
        super().draw()
        for sprite in self.gui:
            sprite.draw(self.game.window_surface)

    def start(self):
        self.pop()

    def quit(self):
        self.game.quit()

    def open_settings(self):
        self.game.stack.appendleft(SettingsMenu(self.game))


class NameInputMenu(game_state.GameState):
    MAX_CHARS = 16

    def __init__(self, game):
        super().__init__(game, "black")
        background_rect = game.screen_rect.inflate(-16, -16)
        self.gui = [
            Image(
                self,
                pygame.transform.scale(
                    game.loader.get_surface("background.png"), game.screen_rect.size
                ),
                game.screen_rect,
            ),
            Background(self, background_rect, -1),
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
        button_dict = {}

        for i, letter in enumerate(letters):
            button = TextButton(
                self, letter_rect, letter, partial(self.click_letter, letter)
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
            (0, keyboard_rect.bottom), self.game.loader.font.size("ABCD")
        )
        button_rect.centerx = keyboard_rect.centerx
        cancel_button = TextButton(self, button_rect, "Back", self.cancel)
        self.gui.append(cancel_button)
        button_dict[(None, button_y + 1)] = cancel_button

        button_rect.bottom = keyboard_rect.top
        confirm_button = TextButton(self, button_rect, "Done", self.confirm_name)
        self.gui.append(confirm_button)
        button_dict[(None, -1)] = confirm_button

        self.gui.append(KnifeIndicator(self, button_dict, (0, 0), 1))

        start_text = "_" * self.MAX_CHARS
        name_rect = pygame.Rect((0, 0), self.game.loader.font.size(start_text))
        name_rect.bottom = button_rect.top - 10
        name_rect.centerx = background_rect.centerx
        self.input = TextInput(self, name_rect)
        self.gui.append(self.input)

    def update(self, dt):
        self.gui = [sprite for sprite in self.gui if sprite.update(dt)]
        if "quit" in self.game.input_queue.just_pressed:
            self.game.quit()
        return super().update(dt)

    def draw(self):
        super().draw()
        for sprite in self.gui:
            sprite.draw(self.game.window_surface)

    def click_letter(self, letter):
        self.input.input_character(letter)

    def confirm_name(self):
        self.game.save.load("start1")
        save_name = "".join(self.input.text).replace("_", "")
        if save_name:
            self.game.save.loaded_path = save_name
            self.game.save.save()
            self.game.load_save(save_name)

    def cancel(self):
        self.pop()


class DeleteConfirmationMenu(game_state.GameState):
    def __init__(self, game, save_name):
        self.save_name = save_name
        super().__init__(game, (0, 0, 0, 0))
        background_rect = pygame.Rect(0, 0, 256, 48)
        background_rect.center = self.game.screen_rect.center
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
        button_dict = {
            (0, 0): Button(
                self,
                button1_rect,
                self.game.loader.font.render(f"Keep '{save_name}'"),
                self.keep,
            ),
            (0, 1): Button(
                self,
                button2_rect,
                self.game.loader.font.render(f"Delete '{save_name}'"),
                self.delete,
            ),
        }
        self.gui = [
            Image(
                self,
                pygame.transform.scale(
                    game.loader.get_surface("background.png"), game.screen_rect.size
                ),
                game.screen_rect,
            ),
            Background(self, background_rect, -1),
            *button_dict.values(),
            KnifeIndicator(self, button_dict),
        ]

    def update(self, dt):
        self.gui = [sprite for sprite in self.gui if sprite.update(dt)]
        if "quit" in self.game.input_queue.just_pressed:
            self.game.quit()
        return super().update(dt)

    def draw(self):
        super().draw()
        for sprite in self.gui:
            sprite.draw(self.game.window_surface)

    def keep(self):
        self.pop()

    def delete(self):
        self.game.save.delete(self.save_name)
        print(self.game.loader.get_save_names())
        self.game.stack.clear()
        self.game.stack.appendleft(MainMenu(self.game))


class SettingsMenu(game_state.GameState):
    def __init__(self, game):
        super().__init__(game, "black")
        background_rect = game.screen_rect.inflate(-16, -16)
        button_dict = {}
        self.gui = []
        y = 0
        z = 1
        print(self.game.settings)
        for name, value in self.game.settings.items():
            rect = pygame.Rect(32, y * 20 + 48, background_rect.width - 32 - 8, 16)
            if value in {True, False}:
                setting_type = Setting.TYPE_BOOL
            elif value in util_draw.SCALEMODES:
                setting_type = Setting.TYPE_SCALEMODE
            elif value in util_draw.QUALITY_PRESETS:
                setting_type = Setting.TYPE_GRAPHICS_PRESET
            elif value in util_draw.FRAMECAPS:
                setting_type = Setting.TYPE_FRAMECAP
            else:
                print(name, value)
                raise
            element = Setting(
                self,
                rect,
                name,
                setting_type,
                value,
                partial(self.game.switch_setting, name),
                z,
            )
            self.gui.append(element)
            button_dict[(0, y)] = element
            y += 1

        rect = pygame.Rect(32, y * 20 + 48, 128, 16)
        rect.centerx = background_rect.centerx
        back_button = Button(
            self, rect, self.game.loader.font.render("OK"), self.pop, 1
        )
        button_dict[(0, y)] = back_button

        self.gui.extend(
            [
                Image(
                    self,
                    pygame.transform.scale(
                        game.loader.get_surface("background.png"), game.screen_rect.size
                    ),
                    game.screen_rect,
                ),
                Background(self, background_rect, -1),
                *button_dict.values(),
                KnifeIndicator(self, button_dict),
                back_button,
            ]
        )

    def update(self, dt):
        self.gui = [sprite for sprite in self.gui if sprite.update(dt)]
        if "quit" in self.game.input_queue.just_pressed:
            self.game.quit()
        return super().update(dt)

    def draw(self):
        super().draw()
        for sprite in self.gui:
            sprite.draw(self.game.window_surface)


class ItemMenu(game_state.GameState): ...  # TODO
