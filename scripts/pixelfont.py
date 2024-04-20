import pygame


class PixelFont:
    def __init__(self, char_surfs, encoding="ascii"):
        self.chars = char_surfs
        self.encoding = encoding

    def get_word_size(self, word):
        width = 0
        height = 0
        for char in word.encode(self.encoding):
            width += self.chars[char].get_width()
            height = max(height, self.chars[char].get_width())
        return width, height

    def render_to(self, surface, rect, text):
        position = pygame.Vector2(rect.topleft)
        paragraphs = text.split("\n")
        space_surface = self.chars[" ".encode(self.encoding)[0]]
        space_size = space_surface.get_size()
        for paragraph in paragraphs:
            words = paragraph.split(" ")
            line_height = 0
            for word in words:
                word_width, word_height = self.get_word_size(word)
                line_height = max(line_height, word_height)
                if position.x + word_width > rect.right:
                    position.y += line_height
                    position.x = 0
                for ind in word.encode(self.encoding):
                    char = self.chars[ind]
                    surface.blit(char, position)
                    position.x += char.get_width()
                if position.x + space_size[0] <= rect.right:
                    surface.blit(space_surface, position)
                    position.x += space_size[0]
                    line_height = max(line_height, space_size[1])
            position.y += line_height
            position.x = 0
