from scripts import snek, visual_fx, util_draw


class Write(snek.SnekCommand):
    UNWRITTEN = 0
    WRITING = 1
    WRITTEN = 2

    def __init__(self, text):
        super().__init__(required_context=("LEVEL",))
        self.state = self.UNWRITTEN
        self.text = text

    def finish_writing(self, _):
        self.state = self.WRITTEN

    def get_value(self):
        if self.context["LEVEL"] == snek.NULL:
            self.post_warning(
                "Unable to locate level context.  Dialog request ignored."
            )
            return 1
        elif self.state == self.UNWRITTEN:
            self.context["LEVEL"].start_dialog(self.text, on_finish=self.finish_writing)
            self.state = self.WRITING
            return snek.UNFINISHED
        elif self.state == self.WRITING:
            return snek.UNFINISHED
        elif self.state == self.WRITTEN:
            return 0


class Ask(Write):
    def __init__(self, question, *answers):
        super().__init__(question)
        self.answers = answers
        self.chosen = None

    def finish_writing(self, answer):
        self.state = self.WRITTEN
        self.chosen = answer

    def get_value(self):
        if self.context["LEVEL"] == snek.NULL:
            self.post_warning(
                "Unable to locate level context.  Dialog request ignored."
            )
            return 1
        elif self.state == self.UNWRITTEN:
            self.context["LEVEL"].start_dialog(
                self.text, *self.answers, on_finish=self.finish_writing
            )
            self.state = self.WRITING
            return snek.UNFINISHED
        elif self.state == self.WRITING:
            return snek.UNFINISHED
        elif self.state == self.WRITTEN:
            return self.chosen


class Fade(snek.SnekCommand):
    IN_CIRCLE = 0
    OUT_CIRCLE = 1
    POS = "get_player_pos()"  # snek expression to get the player's position
    FADES = (
        visual_fx.GrowingCircle,
        visual_fx.ShrinkingCircle,
    )

    def __init__(self, fade_type, x=None, y=None):
        super().__init__((self.POS, "LEVEL"))
        self.fade_type = fade_type
        self.pos = [x, y]
        self.fader = None

    def get_value(self):
        if self.fader is None:
            player_pos = self.context[self.POS]
            if self.pos[0] is None:
                self.pos[0] = player_pos[0]
            if self.pos[1] is None:
                self.pos[1] = player_pos[1]
            if self.fade_type in {self.IN_CIRCLE, self.OUT_CIRCLE}:
                self.fader = self.FADES[self.fade_type](util_draw.RESOLUTION, self.pos, speed=192)
            else:
                # TODO: other fades...?
                pass
            self.context["LEVEL"].add_effect(self.fader)
            return snek.UNFINISHED
        if self.fader.done:
            return snek.NULL
        return snek.UNFINISHED


def cutscene(script, runner=snek.NULL, level=None):
    if runner is not snek.NULL:
        level = runner.level
    return snek.SNEKProgram(
        script,
        {
            "RUNNER": runner,
            "LEVEL": level,
            "PLANET": level.name.split("_")[0],
            "LEVEL_NAME": level.name,
            "FADEIN_CIRCLE": Fade.IN_CIRCLE,
            "FADEOUT_CIRCLE": Fade.OUT_CIRCLE,
        },
        {
            "lock_player": snek.snek_command(level.player.lock),
            "unlock_player": snek.snek_command(level.player.unlock),
            "lock": snek.snek_command(level.lock),
            "unlock": snek.snek_command(level.unlock),
            "write": Write,
            "ask": Ask,
            "pop_state": snek.snek_command(level.pop),
            "fade": Fade,
            "get_player_pos": snek.snek_command(lambda: level.player.pos),
        },
    )