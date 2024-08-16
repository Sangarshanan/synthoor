import _thread
import logging
import queue
import time

import sounddevice as sd

import soundcard as sc

import numpy as np

from .config import FPS

logger = logging.getLogger(__name__)
    

def disable_audio():
    global sd
    sd = None

    
_schedule = None


def set_schedule(t):
    global _schedule
    _schedule = t


def get_schedule():
    return _schedule


def t2frames(t):
    return int(FPS * t)

def get_time():
    return time.time()

_bpm = 240
def get_bpm():
    return _bpm


_worker_tid = None


def _init_worker_thread():
    logger.info('Enter _init_worker_thread().')

    global _worker_tid
    
    if not _worker_tid and sd is not None:
        _worker_tid = _thread.start_new_thread(_start_sound_stream, ())
        
#
# This queue is only used to keep the sound stream running.
#
_workerq = queue.Queue()
_sp = {}


def _start_sound_stream():
    """Start the sound device output stream handler."""
    logger.info('Enter _start_sound_stream().')
    
    while True:

        if _sp.pop('reset', None):
            _reset()
        with sd.OutputStream(samplerate=FPS, channels=2, callback=_stream_callback, **_sp):
            _workerq.get()
    

_nresets = 0

def _reset():
    
    global _nresets

    sd._exit_handler()
    sd._initialize()

    _nresets += 1


def _set_stream_params(**kwargs):
    _sp.update(kwargs)
    _workerq.put(1)


_al_seconds = 1
_al = []


def start_recording(limit=60):

    global _al_seconds
    global _al
    
    _al_seconds = limit    
    _al.clear()


def stop_recording():

    global _al_seconds

    a0 = np.concatenate(_al)
    _al_seconds = 1
    return a0


def _get_default_sc_device():

    global _oe

    if sc is None:
        return None
    
    if _oe:
        return None
    
    try:
        return sc.default_speaker().id
    
    except:
        _oe += 1
    

_oe = 0
_ot = 0
_od = _get_default_sc_device()


_dt = []
_safety_event0 = 0

def _stream_callback(outdata, frames, _time, status):
    """Compute and set the sound data to be played in a few milliseconds.

    Args:
        outdata (ndarray): The sound device output buffer.
        frames (int): The number of frames to compute and set into the output
            buffer.
        _time (struct): A bunch of clocks.
    """
    global _safety_event0, _ot, _od

    t0 = time.time()
    dt = _time.outputBufferDacTime - _time.currentTime

    if t0 - _ot > 1:

        _ot = t0
        od_ = _get_default_sc_device()

        if _od != od_:
            _od = od_
            _set_stream_params(reset=True)

    set_schedule(t0 + dt)
    
    if status:
        logger.warning('Stream callback called with status: %r.', status)
        _safety_event0 = t0

    #
    # Get all sound objects currently playing, mix them, and set the mixed
    # array into the output buffer.
    #

    sounds = _get_sounds()
    
    if not sounds:
        a0 = np.zeros_like(outdata)  
    else: 
        a0 = _mix_sounds(sounds, frames)

    a0 = (a0 * _master_volume).clip(-1, 1)
    
    if t0 < _safety_event0 + 1:
        a0 *= max(0.01, min(1, t0 - _safety_event0))

    outdata[:] = a0

    # 
    # Aggregate the output data and timers for the oscilloscope.
    #

    while len(_al) * frames > _al_seconds * FPS:
        _al.pop(0)
        _dt.pop(0)

    _al.append(a0)
    _dt.append((
        t0, 
        frames, 
        _time.inputBufferAdcTime,
        _time.outputBufferDacTime,
        _time.currentTime,
    ))


_master_volume = 0.5


def get_master_volume():
    return _master_volume


def set_master_volume(amp):
    global _master_volume
    _master_volume = amp

#
# A list of all currently playing sound objects.
#
_sounds0 = []
_sounds1 = []


def stop_sound():
    _sounds0.clear()
    _sounds1.clear()


def add_sound(sound):
    """Add sound to the set of currently playing sound objects."""

    if sd is None:
        return

    if _worker_tid is None:
        _init_worker_thread()

    _sounds0.append(sound)

         
def _get_sounds():
    """Get currently playing sound objects."""

    sd_ = set()
    sl_ = []

    while _sounds0:
        s = _sounds0.pop(0)
        if s not in sd_ and not s.done:
            sl_.append(s)
            sd_.add(s)

    while _sounds1:
        s = _sounds1.pop(0)
        if s not in sd_ and not s.done:
            sl_.append(s)
            sd_.add(s)

    _sounds1[:] = sl_

    return sl_
      

def _mix_sounds(sounds, frames):
    """Mix sound data from given sounds into a single numpy array.

    Args:
        sounds: Currently playing sound objects.
        frames (int): Number of frames to consume from each sound object.

    Returns:
        ndarray
    """
    es = {}

    for s0 in sounds:
        es.setdefault((), []).append(s0)

    al = []

    for _, sl in es.items():
        a0 = _mix_sounds0(sl, frames)
        al.append(a0)
    return np.stack(al).sum(0)


def _mix_sounds0(sounds, frames):

    al = [s.consume(frames) for s in sounds]
    return np.stack(al).sum(0)
