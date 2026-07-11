import unittest
import numpy as np

from synthoor.sound import Sound, GatedSound, LatencyGate, key2freq, freq2key
from synthoor.config import FPS, MIDDLE_C


FRAMES = 512


class TestKey2Freq(unittest.TestCase):

    def test_middle_c_key_60(self):
        """MIDI key 60 = Middle C = 261.63 Hz."""
        freq = key2freq(60)
        self.assertAlmostEqual(freq, 261.63, delta=0.5)

    def test_a4_key_69(self):
        """MIDI key 69 = A4 = 440 Hz."""
        freq = key2freq(69)
        self.assertAlmostEqual(freq, 440.0, delta=0.5)

    def test_octave_doubles_frequency(self):
        f_low = key2freq(60)
        f_high = key2freq(72)   # one octave up
        self.assertAlmostEqual(f_high / f_low, 2.0, places=5)

    def test_semitone_ratio(self):
        """Each semitone should multiply freq by 2**(1/12)."""
        ratio = key2freq(61) / key2freq(60)
        self.assertAlmostEqual(ratio, 2 ** (1 / 12), places=6)

    def test_freq2key_roundtrip(self):
        """key2freq and freq2key must be inverses."""
        for key in [21, 60, 69, 84, 108]:
            self.assertAlmostEqual(freq2key(key2freq(key)), key, places=5)


class TestSound(unittest.TestCase):

    def _make(self):
        class Passthrough(Sound):
            def forward(self):
                return np.zeros((self.frames, 1))
        p = Passthrough()
        p.frames = FRAMES
        return p

    def test_call_returns_2d(self):
        p = self._make()
        out = p()
        self.assertEqual(out.ndim, 2)
        self.assertEqual(out.shape, (FRAMES, 1))

    def test_frames_attribute_set(self):
        p = self._make()
        p.frames = 128
        out = p()
        self.assertEqual(out.shape, (128, 1))

    def test_consume_returns_scaled_2d(self):
        p = self._make()
        p.frames = FRAMES
        out = p.consume(FRAMES, velocity=64, amp=1.0)
        self.assertEqual(out.shape, (FRAMES, 1))
        # velocity=64 is 64/128 = 0.5; DEFAULT_AMP = 0.5 → scale = 0.25
        # passthrough is zeros so result is zeros
        np.testing.assert_array_equal(out, 0)

    def test_reset_clears_cache(self):
        p = self._make()
        out1 = p()
        p.reset()
        p.frames = FRAMES
        out2 = p()
        self.assertEqual(out2.shape, (FRAMES, 1))


if __name__ == "__main__":
    unittest.main()
