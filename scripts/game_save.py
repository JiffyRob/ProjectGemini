class GameSave:
    def __init__(self, game):
        self.game = game
        self.data = {
            "health": 6,
            "health_capacity": 6,
            "planet": "GeminiII",
            "bush_interactions": 0,
            "emeralds": 10,
        }
        self.loaded_path = None

    def __getattr__(self, attr):
        if attr in {"data", "game"} or attr[:2] == attr[-2:] == "__":
            return super().__getattribute__(attr)
        return self.data[attr]

    def __setattr__(self, name, value):
        if name in {"data", "game"}:
            return super().__setattr__(name, value)
        self.data[name] = value

    def load(self, path):
        self.data = self.game.loader.get_save(path)
        self.loaded_path = path

    def save(self, path=None):
        if path is None:
            path = self.loaded_path
        self.game.loader.save_data(path, self.data)