import numpy as np

sample_rate = 44100  # CD-quality audio (samples per second)
duration = 2  # seconds
frequency = 440  # Hz (A4 note)
amplitude = 0.4 # loudness

# Range of the sound: nsamples points equaly spaced in the range
sample_space = np.linspace(
    0, # start
    duration, # stop
    int(sample_rate * duration), # Number of samples to generate
    endpoint=False
)

# Convert Frequency in Hz to Angular Frequency cause that is what numpy needs to create a wave
def angular_freq(frequency, sample_space=sample_space):
    return 2*np.pi*frequency*sample_space
