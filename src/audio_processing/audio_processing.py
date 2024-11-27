import asyncio

import sounddevice as sd
import numpy as np
from gtts import gTTS
import io
import time

def normalize_audio(audio):
    return audio / np.max(np.abs(audio)) if np.max(np.abs(audio)) > 0 else audio

def record_audio(duration=5, sample_rate=16000):
    """
    Запмсь аудио
    :param duration:
    :param sample_rate:
    :return:
    """
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype=np.float32)
    sd.wait()
    return np.squeeze(audio)

async def text_to_speech(text, language="ru"):
    """
    Asynchronous wrapper for TTS with blocking I/O offloaded to a thread.
    """
    if "No-op" in text:
        print("Ignoring placeholder response for text-to-speech.")
        return generate_silent_audio(duration=1)

    # Offload blocking TTS operation to a thread
    audio_data = await asyncio.to_thread(generate_tts_audio, text, language)
    return audio_data

def generate_tts_audio(text, language):
    """
    Generate TTS audio using gTTS (blocking operation).
    """
    tts = gTTS(text=text, lang=language, slow=False)
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer.read()


def record_audio_until_silence(sample_rate=16000, silence_threshold=0.05, silence_duration=5.0, max_duration=60):
    """
    Records audio until the user stops speaking (based on silence detection), with verbosity.

    :param sample_rate: Sampling rate of the audio
    :param silence_threshold: Amplitude threshold to detect silence
    :param silence_duration: Duration of silence (in seconds) to stop recording
    :param max_duration: Maximum recording duration to prevent infinite loops
    :return: Recorded audio as a NumPy array
    """
    buffer = []
    start_time = time.time()
    silent_start = None

    print("Recording audio...")
    while True:
        # Record a short segment of audio
        segment = sd.rec(int(0.5 * sample_rate), samplerate=sample_rate, channels=1, dtype=np.float32)
        sd.wait()
        segment = np.squeeze(segment)
        buffer.append(segment)

        # Detect silence
        if np.max(np.abs(segment)) < silence_threshold:
            if silent_start is None:
                silent_start = time.time()
            time_since_silence = time.time() - silent_start
            time_left = silence_duration - time_since_silence
            if time_left > 0:
                print(f"Silence detected. Stopping in {time_left:.2f} seconds if no sound is detected.")
            if time_since_silence >= silence_duration:
                print("Silence duration exceeded. Stopping recording.")
                break
        else:
            if silent_start is not None:
                print("Sound detected. Resetting silence timer.")
            silent_start = None  # Reset silence timer if sound is detected

        # Stop after max duration
        elapsed_time = time.time() - start_time
        if elapsed_time >= max_duration:
            print("Maximum recording duration reached. Stopping recording.")
            break

    print("Recording stopped.")
    # Concatenate all segments into one audio array
    return np.concatenate(buffer)


def record_audio_for_wake_word(duration=2, sample_rate=16000, threshold=0.06):

    """
    отслеживание wake-word
    :param duration:
    :param sample_rate:
    :param threshold:
    :return:
    """
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype=np.float32)
    sd.wait()
    audio = np.squeeze(audio)

    # Check if there is sufficient sound level to consider this as an actual wake word attempt
    if np.max(np.abs(audio)) < threshold:
        print("Wake word not detected (sound level too low). Waiting...")
        return None

    return audio


def recognize_speech_whisper( whisper_model,language='ru'):

    """
    Распознование аудио
    :param whisper_model:
    :param language:
    :return:
    """
    print("Listening...")
    audio = record_audio()
    print("Processing audio with Whisper...")
    result = whisper_model.transcribe(np.array(audio), fp16=True, language=language)
    print(f"Transcription result: {result['text']}")
    return result['text']

def generate_silent_audio(duration=1):
    # Creates a silent audio file of the specified duration in seconds
    sample_rate = 16000  # Example rate
    num_samples = duration * sample_rate
    silent_audio = np.zeros(num_samples, dtype=np.float32)
    audio_bytes = silent_audio.tobytes()  # Convert to bytes for sending
    return audio_bytes

async def main():
    audio_data = await text_to_speech("Транзакция 1 успешно оплачена.")
    print("Audio data generated:", len(audio_data), "bytes")

if __name__ == "__main__":
    asyncio.run(main())