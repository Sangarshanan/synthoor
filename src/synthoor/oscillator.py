import numpy as np
import math
import functools
from .sound import Sound, key2freq
from .config import MIDDLE_C, FPS

_NP_ZERO = np.zeros((1,), dtype='float64')


def get_radians(freq, start=0, frames=8192):
    
    pt = 2 * math.pi / FPS * freq
    
    if isinstance(pt, np.ndarray):
        pt = pt.reshape(-1)
    else:
        pt = pt * np.ones((frames,), dtype='float64')
            
    p0 = start + _NP_ZERO
    p1 = np.concatenate((p0, pt))
    p2 = np.cumsum(p1)
    
    radians = p2[:-1]
    next_start = p2[-1] 
    
    return radians, next_start


def get_sine_wave(freq, phase=0, frames=8192, **kwargs):
    
    radians, phase_o = get_radians(freq, phase, frames)
    
    a0 = np.sin(radians)
    
    return a0, phase_o


def get_triangle_wave(freq, phase=0, frames=8192, **kwargs):
    
    radians, phase_o = get_radians(freq, phase, frames)

    a0 = radians % (2 * math.pi)
    a1 = a0 / math.pi - 1
    a2 = a1 * np.sign(-a1)
    a3 = a2 * 2 + 1

    return a3, phase_o


@functools.lru_cache(maxsize=256)
def get_sawtooth_cycle(nharmonics, size=1024):
    
    k = nharmonics
    radians = 2 * math.pi * np.arange(0, 1, 1 / size)
    harmonic = - 2 / math.pi * ((-1) ** k) / k * np.sin(k * radians)

    if k == 1:
        return harmonic

    return harmonic + get_sawtooth_cycle(nharmonics - 1, size)
    
# Warmup
len(get_sawtooth_cycle(128))


def get_sawtooth_wave(freq, phase=0, frames=8192, sign=1., **kwargs):
    
    radians, phase_o = get_radians(freq, phase, frames)

    size = 1024

    # Use mean frequency for the purpose of determining number of 
    # harmonics to use - this may introduce some aliasing.
    if type(freq) not in (int, float):
        freq = float(np.mean(freq))

    nharmonics = max(1, min(128, FPS / 2 // freq))
    nharmonics = kwargs.get('nharmonics', nharmonics)

    sawtooth = get_sawtooth_cycle(nharmonics, size)

    indices = (size / 2 / math.pi * radians).astype('int32') % size
    samples = sawtooth[indices]
    
    if sign != 1.:
        samples = samples * sign

    return samples, phase_o


_nduties = 64
_nharmonics = 128

_km = np.arange(0, _nharmonics+1)[:, None, None] 
_dm = np.linspace(0, 1, _nduties+1)[None, :, None]
_kdm = _km * _dm


@functools.lru_cache(maxsize=256)
def get_square_cycle(nharmonics, size=1024):
    
    k = nharmonics
    radians = 2 * math.pi * np.arange(0, 1, 1 / size)
    harmonic = 4 / math.pi / k * np.sin(math.pi * _kdm[k]) * np.cos(k * radians)[None, :]
    
    if k == 1:
        return harmonic + 2 * _kdm[1] - 1

    return harmonic + get_square_cycle(nharmonics - 1, size)

def get_square_wave(freq, phase=0, frames=8192, duty=0.5, **kwargs):
    
    if isinstance(duty, np.ndarray):
        duty = duty.reshape(-1).clip(0.01, 0.99)
        
    radians, phase_o = get_radians(freq, phase, frames)

    # Use mean frequency for the purpose of determining number of 
    # harmonics to use - this may introduce some aliasing.
    if type(freq) not in (int, float):
        freq = float(np.mean(freq))

    nharmonics = max(1, min(128, FPS / 2 // freq))
    nharmonics = kwargs.get('nharmonics', nharmonics)

    size = 1024

    square0 = get_square_cycle(nharmonics, size)

    indices = (size / 2 / math.pi * radians).astype('int32') % size

    #
    # When duty is a modulating array, the following simple scheme
    # may result in aliasing. It would be preferable to find
    # a scheme that can efficiently sync changes in duty with the
    # begining of wave cycles.
    #
    if type(duty) in (int, float):
        duty = int(duty * _nduties)
    else:
        duty = (duty * _nduties).astype('int32')

    samples = square0[duty, indices]

    return samples, phase_o


class Oscillator(Sound):

    """Waveform generator for `sine`, `triangle`, anti-aliased `sawtooth`, and 
    variable duty anti-aliased `square` waveforms.

    Args:
        shape (str): Waveform to generate - one of `sine`, `triangle`, 
            `sawtooth`, or `square`.
        freq (float): Fundamental frequency of generator.
        key (float, optional): Fundamental frequency of generator in semitone
            units where middle C is 60.
        sign (float): Set to -1 to flip sawtooth waveform upside down.
        duty (float): The fraction of the square waveform cycle its value is 1.

    Note:
        An Oscillator inherits all the methods and properties of a Sound class.
    """
    
    def __init__(self, shape='sine', freq=MIDDLE_C, key=None, phase=0., sign=1, duty=0.5, **kwargs):
        """"""

        super().__init__(freq=freq)
        
        self.shape = shape
        self.phase = phase

        if key is not None:
            self.key = key
                
        self.sign = sign
        self.duty = duty
        self.kwargs = kwargs
        
    def forward(self, key_modulation=None, sign=None, duty=None, **kwargs):
        
        if key_modulation is not None:
            freq = key2freq(self.key + key_modulation)
        else:
            freq = self.freq

        if sign is None:
            sign = self.sign
            
        if duty is None:
            duty = self.duty
            
        if self.kwargs:
            kwargs = dict(kwargs)
            kwargs.update(self.kwargs)
        
        get_wave = dict(
            sine = get_sine_wave,
            triangle = get_triangle_wave,
            sawtooth = get_sawtooth_wave,
            square = get_square_wave,
            pulse = get_square_wave,
            saw = get_sawtooth_wave,
            tri = get_triangle_wave,
        ).get(self.shape, self.shape)
        
        a0, self.phase = get_wave(
            freq, 
            self.phase, 
            self.frames, 
            sign=self.sign,
            duty=duty, 
            **kwargs
        )
        
        return a0[:,None]
