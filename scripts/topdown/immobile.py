import pygame

from scripts import snekgemini, sprite


class Interactable(sprite.Sprite):
    groups = {"interactable"}

    def __init__(self, level, image=None, rect=(0, 0, 16, 16), z=0, script="oops", **custom_fields):
        super().__init__(level, image, rect, z)
        self.script = script
        self.running_script = False
        self.interpreter = None

    def interact(self):
        if not self.running_script:
            self.running_script = True
            self.interpreter = snekgemini.cutscene(self.script, self)

    def update(self, dt):
        if self.running_script:
            self.interpreter.cycle()
            if self.interpreter.done():
                self.running_script = False
                self.interpreter = None
        super().update(dt)
        return True


class Ship(Interactable):
    groups = {"interactable", "static-collision"}

    def __init__(self, level, rect=(0, 0, 48, 24), z=0, **custom_fields):
        rect = (rect[0], rect[1], 48, 32)  # ldtk always has single tile rects :/
        self.collision_rect = pygame.FRect(rect[0] + 10, rect[1] + 10, 32, 12)
        super().__init__(
            level,
            level.game.loader.get_surface("tileset.png", rect=(208, 0, 48, 32)),
            rect=rect,
            z=z,
            script="ship",
        )


class BrokenShip(Interactable):
    groups = {"interactable", "static-collision"}

    def __init__(self, level, rect=(0, 0, 48, 24), z=0, **custom_fields):
        rect = (rect[0], rect[1], 48, 32)
        self.collision_rect = pygame.FRect(rect[0] + 10, rect[1] + 10, 32, 12)
        super().__init__(
            level,
            level.game.loader.get_surface("tileset.png", rect=(160, 0, 48, 32)),
            rect=rect,
            z=z,
            script="broken_ship",
        )


class House(sprite.Sprite):
    groups = {"static-collision"}
    def __init__(self, level, rect=(0, 0, 64, 48), z=0, **custom_fields):
        # three rects to represent the house without the doorway
        self.collision_rect = pygame.FRect(rect[0], rect[1] + 10, 64, 22)
        self.extra_collision_rects = (
            pygame.FRect(self.collision_rect.left, self.collision_rect.bottom, 32, 16),
            pygame.FRect(
                self.collision_rect.left + 48,
                self.collision_rect.bottom,
                16,
                16,
            ),
        )
        # the doorway
        self.teleport_rect = pygame.FRect(
            self.collision_rect.left + 32,
            self.collision_rect.bottom,
            16,
            16,
        )
        print(custom_fields)
        self.dest_map = custom_fields["map"]
        super().__init__(
            level,
            image=level.game.loader.get_surface("tileset.png", rect=(0, 208, 64, 48)),
            rect=rect,
            z=z,
        )

    def update(self, dt):
        super().update(dt)
        if self.level.player.collision_rect.colliderect(self.teleport_rect):
            self.level.player.rect.top += self.teleport_rect.bottom - self.level.player.collision_rect.top
            self.level.switch_level(self.dest_map)
        return True
