import webbrowser
import pygame

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


class FadeInCircle(snek.SnekCommand):
    def __init__(self, x=None, y=None, blocking=True):
        super().__init__(("get_player_pos()", "LEVEL"))
        self.pos = [x, y]
        self.blocking = blocking
        self.fader = None

    def get_value(self):
        if self.fader is None:
            player_pos = self.context["get_player_pos()"]
            level = self.context["LEVEL"]
            if self.pos[0] is None:
                self.pos[0] = player_pos[0]
            if self.pos[1] is None:
                self.pos[1] = player_pos[1]
            screen_pos = level.world_to_screen(self.pos)
            self.fader = visual_fx.CircleTransitionIn(util_draw.RESOLUTION, screen_pos, speed=400)
            level.add_effect(self.fader)
        if self.blocking and not self.fader.done:
            return snek.UNFINISHED
        return snek.NULL


# TODO: Possibly reduce repetition...?
class FadeOutCircle(snek.SnekCommand):
    def __init__(self, x=None, y=None, blocking=True):
        super().__init__(("get_player_pos()", "LEVEL"))
        self.pos = [x, y]
        self.blocking = blocking
        self.fader = None

    def get_value(self):
        if self.fader is None:
            player_pos = self.context["get_player_pos()"]
            level = self.context["LEVEL"]
            if self.pos[0] is None:
                self.pos[0] = player_pos[0]
            if self.pos[1] is None:
                self.pos[1] = player_pos[1]
            screen_pos = level.world_to_screen(self.pos)
            self.fader = visual_fx.CircleTransitionOut(util_draw.RESOLUTION, screen_pos, speed=400)
            level.add_effect(self.fader)
        if self.blocking and not self.fader.done:
            return snek.UNFINISHED
        return snek.NULL


class FadeIn(snek.SnekCommand):
    def __init__(self, r=0, g=0, b=0, blocking=True):
        super().__init__(("LEVEL",))
        self.color = pygame.Color(r, g, b)
        self.blocking = blocking
        self.fader = None

    def get_value(self):
        if self.fader is None:
            self.fader = visual_fx.ColorTransitionIn(self.color)
            self.context["LEVEL"].add_effect(self.fader)
        if self.blocking and not self.fader.done:
            return snek.UNFINISHED
        return snek.NULL


class FadeOut(snek.SnekCommand):
    def __init__(self, r=0, g=0, b=0, blocking=True):
        super().__init__(("LEVEL",))
        self.color = pygame.Color(r, g, b)
        self.blocking = blocking
        self.fader = None

    def get_value(self):
        if self.fader is None:
            self.fader = visual_fx.ColorTransitionOut(self.color)
            self.context["LEVEL"].add_effect(self.fader)
        if self.blocking and not self.fader.done:
            return snek.UNFINISHED
        return snek.NULL


class Fill(snek.SnekCommand):
    def __init__(self, r=0, g=0, b=0, duration=0):
        super().__init__(("LEVEL",))
        self.color = pygame.Color(r, g, b)
        self.duration = duration
        self.fader = None

    def get_value(self):
        if self.fader is None:
            self.fader = visual_fx.Fill(self.color, self.duration)
            self.context["LEVEL"].add_effect(self.fader)
        if self.duration and not self.fader.done:
            return snek.UNFINISHED
        return snek.NULL


def spawn_ship(level, ship_type, start_x, start_y, dest_x, dest_y):
    level.spawn("Ship", pygame.Rect(start_x - 24, start_y - 16, 48, 32), start=(start_x, start_y), dest=(dest_x, dest_y), ship_type=ship_type)


def cutscene(script_name, runner=snek.NULL, level=None, extra_constants=None):
    if runner is not snek.NULL:
        level = runner.level
    if extra_constants is None:
        extra_constants = {}
    return snek.SNEKProgram(
        level.game.loader.get_script(f"{script_name}.snek"),
        {
            "RUNNER": runner,
            "LEVEL": level,
            "PLANET": level.name.split("_")[0],
            "LEVEL_NAME": level.name,
            "LEVEL_SOUNDTRACK": level.soundtrack,
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
            "get_player_pos": snek.snek_command(lambda: level.player.pos),
            "get_player_name": snek.snek_command(lambda: level.player.name),
            "map_switch": snek.snek_command(level.game.load_map),
            "spawn_ship": snek.snek_command(lambda *args: spawn_ship(level, *args)),
            "play_soundtrack": snek.snek_command(level.game.play_soundtrack),
            "save": snek.snek_command(level.game.save_to_disk),
            "quit": snek.snek_command(level.game.quit),
            "rickroll": snek.snek_command(lambda: webbrowser.open("https://youtu.be/E4WlUXrJgy4")),
            "fadein": FadeIn,
            "fadeout": FadeOut,
            "fadein_circle": FadeInCircle,
            "fadeout_circle": FadeOutCircle,
            "fill": Fill,
            "clear_effects": snek.snek_command(level.clear_effects),
            "run_cutscene": snek.snek_command(lambda *args: level.run_cutscene(*args, override=True)),
            "attempt_map_cutscene": snek.snek_command(level.attempt_map_cutscene),
        },
    )
