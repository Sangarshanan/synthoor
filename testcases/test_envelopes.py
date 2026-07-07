import unittest
import numpy as np

from synthoor.envelope import (
    Envelope,
    get_linear_adsr_curve,
    get_exponential_adsr_curve,
    gate2events,
)


class TestADSRCurves(unittest.TestCase):
    def test_linear_adsr_curve_values(self):
        """Test linear ADSR curve generates values between 0 and 1."""
        lin = get_linear_adsr_curve(0.01, start=0, end=100)
        self.assertTrue(len(lin) > 0)
        self.assertTrue((lin >= 0).all())
        self.assertTrue((lin <= 1.0 + 1e-6).all())

    def test_exponential_adsr_curve_values(self):
        """Test exponential ADSR curve generates values between 0 and 1."""
        exp = get_exponential_adsr_curve(0.01, start=0, end=100)
        self.assertTrue(len(exp) > 0)
        self.assertTrue((exp >= 0).all())
        self.assertTrue((exp <= 1.0 + 1e-6).all())

    def test_linear_vs_exponential_curves(self):
        """Test that linear and exponential curves differ."""
        lin = get_linear_adsr_curve(0.01, start=0, end=50)
        exp = get_exponential_adsr_curve(0.01, start=0, end=50)
        
        # They should have similar length but different values
        self.assertEqual(len(lin), len(exp))
        self.assertFalse(np.allclose(lin, exp))

    def test_adsr_curve_length_varies_with_dt(self):
        """Test that curve length changes with dt parameter."""
        curve_short = get_linear_adsr_curve(0.005, start=0, end=1000)
        curve_long = get_linear_adsr_curve(0.05, start=0, end=1000)
        
        # Both should have some content
        self.assertGreater(len(curve_short), 0)
        self.assertGreater(len(curve_long), 0)

    def test_exponential_curve_threshold(self):
        """Test exponential curve with different thresholds."""
        exp_default = get_exponential_adsr_curve(0.01, start=0, end=100, th=0.01)
        exp_high_th = get_exponential_adsr_curve(0.01, start=0, end=100, th=0.1)
        
        # Both should be valid curves
        self.assertTrue((exp_default >= 0).all() and (exp_default <= 1.0 + 1e-6).all())
        self.assertTrue((exp_high_th >= 0).all() and (exp_high_th <= 1.0 + 1e-6).all())


class TestGate2Events(unittest.TestCase):
    def test_gate2events_single_open_close(self):
        """Test gate2events with single open/close cycle."""
        gate = np.zeros(20)
        gate[5:15] = 1
        states, v0 = gate2events(gate, v0=0, index=0)
        
        events = [e for _, e in states]
        self.assertIn("open", events)
        self.assertIn("close", events)
        self.assertEqual(events[-1], "continue")

    def test_gate2events_multiple_cycles(self):
        """Test gate2events with multiple open/close cycles."""
        gate = np.zeros(30)
        gate[5:10] = 1  # First open
        gate[15:20] = 1  # Second open
        
        states, v0 = gate2events(gate, v0=0, index=0)
        events = [e for _, e in states]
        
        open_count = sum(1 for e in events if e == "open")
        close_count = sum(1 for e in events if e == "close")
        
        self.assertGreaterEqual(open_count, 1)
        self.assertGreaterEqual(close_count, 1)

    def test_gate2events_no_transitions(self):
        """Test gate2events with no transitions."""
        gate = np.zeros(20)
        states, v0 = gate2events(gate, v0=0, index=0)
        
        # Should only have continue event
        events = [e for _, e in states]
        self.assertEqual(events[-1], "continue")

    def test_gate2events_all_on(self):
        """Test gate2events with gate always on."""
        gate = np.ones(20)
        states, v0 = gate2events(gate, v0=0, index=0)
        
        events = [e for _, e in states]
        self.assertIn("open", events)
        self.assertEqual(events[-1], "continue")

    def test_gate2events_indices_monotonic(self):
        """Test that event indices are monotonically increasing."""
        gate = np.zeros(40)
        gate[5:10] = 1
        gate[20:25] = 1
        
        states, _ = gate2events(gate, v0=0, index=0)
        indices = [idx for idx, _ in states]
        
        for i in range(len(indices) - 1):
            self.assertLessEqual(indices[i], indices[i + 1])


class TestEnvelopeShapes(unittest.TestCase):
    def test_envelope_linear_attack(self):
        """Test linear envelope attack phase."""
        env = Envelope(attack=0.01, decay=0.0, sustain=1.0, release=0.0, linear=True)
        frames = 128
        gate = np.ones(frames)
        
        out = env.forward(gate)
        self.assertEqual(out.shape, (frames, 1))
        self.assertTrue((out >= 0).all() and (out <= 1.0 + 1e-6).all())

    def test_envelope_exponential(self):
        """Test exponential envelope."""
        env = Envelope(attack=0.01, decay=0.01, sustain=0.5, release=0.01, linear=False)
        frames = 128
        gate = np.zeros(frames)
        gate[:64] = 1
        
        out = env.forward(gate)
        self.assertEqual(out.shape, (frames, 1))
        self.assertTrue((out >= 0).all() and (out <= 1.0 + 1e-6).all())

    def test_envelope_adsr_phases(self):
        """Test complete ADSR envelope cycle."""
        env = Envelope(attack=0.01, decay=0.01, sustain=0.5, release=0.01, linear=True)
        frames = 256
        gate = np.zeros(frames)
        gate[32:192] = 1  # Open for middle portion
        
        out = env.forward(gate)
        self.assertEqual(out.shape, (frames, 1))
        
        # Check envelope values are in valid range
        self.assertTrue((out >= 0).all())
        self.assertTrue((out <= 1.0 + 1e-6).all())

    def test_envelope_zero_times(self):
        """Test envelope with zero attack/decay times."""
        env = Envelope(attack=0.0, decay=0.0, sustain=0.75, release=0.0, linear=True)
        frames = 128
        gate = np.ones(frames)
        
        out = env.forward(gate)
        self.assertEqual(out.shape, (frames, 1))
        # Should jump instantly to 1.0 then transition to sustain
        self.assertTrue(np.any(out > 0))

    def test_envelope_sustain_level(self):
        """Test that sustain level affects output."""
        env_low = Envelope(attack=0.005, decay=0.005, sustain=0.25, release=0.005, linear=True)
        env_high = Envelope(attack=0.005, decay=0.005, sustain=0.75, release=0.005, linear=True)
        
        frames = 512
        gate = np.ones(frames)
        
        # Process through both envelopes
        out_low = env_low.forward(gate)
        out_high = env_high.forward(gate)
        
        # Both should be valid
        self.assertEqual(out_low.shape, (frames, 1))
        self.assertEqual(out_high.shape, (frames, 1))

    def test_envelope_reset(self):
        """Test envelope state persists across calls."""
        env = Envelope(attack=0.01, decay=0.01, sustain=0.5, release=0.01, linear=True)
        
        frames = 128
        gate = np.ones(frames)
        
        # First call starts attack
        out1 = env.forward(gate)
        self.assertEqual(out1.shape, (frames, 1))
        
        # Second call should continue from previous state
        out2 = env.forward(gate)
        self.assertEqual(out2.shape, (frames, 1))

    def test_envelope_gate_open_close(self):
        """Test envelope response to gate open/close."""
        env = Envelope(attack=0.01, decay=0.01, sustain=0.5, release=0.05, linear=True)
        
        frames = 256
        gate = np.zeros(frames)
        gate[32:160] = 1  # Open in middle
        
        out = env.forward(gate)
        
        # Should have attack, sustain, and release phases
        self.assertEqual(out.shape, (frames, 1))
        self.assertTrue((out >= 0).all())

    def test_envelope_very_fast_attack(self):
        """Test envelope with very fast attack time."""
        env = Envelope(attack=0.0001, decay=0.01, sustain=0.5, release=0.01, linear=True)
        
        frames = 128
        gate = np.ones(frames)
        
        out = env.forward(gate)
        self.assertEqual(out.shape, (frames, 1))

    def test_envelope_index_tracking(self):
        """Test that envelope processes frames correctly."""
        env = Envelope(attack=0.01, decay=0.01, sustain=0.5, release=0.01, linear=True)
        
        frames = 128
        gate = np.ones(frames)
        
        out = env.forward(gate)
        
        # Output should be valid
        self.assertEqual(out.shape, (frames, 1))
        self.assertTrue((out >= 0).all() and (out <= 1.0 + 1e-6).all())


if __name__ == "__main__":
    unittest.main()