import functools

import pygame
import pygame._sdl2 as sdl2
import pygame._sdl2.video as sdl2  # needed for WASM compat

RESOLUTION = (256, 224)
ASPECT_RATIO = RESOLUTION[0] / RESOLUTION[1]

COLORKEY = (255, 0, 255)

SCALEMODE_INTEGER = "integer"
SCALEMODE_STRETCH = "stretch"
SCALEMODE_ASPECT = "aspect"

SCALEMODES = [SCALEMODE_INTEGER, SCALEMODE_STRETCH, SCALEMODE_ASPECT]

PRESET_LOWEST = "budget potato"
PRESET_LOW = "average potato"
PRESET_MEDIUM = "snazzy potato"
PRESET_HIGH = "expensive potato"
PRESET_ULTRA = "ludicrous potato"

QUALITY_PRESETS = [
    PRESET_LOWEST,
    PRESET_LOW,
    PRESET_MEDIUM,
    PRESET_HIGH,
    PRESET_ULTRA,
]

FRAMECAP_LOW = 15
FRAMECAP_MED = 30
FRAMECAP_HIGH = 60
FRAMECAP_NONE = None

# physics are not deterministic enough for high FPS gaming RN
FRAMECAPS = [
    FRAMECAP_LOW,
    FRAMECAP_MED,
    FRAMECAP_HIGH,
    # FRAMECAP_NONE,
]


def debug_show(surface):
    window = sdl2.Window("debug", pygame.Vector2(surface.get_size()) * 4)
    window.get_surface().fill("black")
    window.get_surface().blit(pygame.transform.scale_by(surface, (4, 4)), (0, 0))
    window.flip()
    pygame.time.delay(1000)
    window.hide()


def surface_with_same_transparency_format(surface, size):
    new_surface = pygame.Surface(size, pygame.SRCALPHA).convert(surface)
    if colorkey := surface.get_colorkey():
        new_surface.set_colorkey(colorkey)
        new_surface.fill(colorkey)
    new_surface.set_alpha(surface.get_alpha())
    return new_surface


def repeat_surface(surface, size, offset=(0, 0)):
    @functools.cache
    def cached_repeat(surface, size, offset):
        size = round(size[0]), round(size[1])
        new_surface = surface_with_same_transparency_format(surface, size)
        surface_size = surface.get_size()
        offset = (offset[0] % surface_size[0], offset[1] % surface_size[1])
        new_surface.fblits(
            [
                (surface, (x, y))
                for x in range(
                    round(offset[0] - surface_size[0]),
                    size[0] + surface_size[0],
                    surface_size[0],
                )
                for y in range(
                    round(offset[1] - surface_size[1]),
                    size[1] + surface_size[1],
                    surface_size[1],
                )
            ]
        )
        return new_surface

    return cached_repeat(surface, tuple(size), tuple(offset))
