import numpy as np

SAMPLE_RATE=44100
PI = np.pi

duration=1
amp = 1E4

# The total number of sample points that define your sound
nsamples = int(duration * SAMPLE_RATE)

# Range of the sound: nsamples points equaly spaced in the range
sample_space = np.linspace(0, duration, nsamples, endpoint=False)

def angular_freq(
    frequency,
    sample_space=None
):
    if sample_space is None:
        # 1 sec duration sample space
        sample_space=np.linspace(0, 1, int(duration * SAMPLE_RATE), endpoint=False)
    return 2*PI*frequency*sample_space
