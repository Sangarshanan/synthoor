import math
import numpy as np
from .sound import Sound
from .config import FPS, EPSILON

def get_exponential_adsr_curve(dt, start=0, end=None, th=0.01):
    """Compute a section of an exponential envelope curve.
    
    Args:
        dt (float): The time it should take the curve to go from 0. to 1.
            minus the given threshold (th).
        start (int): The start frame for the curve.
        end (int): The end frame for the curve.

    Returns:
        ndarray: Array with curve values.    
    """
    df = max(math.ceil(dt * FPS), 1)
    end = min(df, end if end is not None else 60 * FPS)
    start = start + 1
        
    a0 = np.arange(start/df, end/df + EPSILON, 1/df, dtype='float64')
    a1 = np.exp(a0 * math.log(th))
    a2 = (1. - a1) / (1. - th)
    
    return a2


def get_linear_adsr_curve(dt, start=0, end=None):
    """Compute a section of a linear envelope curve.
    
    Args:
        dt (float): The time it should take the curve to go from 0. to 1.
        start (int): The start frame for the curve.
        end (int): The end frame for the curve.

    Returns:
        ndarray: Array with curve values.    
    """
    df = max(math.ceil(dt * FPS), 1)
    end = min(df, end if end is not None else 60 * FPS)
    start = start + 1
    
    a0 = np.arange(start/df, end/df + EPSILON, 1/df, dtype='float64')
    
    return a0


def gate2events(gate, v0=0, index=0):
    
    states = []

    end = index + len(gate)
    gate = gate > 0
    
    while len(gate):

        if v0 == 0:

            am = int(gate.argmax())
            gv = int(bool(gate[am]))

            if gv == v0:
                break
            
            v0 = gv
            index += am            
            states.append((index, 'open'))
            gate = gate[am:]
            
        else:
            
            am = int(gate.argmin())
            gv = int(bool(gate[am]))

            if gv == v0:
                break
            
            v0 = gv
            index += am            
            states.append((index, 'close'))
            gate = gate[am:]
            
    states.append((end, 'continue'))
    
    return states, v0, end


#
# Envelopes are currently the only consumers of gate open/close signals.
#

class Envelope(Sound):
    
    def __init__(
        self, 
        attack=0.,
        decay=0., 
        sustain=1., 
        release=0.,
        linear=True,
    ):
        
        super().__init__()
        
        self.attack = attack
        self.decay = decay
        self.sustain = sustain
        self.release = release

        # Linear or exponential envelope curve.
        self.linear = linear

        # The current state of the envelope, one of attack, decay, ...
        self._state = None

        # The first frame index of the current envelope state.
        self._start = 0

        #
        # Pure envelope curves go from 0 to 1, but in practice a curve may go
        # from arbitrary level A to level B. e.g. release may start at sustain
        # level and go down to 0. The following two properties are use to 
        # implement this.
        #
        self._valu0 = 0
        self._valu1 = 0
        
        # Last gate value.
        self._lgate = 0

    def forward(self, gate):
        
        if isinstance(gate, np.ndarray):
            states, self._lgate, end = gate2events(gate, self._lgate, self.index)
        else:
            states = gate

        index = self.index
        
        # TODO: This code assumes the envelope frame index and the gate frame
        # index are synchronized (the same). In practice this is correct, but
        # it should not be assumed. Instead the gate itself should include 
        # its buffer start and end index. 

        curves = []
        
        for event_index, event in states:
            
            while index < event_index:
                curves.append(self.get_curve(index, event_index))
                index += len(curves[-1])
                    
            if event == 'open' and self._state != 'attack':
                self._state = 'attack'
                self._start = index
                self._valu0 = self._valu1
            
            if event == 'close' and self._state not in ('release', None):
                self._state = 'release'
                self._start = index
                self._valu0 = self._valu1
            
        return np.concatenate(curves)[:,None]
    
    def get_curve(self, start, end):

        end = max(start, end)

        if self._state in (None, 'sustain'):
            return np.ones((end - start,), dtype='float64') * self._valu0
        
        start = start - self._start
        end = end - self._start
        dt = getattr(self, self._state)
                    
        if self.linear:
            curve = get_linear_adsr_curve(dt, start, end)
        else:
            curve = get_exponential_adsr_curve(dt, start, end)
    
        if len(curve) == 0:
            return curve

        done = curve[-1] >= 1 - EPSILON
        
        if self._state == 'attack':
            target = 1.
            next_state = 'decay'
            
        elif self._state == 'decay':
            target = self.sustain * self._valu0
            next_state = 'sustain' if self.sustain else None
            
        elif self._state == 'release':
            target = 0.
            next_state = None
        
        else:
            target = 0.
            next_state = None

        curve = (target - self._valu0) * curve  + self._valu0
        
        if done:
            self._state = next_state
            self._start += start + len(curve)
            self._valu0 = curve[-1]
            
        self._valu1 = curve[-1]
        
        return curve
