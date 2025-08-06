from gamelibs.loader import Loader
from gamelibs.sound import SoundManager
from gamelibs.input_binding import InputQueue
from gamelibs import interfaces
from gamelibs.game_save import GameSave

loader: interfaces.Loader = Loader()
sound_manager: interfaces.SoundManager = SoundManager(loader)
input_queue: interfaces.InputQueue = InputQueue()
save: interfaces.GameSave = GameSave()
settings: interfaces.GameSettings = interfaces.GameSettings()