from gtts import gTTS
from pydub import AudioSegment
from pydub.playback import play
import simpleaudio as sa
import speech_recognition as sr
from dotenv import load_dotenv
import time
from google.cloud import texttospeech_v1 as texttospeech

load_dotenv()

def synthesize_text(text, language_code):
    time_rec = time.time()
    """Synthesizes speech from the input string of text."""
    from google.cloud import texttospeech

    client = texttospeech.TextToSpeechClient()

    input_text = texttospeech.SynthesisInput(text=text)

    # Note: the voice can also be specified by name.
    # Names of voices can be retrieved with client.list_voices().
    print('voice')
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        # name="en-US-Standard-C",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )

    print('audio_config')
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )

    print('response')
    # print time
    print("8.1 Elapsed time: {:.2f} seconds".format(time.time()-time_rec))
    time_rec = time.time()
    response = client.synthesize_speech(
        request={"input": input_text, "voice": voice, "audio_config": audio_config}
    )
    # print time
    print("8.1 Elapsed time: {:.2f} seconds".format(time.time()-time_rec))
    time_rec = time.time()

    print('open ', time.time())
    # The response's audio_content is binary.
    with open("output.mp3", "wb") as out:
        out.write(response.audio_content)
        print('opened')
        print('Audio content written to file "output.mp3"')

synthesize_text('Hello, I"m Jarvis, your personal assistant. Say my name and ask me anything:',"he-IL")
print('gtts done ', time.time())
import pyttsx3

engine = pyttsx3.init()
engine.say("Hello, I'm Jarvis, your personal assistant. Say my name and ask me anything:")
engine.runAndWait()
print('msft done ', time.time())