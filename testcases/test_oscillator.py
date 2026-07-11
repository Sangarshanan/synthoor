import unittest
import numpy as np

from synthoor.oscillator import (
    Oscillator,
    get_radians,
    get_sine_wave,
    get_triangle_wave,
    get_sawtooth_wave,
    get_square_wave,
    get_sawtooth_cycle,
)
from synthoor.config import FPS


FRAMES = 512


class TestGetRadians(unittest.TestCase):

    def test_output_length_equals_frames(self):
        for n in [64, 128, 256, 512, 1024]:
            r, _ = get_radians(440.0, start=0.0, frames=n)
            self.assertEqual(len(r), n, f"Length mismatch for frames={n}")

    def test_output_is_finite(self):
        r, _ = get_radians(440.0, start=0.0, frames=FRAMES)
        self.assertTrue(np.all(np.isfinite(r)))

    def test_next_start_is_scalar(self):
        """next_start must be a scalar (not an array) so phase stays scalar."""
        _, ns = get_radians(440.0, start=0.0, frames=FRAMES)
        self.assertEqual(np.asarray(ns).ndim, 0,
                         f"next_start is not scalar: shape={np.asarray(ns).shape}")

    def test_phase_continuity(self):
        """Second call with start=next_start must continue the phase ramp."""
        freq = 440.0
        r1, ns1 = get_radians(freq, start=0.0, frames=64)
        r2, _ = get_radians(freq, start=ns1, frames=64)
        step = 2 * np.pi / FPS * freq
        self.assertAlmostEqual(float(r2[0] - r1[-1]), step, places=8)

    def test_monotone_increasing(self):
        """Radians must increase monotonically for constant frequency."""
        r, _ = get_radians(440.0, start=0.0, frames=FRAMES)
        diffs = np.diff(r)
        self.assertTrue(np.all(diffs > 0), "Radians are not monotonically increasing")

    def test_numpy_scalar_start_does_not_break_concatenation(self):
        """
        After one call, next_start is a numpy scalar (0-d).
        A second call with that start must not raise
        'zero-dimensional arrays cannot be concatenated'.
        """
        _, ns = get_radians(220.0, start=0.0, frames=FRAMES)
        # ns is np.float64 (0-d array)
        try:
            r2, _ = get_radians(220.0, start=ns, frames=FRAMES)
        except ValueError as e:
            self.fail(f"0-d start raised ValueError: {e}")
        self.assertEqual(len(r2), FRAMES)

    def test_different_frequencies_produce_different_rates(self):
        r440, _ = get_radians(440.0, start=0.0, frames=FRAMES)
        r880, _ = get_radians(880.0, start=0.0, frames=FRAMES)
        step440 = float(r440[1] - r440[0])
        step880 = float(r880[1] - r880[0])
        self.assertAlmostEqual(step880 / step440, 2.0, places=6)


class TestWaveGenerators(unittest.TestCase):

    def _check_wave(self, fn, freq=220.0, frames=FRAMES, amp_max=1.1, **kw):
        a, phase = fn(freq, phase=0.0, frames=frames, **kw)
        self.assertEqual(len(a), frames, f"{fn.__name__} length wrong")
        self.assertTrue(np.all(np.isfinite(a)), f"{fn.__name__} contains inf/nan")
        self.assertLessEqual(np.abs(a).max(), amp_max,
                             f"{fn.__name__} amplitude out of range")
        return a, phase

    def test_sine_shape_and_bounds(self):
        a, _ = self._check_wave(get_sine_wave, amp_max=1.001)
        # Sine must oscillate — not flat
        self.assertGreater(a.max() - a.min(), 1.0)

    def test_sine_is_in_minus1_to_1(self):
        a, _ = get_sine_wave(440.0, phase=0.0, frames=FRAMES)
        self.assertTrue(np.all(a >= -1.0 - 1e-9))
        self.assertTrue(np.all(a <= 1.0 + 1e-9))

    def test_triangle_shape_and_bounds(self):
        self._check_wave(get_triangle_wave, amp_max=1.001)

    def test_sawtooth_shape(self):
        a, _ = self._check_wave(get_sawtooth_wave, amp_max=1.2)
        self.assertGreater(a.max() - a.min(), 1.0)

    def test_square_shape(self):
        self._check_wave(get_square_wave, amp_max=1.5)

    def test_square_with_duty_25(self):
        self._check_wave(get_square_wave, duty=0.25, amp_max=1.5)

    def test_phase_is_scalar_after_call(self):
        """phase_out must be a scalar so Oscillator.phase stays scalar."""
        for fn in (get_sine_wave, get_triangle_wave, get_sawtooth_wave, get_square_wave):
            _, phase_out = fn(440.0, phase=0.0, frames=FRAMES)
            self.assertEqual(np.asarray(phase_out).ndim, 0,
                             f"{fn.__name__} returned non-scalar phase: "
                             f"shape={np.asarray(phase_out).shape}")

    def test_phase_continuation_all_waves(self):
        """Second call starting from phase_out of first must continue smoothly."""
        for fn in (get_sine_wave, get_triangle_wave, get_sawtooth_wave):
            a1, ph1 = fn(220.0, phase=0.0, frames=64)
            a2, _ = fn(220.0, phase=ph1, frames=64)
            combined = np.concatenate([a1, a2])
            # No sudden jump at the join
            jump = abs(float(combined[63]) - float(combined[64]))
            self.assertLess(jump, 0.5,
                            f"{fn.__name__} has a phase discontinuity: jump={jump:.4f}")

    def test_different_frame_sizes_produce_correct_length(self):
        for fn in (get_sine_wave, get_sawtooth_wave, get_square_wave):
            for n in [64, 128, 256, 512, 1024]:
                a, _ = fn(440.0, phase=0.0, frames=n)
                self.assertEqual(len(a), n,
                                 f"{fn.__name__} wrong length for frames={n}")


class TestSawtoothCycle(unittest.TestCase):

    def test_same_args_returns_same_object(self):
        c1 = get_sawtooth_cycle(4, size=256)
        c2 = get_sawtooth_cycle(4, size=256)
        self.assertIs(c1, c2, "Cache did not return the same object")

    def test_length_equals_size(self):
        for size in [256, 512, 1024]:
            c = get_sawtooth_cycle(4, size=size)
            self.assertEqual(c.shape[0], size)

    def test_different_harmonics_produce_different_cycles(self):
        c1 = get_sawtooth_cycle(1, size=256)
        c8 = get_sawtooth_cycle(8, size=256)
        self.assertFalse(np.allclose(c1, c8),
                         "Different harmonic counts produced identical cycles")


class TestOscillator(unittest.TestCase):

    def _make(self, shape="sine", freq=440.0, frames=FRAMES):
        osc = Oscillator(shape=shape, freq=freq)
        osc.frames = frames
        return osc

    def test_all_shapes_output_2d(self):
        """Oscillator.forward() must always return (frames, 1)."""
        for shape in ("sine", "tri", "saw", "square"):
            osc = self._make(shape=shape)
            out = osc.forward()
            self.assertEqual(out.shape, (FRAMES, 1),
                             f"shape={shape} returned {out.shape}")

    def test_output_is_finite(self):
        for shape in ("sine", "tri", "saw", "square"):
            osc = self._make(shape=shape)
            out = osc.forward()
            self.assertTrue(np.all(np.isfinite(out)),
                            f"{shape} oscillator output contains inf/nan")

    def test_sine_amplitude_in_range(self):
        osc = self._make(shape="sine")
        out = osc.forward()
        self.assertTrue(np.all(out >= -1.0 - 1e-9))
        self.assertTrue(np.all(out <= 1.0 + 1e-9))

    def test_phase_is_scalar_after_forward(self):
        """
        Oscillator.phase must remain a scalar after forward().
        If it becomes an array, subsequent get_radians calls could fail.
        """
        osc = self._make(shape="saw")
        osc.forward()
        self.assertEqual(np.asarray(osc.phase).ndim, 0,
                         f"phase became non-scalar: shape={np.asarray(osc.phase).shape}")

    def test_phase_persists_across_calls(self):
        """Phase must advance on each call (not reset)."""
        osc = self._make(shape="sine")
        osc.forward()
        phase1 = float(osc.phase)
        osc.forward()
        phase2 = float(osc.phase)
        self.assertNotEqual(phase1, phase2, "Phase did not advance")

    def test_reset_does_not_zero_phase(self):
        """
        BUG DOCUMENTATION: Sound.reset() does NOT reset self.phase to 0;
        it only clears index/_done/_a0. Phase persists across reset().
        This test documents the current behaviour. If reset() is changed
        to zero phase in future, update this test to assert osc.phase == 0.0.
        """
        osc = self._make(shape="sine")
        osc.forward()
        phase_after_forward = float(osc.phase)
        osc.reset()
        # phase is NOT zeroed — it retains the value it had after forward()
        self.assertEqual(float(osc.phase), phase_after_forward,
                         "Expected phase to be unchanged by reset() "
                         f"(phase_after_forward={phase_after_forward})")

    def test_reset_then_forward_works(self):
        """After reset(), forward() must still run without error."""
        osc = self._make(shape="sine")
        osc.forward()
        osc.reset()
        osc.frames = FRAMES
        out = osc.forward()
        self.assertEqual(out.shape, (FRAMES, 1))
        self.assertTrue(np.all(np.isfinite(out)))

    def test_call_sets_freq_and_returns_2d(self):
        """osc(freq=X) must set osc.freq and return (frames, 1)."""
        osc = self._make()
        osc.frames = FRAMES
        out = osc(freq=330.0)
        self.assertAlmostEqual(osc.freq, 330.0)
        self.assertEqual(np.asarray(out).shape, (FRAMES, 1))

    def test_fm_key_modulation_path(self):
        """key_modulation kwarg must be accepted and not raise."""
        osc = self._make(shape="saw")
        osc.frames = FRAMES
        mod = np.zeros(FRAMES)     # zero modulation → same as no FM
        out = osc.forward(key_modulation=mod)
        self.assertEqual(out.shape, (FRAMES, 1))

    def test_fm_modulation_changes_output(self):
        """Non-zero key_modulation must produce a different output than zero."""
        osc_ref = self._make(shape="sine", freq=220.0)
        osc_fm  = self._make(shape="sine", freq=220.0)
        osc_ref.frames = FRAMES
        osc_fm.frames  = FRAMES

        out_ref = osc_ref.forward()
        out_fm  = osc_fm.forward(key_modulation=np.full(FRAMES, 12.0))
        self.assertFalse(np.allclose(out_ref, out_fm),
                         "FM modulation had no effect on output")

    def test_multiple_resets_do_not_corrupt_output(self):
        """reset() then forward() must work correctly many times."""
        osc = self._make(shape="saw")
        for _ in range(5):
            osc.reset()
            osc.frames = FRAMES
            out = osc.forward()
            self.assertEqual(out.shape, (FRAMES, 1))
            self.assertTrue(np.all(np.isfinite(out)))


if __name__ == "__main__":
    unittest.main()
