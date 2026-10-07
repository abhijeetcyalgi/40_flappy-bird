import array
import math

import pygame


def _make_tone(freq_start, freq_end, duration, volume=0.35):
    """Synthesize a short sine sweep as a pygame Sound (no audio files needed).

    Returns None if the mixer isn't available or uses an unexpected format.
    """
    init = pygame.mixer.get_init()
    if not init:
        return None
    rate, fmt, channels = init
    if fmt != -16:  # we generate signed 16-bit samples
        return None

    total = int(rate * duration)
    samples = array.array("h")
    phase = 0.0
    for i in range(total):
        t = i / total
        freq = freq_start + (freq_end - freq_start) * t
        phase += 2 * math.pi * freq / rate
        envelope = 1.0 - t  # fade out to avoid clicks
        value = int(32767 * volume * envelope * math.sin(phase))
        for _ in range(channels):
            samples.append(value)
    return pygame.mixer.Sound(buffer=samples.tobytes())


class SoundManager:
    """Flap / score / die sound effects. Silently does nothing if audio fails."""

    def __init__(self):
        self.flap = self.score = self.die = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            self.flap = _make_tone(400, 700, 0.12)    # quick rising chirp
            self.score = _make_tone(800, 1200, 0.15)  # bright blip
            self.die = _make_tone(400, 80, 0.50)      # falling tone
        except Exception as exc:  # no audio device, etc.
            print(f"Sound disabled: {exc}")

    def play(self, name):
        sound = getattr(self, name, None)
        if sound is not None:
            sound.play()
