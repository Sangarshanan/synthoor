# Synthoor

A Toy Software Synth written in Python.

```sh
pip install synthoor
```

### Setup for Tutorial

Hope you have [Python>=3.10](https://www.python.org/downloads/) already, Once you got that you can go ahead and [install uv](https://docs.astral.sh/uv/getting-started/installation/) to get everything set up locally.

```sh
uv sync
uv run jupyter notebook
```

Try to get a local venv setup working because we need the sounddevice module to run the package but if you are not able to get it working, you can also install [Docker](https://www.docker.com/get-started/) and [docker-compose](https://docs.docker.com/compose/install/)

```sh
docker-compose up
```

Or

```
docker build -t synthoor .
docker run -it --rm -p 8888:8888 synthoor
```

**Extra:** The last section of the tutorial directly uses the package which would not directly work with docker because it needs a sounddevice, If you are on a Linux machine with PortAudio you can add `--device /dev/snd` to the docker run command and for MacOs follow this instruction: https://devops.datenkollektiv.de/running-a-docker-soundbox-on-mac.html


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
