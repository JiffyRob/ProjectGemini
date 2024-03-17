import pygame

from scripts import sprite
from scripts.animation import Animation, flip_surface


class GUISprite(sprite.Sprite):
    def draw(self, surface):
        surface.blit(self.image, self.rect)


class Ship(GUISprite):
    UP = 1
    DOWN = 2
    LEFT = 4
    RIGHT = 8
    TWIST = 16
    ROTATYNESS = 45

    def __init__(self, level, rect):
        super().__init__(
            level, None, rect
        )
        frames = self.level.game.loader.get_spritesheet("ship.png", (24, 32))
        self.anim_dict = {
            "normal": Animation(frames[0:3]),
            "turn": Animation(frames[3:6]),
            "up": Animation(frames[6:9]),
            "down": Animation(frames[9:12]),
        }
        self.flipped_anim_dict = {}
        for key, anim in self.anim_dict.items():
            self.flipped_anim_dict[key] = Animation(anim.frames, anim.speed, True)
        self.surface = pygame.Surface((48, 32), pygame.SRCALPHA).convert_alpha()
        self.direction = 0
        self.anim_left = self.anim_dict["normal"]
        self.anim_right = self.flipped_anim_dict["normal"]

    def up(self):
        self.direction |= self.UP

    def down(self):
        self.direction |= self.DOWN

    def left(self):
        self.direction |= self.LEFT

    def right(self):
        self.direction |= self.RIGHT

    def twist(self):
        self.direction |= self.TWIST

    def update(self, dt):
        for anim in self.anim_dict.values():
            anim.update(dt)
        for anim in self.flipped_anim_dict.values():
            anim.update(dt)

    def draw(self, surface):
        # figure out which animation to use on each side based on direction of travel
        # lots of ifs, it's a right pain
        left_upness = 0
        right_upness = 0
        turn_left = False
        turn_right = False
        rotation = 0
        if self.direction & self.UP and not self.direction & self.DOWN:
            left_upness += 1
            right_upness += 1
        if self.direction & self.DOWN and not self.direction & self.UP:
            left_upness -= 1
            right_upness -= 1
        if self.direction & self.TWIST:
            left_upness += 1
            right_upness -= 1
        if self.direction & self.LEFT and not self.direction & self.RIGHT:
            turn_left = True
            rotation = self.ROTATYNESS
            right_upness += 1
        if self.direction & self.RIGHT and not self.direction & self.LEFT:
            turn_right = True
            rotation = -self.ROTATYNESS
            left_upness += 1
        if left_upness > 0:
            self.anim_left = self.anim_dict["up"]
        if left_upness == 0:
            self.anim_left = self.anim_dict["normal"]
        if left_upness < 0:
            self.anim_left = self.anim_dict["down"]
        if right_upness > 0:
            self.anim_right = self.flipped_anim_dict["up"]
        if right_upness == 0:
            self.anim_right = self.flipped_anim_dict["normal"]
        if right_upness < 0:
            self.anim_right = self.flipped_anim_dict["down"]
        if turn_left:
            self.anim_left = self.anim_dict["turn"]
        if turn_right:
            self.anim_right = self.flipped_anim_dict["turn"]
        self.surface.fill((0, 0, 0, 0))
        self.surface.blit(self.anim_left.image, (0, 0))
        self.surface.blit(self.anim_right.image, (24, 0))
        blit_surface = pygame.transform.rotate(self.surface, rotation)
        surface.blit(blit_surface, blit_surface.get_rect(center=self.rect.center))
        self.direction = 0