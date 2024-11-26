from gtts import gTTS
import io
from concurrent.futures import ThreadPoolExecutor, TimeoutError

def generate_tts_audio_with_timeout(text, language, timeout=10):
    """
    Generate TTS audio with a manual timeout.
    """
    def generate_audio():
        tts = gTTS(text=text, lang=language, slow=False)
        audio_buffer = io.BytesIO()
        tts.write_to_fp(audio_buffer)
        audio_buffer.seek(0)
        return audio_buffer.read()

    # Use ThreadPoolExecutor to run the TTS generation in a separate thread
    with ThreadPoolExecutor() as executor:
        future = executor.submit(generate_audio)
        try:
            return future.result(timeout=timeout)
        except TimeoutError:
            print(f"TTS generation timed out after {timeout} seconds.")
            return None
        except Exception as e:
            print(f"Error during TTS generation: {e}")
            return None

# Example usage
audio_data = generate_tts_audio_with_timeout("Транзакция 1 успешно оплачена.", "ru")
if audio_data:
    print("Audio generated successfully!")
    print(len(audio_data))
else:
    print("Failed to generate audio.")