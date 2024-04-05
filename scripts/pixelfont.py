import pygame


class PixelFont:
    def __init__(self, char_surfs, encoding="ascii"):
        self.chars = char_surfs
        self.encoding = encoding

    def render_to(self, surface, rect, text):
        position = pygame.Vector2(rect.topleft)
        for ind in text.encode(self.encoding):
            char = self.chars[ind]
            char_width = char.get_width()
            if char_width + position.x > rect.right or ind in "\n\r".encode(
                self.encoding
            ):
                position.y += char.get_height()
                position.x = rect.left
            surface.blit(char, position)
            position.x += char.get_width()
