# Get Started

[Pycon US 2025](https://us.pycon.org/2025/schedule/presentation/19/)

The goal of this tutorial is to break down the abstractions that make up a synthesizer by building one using Python, its scientific computing libraries, and Librosa. We will build the basic components of a modern digital synth from scratch. Along the way, you'll learn DSP and audio programming concepts. By the end, you'll be able to make your own tunes with Python! We'll start with theory and then work through Jupyter notebooks both individually and as a group.

This tutorial will be a lot of fun if you’re a musically inclined Python programmer. As someone interested in music, you will discover the components that make up a synthesizer by literally building & making music with it and as someone interested in Python, you’ll learn a lot about audio programming and signal processing techniques.

# Welcome To Synths

A synthesizer is an instrument that can synthesize sounds! That's it. Unlike normal instruments tho synths use electrical signals that generate waveforms which has its own sound, similar to how when you flow the flute or pluck a guitar you hear a sound from waveform moving across air molecules. Sound waves produced by a guitar is different frequency from flute which is why they sound different. In Synths tho since this is a electronic waveform we can tune the intensity, duration, frequency and stuff we create sounds far beyond the range of any conventional musical instrument and this makes them very very powerful!


## Create da Sound

Synths generate electrical signals & these signals are converted to sound using **Voltage Controlled Oscillators (VCO).**

We can use Voltage to tell the oscillator precisely what frequency to oscillate at in order to produce a musical note! Pitch is controlled by tuning the voltage, So if 1V increase on the input changes the output frequency one octave then its a 1V/Octave synthesizer.

The Oscillator’s waveform can be a simple Sine wave or maybe you choose Triangle, Sawtooth, Square, Pulse waves and so on & on...

This is how Synths generate sound.

Aside from the tunable frequency or pitch of the oscillator and its amplitude, one of the most important features is the shape of its waveform

- Sine
- Triangle
- Square
- Rectangular
- Sawtooth

## Change da sound


### Filter

After producing the sound an Oscillator would send its signal over to a VCO (Voltage Controlled Filter)

**Filters** remove certain frequencies in order to shape the sound and alter the waveform, we can use them to boost frequencies

- High-Pass: remove low frequencies
- Low-Pass: remove high frequencies

Along with filtering you can also accentuate frequencies using **Resonance** which helps you further emphasize or suppress signals below a given cutoff frequency

With enough feedback, the filter is unstable and will blow up, oscillating at the cutoff frequency. But then nonlinear saturation in the amplifiers acts against the oscillations blowing up. The result of these two opposing forces in the feedback loop: 
- The linear part which blows up
- The nonlinear part which prevents the oscillation from blowing up

This results in something really cool: A stable oscillation at the cutoff frequency, also called **self-oscillation** resulting waveform is usually fairly close to a sine wave.

### Modulator

Modulator just modifies the original sound or signal. Modulating a sound will change something about the effect your control signal has on the wave from the Oscillator. You can add a sense of movement and depth to the sound to modulating things like the Pitch, timbre, filter cutoff and even the waveform.

There can be multiple sources of modulation like Envelope Groups (EGs), Low Frequency Oscillators  (LFOs) and synth components receiving and reacting to the are modulations are called destinations. These include Oscillators and Filters.

Let us explore the Sources a bit further.

### Envelope

To control the sound behavior over time, we use **Envelopes** these really help shape the sound we hear and are some of the building blocks of sound design!!

They determine how the sound evolves over time, whether it starts abruptly, gradually fades in and out, or sustains at a certain level

The first part is the **Amplifier Envelope** which controls the volume of the amplifier using four common parameters abbrevated as ADSR

- attack (how fast sound reaches full amplitude)
- decay (how quickly the sound declines after attack)
- sustain (how long should the sound last)
- release (how long until sound gradually becomes silence after sustaining)

We can use multiple oscillators with different envelope settings to create really complex and evolving timbre and tonal characters.


### Low Frequency Oscillator

LFOs are oscillators operating at lower frequencies below the audible range but that doesn't mean its useless, LFOs can act as modulators and introduces complex effects to the resulting sound.

LFOs can create **Vibrato**, **Tremolo** and phasing effects!

When routed to control Pitch, LFOs can add a gentle, expressive wobble that adds emotion to the sound called Vibrato! By applying a sine wave LFO to the pitch parameter, we can create a pleasant vibrato effect. We can also tune the LFO's rate which determines how frequently the oscillation occurs/ speed of the vibrato, and the depth, which controls the amount of pitch variation.

An LFO modulating amplitude creates the tremolo effect. LFOs can also be summed and set to different frequencies to create continuously changing slow moving waveforms. 

LFOs are used a lot in dubstep and bass heavy electronic tracks for creating a sort of wobble effect.


### Reading

- https://www.aulart.com/blog/oscillator-waveforms-types-and-uses-part-i/#!
- https://blog.soundparticles.com/synth-tutorial-eg-explained
- https://www.musicgateway.com/blog/how-to/what-is-a-synthesizer-the-beginners-guide-together-in-electric-dreams
- https://www.reddit.com/r/Python/comments/lw50ne/making_a_synthesizer_using_python/
- https://jupylet.readthedocs.io/en/latest/programmers_reference_guide/synthesis.html
