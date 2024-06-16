import webbrowser

from scripts import snek, util_draw, visual_fx


class Write(snek.SnekCommand):
    UNWRITTEN = 0
    WRITING = 1
    WRITTEN = 2

    def __init__(self, text, blocking=True):
        super().__init__(required_context=("LEVEL",))
        self.state = self.UNWRITTEN
        self.text = text
        self.blocking = blocking

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
            if self.blocking:
                return snek.UNFINISHED
            else:
                return snek.NULL
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
    IN_COLORFADE = 2
    OUT_COLORFADE = 3
    STAY_FADED_OUT = 4
    POS = "get_player_pos()"  # snek expression to get the player's position
    FADES = (
        visual_fx.GrowingCircle,
        visual_fx.ShrinkingCircle,
        visual_fx.FadeIn,
        visual_fx.FadeOut,
        visual_fx.EternalSolid,
    )
    UNIT_SCREEN = 0
    UNIT_WORLD = 1

    def __init__(self, fade_type, x_r=None, y_g=None, unit_b=None):
        super().__init__((self.POS, "LEVEL"))
        self.fade_type = fade_type
        self.pos = [x_r, y_g]
        self.coord = self.pos
        self.fader = None
        self.unit = unit_b or self.UNIT_WORLD
        self.color = (x_r, y_g, unit_b)

    def get_value(self):
        if self.fader is None:
            player_pos = self.context[self.POS]
            if self.pos[0] is None:
                self.pos[0] = player_pos[0]
            if self.pos[1] is None:
                self.pos[1] = player_pos[1]
            self.coord = self.pos
            if self.unit == self.UNIT_WORLD:
                self.pos = lambda: self.context["LEVEL"].world_to_screen(self.coord)
            if self.fade_type in {self.IN_CIRCLE, self.OUT_CIRCLE}:
                self.fader = self.FADES[self.fade_type](
                    util_draw.RESOLUTION, self.pos, speed=400
                )
            elif self.fade_type in {self.IN_COLORFADE, self.OUT_COLORFADE, self.STAY_FADED_OUT}:
                self.fader = self.FADES[self.fade_type](
                    self.color
                )
            # TODO: Other fades?
            self.context["LEVEL"].add_effect(self.fader)
            return snek.UNFINISHED
        if self.fader.done or self.fade_type == self.STAY_FADED_OUT:
            return snek.NULL
        return snek.UNFINISHED


def cutscene(script_name, runner=snek.NULL, level=None, extra_constants=None):
    if runner is not snek.NULL:
        level = runner.level
    if extra_constants is None:
        extra_constants = {}
    return snek.SNEKProgram(
        level.game.loader.get_text(f"snek/{script_name}.snek"),
        {
            "RUNNER": runner,
            "LEVEL": level,
            "PLANET": level.name.split("_")[0],
            "LEVEL_NAME": level.name,
            "LEVEL_SOUNDTRACK": level.soundtrack,
            "FADEIN_CIRCLE": Fade.IN_CIRCLE,
            "FADEOUT_CIRCLE": Fade.OUT_CIRCLE,
            "FADEIN_COLOR": Fade.IN_COLORFADE,
            "FADEOUT_COLOR": Fade.OUT_COLORFADE,
            "STAY_FADED_OUT": Fade.STAY_FADED_OUT,
            **extra_constants,
        },
        {
            "lock_player": snek.snek_command(level.player.lock),
            "unlock_player": snek.snek_command(level.player.unlock),
            "lock": snek.snek_command(level.lock),
            "unlock": snek.snek_command(level.unlock),
            "write": Write,
            "ask": Ask,
            "exit_level": snek.snek_command(level.exit_level),
            "pop_state": snek.snek_command(level.game.pop_state),
            "fade": Fade,
            "get_player_pos": snek.snek_command(lambda: level.player.pos),
            "get_player_name": snek.snek_command(lambda: level.player.name),
            "map_switch": snek.snek_command(level.game.load_map),
            "play_soundtrack": snek.snek_command(level.game.play_soundtrack),
            "save": snek.snek_command(level.game.save_to_disk),
            "quit": snek.snek_command(level.game.quit),
            "rickroll": snek.snek_command(lambda: webbrowser.open("https://youtu.be/E4WlUXrJgy4"))
        },
    )
