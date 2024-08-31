import inspect
import logging
import math
import time

import numpy as np

from .config import _LOG_CC, _LOG_CX, DEFAULT_AMP, FPS, LATENCY, MIDDLE_C
from .player import add_sound, get_bpm, get_schedule, get_time, t2frames

logger = logging.getLogger(__name__)

def key2freq(key):
    
    if isinstance(key, np.ndarray):
        return np.exp(key * _LOG_CC + _LOG_CX)
    else:
        return math.exp(key * _LOG_CC + _LOG_CX)
    
 
def freq2key(freq):
    
    if isinstance(freq, np.ndarray):
        return (np.log(freq) - _LOG_CX) / _LOG_CC
    else:
        return (math.log(freq) - _LOG_CX) / _LOG_CC


class Sound(object):
    """The base class for all other sound classes, including audio samples, 
    oscillators and effects.

    Args:
        freq (float): Default frequency.
        amp (float): Output amplitude - a value between 0 and 1.
    """
    def __init__(self, freq=MIDDLE_C, amp=DEFAULT_AMP, shared=False):
        
        self.freq = freq
        
        # MIDI attribute corresponding to velocity of pressed key,
        # between 0 and 128.
        self.velocity = 64

        # Amplitude (or volume) beween 0 and 1.
        self.amp = amp
                
        # The number of frames the forward() method is expected to return.
        self.frames = 1024

        # The frame counter.
        self.index = 0

        self._shared = shared
        
        
        # A somewhat brittle mechanism to force a note to keep "playing"
        # for a few seconds after it's done, so a shared effect may still
        # be applied to it (for example in the case of a long reverb).
        self._done = 0

        # The lastest output arrays of the forward() function.
        self._a0 = None

        self._fargs = None
        self._error = None

    def _rset(self, key, value, force=False):
        """Recursively, but lazily, set property to given value on all child sounds.
        
        This function is used for example to set number of required frames on the entire
        tree of sound objects before calling the forward() method.
        """
        if force or self.__dict__.get(key, '__NONE__') != value:
            for s in self.__dict__.values():
                if isinstance(s, Sound):
                    s._rset(key, value, force=True)
            
        self.__dict__[key] = value
    
    def _ccall(self, name, *args, **kwargs):
        """Recursively call given function of each sound object in the tree 
        of sounds.
        """
        for s in self.__dict__.values():
            if isinstance(s, Sound):
                getattr(s, name)(*args, **kwargs)
                
    def play(self, note=None, **kwargs):
        """Play given note monophonically.
        
        Args:
            note (float): Note to play in units of semitones 
                where 60 is middle C.
            **kwargs: Properties of intrument to modify.
        """               
        self.reset(self._shared)
        
        if note is not None:
            self.note = note

        add_sound(self)

    def reset(self, shared=False):
        
        self.index = 0

        self._done = 0
        self._a0 = None

        self._ccall('reset', shared=shared or self._shared)

               
    @property
    def done(self):
        
        # The done() function is used by the sound device to determine when
        # a playing sound may be considered done and discarded.
        # There are various criteria and the logic is probably brittle and 
        # needs to be considered again and simplified.
        #
        # The general idea is to consider a sound done if after it has played
        # for a while, it becomes nearly zero for an entire output buffer
        # length. 
        #
        # However, in the case effects are applied to the sound, it may be
        # needed around for a while longer even if its output has become 
        # zero. For example in the case of a reverb effect.

        if self._error:
            return True

        if self.index < FPS / 8:
            return False
        
        if self._a0 is None:
            return False
        
        if not self._done:
            if np.abs(self._a0).max() < 1e-4:
                self._done = self.index or 1
                self._a0 = self._a0 * 0

            return False
            
        return True
        
    #
    # This is the function called by the sound device to compute the next
    # *frames* to be sent to the sound device for playing.
    #

    def consume(self, frames, raw=False, *args, **kwargs):
        
        self._rset('frames', frames)
        
        a0 = self(*args, **kwargs)

        if raw:
            return a0

        return a0 * (self.velocity / 128 * self.amp)

    def __call__(self, *args, **kwargs):
        
        assert getattr(self, 'frames', None) is not None, 'You must call super() from the sound class constructor'
        
        for k in list(kwargs.keys()):
            if hasattr(self, k):
                if k == 'frames':
                    self._rset('frames', kwargs.pop('frames'))
                else:        
                    setattr(self, k, kwargs.pop(k))

        if not self._done or self._a0 is None or len(self._a0) != self.frames:
            try:
                self._a0 = self.forward(*args, **kwargs)
            except Exception as e:
                logger.error(e)
                self._a0 = np.zeros((self.frames, 1))

        if isinstance(self._a0, np.ndarray):
            self.index += len(self._a0)
        
        return self._a0

    def _get_forward_args(self):
        if self._fargs is None:
            self._fargs = set(inspect.getfullargspec(self.forward).args)
        return self._fargs

    #
    # The pytorch style forward function to compute the next sound buffer.
    #
    def forward(self, *args, **kwargs):
        return np.zeros((self.frames,))
    
    @property
    def key(self):
        """float: Get current sound frequency in semitone units where 60 is middle C."""
        return freq2key(self.freq)
    
    @key.setter
    def key(self, value):
        self.freq = key2freq(value)


class LatencyGate(Sound):
    """A synthesizer on/off gate.
    
    A synthesizer gate outputs an on/off signal that is used to 
    trigger signal processing such as envelope generators etc...

    This particular latency gate is designed to schedule `on` and `off` 
    transitions using system time to enable triggering notes with precise 
    timing despite fluctuations in the latency of the operating system.
    """
    def __init__(self):
        
        super().__init__()
        
        self.states = []
        self.opened = False
        self.value = 0

    def forward(self):
        
        #
        # open/close events are scheduled in terms of absolute time. Here these 
        # timestamps are converted into a frame index.
        #

        #states = []

        a0 = np.zeros((self.frames, 1))
        i0 = 0

        t0 = time.time()
        schedule = get_schedule()
        
        while self.states:
            
            t, event = self.states[0]
            
            if schedule:
                dt = max(0, t + LATENCY - schedule)
            else:
                dt = max(0, t - t0)
                
            df = t2frames(dt)
            i1 = min(df, self.frames)

            if df > i1:
                break

            if self.value == 0 and event == 'open':
                self.value = 1
                self.opened = True
                i0 = i1
            elif self.value == 1 and event == 'close':
                self.value = 0
                a0[i0:i1] += 1

            self.states.pop(0)

        if self.value == 1 and i0 < self.frames:
            a0[i0:self.frames] += 1

        #states.append((self.index + self.frames, 'continue'))          
        return a0


    def open(self, t=None, dt=None):
        """Schedule gate open at specified time.

        The schedule can be an absolute time given by the argument `t`, or 
        a delta `dt` after the schedule of the latest event already scheduled.

        Args:
            t (float, optional): Time in seconds since epoch, as returned by 
                Python's standard library ``time.time()``.
            dt (float, optional): Time in seconds after the current last 
                scheduled event.
        """
        self.schedule('open', t, dt)
        
    def close(self, t=None, dt=None, **kwargs):
        """Schedule gate close at specified time.

        The schedule can be an absolute time given by the argument `t`, or 
        a delta `dt` after the schedule of the latest event already scheduled.

        Args:
            t (float, optional): Time in seconds since epoch, as returned by 
                Python's standard library ``time.time()``.
            dt (float, optional): Time in seconds after the current last 
                scheduled event.
        """
        self.schedule('close', t, dt)
        
    def schedule(self, event, t=None, dt=None):
        logger.debug('Enter LatencyGate.schedule(event=%r, t=%r, dt=%r).', event, t, dt)

        tt = get_time()

        if not self.states:
            last_t = tt
        else:
            last_t = self.states[-1][0]

        if dt is not None:
            t = dt + last_t
        else:
            t = t or tt

        t = max(t, tt)

        # Discard events scheduled to run after this new event.
        while self.states and self.states[-1][0] > t:
            self.states.pop(-1)

        self.states.append((t, event))
    
class GatedSound(Sound):
    """A sound class capable of precise timing and duration of notes.

     Args:
        freq (float): Fundamental frequency.
        amp (float): Output amplitude - a value between 0 and 1.
        pan (float): Balance between left (-1) and right (1) output channels.
        duration (float, optional): Duration to play note, in whole notes.    
    """
    def __init__(self, freq=MIDDLE_C, amp=DEFAULT_AMP):
        super().__init__(freq=freq, amp=amp)
        self.gate = LatencyGate()


    def play(self, note=None, duration=None):
        """Play given note monophonically.
        
        Args:
            note (float): Note to play in units of semitones 
                where 60 is middle C.
            duration (float, optional): Duration to play note, in whole notes.    
        """
        super().play(note)
        self.gate.open()
        self.gate.close(dt=duration * 4 * 60 / get_bpm())
