class Animation:
    def __init__(self, frames, speed=.2, flip_x=False, flip_y=False):
        self.frames = list(frames)
        self.time = 0
        self.speed = speed
        self.flip_x = flip_x
        self.flip_y = flip_y

    def update(self, dt):
        self.time += dt

    def restart(self):
        self.time = 0

    @property
    def image(self):
        image = self.frames[round(self.time / self.speed) % len(self.frames)]
        image.flip_x = self.flip_x
        image.flip_y = self.flip_y
        return image