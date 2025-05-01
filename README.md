# Synthoor

A Toy Software Synth.

```sh
pip install synthoor
```

### Setup for Tutorial

Install [Docker](https://www.docker.com/get-started/) and [docker-compose](https://docs.docker.com/compose/install/) and run the below command

```sh
docker-compose up
```

### Usage

Initialize a simple Sine wave oscillator and plot it

```python
import sounddevice as sd
from synthoor import Oscillator

osc0 = Oscillator('sine')
osc_play = osc0(
    freq = 200,
    frames = 30000
)
sd.play(osc_play)

plt.plot(osc0(
    freq = 10,
    frames = 30000
))
```


Modulate the sine wave and plot it

```python
osc0 = Oscillator('sine', 100)
osc1 = Oscillator('sine', 1000)
a0 = osc0() * 12
a1 = osc1(a0)
plt.plot(a1)
```

Programming Synthesizers as Classes

```python
class SimpleSynth(GatedSound):

    def __init__(self):

        super().__init__()

        self.osc0 = Oscillator('sine')

    def forward(self):
        
        g0 = self.gate()
        a0 = self.osc0()

        return a0 * g0

s = SimpleSynth()
s.play(
    duration=0.5
)
```

Sound modules are ripped off [Jupylet](https://github.com/nir/jupylet/)
