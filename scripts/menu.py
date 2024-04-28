import pygame

from scripts import game_state, loader, sprite


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
    ...  # TODO


class Button(sprite.GUISprite):
    ...  # TODO


class Save(sprite.GUISprite):
    ...  # TODO


class Label(sprite.GUISprite):
    ...  # TODO


class ToggleSwitch(sprite.GUISprite):
    ...  # TODO


class Image(sprite.GUISprite):
    ...  # TODO...?


class KnifeIndicator(sprite.GUISprite):
    ...  # TODO


class MainMenu(game_state.GameState):
    def __init__(self, game):
        super().__init__(game, "black")
        self.gui = [
            # TODO: Add sprites here, to be rendered in order
        ]


class PauseMenu(game_state.GameState):
    ...  # TODO: Save & Quit, Quit, Save


class ItemMenu(game_state.GameState):
    ...  # TODO

