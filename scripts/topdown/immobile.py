import pygame
from scripts import sprite, snekgemini


class Interactable(sprite.Sprite):
    groups = {"interactable"}

    def __init__(self, level, image=None, rect=(0, 0, 16, 16), z=0, script="oops"):
        super().__init__(level, image, rect, z)
        self.script = self.level.game.loader.get_text(f"scripts/{script}.snek")
        self.running_script = False
        self.interpreter = None

    def interact(self):
        if not self.running_script:
            self.running_script = True
            self.interpreter = snekgemini.interaction(self.script, self)

    def update(self, dt):
        if self.running_script:
            self.interpreter.cycle()
            print("script cycle")
            if self.interpreter.done():
                self.running_script = False
                self.interpreter = None
        super().update(dt)
        return True


class Ship(sprite.Sprite):
    groups = {"interactable", "static-collision"}

    def __init__(self, level, rect=(0, 0, 48, 24), z=0):
        super().__init__(
            level,
            level.game.loader.get_surface("tileset.png", rect=(208, 0, 48, 32)),
            rect=rect,
            z=z
        )


class BrokenShip(Interactable):
    groups = {"interactable", "static-collision"}

    def __init__(self, level, rect=(0, 0, 48, 24), z=0):
        rect = (rect[0], rect[1], 48, 32)
        self.collision_rect = pygame.FRect(rect[0] + 10, rect[1] + 10, 32, 12)
        super().__init__(
            level,
            level.game.loader.get_surface("tileset.png", rect=(160, 0, 48, 32)),
            rect=rect,
            z=z
        )

