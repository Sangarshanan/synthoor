import math
import numpy as np

DEFAULT_AMP = 0.5
MIDDLE_C = 261.63
FPS = 44100
EPSILON = 1e-6
LATENCY = 0.03

_LOG_C4 = math.log(MIDDLE_C)
_LOG_CC = math.log(2) / 12
_LOG_CX = _LOG_C4 - 60 * _LOG_CC    
