import openai
from gtts import gTTS
import io
from pydub import AudioSegment
from pydub.playback import play
import simpleaudio as sa
import speech_recognition as sr
import json
import os
import time
import pyaudio
from dotenv import load_dotenv
from google.cloud import texttospeech_v1 as texttospeech

load_dotenv()

openai.api_key = os.environ.get('OPEN_AI_KEY')

conversation_history_path = 'conversation_history.json'
speaking_rate = .7

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
    
def synthesize_text(text,speaking_rate):
    """Synthesizes speech from the input string of text."""
    client = texttospeech.TextToSpeechClient()

    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="he-IL",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3, speaking_rate=speaking_rate)

    response = client.synthesize_speech(request={"input": input_text, "voice": voice, "audio_config": audio_config})

    # The response's audio_content is binary.
    with open("output.mp3", "wb") as out:
        out.write(response.audio_content)
        print('Audio content written to file "output.mp3"')

# Load conversation history from JSON file or create an empty list if the file doesn't exist
if os.path.exists(conversation_history_path):
    with open(conversation_history_path, 'r', encoding='utf-8') as f:
        conversation_history = json.load(f)
else:
    conversation_history = []
    conversation_history.append({"role": "system", "content": """You are a helpful hebrew language tutor. 
    Respond in Hebrew at the level of the user, which you should infer from his speech. 
    Use male conjugation. Your responses should be very short, never more than 15 words. 
    If he specifically asks for something translated into English, then do so. 
    Keep in mind the text is being sent to you after being transcribed with a speech to text API so there could be errors in the transcription. 
    As such, if there is a word out of place, try to figure out what the word is from context and that it might be similar phentically to the word that seems out of place. 
    For example, if the user asks you to translate a word, assume first that it is a word you said in your last comment."""})

while True:
    # Record audio from the microphone
    with sr.Microphone() as source:
        print("Please speak now...")
        audio = recognizer.listen(source)

    # Save recorded audio to an in-memory file-like object
    audio_buffer = NamedBytesIO(name="temp.wav")
    audio_buffer.write(audio.get_wav_data())
    audio_buffer.seek(0)

    # Transcribe the audio using the Whisper ASR model
    transcript = openai.Audio.transcribe(
        file=audio_buffer,
        model="whisper-1",
        response_format="text",
        temperature=0,
        language="en",
        prompt="The audio may contain both Hebrew and English. האודיו מכיל אדם המקבל שיעורים ומשוחח עם המורה שלו."
    )

    print("Transcript:", transcript)

    if "goodbye" in transcript.lower():
        print("Ending conversation with the tutor.")
        synthesize_text('You mentioned the word goodbye, and that''s my keyword. So have a good one and let''s talk again soon!', speaking_rate=1)
        response_audio = AudioSegment.from_mp3("output.mp3")
        play(response_audio)
        if os.path.exists(conversation_history_path):
            os.remove(conversation_history_path)
        break

    if transcript == '':
        next

    # Make sure the conversation history json is not getting too long
    # Trim the conversation history to a maximum of conversation_history_limit tokens by deleting the oldest messages (excluding system messages)
    conversation_history_limit = 3000
    conversation_history_token_count = sum(len(message["content"].split()) for message in conversation_history if message["role"] != "system")
    if conversation_history_token_count > conversation_history_limit:
        excess_tokens = conversation_history_token_count - conversation_history_limit
        for message in conversation_history:
            if message["role"] == "system":
                continue
            message_token_count = len(message["content"].split())
            if excess_tokens > message_token_count:
                # This message is over the limit so remove it
                excess_tokens -= message_token_count
                conversation_history.remove(message)



    # Add user message to the conversation history
    conversation_history.append({"role": "user", "content": transcript})

    # Feed the conversation history to the GPT model using the Chat API
    print(conversation_history)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation_history
    )

    # Extract the generated response
    generated_response = response['choices'][0]['message']['content']
    print("Generated Response:", generated_response)

    # Add the generated response to the conversation history
    conversation_history.append({"role": "assistant", "content": generated_response})

    # Save the updated conversation history to the JSON file
    with open(conversation_history_path, 'w', encoding='utf-8') as f:
        json.dump(conversation_history, f, ensure_ascii=False, indent=2)

    # Synthesize the generated response and play the audio
    synthesize_text(generated_response, speaking_rate=speaking_rate)
    response_audio = AudioSegment.from_mp3("output.mp3")
    play(response_audio)

