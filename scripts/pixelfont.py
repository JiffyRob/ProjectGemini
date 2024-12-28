from collections import namedtuple
from functools import cache

import pygame

WORD = 0
SPACE = 1
NEWLINE = 2

Chunk = namedtuple("Chunk", ("type", "data", "size"))


class PixelFont:
    def __init__(self, char_surfs, encoding="ascii"):
        self.chars = char_surfs
        self.encoding = encoding

    @cache
    def get_word_size(self, word):
        width = 0
        height = 0
        for char in word.encode(self.encoding):
            width += self.chars[char].get_width()
            height = max(height, self.chars[char].get_height())
        return width, height

    @cache
    def get_surface(self, char):
        return self.chars[char.encode(self.encoding)[0]]

    def chunkify(self, text):
        current = ""
        for char in text:
            whitespace_type = {" ": SPACE, "\n": NEWLINE, "\r": NEWLINE}.get(char)
            if char not in {" ", "\n", "\r"}:
                current += char
            else:
                if current:
                    yield Chunk(WORD, current, self.get_word_size(current))
                    current = ""
                yield Chunk(whitespace_type, None, self.get_surface(" ").get_size())
        if current:
            yield Chunk(WORD, current, self.get_word_size(current))

    @cache
    def positions(self, chunks, width=0):
        row_width = 0
        row_height = 0
        height = 0
        for chunk in chunks:
            row_height = max(row_height, chunk.size[1])
            row_width += chunk.size[0]
            if (width and (row_width > width)) or chunk.type == NEWLINE:
                row_width = chunk.size[0]
                height += row_height + 1
            yield (max(row_width - chunk.size[0], 0), height), chunk

    @cache
    def size(self, text, width=0):
        (last_x, last_y), last_chunk = tuple(self.positions(self.chunkify(text), width))[-1]
        width = width or (last_x + last_chunk.size[0])
        height = last_y + last_chunk.size[1]
        return width, height

    def render_to(self, surface, rect, text):
        position = pygame.Vector2(rect.topleft)
        for offset, chunk in self.positions(self.chunkify(text), rect.width):
            if chunk.type == WORD:
                letter_position = position + offset
                for char in chunk.data:
                    char_surface = self.get_surface(char)
                    surface.blit(char_surface, letter_position)
                    letter_position.x += char_surface.get_width()

    @cache
    def render(self, text, width=0):
        # TODO: Optimize?
        surface = pygame.Surface(self.size(text, width)).convert_alpha()
        surface.fill((0, 0, 0, 0))
        self.render_to(surface, surface.get_rect(), text)
        return surface
