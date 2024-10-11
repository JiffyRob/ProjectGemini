import math

import pygame

from scripts import pixelfont, sprite, timer, util_draw


class HeartMeter(sprite.GUISprite):
    def __init__(self, level, rect=(0, 0, 16, 16)):
        super().__init__(level, None, rect)
        self.heart_frames = self.level.game.loader.get_spritesheet("heart.png", (8, 8))

    def update(self, dt):
        # TODO: Animations and effects?
        pass

    def draw(self, surface):
        heart_count = math.ceil(
            self.level.player.health_capacity / (len(self.heart_frames) - 1)
        )
        columns = self.rect.width // 9
        position = pygame.Vector2()
        health_left = self.level.player.health
        for i in range(heart_count):
            if health_left > len(self.heart_frames) - 1:
                index = len(self.heart_frames) - 1
            else:
                index = health_left
            health_left -= index
            surface.blit(self.heart_frames[index], self.rect.move(position))
            position.x += 9
            if i == columns - 1:
                position.x = 0
                position.y += 9


class EmeraldMeter(sprite.GUISprite):
    X = 10
    EMERALD = 11

    def __init__(self, level, rect=(0, 0, 16, 16)):
        rect = pygame.Rect(rect)
        rect.size = (22, 7)
        super().__init__(level, None, rect)
        self.surface = pygame.Surface(rect.size).convert()
        self.font_frames = self.level.game.loader.get_spritesheet(
            "digifont.png", (3, 5)
        )

    def draw(self, surface):
        numbers = [self.EMERALD, self.X] + [
            int(i) for i in str(self.level.player.emeralds).zfill(3)
        ]
        position = pygame.Vector2(1, 1)
        self.surface.fill("black")
        for i, number in enumerate(numbers):
            self.surface.blit(self.font_frames[number], position + (i * 4, 0))
        surface.blit(self.surface, self.rect)


class Dialog(sprite.GUISprite):
    # pulled and modified from Tred's Adventure (v2)
    STATE_WRITING_PROMPT = 1
    STATE_GETTING_ANSWER = 2
    STATE_COMPLETE = 3

    def __init__(self, level, rect, text, answers, on_kill):
        super().__init__(level, level.game.loader.create_surface(rect.size), rect)
        self.live = True
        self.text = text
        self.displayed_text = ""
        self.answers = answers
        self.answer_index = 0
        self.chosen_index = None
        self.on_kill = on_kill
        self.add_letter_timer = timer.DTimer(20, self.add_text, True)
        self.image.set_colorkey(util_draw.COLORKEY)
        self.state = self.STATE_WRITING_PROMPT
        self.pad = 3
        self.font = pixelfont.PixelFont(
            self.level.game.loader.get_spritesheet("font.png", (7, 8))
        )
        self.motion_cooldown = timer.Timer(100)
        self.rebuild()

    def update_text(self):
        self.rebuild()

    def add_text(self):
        if not self.text:
            self.state = self.STATE_GETTING_ANSWER
            self.update_text()
            if not self.answers:
                self.state = self.STATE_COMPLETE
            self.add_letter_timer = timer.DTimer()
        else:
            self.displayed_text += self.text[0]
            self.text = self.text[1:]
            self.update_text()

    def get_full_text(self):
        # beginning prompt
        text = self.displayed_text
        # add all the choices
        if self.state == self.STATE_GETTING_ANSWER:
            for i, choice in enumerate(self.answers):
                text += "\n"
                if i == self.answer_index:
                    # put a dash before selected answer
                    text += f"-{choice}"
                else:
                    text += f" {choice}"
        return text

    def rebuild(self):
        self.image.fill(util_draw.COLORKEY)
        text = self.get_full_text()
        self.font.render_to(
            self.image,
            self.image.get_rect().inflate(-self.pad * 2, -self.pad * 2),
            text,
        )
        pygame.draw.rect(self.image, "black", ((0, 0), self.rect.size), 1)

    def choose(self):
        self.chosen_index = self.answer_index
        self.state = self.STATE_COMPLETE
        self.on_kill(self.get_answer())
        self.live = False

    def get_answer(self):
        if not self.answers or self.chosen_index is None:
            return None
        return self.answers[self.chosen_index]

    def update(self, time_delta: float):
        super().update(time_delta)
        self.motion_cooldown.update()
        self.add_letter_timer.update(time_delta)
        pressed = self.level.game.input_queue.just_pressed
        if self.state == self.STATE_GETTING_ANSWER:
            if "up" in pressed and self.motion_cooldown.done():
                self.answer_index = max(self.answer_index - 1, 0)
                self.update_text()
                self.motion_cooldown.reset()
            if "down" in pressed and self.motion_cooldown.done():
                self.answer_index = min(self.answer_index + 1, len(self.answers) - 1)
                self.update_text()
                self.motion_cooldown.reset()
            if "interact" in pressed:
                self.choose()
        if (
            self.state == self.STATE_COMPLETE
            and not self.answers
            and "interact" in pressed
        ):
            self.choose()
        return self.live


def dialog_rect(with_face=False):
    rect = pygame.Rect(8, 0, util_draw.RESOLUTION[0] - 16, 100)
    rect.bottom = util_draw.RESOLUTION[1] - 8
    if with_face:
        rect.left = 72  # 64 + 8
        rect.width -= 64
    return rect
