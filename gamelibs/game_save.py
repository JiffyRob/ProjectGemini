from typing import Any

from gamelibs import interfaces

class GameSave:
    def __init__(self, game: interfaces.Game):
        self.game = game
        self.data = {}
        self.tmp_data = {}
        self.loaded_path = None

    def __getattr__(self, attr: str):
        if attr in {"data", "game"} or attr[:2] == attr[-2:] == "__":
            return super().__getattribute__(attr)
        return self.data[attr]

    def __setattr__(self, name: str, value: Any):
        if name in {"data", "game"}:
            return super().__setattr__(name, value)
        self.data[name] = value

    def get_state(self, key):
        return self.data[key]

    def set_state(self, key, value):
        self.data[key] = value

    def get_tmp(self, key):
        return self.tmp_data[key]

    def set_tmp(self, key, value):
        self.tmp_data[key] = value

    def load(self, path):
        self.data = self.game.loader.get_save(path)
        self.loaded_path = path

    def save(self, path=None):
        if path is None:
            path = self.loaded_path
        old_health = self.health
        self.health = self.health_capacity
        self.game.loader.save_data(path, self.data)
        self.health = old_health

    def delete(self, path=None):
        if path is None:
            path = self.loaded_path
        self.game.loader.delete_save(path)
