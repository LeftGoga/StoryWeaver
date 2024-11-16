import sounddevice as sd
import numpy as np
from gtts import gTTS
import io


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
    имплементация TTS
    :param text:
    :param language:
    :return:
    """
    if "No-op" in text:
        print("Ignoring placeholder response for text-to-speech.")
        return generate_silent_audio(duration=1)
    tts = gTTS(text=text, lang=language, slow=False)
    audio_buffer = io.BytesIO()
    tts.write_to_fp(audio_buffer)
    audio_buffer.seek(0)
    return audio_buffer.read()

def record_audio_fixed_duration(duration=5, sample_rate=16000):
    print("Recording input after wake word...")
    audio = sd.rec(int(duration * sample_rate), samplerate=sample_rate, channels=1, dtype=np.float32)
    sd.wait()
    return np.squeeze(audio)

def record_audio_for_wake_word(duration=2, sample_rate=16000, threshold=0.03):

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