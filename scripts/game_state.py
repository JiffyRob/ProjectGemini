import pygame
import pygame._sdl2 as sdl2


class GameState:
    def __init__(self, game, color='gray', vsync=True):
        self.game = game
        self.renderer = sdl2.Renderer(game.window, -1, -1, vsync)
        self.renderer.draw_color = color

    def update(self, dt):
        for event in pygame.event.get():
            match event:
                case pygame.Event(type=pygame.QUIT):
                    self.game.quit()

    def draw(self):
        self.renderer.clear()
        self.renderer.present()
