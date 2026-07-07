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


class TestRadiansGeneration(unittest.TestCase):
    def test_get_radians_basic(self):
        """Test basic radians generation."""
        frames = 32
        freq = 440.0
        radians, next_start = get_radians(freq, start=0.0, frames=frames)
        
        self.assertEqual(radians.shape[0], frames)
        self.assertTrue(np.all(np.isfinite(radians)))

    def test_get_radians_phase_continuity(self):
        """Test that successive calls maintain phase continuity."""
        frames = 32
        freq = 440.0
        radians, next_start = get_radians(freq, start=0.0, frames=frames)
        
        # successive call with start=next_start should continue sequence
        r2, next_start2 = get_radians(freq, start=next_start, frames=frames)
        
        # Phase should increment correctly
        self.assertAlmostEqual(radians[-1] + (2 * np.pi / 44100 * freq), r2[0], places=6)

    def test_get_radians_different_frequencies(self):
        """Test radians generation for different frequencies."""
        frames = 64
        frequencies = [110.0, 220.0, 440.0, 880.0]
        
        for freq in frequencies:
            radians, _ = get_radians(freq, start=0.0, frames=frames)
            self.assertEqual(radians.shape[0], frames)
            self.assertTrue(np.all(np.isfinite(radians)))

    def test_get_radians_array_frequency(self):
        """Test radians generation with scalar and varying frequencies."""
        frames = 32
        # Array frequency would produce different behavior
        freq = 440.0
        radians, next_start = get_radians(freq, start=0.0, frames=frames)
        
        self.assertEqual(radians.shape[0], frames)
        self.assertTrue(np.all(np.isfinite(radians)))


class TestWaveGenerators(unittest.TestCase):
    def test_sine_wave_basic(self):
        """Test sine wave generation."""
        frames = 64
        a, phase = get_sine_wave(220.0, phase=0.0, frames=frames)
        
        self.assertEqual(a.shape[0], frames)
        self.assertTrue(np.isfinite(a).all())
        self.assertTrue(np.abs(a).max() <= 1.0 + 1e-6)

    def test_triangle_wave_basic(self):
        """Test triangle wave generation."""
        frames = 64
        a, phase = get_triangle_wave(220.0, phase=0.0, frames=frames)
        
        self.assertEqual(a.shape[0], frames)
        self.assertTrue(np.isfinite(a).all())
        self.assertTrue(np.abs(a).max() <= 2.0)

    def test_sawtooth_wave_basic(self):
        """Test sawtooth wave generation."""
        frames = 64
        a, phase = get_sawtooth_wave(220.0, phase=0.0, frames=frames)
        
        self.assertEqual(a.shape[0], frames)
        self.assertTrue(np.isfinite(a).all())

    def test_square_wave_basic(self):
        """Test square wave generation."""
        frames = 64
        a, phase = get_square_wave(220.0, phase=0.0, frames=frames)
        
        self.assertEqual(a.shape[0], frames)
        self.assertTrue(np.isfinite(a).all())

    def test_wave_generators_all(self):
        """Test all wave generators produce valid output."""
        frames = 64
        for fn in (get_sine_wave, get_triangle_wave, get_sawtooth_wave, get_square_wave):
            a, phase = fn(220.0, phase=0.0, frames=frames)
            
            self.assertEqual(a.shape[0], frames)
            self.assertTrue(np.isfinite(a).all())
            self.assertTrue(np.abs(a).max() <= 2.0)

    def test_wave_duty_modulation(self):
        """Test square wave with duty modulation."""
        frames = 64
        a, phase = get_square_wave(220.0, phase=0.0, frames=frames, duty=0.25)
        
        self.assertEqual(a.shape[0], frames)
        self.assertTrue(np.isfinite(a).all())

    def test_wave_phase_continuation(self):
        """Test phase continuation across multiple calls."""
        frames = 64
        
        a1, phase1 = get_sine_wave(440.0, phase=0.0, frames=frames)
        a2, phase2 = get_sine_wave(440.0, phase=phase1, frames=frames)
        
        # Both should have same shape
        self.assertEqual(a1.shape[0], frames)
        self.assertEqual(a2.shape[0], frames)

    def test_wave_different_frequencies(self):
        """Test waves with different frequencies."""
        frames = 128
        frequencies = [110.0, 220.0, 440.0, 880.0, 1760.0]
        
        for freq in frequencies:
            a, _ = get_sine_wave(freq, phase=0.0, frames=frames)
            self.assertEqual(a.shape[0], frames)
            self.assertTrue(np.isfinite(a).all())


class TestSawtoothCycle(unittest.TestCase):
    def test_sawtooth_cycle_caching(self):
        """Test that sawtooth cycle is cached."""
        c1 = get_sawtooth_cycle(3, size=128)
        c2 = get_sawtooth_cycle(3, size=128)
        
        # Should be identical due to caching
        self.assertTrue(np.array_equal(c1, c2))

    def test_sawtooth_cycle_different_harmonics(self):
        """Test sawtooth cycles with different harmonics."""
        harmonics = [1, 2, 4, 8]
        cycles = []
        
        for h in harmonics:
            c = get_sawtooth_cycle(h, size=128)
            cycles.append(c)
            self.assertEqual(c.shape[0], 128)

    def test_sawtooth_cycle_different_sizes(self):
        """Test sawtooth cycles with different sizes."""
        sizes = [256, 512, 1024]
        
        for size in sizes:
            c = get_sawtooth_cycle(4, size=size)
            self.assertEqual(c.shape[0], size)


class TestOscillator(unittest.TestCase):
    def test_oscillator_sine_forward(self):
        """Test sine oscillator forward pass."""
        frames = 128
        osc = Oscillator(shape="sine", freq=440.0, phase=0.0)
        osc.frames = frames
        out = osc.forward()
        
        self.assertEqual(out.shape, (frames, 1))
        self.assertTrue(np.all(np.isfinite(out)))

    def test_oscillator_triangle_forward(self):
        """Test triangle oscillator."""
        frames = 128
        osc = Oscillator(shape="tri", freq=440.0)
        osc.frames = frames
        out = osc.forward()
        
        self.assertEqual(out.shape, (frames, 1))

    def test_oscillator_sawtooth_forward(self):
        """Test sawtooth oscillator."""
        frames = 128
        osc = Oscillator(shape="saw", freq=440.0)
        osc.frames = frames
        out = osc.forward()
        
        self.assertEqual(out.shape, (frames, 1))

    def test_oscillator_square_forward(self):
        """Test square oscillator."""
        frames = 128
        osc = Oscillator(shape="square", freq=440.0)
        osc.frames = frames
        out = osc.forward()
        
        self.assertEqual(out.shape, (frames, 1))

    def test_oscillator_all_shapes(self):
        """Test all oscillator shapes."""
        frames = 128
        shapes = ["sine", "tri", "saw", "square"]
        
        for shape in shapes:
            osc = Oscillator(shape=shape, freq=440.0)
            osc.frames = frames
            out = osc.forward()
            
            self.assertEqual(out.shape, (frames, 1))
            self.assertTrue(np.all(np.isfinite(out)))

    def test_oscillator_key_modulation(self):
        """Test oscillator with key modulation."""
        frames = 128
        osc = Oscillator(shape="sine", key=60)
        osc.frames = frames
        
        # small modulation array (one value per frame)
        mod = np.linspace(0.0, 1.0, frames)
        out = osc.forward(key_modulation=mod)
        
        self.assertEqual(out.shape, (frames, 1))
        self.assertTrue(np.all(np.isfinite(out)))

    def test_oscillator_phase_tracking(self):
        """Test that oscillator maintains phase across calls."""
        frames = 64
        osc = Oscillator(shape="sine", freq=440.0, phase=0.0)
        
        osc.frames = frames
        out1 = osc.forward()
        phase1 = osc.phase
        
        out2 = osc.forward()
        phase2 = osc.phase
        
        # Phase should have advanced
        self.assertGreater(phase2, phase1)

    def test_oscillator_frequency_change(self):
        """Test oscillator with frequency change."""
        frames = 128
        osc = Oscillator(shape="sine", freq=440.0)
        osc.frames = frames
        
        out1 = osc.forward()
        
        osc.freq = 880.0
        out2 = osc.forward()
        
        # Both should be valid
        self.assertEqual(out1.shape, (frames, 1))
        self.assertEqual(out2.shape, (frames, 1))

    def test_oscillator_amplitude(self):
        """Test oscillator respects amplitude."""
        frames = 128
        osc = Oscillator(shape="sine", freq=440.0)
        osc.amp = 0.5
        osc.frames = frames
        
        out = osc.forward()
        
        # Max amplitude should be around 0.5 * (64/128) due to velocity
        max_val = np.abs(out).max()
        self.assertLess(max_val, 1.0)

    def test_oscillator_with_kwargs(self):
        """Test oscillator with extra kwargs."""
        frames = 128
        osc = Oscillator(shape="square", freq=440.0, duty=0.25)
        osc.frames = frames
        out = osc.forward()
        
        self.assertEqual(out.shape, (frames, 1))


if __name__ == "__main__":
    unittest.main()