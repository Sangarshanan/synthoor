# HAVE FUN :) AND TRY NOT TO PEEK

# Stacking different Frequencies
sequence = np.hstack([tone1,tone2,tone3, tone4])
ipd.Audio(sequence, rate=sample_rate)


# Oscillator class
class Oscillator:
    def __init__(self, shape="sine"):
        self.shape = shape
        self.get_wave = dict(
            sine=get_sine_wave,
            tri=get_triangle_wave,
            square=get_square_wave,
            saw=get_sawtooth_wave,
        ).get(self.shape)

    def play(self, frequency, amp=1, duration=1):
        waveform = self.get_wave(frequency, amp, duration)
        sd.play(waveform)
        return waveform


# Amplitude Modulation

am_signal = carrier_amplitude * (1 + modulating_signal) * np.sin(carrier_omega)


# ASDR Duration Sanity check

if attack_time + decay_time + release_time > duration:
    print("Warning: Sum of Attack, Decay, and Release times exceeds total duration. Envelope might be truncated.")

# Max Volume right after the Attack finishes and hold it there until the Release phase begins
attack_t = 0.01
decay_t = 0
sustain_l = 1
release_t = 0.01



