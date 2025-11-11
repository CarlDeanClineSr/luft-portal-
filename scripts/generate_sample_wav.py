#!/usr/bin/env python3
"""
Generate a sample WAV file with a 7,468 Hz tone for testing
"""

import wave
import numpy as np

# Parameters
sample_rate = 44100  # Standard audio sample rate
duration = 3.0  # seconds
frequency = 7468  # Hz - target LUFT frequency
amplitude = 0.3  # Keep it moderate to avoid clipping

# Generate time array
t = np.linspace(0, duration, int(sample_rate * duration), False)

# Generate sine wave at target frequency
audio_signal = amplitude * np.sin(2 * np.pi * frequency * t)

# Add a small amount of noise to make it more realistic
noise_level = 0.02
audio_signal += noise_level * np.random.randn(len(audio_signal))

# Convert to 16-bit PCM
audio_signal = np.int16(audio_signal * 32767)

# Save as WAV file
output_path = 'recordings/sample.wav'
with wave.open(output_path, 'w') as wav_file:
    wav_file.setnchannels(1)  # Mono
    wav_file.setsampwidth(2)  # 16-bit
    wav_file.setframerate(sample_rate)
    wav_file.writeframes(audio_signal.tobytes())

print(f"Sample WAV file created: {output_path}")
print(f"  Frequency: {frequency} Hz")
print(f"  Sample rate: {sample_rate} Hz")
print(f"  Duration: {duration} seconds")
