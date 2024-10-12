from scripts import sprite
from scripts.animation import Animation


class Player(sprite.Sprite):
    BANK_SPEED = 32
    MIN_Y = 32
    MAX_Y = 32

    def __init__(self, level, rect=(0, 0, 32, 32), z=0):
        frames = level.game.loader.load_spritesheet("hoverboard.png", (32, 32))
        self.anim_dict = {
            "idle-right": Animation(frames[4:8], 0.1),
            "lookback-right": Animation(frames[8:12], 0.1),
        }
        self.state = "idle"
        self.facing = "right"
        super().__init__(level, self.anim_dict[f"{self.state}-{self.facing}"], rect, z)

    def update(self, dt):
        held_input = self.level.game.input_queue.held
        just_input = self.level.game.input_queue.just_pressed
        if held_input["down"]:
            self.rect.y = min(self.MAX_Y, self.rect.y + self.BANK_SPEED * dt)
        if held_input["up"]:
            self.rect.y = max(self.MIN_Y, self.rect.y + self.BANK_SPEED * dt)
        return super().update(dt)


class Drone(sprite.Sprite):
    def __init__(self, level, rect=(0, 0, 32, 32), z=0):
        pass


class Rock(sprite.Sprite):
    ...


class Stump(sprite.Sprite):
    ...