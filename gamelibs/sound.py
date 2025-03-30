import pygame

pygame.mixer.init()


class ChannelRack:
    def __init__(self, channels, start_index=0):
        self._free_channels = [
            pygame.mixer.Channel(i + start_index) for i in range(channels)
        ]
        self._free_channels = [i for i in self._free_channels if i is not None]
        self._used_channels = []

    def _get_least_priority(self):
        return sorted(self._used_channels, key=lambda x: x[0])[0]

    def allocate_channel(self, priority):
        self.free_done()
        if self._free_channels:
            channel = self._free_channels.pop(-1)
            self._used_channels.append([priority, channel])
        else:
            channel_data = self._get_least_priority()
            least_priority, channel = channel_data
            if priority > least_priority:
                channel.stop()
                channel_data[0] = priority
        return channel

    def free_done(self):
        to_free = []
        for channel_data in self._used_channels:
            if not channel_data[1].get_busy():
                to_free.append(channel_data)
        for channel_data in to_free:
            self._used_channels.remove(channel_data)
            self._free_channels.append(channel_data[1])


class SoundManager:
    def __init__(self, loader, channels=8):
        self._channel_rack = ChannelRack(channels)
        self.loader = loader
        self.current_track = None
        self.sound_volume = 1
        self.music_volume = 1

    def play_sound(
        self, path, priority=10, loops=0, volume=1, fade_ms=0, polar_location=(0, 0)
    ):
        sound = self.loader.load_sound(path)
        channel = self._channel_rack.allocate_channel(priority)
        if channel is not None:  # if all channels are in use and of higher priority
            channel.set_source_location(*polar_location)
            channel.set_volume(volume * self.sound_volume)
            channel.play(sound, loops, 0, fade_ms)
        return channel is not None

    def set_sound_volume(self, value):
        self.sound_volume = pygame.math.clamp(value, 0, 1)
        return self.sound_volume

    def get_sound_value(self):
        return self.sound_volume

    def set_music_volume(self, value):
        self.music_volume = pygame.math.clamp(value, 0, 1)
        return self.music_volume

    def get_music_volume(self, value):
        return self.music_volume

    def switch_track(self, track=None, volume=1, loops=-1, start=0.0, fade_ms=0):
        if track is None:
            return
        track = self.loader.join(track)
        if track != self.current_track:
            pygame.mixer.music.set_volume(self.music_volume * volume)
            pygame.mixer.music.stop()
            pygame.mixer.music.load(track)
            pygame.mixer.music.play(loops, start, fade_ms)
            self.current_track = track
        else:
            pass

    def stop_track(self):
        pygame.mixer.music.stop()
        self.current_track = None
