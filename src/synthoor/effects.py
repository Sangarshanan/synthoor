import numpy as np
import scipy.signal

from .sound import Sound
from .config import FPS

"""
Effects module, Under construction.
"""

def _as_2d(x):
    """Return (x_2d, was_1d) where x_2d has shape (frames, channels)."""
    x = np.asarray(x, dtype="float64")
    if x.ndim == 1:
        return x[:, None], True
    return x, False


def _comb_coeffs(delay, feedback):
    """Feedback comb filter: y[n] = x[n] + feedback * y[n - delay]."""
    a = np.zeros(delay + 1, dtype="float64")
    a[0] = 1.0
    a[delay] = -feedback
    b = np.array([1.0], dtype="float64")
    return b, a


def _allpass_coeffs(delay, gain):
    """Schroeder allpass: y[n] = -g*x[n] + x[n-delay] + g*y[n-delay]."""
    b = np.zeros(delay + 1, dtype="float64")
    b[0] = -gain
    b[delay] = 1.0
    a = np.zeros(delay + 1, dtype="float64")
    a[0] = 1.0
    a[delay] = -gain
    return b, a


class _IIRStage(object):
    """An lfilter stage that keeps its filter state across processing blocks."""

    def __init__(self, b, a):
        self.b = b
        self.a = a
        self._zi = None

    def reset(self):
        self._zi = None

    def process(self, x):
        # x has shape (frames, channels).
        n = max(len(self.a), len(self.b)) - 1

        if self._zi is None or self._zi.shape[1] != x.shape[1]:
            self._zi = np.zeros((n, x.shape[1]), dtype="float64")

        y, self._zi = scipy.signal.lfilter(self.b, self.a, x, axis=0, zi=self._zi)
        return y


class Reverb(Sound):
    """Schroeder reverb: parallel feedback comb filters followed by series
    allpass diffusers.

    Args:
        decay_time (float): Time for the reverb tail to decay by 60 dB, in
            seconds.
        wet_mix (float): Wet/dry balance between 0.0 (dry) and 1.0 (wet).
    """

    # Comb / allpass delays in samples at 44.1 kHz (Freeverb tuning).
    _COMB_DELAYS = (1116, 1188, 1277, 1356)
    _ALLPASS_DELAYS = (556, 441)
    _ALLPASS_GAIN = 0.7

    def __init__(self, decay_time=2.0, wet_mix=0.3):
        super().__init__()
        self.decay_time = float(decay_time)
        self.wet_mix = float(np.clip(wet_mix, 0.0, 1.0))

        self._combs = None
        self._allpasses = None
        self._built_decay = None

    def _build(self):
        combs = []
        for delay in self._COMB_DELAYS:
            # Per-comb feedback for a -60 dB decay over decay_time.
            feedback = 10.0 ** (-3.0 * delay / (self.decay_time * FPS))
            feedback = float(np.clip(feedback, 0.0, 0.999))
            combs.append(_IIRStage(*_comb_coeffs(delay, feedback)))

        allpasses = [
            _IIRStage(*_allpass_coeffs(delay, self._ALLPASS_GAIN))
            for delay in self._ALLPASS_DELAYS
        ]

        self._combs = combs
        self._allpasses = allpasses
        self._built_decay = self.decay_time

    def reset(self, shared=False):
        super().reset(shared)
        if self._combs is not None:
            for stage in self._combs:
                stage.reset()
        if self._allpasses is not None:
            for stage in self._allpasses:
                stage.reset()

    def forward(self, x, key_modulation=None):
        """Process input through the reverb.

        Args:
            x (ndarray): Input signal of shape (frames,) or (frames, channels).
            key_modulation: Unused, for API compatibility.

        Returns:
            ndarray: Reverberated signal with the same shape as the input.
        """
        if self._combs is None or self._built_decay != self.decay_time:
            self._build()

        x, was_1d = _as_2d(x)

        # Sum the parallel comb filters, then run the series allpass diffusers.
        wet = np.zeros_like(x)
        for comb in self._combs:
            wet += comb.process(x)
        wet /= len(self._combs)

        for allpass in self._allpasses:
            wet = allpass.process(wet)

        out = (1.0 - self.wet_mix) * x + self.wet_mix * wet

        return out[:, 0] if was_1d else out


class Delay(Sound):
    """Feedback delay (echo) effect.

    Args:
        delay_samples (int): Delay length in samples.
        feedback (float): Feedback amount for the echo tail (0.0 to 0.99).
        wet_mix (float): Wet/dry balance between 0.0 (dry) and 1.0 (wet).
    """

    def __init__(self, delay_samples=FPS * 0.5, feedback=0.5, wet_mix=0.5):
        super().__init__()
        self.delay_samples = int(delay_samples)
        self.feedback = float(np.clip(feedback, 0.0, 0.99))
        self.wet_mix = float(np.clip(wet_mix, 0.0, 1.0))

        self._stage = None
        self._built = None

    def _build(self):
        self._stage = _IIRStage(*_comb_coeffs(self.delay_samples, self.feedback))
        self._built = (self.delay_samples, self.feedback)

    def reset(self, shared=False):
        super().reset(shared)
        if self._stage is not None:
            self._stage.reset()

    def forward(self, x, key_modulation=None):
        """Process input through the delay line.

        Args:
            x (ndarray): Input signal of shape (frames,) or (frames, channels).
            key_modulation: Unused, for API compatibility.

        Returns:
            ndarray: Delayed signal with the same shape as the input.
        """
        if self._stage is None or self._built != (self.delay_samples, self.feedback):
            self._build()

        x, was_1d = _as_2d(x)

        # Comb output contains the dry signal plus the recirculating echoes.
        wet = self._stage.process(x)
        out = (1.0 - self.wet_mix) * x + self.wet_mix * wet

        return out[:, 0] if was_1d else out


class Compressor(Sound):
    """Dynamic range compressor with a peak envelope follower.

    Args:
        threshold (float): Threshold in dB above which compression applies.
        ratio (float): Compression ratio (e.g. 4.0 means 4:1).
        attack_time (float): Attack time in seconds.
        release_time (float): Release time in seconds.
        makeup_gain (float): Output make-up gain in dB.
    """

    def __init__(
        self,
        threshold=-30.0,
        ratio=4.0,
        attack_time=0.01,
        release_time=0.1,
        makeup_gain=0.0,
    ):
        super().__init__()
        self.threshold = float(threshold)
        self.ratio = float(max(1.0, ratio))
        self.attack_time = float(attack_time)
        self.release_time = float(release_time)
        self.makeup_gain = float(makeup_gain)

        self.envelope = 0.0

    @property
    def attack_coeff(self):
        return np.exp(-1.0 / (self.attack_time * FPS)) if self.attack_time > 0 else 0.0

    @property
    def release_coeff(self):
        return np.exp(-1.0 / (self.release_time * FPS)) if self.release_time > 0 else 0.0

    def reset(self, shared=False):
        super().reset(shared)
        self.envelope = 0.0

    def forward(self, x, key_modulation=None):
        """Apply compression to the input signal.

        Args:
            x (ndarray): Input signal of shape (frames,) or (frames, channels).
            key_modulation: Unused, for API compatibility.

        Returns:
            ndarray: Compressed signal with the same shape as the input.
        """
        x, was_1d = _as_2d(x)

        # Stereo-linked detection: follow the loudest channel so a single
        # shared gain is applied to all channels and the image is preserved.
        mag = np.abs(x).max(axis=1)

        attack = self.attack_coeff
        release = self.release_coeff

        # Peak envelope follower (data-dependent, computed sequentially).
        env = np.empty_like(mag)
        e = self.envelope
        for i in range(len(mag)):
            m = mag[i]
            coeff = attack if m > e else release
            e = coeff * e + (1.0 - coeff) * m
            env[i] = e
        self.envelope = e

        # Static gain curve in the log domain, applied above the threshold.
        env_db = 20.0 * np.log10(env + 1e-10)
        over = env_db > self.threshold

        gain_db = np.zeros_like(env_db)
        gain_db[over] = (self.threshold - env_db[over]) * (1.0 - 1.0 / self.ratio)
        gain_db += self.makeup_gain

        gain = (10.0 ** (gain_db / 20.0))[:, None]
        out = x * gain

        return out[:, 0] if was_1d else out
