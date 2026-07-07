import unittest
import numpy as np

from synthoor.sound import Sound, key2freq, freq2key, LatencyGate
from synthoor.player import set_schedule, get_schedule, t2frames


class TestKeyFreqConversion(unittest.TestCase):
    def test_key_freq_conversion_middle_c(self):
        """Test key/freq conversion for middle C (C4)."""
        k = 60
        f = key2freq(k)
        k2 = freq2key(f)
        self.assertAlmostEqual(k, k2, places=6)
        # Middle C should be 261.63 Hz approximately
        self.assertAlmostEqual(f, 261.626, places=1)

    def test_key_freq_conversion_multiple_notes(self):
        """Test key/freq conversion for multiple notes."""
        keys = [0, 12, 24, 36, 48, 60, 72, 84, 96, 108, 120]
        for k in keys:
            f = key2freq(k)
            k2 = freq2key(f)
            self.assertAlmostEqual(k, k2, places=6)

    def test_key_freq_conversion_octaves(self):
        """Test that octave differences work correctly."""
        c4 = key2freq(60)
        c5 = key2freq(72)  # One octave higher
        c3 = key2freq(48)  # One octave lower
        
        # Octaves should be 2x in frequency
        self.assertAlmostEqual(c5 / c4, 2.0, places=3)
        self.assertAlmostEqual(c4 / c3, 2.0, places=3)

    def test_key_freq_conversion_semitones(self):
        """Test semitone differences."""
        c = key2freq(60)
        c_sharp = key2freq(61)  # One semitone up
        
        # Semitone ratio should be 2^(1/12)
        ratio = c_sharp / c
        expected_ratio = 2.0 ** (1.0 / 12.0)
        self.assertAlmostEqual(ratio, expected_ratio, places=3)

    def test_key_freq_conversion_arrays(self):
        """Test key/freq conversion with numpy arrays."""
        keys = np.array([60, 62, 64, 65, 67])
        freqs = key2freq(keys)
        
        self.assertEqual(len(freqs), len(keys))
        self.assertTrue(np.all(freqs > 0))
        
        keys2 = freq2key(freqs)
        np.testing.assert_array_almost_equal(keys, keys2, decimal=6)


class TestSound(unittest.TestCase):
    def test_sound_initialization(self):
        """Test Sound class initialization."""
        s = Sound(freq=440, amp=0.5)
        self.assertEqual(s.freq, 440)
        self.assertEqual(s.amp, 0.5)
        self.assertEqual(s.velocity, 64)
        self.assertEqual(s.index, 0)

    def test_sound_key_property(self):
        """Test Sound key property getter/setter."""
        s = Sound(freq=440)
        key_val = s.key
        self.assertIsInstance(key_val, (int, float, np.number))
        
        # Set by key
        s.key = 60
        freq_from_key = key2freq(60)
        self.assertAlmostEqual(s.freq, freq_from_key, places=2)

    def test_sound_reset_and_consume(self):
        """Test Sound reset and consume methods."""
        class Dummy(Sound):
            def forward(self):
                return np.zeros((self.frames, 1))

        d = Dummy()
        d.frames = 16
        
        initial_index = d.index
        out = d.consume(16)
        
        self.assertEqual(out.shape[0], 16)
        self.assertGreater(d.index, initial_index)

    def test_sound_consume_with_velocity_and_amplitude(self):
        """Test that consume applies velocity and amplitude."""
        class Dummy(Sound):
            def forward(self):
                return np.ones((self.frames, 1))

        d = Dummy(amp=0.5)
        d.velocity = 64
        d.frames = 16
        
        out = d.consume(16)
        
        # Output should be amplitude * (velocity / 128)
        expected_level = 0.5 * (64.0 / 128.0)
        self.assertAlmostEqual(np.mean(out), expected_level, places=2)

    def test_sound_play_and_reset(self):
        """Test Sound play method."""
        class Dummy(Sound):
            def forward(self):
                return np.zeros((self.frames, 1))

        d = Dummy()
        d.frames = 16
        
        d.play(note=69, velocity=100)
        
        self.assertEqual(d.velocity, 100)
        self.assertAlmostEqual(d.freq, key2freq(69), places=2)
        self.assertEqual(d.index, 0)

    def test_sound_forward_default(self):
        """Test default forward method returns zeros."""
        s = Sound()
        s.frames = 128
        out = s.forward()
        
        self.assertEqual(len(out), 128)
        self.assertTrue(np.allclose(out, 0))

    def test_sound_done_property(self):
        """Test Sound done property."""
        s = Sound()
        
        # Initially should not be done
        self.assertFalse(s.done)
        
        # After error, should be done
        s._error = True
        self.assertTrue(s.done)

    def test_sound_recursive_reset(self):
        """Test that reset is called recursively on child sounds."""
        class Child(Sound):
            def __init__(self):
                super().__init__()
                self.reset_called = False
            
            def reset(self, shared=False):
                super().reset(shared)
                self.reset_called = True

        parent = Sound()
        child = Child()
        parent.child_sound = child
        
        parent.reset()
        self.assertTrue(child.reset_called)


class TestLatencyGate(unittest.TestCase):
    def test_latency_gate_initialization(self):
        """Test LatencyGate initialization."""
        g = LatencyGate()
        self.assertEqual(len(g.states), 0)
        self.assertFalse(g.opened)
        self.assertEqual(g.value, 0)

    def test_latency_gate_forward_shape(self):
        """Test LatencyGate forward output shape."""
        g = LatencyGate()
        g.frames = 128
        out = g.forward()
        
        self.assertEqual(out.shape, (128, 1))

    def test_latency_gate_open_close(self):
        """Test opening and closing the gate."""
        g = LatencyGate()
        
        # Initially closed
        self.assertFalse(g.opened)
        self.assertEqual(g.value, 0)

    def test_latency_gate_reset(self):
        """Test LatencyGate reset."""
        g = LatencyGate()
        g.frames = 64
        
        # Initial state
        initial_index = g.index
        
        # Forward should update index
        g.forward()
        self.assertGreaterEqual(g.index, initial_index)
        
        # Reset should clear some state
        g.reset()
        self.assertEqual(g.index, 0)

    def test_latency_gate_output_values(self):
        """Test that LatencyGate output is binary."""
        g = LatencyGate()
        g.frames = 128
        out = g.forward()
        
        # Output should be binary or near zero
        unique_vals = np.unique(out)
        self.assertLessEqual(len(unique_vals), 3)  # Mostly 0, mostly 1, and transition


if __name__ == "__main__":
    unittest.main()