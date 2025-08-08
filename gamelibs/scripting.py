# type: ignore
# TODO: Stub files for SNEK2, then typing can happen

import pygame

from SNEK2 import SNEKCallable, AsyncSNEKCallable, SNEKProgram, Arity
from gamelibs import hardware, interfaces


class Write(AsyncSNEKCallable):
    def __init__(self, game) -> None:
        self.game = game
        self._arity = 1

    async def call(self, interpreter, args) -> None:
        await self.game.get_state().run_dialog(*args)


class Ask(AsyncSNEKCallable):
    def __init__(self, game) -> None:
        self.game = game
        # question, *answers
        self._arity = Arity(1, None)

    async def call(self, interpreter, args) -> str:
        return await self.game.get_state().run_dialog(*args)


class Transition(AsyncSNEKCallable):
    def __init__(self, game) -> None:
        self.game = game
        # type
        # type, x, y
        # type, color
        self._arity = Arity(1, 3)

    async def call(self, interpreter, args):
        return await self.game.get_state().transition(*args)


class Rickroll(AsyncSNEKCallable):
    def __init__(self) -> None:
        self._arity = 0

    async def call(self, interpreter, args) -> None:
        raise NotImplementedError("Better get the rickroll written....")


class Run(AsyncSNEKCallable):
    def __init__(self, game) -> None:
        self.game = game
        self._arity = Arity(1, 2)

    async def call(self, interpreter, args) -> None:
        return await self.game.run_sub_cutscene(args[0], **args[1])


class RunMap(AsyncSNEKCallable):
    def __init__(self, game) -> None:
        self.game = game
        self._arity = Arity(0, 1)

    async def call(self, interpreter, args) -> None:
        return await self.game.get_state().attempt_map_cutscene()


class Spawn(SNEKCallable):
    def __init__(self, game) -> None:
        self.game = game
        self._arity = Arity(5, 6)

    async def call(self, interpreter, args) -> interfaces.Sprite:
        if len(args) == 6:
            args = list(args)
            args.append(0)
        return self.game.get_state().spawn(
            args[0],  # sprite name
            args[1:5],  # rect
            args[5],  # z
        )


class SpawnShip(SNEKCallable):
    def __init__(self, game):
        self.game = game
        self._arity = 5

    async def call(self, interpreter, args):
        self.game.get_state().spawn(
            "Ship",
            pygame.Rect(args[1] - 24, args[2] - 16, 48, 32),
            start=(args[1], args[2]),
            dest=(args[3], args[4]),
            ship_type=args[0],
        )


class Fade(AsyncSNEKCallable):
    def __init__(self, game):
        self.game = game
        self._arity = Arity(1, 5)

    async def call(self, interpreter, args):
        return await self.game.get_state().fade(*args)


class Script(SNEKProgram):
    def __init__(self, game, script, api=None):
        if api is None:
            api = {}
        api = {
            "write": Write(game),
            "ask": Ask(game),
            "transition": Transition(game),
            "rickroll": Rickroll(),
            "run": Run(game),
            "attempt_map_cutscene": RunMap(game),
            "spawn": Spawn(game),
            "lock": SNEKCallable(
                lambda *args: game.get_state().lock(*args), Arity(0, 1)
            ),
            "unlock": SNEKCallable(
                lambda *args: game.get_state().unlock(*args), Arity(0, 1)
            ),
            "hide": SNEKCallable(
                lambda *args: game.get_state().hide(*args), Arity(0, 1)
            ),
            "show": SNEKCallable(
                lambda *args: game.get_state().show(*args), Arity(0, 1)
            ),
            "fade": Fade(game),
            "clear_effects": SNEKCallable(lambda: game.get_state().clear_effects(), 0),
            "play_soundtrack": SNEKCallable(game.play_soundtrack, Arity(0, 1)),
            "spawn_ship": SpawnShip(game),
            "fill": SNEKCallable(
                lambda *args: game.get_state().fill(*args), Arity(0, 4)
            ),
            "clear": SNEKCallable(lambda *args: game.get_state().clear(*args), 0),
            "map_switch": SNEKCallable(lambda *args: game.load_map(*args), Arity(1, 4)),
            "exit_level": SNEKCallable(lambda: game.pop_state(), 0),
            "pop_state": SNEKCallable(lambda: game.pop_state(), 0),
            "get_save_state": SNEKCallable(hardware.save.get_state, 1),
            "set_save_state": SNEKCallable(hardware.save.set_state, 2),
            "get_current_planet_name": SNEKCallable(game.get_current_planet_name, 0),
            "get_x": SNEKCallable(
                lambda *args: game.get_state().get_x(*args), Arity(0, 1)
            ),
            "get_y": SNEKCallable(
                lambda *args: game.get_state().get_y(*args), Arity(0, 1)
            ),
            "get_z": SNEKCallable(
                lambda *args: game.get_state().get_z(*args), Arity(0, 1)
            ),
            "get_facing": SNEKCallable(
                lambda *args: game.get_state().get_facing(*args), Arity(0, 1)
            ),
            "save": SNEKCallable(hardware.save.save, 0),
            "quit": SNEKCallable(game.quit, 0),
            **api,
        }
        super().__init__(script=script, api=api)
