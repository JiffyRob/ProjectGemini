from scripts import snek


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


def interaction(script, runner):
    return snek.SNEKProgram(
        script,
        {
            "LEVEL": runner.level,
            "PLANET": runner.level.name.split("_")[0],
        },
        {
            "lock_player": snek.snek_command(runner.level.player.lock_input),
            "unlock_player": snek.snek_command(runner.level.player.unlock_input),
            "write": Write,
            "ask": Ask,
            "pop_state": snek.snek_command(runner.level.pop),
        },
    )


def cutscene(script, level):
    pass  # TODO: implement cutscenes
