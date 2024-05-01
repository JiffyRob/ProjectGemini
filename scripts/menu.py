from math import sin

import pygame

from scripts import animation, game_state, loader, sprite


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


class Background(sprite.GUISprite):
    def __init__(self, level, rect, z=0):
        super().__init__(
            level,
            nine_slice(
                [level.loader.get_image("gui.png", f"Border{i}") for i in range(9)],
                rect.size,
            ),
            rect,
            z,
        )


class Button(sprite.GUISprite):
    STATE_NORMAL = 0
    STATE_DISABLED = 1
    STATE_SELECTED = 2

    def __init__(self, level, rect, on_click=lambda: None, z=0):
        self.image_dict = {
            self.STATE_NORMAL: level.loader.get_image("gui.png", "ButtonNormal"),
            self.STATE_SELECTED: level.loader.get_image("gui.png", "ButtonSelected"),
            self.STATE_DISABLED: level.loader.get_image("gui.png", "ButtonDisabled"),
        }
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


class KnifeIndicator(sprite.GUISprite):
    def __init__(self, level, button_dict, start_pos=(0, 0), z=0):
        button_coords = list(button_dict.keys())
        button_xs = [i[0] for i in button_coords]
        button_ys = [i[1] for i in button_coords]
        self.button_dict = button_dict
        self.button_bounds = pygame.Rect(min(button_xs), min(button_ys), 0, 0)
        self.button_bounds.size = max(button_xs), max(button_ys)
        self.anim = animation.Animation(
            [self.level.game.loader.get_image("gui.png", f"Knife{i}") for i in range(4)]
        )
        self.age = 0
        self.button_coord = start_pos
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
        self.rect.midright = self.button.rect.left
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
        if "enter" in pressed:
            self.button.click()
        self.age += dt

    def draw(self, surface):
        surface.blit(self.anim.image, self.rect.move(sin(self.age * 1.5) * 2, 0))


class Save(sprite.GUISprite): ...  # TODO


class Label(sprite.GUISprite): ...  # TODO


class ToggleSwitch(sprite.GUISprite): ...  # TODO


class Image(sprite.GUISprite): ...  # TODO...?


class MainMenu(game_state.GameState):
    def __init__(self, game):
        super().__init__(game, "black")
        self.gui = [
            # TODO: Add sprites here, to be rendered in order
        ]


class PauseMenu(game_state.GameState): ...  # TODO: Save & Quit, Quit, Save


class ItemMenu(game_state.GameState): ...  # TODO
