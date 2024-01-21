import pygame
import pygame._sdl2 as sdl2
import functools

RESOLUTION = (320, 240)


@functools.cache
def square_image(renderer, color="red"):
    surface = pygame.Surface((1, 1))
    surface.set_at((0, 0), color)
    return sdl2.Image(sdl2.Texture.from_surface(renderer, surface))