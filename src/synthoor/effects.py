import numpy as np

from .sound import Sound
from .config import FPS

"""
This place is under constructions
"""


class Reverb(Sound):
    """Simple reverb effect using parallel delay lines (Schroeder-style).
    
    Args:
        decay_time (float): Time for signal to decay by 60dB in seconds.
        wet_mix (float): Wet signal mix amount (0.0 to 1.0).
    """
    def __init__(self, decay_time=2.0, wet_mix=0.5):
        super().__init__()
        self.decay_time = float(decay_time)
        self.wet_mix = float(np.clip(wet_mix, 0.0, 1.0))
        
        # Use four parallel comb filters with different delays
        # Delay times in samples (at 44.1kHz)
        self.delays = [1116, 1188, 1277, 1356]
        self.delay_buffers = [np.zeros(d, dtype="float64") for d in self.delays]
        self.write_positions = [0] * len(self.delays)
        
        # Calculate feedback coefficient from decay time
        self._update_feedback()

    def _update_feedback(self):
        """Calculate feedback coefficient from decay time."""
        # decay_time is the time for -60dB decay
        # feedback = 10^(-3 * delay_time / decay_time)
        self.feedback_coeff = 10.0 ** (-3.0 * np.mean(self.delays) / (self.decay_time * FPS))
        self.feedback_coeff = float(np.clip(self.feedback_coeff, 0.0, 0.99))

    def reset(self, shared=False):
        super().reset(shared)
        for buf in self.delay_buffers:
            buf.fill(0)
        self.write_positions = [0] * len(self.delays)

    def forward(self, x, key_modulation=None):
        """Process input through reverb.
        
        Args:
            x (ndarray): Input signal of shape (frames,) or (frames, channels).
            key_modulation: Unused, for API compatibility.
            
        Returns:
            ndarray: Output signal with same shape as input.
        """
        if isinstance(x, np.ndarray) and x.ndim > 1:
            x = x.flatten()
        
        x = np.asarray(x, dtype="float64")
        output = np.zeros_like(x)
        
        for i, sample in enumerate(x):
            # Process through all delay lines
            delayed_sum = 0.0
            
            for j, (buf, delay_len) in enumerate(zip(self.delay_buffers, self.delays)):
                read_pos = self.write_positions[j]
                delayed = buf[read_pos]
                
                # Comb filter: feedback from delayed output
                buf[self.write_positions[j]] = sample + self.feedback_coeff * delayed
                
                # Accumulate delayed outputs
                delayed_sum += delayed
                
                # Update write position
                self.write_positions[j] = (self.write_positions[j] + 1) % delay_len
            
            # Mix dry and wet
            avg_delayed = delayed_sum / len(self.delay_buffers)
            output[i] = sample * (1.0 - self.wet_mix) + avg_delayed * self.wet_mix
        
        return output


class Delay(Sound):
    """Simple delay effect using a circular buffer.
    
    Args:
        delay_samples (int): Number of samples for the delay.
        feedback (float): Feedback amount (0.0 to 0.99).
    """
    def __init__(self, delay_samples=44100 * 0.5, feedback=0.5):
        super().__init__()
        self.delay_samples = int(delay_samples)
        self.feedback = float(np.clip(feedback, 0.0, 0.99))
        self.delay_buffer = np.zeros(self.delay_samples, dtype="float64")
        self.write_pos = 0

    def reset(self, shared=False):
        super().reset(shared)
        self.delay_buffer.fill(0)
        self.write_pos = 0

    def forward(self, x, key_modulation=None):
        """Process input through delay line.
        
        Args:
            x (ndarray): Input signal of shape (frames,) or (frames, channels).
            key_modulation: Unused, for API compatibility.
            
        Returns:
            ndarray: Output signal with same shape as input.
        """
        if isinstance(x, np.ndarray) and x.ndim > 1:
            x = x.flatten()
        
        x = np.asarray(x, dtype="float64")
        output = np.zeros_like(x)
        
        for i, sample in enumerate(x):
            # Read from delay buffer
            read_pos = self.write_pos
            delayed = self.delay_buffer[read_pos]
            
            # Write input + feedback to delay buffer
            self.delay_buffer[self.write_pos] = sample + self.feedback * delayed
            
            # Mix dry and delayed
            output[i] = sample + 0.5 * delayed
            
            # Update write position
            self.write_pos = (self.write_pos + 1) % self.delay_samples
        
        return output


class Compressor(Sound):
    """Dynamic range compressor with envelope following.
    
    Args:
        threshold (float): Threshold in dB.
        ratio (float): Compression ratio (e.g., 4.0 = 4:1).
        attack_time (float): Attack time in seconds.
        release_time (float): Release time in seconds.
    """
    def __init__(self, threshold=-30.0, ratio=4.0, attack_time=0.01, release_time=0.1):
        super().__init__()
        self.threshold = float(threshold)
        self.ratio = float(max(1.0, ratio))
        self.attack_time = float(attack_time)
        self.release_time = float(release_time)
        
        # Envelope follower state
        self.envelope = 0.0
        
        # Calculate coefficients
        self._update_coefficients()

    def _update_coefficients(self):
        """Calculate attack and release coefficients."""
        self.attack_coeff = np.exp(-1.0 / (self.attack_time * FPS)) if self.attack_time > 0 else 0.0
        self.release_coeff = np.exp(-1.0 / (self.release_time * FPS)) if self.release_time > 0 else 0.0

    def reset(self, shared=False):
        super().reset(shared)
        self.envelope = 0.0

    def forward(self, x, key_modulation=None):
        """Apply compression to input signal.
        
        Args:
            x (ndarray): Input signal of shape (frames,) or (frames, channels).
            key_modulation: Unused, for API compatibility.
            
        Returns:
            ndarray: Compressed output signal with same shape as input.
        """
        if isinstance(x, np.ndarray) and x.ndim > 1:
            x = x.flatten()
        
        x = np.asarray(x, dtype="float64")
        output = np.zeros_like(x)
        
        # Convert threshold from dB to linear
        threshold_linear = 10.0 ** (self.threshold / 20.0)
        
        for i, sample in enumerate(x):
            # Get magnitude
            magnitude = np.abs(sample)
            
            # Envelope following with attack/release
            if magnitude > self.envelope:
                self.envelope = self.attack_coeff * self.envelope + (1.0 - self.attack_coeff) * magnitude
            else:
                self.envelope = self.release_coeff * self.envelope + (1.0 - self.release_coeff) * magnitude
            
            # Calculate gain reduction
            if self.envelope > threshold_linear:
                # Gain reduction in dB then convert to linear
                input_db = 20.0 * np.log10(self.envelope + 1e-10)
                output_db = self.threshold + (input_db - self.threshold) / self.ratio
                gain = 10.0 ** ((output_db - input_db) / 20.0)
            else:
                gain = 1.0
            
            output[i] = sample * gain
        
        return output
