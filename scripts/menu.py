from math import sin

import pygame

from scripts import animation, game_state, loader, sprite, util_draw


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
        surface.blit(self.top_image, self.top_image_rect)


class KnifeIndicator(sprite.GUISprite):
    def __init__(self, level, button_dict, start_pos=(0, 0), z=0):
        button_coords = list(button_dict.keys())
        button_xs = [i[0] for i in button_coords]
        button_ys = [i[1] for i in button_coords]
        self.button_dict = button_dict
        self.button_bounds = pygame.Rect(
            min(button_xs), min(button_ys), max(button_xs) + 1, max(button_ys) + 1
        )
        self.anim = animation.Animation(
            [level.game.loader.get_image("gui.png", f"Knife{i}") for i in range(4)]
        )
        self.age = 0
        self.button_coord = start_pos
        self.button.select()
        super().__init__(
            level,
            None,
            z=z,
        )

    @property
    def button(self):
        return self.button_dict[self.button_coord]

    def search(self, direction):
        delta_x, delta_y = direction
        current_x, current_y = self.button_coord
        while self.button_bounds.collidepoint(current_x, current_y):
            current_x += delta_x
            current_y += delta_y
            current_coord = (current_x, current_y)
            if (
                current_coord in self.button_dict
                and self.button_dict[current_coord].state == Button.STATE_NORMAL
            ):
                return current_coord
        return None

    def move(self, direction):
        new_coord = self.search(direction)
        if new_coord is None:
            return None
        old_button = self.button
        self.button_coord = new_coord
        self.rect.midright = self.button.rect.midleft
        old_button.deselect()
        self.button.select()

    def update(self, dt):
        pressed = self.level.game.input_queue.just_pressed
        if "up" in pressed:
            self.move((0, -1))
        if "down" in pressed:
            self.move((0, 1))
        if "left" in pressed:
            self.move((-1, 0))
        if "right" in pressed:
            self.move((1, 0))
        if "interact" in pressed:
            self.button.click()
        self.age += dt
        self.rect.midright = self.button.rect.midleft
        self.anim.update(dt)
        return True

    def draw(self, surface):
        surface.blit(self.anim.image, self.rect.move(sin(self.age * 5) * 2, 0))


class TextButton(Button):
    def __init__(self, level, rect, text, on_click=lambda: None):
        super().__init__(
            level,
            rect,
            level.game.loader.font.render(text),
            on_click=on_click,
        )

    def draw(self, surface):
        surface.blit(self.top_image, self.rect)


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
        self.level.game.load_save(self.name)


class Label(sprite.GUISprite): ...  # TODO


class ToggleSwitch(sprite.GUISprite): ...  # TODO


class Image(sprite.GUISprite):
    pass


class MainMenu(game_state.GameState):
    def __init__(self, game):
        super().__init__(game, "black")
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
        for i, save_name in enumerate(save_names):
            button = Save(self, button_rect, i + 1, save_name)
            self.gui.append(button)
            button_dict[(0, i)] = button
            button_rect.top = button_rect.bottom + 3

        self.gui.append(KnifeIndicator(self, button_dict=button_dict))

    def update(self, dt):
        self.gui = [sprite for sprite in self.gui if sprite.update(dt)]
        if "quit" in self.game.input_queue.just_pressed:
            self.game.quit()
        return super().update(dt)

    def draw(self):
        super().draw()
        for sprite in self.gui:
            sprite.draw(self.game.window_surface)

    def start(self):
        self.pop()

    def quit(self):
        self.game.quit()


class PauseMenu(game_state.GameState): ...  # TODO: Save & Quit, Quit, Save


class ItemMenu(game_state.GameState): ...  # TODO
