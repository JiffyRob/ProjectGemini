import functools

import pygame
import pygame._sdl2 as sdl2
import pygame._sdl2.video as sdl2  # needed for WASM compat

RESOLUTION = (256, 224)
ASPECT_RATIO = RESOLUTION[0] / RESOLUTION[1]


def debug_show(surface):
    window = sdl2.Window("debug", pygame.Vector2(surface.get_size()) * 4)
    window.get_surface().fill("black")
    window.get_surface().blit(pygame.transform.scale_by(surface, (4, 4)), (0, 0))
    window.flip()
    pygame.time.delay(1000)
    window.hide()