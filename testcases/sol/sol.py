# For the Cheaters

# Oscillator

def phase_from_frequency(frequency, duration, sample_rate=44100):
    time = np.linspace(
        0, # start
        duration, # stop
        int(sample_rate * duration),
        endpoint=False
    )
    angular_freq = 2*np.pi*frequency
    return angular_freq * time

def get_sine_wave(frequency, amp, duration):
    return np.sin(phase_from_frequency(frequency, duration)) * amp

def get_triangle_wave(frequency, amp, duration):
    return signal.sawtooth(phase_from_frequency(frequency, duration),  width=0.5)*amp

def get_square_wave(frequency, amp, duration):
    return signal.square(phase_from_frequency(frequency, duration)) * amp

def get_sawtooth_wave(frequency, amp, duration):
    return signal.sawtooth(phase_from_frequency(frequency, duration)) * amp


class Oscillator:
    def __init__(self, shape):
        """
        Initialise an Oscillator
        """
        self.shape = shape
        self.waveform = {
            "sine": get_sine_wave,
            "saw": get_sawtooth_wave,
            "square": get_square_wave,
            "tri": get_triangle_wave
        }.get(self.shape)

    def play(self, frequency, amp=1, duration=1):
        """
        Play the sound
        """
        wave_to_play = self.waveform(frequency, amp, duration)
        sd.play(wave_to_play)
        return wave_to_play


# Envelope

class Envelope:
    """
    Envelope class.
    """
    def __init__(self, attack_time, decay_time, sustain_level, release_time):
        self.attack_time = float(attack_time)
        self.decay_time = float(decay_time)
        self.sustain_level = float(sustain_level)
        self.release_time = float(release_time)

    def apply(self, waveform):
        """
        Applies the ASDR envelope
        """
        
        total_samples = len(waveform)
        envelope = np.zeros(total_samples)
        
        attack_samples = int(self.attack_time * sample_rate)
        decay_samples = int(self.decay_time * sample_rate)
        release_samples = int(self.release_time * sample_rate)

        if attack_samples + decay_samples + release_samples > len(waveform):
            raise Exception("No way you cannot do this")

        # Attack
        envelope[0:attack_samples] = np.linspace(0, 1, attack_samples)

        # Decay
        decay_end_sample = attack_samples + decay_samples
        number_of_decay_samples = decay_end_sample - attack_samples
        envelope[attack_samples:decay_end_sample] = np.linspace(1, self.sustain_level, number_of_decay_samples)

        # Release
        release_start_sample = total_samples - release_samples
        envelope[decay_end_sample:release_start_sample] = self.sustain_level

        # Sustain
        number_of_release_samples = total_samples - release_start_sample
        level_before_release = envelope[release_start_sample -1]
        envelope[release_start_sample:total_samples] = np.linspace(level_before_release, 0, number_of_release_samples)

        # Return shaped waveform
        return waveform * envelope, envelope


# Envelope parameters

# Ensure total time fits reasonably within 'duration'
# Define ADSR parameters 
attack_t = 0.2   # seconds
decay_t = 0    # seconds
sustain_l = 1  # level (60% of peak amplitude)
release_t = 1  # seconds

# Create an Envelope instance
adsr_envelope = Envelope(
    attack_time=attack_t,
    decay_time=decay_t,
    sustain_level=sustain_l,
    release_time=release_t,
)
shaped_wave, envelope_shape = adsr_envelope.apply(original_wave)
ipd.Audio(shaped_wave, rate=sample_rate)

# Filters stuff

# Sinc Filter
low_pass = np.sin(np.pi * low * n) / (np.pi * n)
# np.sin create an oscilation centered
# Dividing by (np.pi * n) makes the wave decay/ripple outward instead of just being flat

# Highpass = NOT lowpass, so allpass - lowpass
h_highpass = -np.sin(np.pi * cutoff * n) / (np.pi * n)
h_highpass[numtaps // 2] = 1 - cutoff  # n=0 case: "all-pass" (1) minus lowpass cutoff
h_highpass *= np.hamming(numtaps)

# Bandpass = highpass - lowpass


def simple_filtfilt(h, x):
    y = np.convolve(x, h, mode='same')              # forward pass
    y = np.convolve(y[::-1], h, mode='same')[::-1]   # reversed pass (cancels phase shift)
    return y

"""
filtering doesn't just change which frequencies are present, it also slightly shifts the signal in time. 
This shift is called "phase delay," and it happens with basically every FIR filter

So we reserve the filter convolve it again
If filtering forward always delays things later,
then filtering a reversed signal delays it later in reversed-time 
which means, once you flip it back, that delay actually points earlier.

So the two delays are equal and opposite, and they cancel each other out.

Noice
"""
