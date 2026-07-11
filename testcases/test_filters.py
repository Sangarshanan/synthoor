import unittest
import numpy as np

from synthoor.filters import ButterFilter, BaseFilter
from synthoor.config import FPS


def _make_butter(freq=1000, btype="lowpass", **kw):
    orig = ButterFilter.warmup
    ButterFilter.warmup = lambda self: None
    bf = ButterFilter(freq=freq, btype=btype, **kw)
    ButterFilter.warmup = orig
    return bf


def _sine(freq_hz, frames, amplitude=0.9):
    t = np.arange(frames) / FPS
    return (amplitude * np.sin(2 * np.pi * freq_hz * t)).astype(np.float64)


class TestBaseFilter(unittest.TestCase):

    def test_passthrough_returns_input_unchanged(self):
        bf = BaseFilter(freq=1000)
        x = np.linspace(-1, 1, 256)
        out, z = bf.filter(x, 1000)
        np.testing.assert_array_equal(out, x)
        self.assertIsNone(z)

    def test_forward_shape_matches_input_1d(self):
        """BaseFilter passthrough (filter() returns x unchanged) preserves 1D shape."""
        for n in [64, 128, 256, 443, 444, 512, 1024]:
            bf = BaseFilter(freq=500)
            x = np.zeros(n)
            out = bf.forward(x)
            self.assertEqual(out.shape, x.shape, f"1D shape mismatch n={n}")

    def test_forward_shape_matches_input_2d(self):
        for n in [64, 256, 443, 444, 512]:
            bf = BaseFilter(freq=500)
            x = np.zeros((n, 1))
            out = bf.forward(x)
            self.assertEqual(out.shape, x.shape, f"2D shape mismatch n={n}")

    def test_forward_initialises_state_after_first_call(self):
        bf = BaseFilter(freq=500)
        self.assertIsNone(bf._f)
        self.assertIsNone(bf._x)
        bf.forward(np.zeros(128))
        self.assertIsNotNone(bf._f)
        self.assertIsNotNone(bf._x)

    def test_forward_same_freq_path_no_error(self):
        bf = BaseFilter(freq=500)
        x = np.zeros(128)
        bf.forward(x)
        out = bf.forward(x)   # same freq → cached path
        self.assertEqual(out.shape, x.shape)

    def test_crossfade_no_shape_mismatch_various_sizes(self):
        """
        Regression for the np.linspace fix in BaseFilter.forward.
        Frequency change triggers crossfade; must never raise a broadcast error
        or produce wrong output shape.
        BaseFilter.forward expects 2D (N, 1) input in practice.
        """
        for n in [443, 444, 511, 512, 513, 1023, 1024]:
            bf = BaseFilter(freq=500)
            bf.forward(np.zeros((n, 1)))   # prime _f = 500
            bf.freq = 800                  # different freq → crossfade branch
            x = np.zeros((n, 1))
            try:
                out = bf.forward(x)
            except ValueError as e:
                self.fail(f"Crossfade raised ValueError for n={n}: {e}")
            self.assertEqual(out.shape, x.shape,
                             f"Crossfade output shape wrong for n={n}")

    def test_crossfade_no_shape_mismatch_2d_input(self):
        """Same regression test with 2D (frames, 1) input."""
        for n in [443, 444, 512]:
            bf = BaseFilter(freq=500)
            bf.forward(np.zeros((n, 1)))
            bf.freq = 800
            x = np.zeros((n, 1))
            try:
                out = bf.forward(x)
            except ValueError as e:
                self.fail(f"2D crossfade ValueError for n={n}: {e}")
            self.assertEqual(out.shape, x.shape)

    def test_multiple_freq_changes_no_error(self):
        bf = BaseFilter(freq=200)
        x = np.zeros((512, 1))
        bf.forward(x)
        for freq in [300, 400, 500, 600, 500, 400, 300, 200]:
            bf.freq = freq
            out = bf.forward(x)
            self.assertEqual(out.shape, x.shape,
                             f"Shape mismatch after freq→{freq}")

    def test_key_modulation_does_not_raise(self):
        bf = BaseFilter(freq=500)
        x = np.zeros((128, 1))
        mod = np.zeros((128, 1))
        out = bf.forward(x, key_modulation=mod)
        self.assertIsNotNone(out)
        self.assertEqual(out.shape[0], 128)

    def test_reset_clears_all_state(self):
        bf = BaseFilter(freq=1000)
        bf.forward(np.zeros(128))
        bf.reset()
        self.assertIsNone(bf._f)
        self.assertIsNone(bf._x)
        self.assertIsNone(bf._z)

    def test_reset_then_forward_works(self):
        bf = BaseFilter(freq=1000)
        x = np.zeros(128)
        bf.forward(x)
        bf.reset()
        out = bf.forward(x)
        self.assertEqual(out.shape, x.shape)


class TestButterFilterSignal(unittest.TestCase):

    FRAMES = 4096

    def test_lowpass_passes_low_freq(self):
        """Signal well below cutoff must pass through with amplitude > 0.5."""
        bf = _make_butter(freq=2000, btype="lowpass")
        bf.frames = self.FRAMES
        x = _sine(200, self.FRAMES)[:, None]    # 200 Hz << 2000 Hz cutoff
        bf.forward(x)                           # warm-up
        out = bf.forward(x)
        self.assertGreater(np.abs(out).max(), 0.5)

    def test_lowpass_attenuates_high_freq(self):
        """Signal well above cutoff must be significantly attenuated."""
        bf = _make_butter(freq=500, btype="lowpass")
        bf.frames = self.FRAMES
        x = _sine(5000, self.FRAMES)[:, None]   # 5000 Hz >> 500 Hz cutoff
        bf.forward(x)
        out = bf.forward(x)
        self.assertLess(np.abs(out).max(), 0.3,
                        "Lowpass failed to attenuate 5000 Hz signal")

    def test_highpass_passes_high_freq(self):
        """Highpass must let high frequencies through."""
        bf = _make_butter(freq=500, btype="highpass")
        bf.frames = self.FRAMES
        x = _sine(5000, self.FRAMES)[:, None]
        bf.forward(x)
        out = bf.forward(x)
        self.assertGreater(np.abs(out).max(), 0.3)

    def test_highpass_attenuates_low_freq(self):
        bf = _make_butter(freq=2000, btype="highpass")
        bf.frames = self.FRAMES
        # Multiple passes to reach steady-state attenuation
        # Need continuous phase across blocks to avoid high-freq transient spikes!
        for i in range(5):
            t = (np.arange(self.FRAMES) + i * self.FRAMES) / FPS
            x = (0.9 * np.sin(2 * np.pi * 100 * t)).astype(np.float64)[:, None]
            out = bf.forward(x)
        self.assertLess(np.abs(out).max(), 0.1,
                        "Highpass failed to attenuate 100 Hz signal")

    def test_no_nan_or_inf_in_output(self):
        bf = _make_butter(freq=800)
        bf.frames = 512
        x = _sine(440, 512)[:, None]
        for _ in range(20):
            out = bf.forward(x)
            self.assertTrue(np.all(np.isfinite(out)),
                            "Filter output contains NaN or Inf")

    def test_zero_input_returns_zero(self):
        """Filtering silence must produce silence (no DC injection)."""
        bf = _make_butter(freq=1000)
        bf.frames = 512
        x = np.zeros((512, 1))
        bf.forward(x)
        out = bf.forward(x)
        np.testing.assert_allclose(out, 0, atol=1e-6,
                                   err_msg="Zero input produced non-zero output")

    def test_output_shape_2d_input(self):
        bf = _make_butter(freq=1000)
        bf.frames = 512
        x = _sine(440, 512)[:, None]
        out = bf.forward(x)
        self.assertEqual(out.shape, (512, 1))

    def test_output_shape_consistent_across_buffer_sizes(self):
        for n in [64, 256, 441, 443, 444, 512, 1024]:
            bf = _make_butter(freq=1000)
            bf.frames = n
            x = np.zeros((n, 1))
            out = bf.forward(x)
            self.assertEqual(out.shape, (n, 1),
                             f"Output shape wrong for buffer size {n}")


class TestButterFilterStateManagement(unittest.TestCase):

    def test_reset_then_replay_same_freq(self):
        """reset() + replay must never raise."""
        bf = _make_butter(freq=1000)
        bf.frames = 512
        x = _sine(440, 512)[:, None]
        for _ in range(5):
            bf.reset()
            for _ in range(5):
                out = bf.forward(x)
                self.assertEqual(out.shape, (512, 1))

    def test_reset_then_replay_different_freqs(self):
        """
        Regression for TB303 multi-note loop:
        reset → new note freq → forward() sequence must never corrupt shape.
        """
        bf = _make_butter(freq=1000)
        bf.frames = 512
        note_freqs = [220.0, 246.9, 261.6, 293.7, 329.6, 349.2]
        for freq_hz in note_freqs:
            bf.reset()
            x = _sine(freq_hz, 512)[:, None]
            for i in range(8):
                try:
                    out = bf.forward(x)
                except Exception as e:
                    self.fail(
                        f"forward() raised on {freq_hz} Hz call {i}: {e}"
                    )
                self.assertEqual(out.shape, (512, 1))

    def test_key_modulation_causes_crossfade_repeatedly(self):
        """
        Simulate TB303: key_modulation changes freq every frame,
        triggering the crossfade path on nearly every call.
        Must never raise or produce wrong shapes.
        """
        bf = _make_butter(freq=1000)
        bf.frames = 512
        x = _sine(220, 512)[:, None]

        for rep in range(3):
            bf.reset()
            for semitone_mod in np.linspace(0, 120, 15):
                mod = np.full((512, 1), semitone_mod)
                try:
                    out = bf.forward(x, key_modulation=mod)
                except Exception as e:
                    self.fail(f"rep={rep} mod={semitone_mod:.1f}: {e}")
                self.assertEqual(out.shape, (512, 1))

    def test_tail_chunk_size_does_not_break_filter(self):
        """
        Audio callback delivers a smaller tail chunk at end of note.
        Filter must handle arbitrary frame sizes even mid-note.
        """
        bf = _make_butter(freq=1000)
        # Process full-size chunks then a tiny tail
        bf.forward(np.zeros((512, 1)))
        bf.forward(np.zeros((512, 1)))
        for tail in [1, 7, 43, 128, 443, 444]:
            out = bf.forward(np.zeros((tail, 1)))
            self.assertEqual(out.shape, (tail, 1),
                             f"Tail chunk size {tail} produced wrong shape")

    def test_filter_state_z_shape_stable_after_freq_change(self):
        """_z shape must not change after a frequency transition."""
        bf = _make_butter(freq=500)
        bf.frames = 512
        x = np.zeros((512, 1))
        bf.forward(x)
        z_before = np.asarray(bf._z).shape
        bf.freq = 800
        bf.forward(x)                   # crossfade
        z_after = np.asarray(bf._z).shape
        self.assertEqual(z_before, z_after,
                         "Filter _z shape changed after freq transition")


class TestButterFilterGetWp(unittest.TestCase):

    def test_lowpass_returns_positive_scalar(self):
        bf = _make_butter(freq=1000, btype="lowpass")
        wp = bf.get_wp(1000)
        self.assertIsInstance(wp, (int, float))
        self.assertGreater(wp, 0)
        self.assertLess(wp, FPS // 2)

    def test_highpass_returns_positive_scalar(self):
        bf = _make_butter(freq=1000, btype="highpass")
        wp = bf.get_wp(1000)
        self.assertIsInstance(wp, (int, float))
        self.assertGreater(wp, 0)

    def test_bandpass_returns_ordered_tuple(self):
        bf = _make_butter(freq=1000, btype="bandpass", bandwidth=400)
        wp = bf.get_wp(1000)
        self.assertIsInstance(wp, tuple)
        self.assertEqual(len(wp), 2)
        self.assertLess(wp[0], wp[1])

    def test_clamps_above_nyquist(self):
        bf = _make_butter(freq=25000, btype="lowpass")
        wp = bf.get_wp(25000)
        self.assertLess(wp, FPS // 2)


if __name__ == "__main__":
    unittest.main()
