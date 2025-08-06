from functools import cache
from typing import Sequence, Iterator
from pygame.typing import RectLike
import pygame
from dataclasses import dataclass
from enum import Enum


class ChunkType(Enum):
    WORD = 0
    SPACE = 1
    NEWLINE = 2

@dataclass(frozen=True)
class Chunk:
    type: ChunkType
    data: str
    size: tuple[int, int]


class PixelFont:
    def __init__(self, char_surfs: Sequence[pygame.Surface], encoding: str = "ascii"):
        self.chars = list(char_surfs)
        self.encoding = encoding

    @cache
    def get_word_size(self, word: str) -> tuple[int, int]:
        width = 0
        height = 0
        for char in word.encode(self.encoding):
            width += self.chars[char].get_width()
            height = max(height, self.chars[char].get_height())
        return width, height

    @cache
    def get_surface(self, char: str) -> pygame.Surface:
        return self.chars[char.encode(self.encoding)[0]]

    def chunkify(self, text: str) -> Iterator[Chunk]:
        current = ""
        for char in text:
            whitespace_type = {" ": ChunkType.SPACE, "\n": ChunkType.NEWLINE, "\r": ChunkType.NEWLINE}.get(char)
            if whitespace_type is None:
                current += char
            else:
                if current:
                    yield Chunk(ChunkType.WORD, current, self.get_word_size(current))
                    current = ""
                yield Chunk(whitespace_type, "", self.get_surface(" ").get_size())
        if current:
            yield Chunk(ChunkType.WORD, current, self.get_word_size(current))

    @cache
    def positions(
        self, chunks: tuple[Chunk], width: int = 0
    ) -> Iterator[tuple[tuple[int, int], Chunk]]:
        row_width = 0
        row_height = 0
        height = 0
        for chunk in chunks:
            row_height = max(row_height, chunk.size[1])
            row_width += chunk.size[0]
            if (width and (row_width > width)) or chunk.type == ChunkType.NEWLINE:
                row_width = chunk.size[0]
                height += row_height + 1
            yield (max(row_width - chunk.size[0], 0), height), chunk

    @cache
    def size(self, text: str, width: int = 0) -> tuple[int, int]:
        (last_x, last_y), last_chunk = tuple(
            self.positions(tuple(self.chunkify(text)), width)
        )[-1]
        width = width or (last_x + last_chunk.size[0])
        height = last_y + last_chunk.size[1]
        return width, height

    def render_to(self, surface: pygame.Surface, rect: RectLike, text: str) -> None:
        position = pygame.Vector2(pygame.Rect(rect)[:2])
        rect = pygame.Rect(rect)
        for offset, chunk in self.positions(tuple(self.chunkify(text)), rect.width):
            if chunk.type == ChunkType.WORD:
                letter_position = position + offset
                for char in chunk.data:
                    char_surface = self.get_surface(char)
                    surface.blit(char_surface, letter_position)
                    letter_position.x += char_surface.get_width()

    @cache
    def render(self, text: str, width: int = 0) -> pygame.Surface:
        # TODO: Optimize?
        surface = pygame.Surface(self.size(text, width)).convert_alpha()
        surface.fill((0, 0, 0, 0))
        self.render_to(surface, surface.get_rect(), text)
        return surface
