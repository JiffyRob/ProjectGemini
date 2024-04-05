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
            self.post_warning("Unable to locate level context.  Dialog request ignored.")
            return 1
        elif self.state == self.UNWRITTEN:
            self.context["LEVEL"].start_dialog(self.text, on_finish=self.finish_writing)
            self.state = self.WRITING
        elif self.state == self.WRITING:
            return snek.UNFINISHED
        elif self.state == self.WRITTEN:
            return 0


def interaction(script, runner):
    return snek.SNEKProgram(
        script,
        {
            "LEVEL": runner.level,
            "PLANET": runner.level.name.split("_")[0],
        },
        {
            "write": Write
        }
    )


def cutscene(script, level):
    pass  # TODO: implement cutscenes
