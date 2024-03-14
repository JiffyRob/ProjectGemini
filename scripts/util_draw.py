import functools

import pygame
import pygame._sdl2 as sdl2
import pygame._sdl2.video as sdl2  # needed for WASM compat

RESOLUTION = (256, 224)
ASPECT_RATIO = RESOLUTION[0] / RESOLUTION[1]
