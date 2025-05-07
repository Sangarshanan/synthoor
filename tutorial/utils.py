import numpy as np
from scipy import signal
from scipy.fft import fft, fftfreq

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
def phase_from_frequency(frequency, sample_space=sample_space):
    return 2*np.pi*frequency*sample_space

def plot_fft(ax, y, fs, title, max_freq=1000):
    """Calculates and plots the FFT of a signal y."""
    N = len(y)
    yf = fft(y)
    xf = fftfreq(N, 1 / fs)

    # Plot only positive frequencies
    positive_mask = xf >= 0
    xf_pos = xf[positive_mask]
    yf_pos = np.abs(yf[positive_mask]) / N * 2 # Normalize amplitude

    ax.plot(xf_pos, yf_pos)
    ax.set_title(title)
    ax.set_xlabel('Frequency [Hz]')
    ax.set_ylabel('Amplitude')
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax.set_xlim(0, max_freq)        
    ax.set_ylim(0, np.max(yf_pos[xf_pos > 0])*1.1 if np.max(yf_pos[xf_pos > 0]) > 0 else 0.1)


def plot_fft_simple(ax, y, fs, title, max_freq_plot, line_color='blue'):
    """Calculates and plots the FFT of a signal y."""
    N = len(y)
    yf = fft(y)
    xf = fftfreq(N, 1 / fs)

    # Plot only positive frequencies and normalize
    positive_mask = xf >= 0
    xf_pos = xf[positive_mask]
    yf_pos = np.abs(yf[positive_mask]) / N * 2 # Multiply by 2 for single-sided spectrum

    ax.plot(xf_pos, yf_pos, color=line_color, alpha=0.8)
    ax.set_title(title)
    ax.set_xlabel('Frequency [Hz]')
    ax.set_ylabel('Amplitude')
    ax.grid(True, which='both', linestyle='--', linewidth=0.5)
    ax.set_xlim(0, max_freq_plot)
    
    # Adjust y-axis for better visibility
    relevant_yf_pos = yf_pos[xf_pos <= max_freq_plot]
    if len(relevant_yf_pos) > 0 and np.max(relevant_yf_pos) > 0:
         ax.set_ylim(0, np.max(relevant_yf_pos) * 1.1)
    else:
        ax.set_ylim(0, 0.1) # Default if no significant peaks

def plot_fft_and_filter_response(ax, audio_y, b, a, fs, title, color='blue', cutoff_freq=None):
    N = len(audio_y)
    # Audio FFT
    yf_audio = np.abs(fft(audio_y)[0:N//2]) / N * 2
    xf_audio = fftfreq(N, 1/fs)[0:N//2]
    ax.plot(xf_audio, 20 * np.log10(yf_audio + 1e-9), color=color, alpha=0.5, label='Audio Spectrum')

    # Filter Response
    w_filt, h_filt = signal.freqz(b, a, worN=2048, fs=fs)
    ax.plot(w_filt, 20 * np.log10(np.abs(h_filt) + 1e-9), color='black', linestyle='-', linewidth=1.5, label='Filter Response')

    ax.set_title(title)
    ax.set_xlabel('Frequency [Hz]')
    ax.set_ylabel('Magnitude [dB]')
    # Zoom to see the effect around the cutoff, but also some higher frequencies
    ax.set_xlim(0, cutoff_freq * 8 if cutoff_freq else fs / 4)
    ax.set_ylim(-80, 20) # Allow for positive dB from resonance
    ax.grid(True, which='both', linestyle='--')
    if cutoff_freq:
        ax.axvline(cutoff_freq, color='red', linestyle=':', label=f'Cutoff @ {cutoff_freq}Hz')
    ax.legend(fontsize='small')
