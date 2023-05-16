import io
import speech_recognition as sr
from pydub import AudioSegment
from pydub.playback import play
from audio_processing import process_audio

# Initialize the recognizer
recognizer = sr.Recognizer()

# Custom BytesIO class with a name attribute
class NamedBytesIO(io.BytesIO):
    def __init__(self, *args, **kwargs):
        self._name = kwargs.pop("name", "temp.wav")
        super().__init__(*args, **kwargs)

    @property
    def name(self):
        return self._name
    
# Record audio from the microphone
with sr.Microphone() as source:
    print("Please speak now...")
    audio = recognizer.listen(source)

# Save recorded audio to an in-memory file-like object
audio_buffer = NamedBytesIO()
audio_buffer.write(audio.get_wav_data())
audio_buffer.seek(0)

# Call the process_audio function
response_audio = process_audio(audio_buffer)

# Play the response audio
play(response_audio[0])
