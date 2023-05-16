import openai
import io
from pydub import AudioSegment
from pydub.playback import play
import simpleaudio as sa
import speech_recognition as sr
import json
import re
import os
from dotenv import load_dotenv
from google.cloud import texttospeech_v1 as texttospeech

load_dotenv()

openai.api_key = os.environ.get('OPEN_AI_KEY')

# conversation_history_path = 'conversation_history.json'
speaking_rate = 1
    
def synthesize_text(text,speaking_rate):
    """Synthesizes speech from the input string of text."""
    client = texttospeech.TextToSpeechClient()
    # print("text is: ", text)
    input_text = texttospeech.SynthesisInput(text=text)
    voice = texttospeech.VoiceSelectionParams(
        language_code="he-IL",
        ssml_gender=texttospeech.SsmlVoiceGender.FEMALE,
    )
    audio_config = texttospeech.AudioConfig(audio_encoding=texttospeech.AudioEncoding.MP3, speaking_rate=speaking_rate, volume_gain_db=10)

    response = client.synthesize_speech(request={"input": input_text, "voice": voice, "audio_config": audio_config})

    # The response's audio_content is binary.
    with open("output.mp3", "wb") as out:
        out.write(response.audio_content)
        print('Audio content written to file "output.mp3"')

def update_conversation_history(initial_conversation_history, transcript, level):
    if not initial_conversation_history:
        conversation_history = []
        conversation_history.append({"role": "system", "content": f"""You are a Hebrew language tutor conversing with a student, and you speak only Hebrew. Using Hebrew language level {level} (where the level is between 1 and 10), engage in a collaborative storytelling game. Greet your student and explain the rules: You will say the first sentence of the story, the student will say the second sentence, you will say the third, and so on. In each of your messages, provide an IMPROVEMENT suggestion for the last TRANSCRIPT in terms of grammar and vocabulary, a RESPONSE in Hebrew, and a TRANSLATION of the response in English. Structure your response as follows:
IMPROVEMENT: <suggestion to improve the last TRANSCRIPT in terms of grammar and vocabulary, it should be in English except for the particular Hebrew words you recommend the user use>
RESPONSE: <your response in Hebrew, at language level {level}>
TRANSLATION: <English translation of your Hebrew response>"""})
        conversation_history.append({"role": "user", "content": "TRANSCRIPT: "+transcript})
    else:
        conversation_history = initial_conversation_history
        conversation_history.append({"role": "user", "content": "TRANSCRIPT: "+transcript})
    
    return conversation_history

def process_audio(audio_buffer, playback_speed, level, language, initial_conversation_history):

    # convert language to ISO-639-1 
    if language == "hebrew":
        language_code = "iw"
    else:
        language_code = "en"

    # Transcribe the audio using the Whisper ASR model
    transcript = openai.Audio.transcribe(
        file=audio_buffer,
        model="whisper-1",
        response_format="text",
        temperature=0,
        language=language_code, #"he-il",
        # prompt="האודיו מכיל אדם המקבל שיעורים ומשוחח עם המורה שלו."
    )

    print("Convo Hisotry:", initial_conversation_history,'\n\n')
    print("Transcript:", transcript,'\n\n')

    if transcript == '':
        return None

    # Update conversation history
    conversation_history = update_conversation_history(initial_conversation_history, transcript, level)

    # Make sure the conversation history json is not getting too long
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

    # Feed the conversation history to the GPT model using the Chat API
    # print(conversation_history)
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation_history
    )

    # Extract the generated response and its English translation
    generated_response = response['choices'][0]['message']['content']
    # print(conversation_history)
    conversation_history.append({"role": "assistant", "content": generated_response})
    # print(conversation_history)
    print("Generated Response:", generated_response,'\n\n')
    
    # Assume the generated_response variable contains the full response string

    response_pattern = r"RESPONSE:(.*?)(?=TRANSLATION:|$)"
    translation_pattern = r"TRANSLATION:(.*?)(?=IMPROVEMENT:|$)"
    improvement_pattern = r"IMPROVEMENT:(.*?)(?=RESPONSE:|$)"

    response_match = re.search(response_pattern, generated_response, re.DOTALL)
    translation_match = re.search(translation_pattern, generated_response, re.DOTALL)
    improvement_match = re.search(improvement_pattern, generated_response, re.DOTALL)

    response_text = response_match.group(1).strip() if response_match else ""
    translation_text = translation_match.group(1).strip() if translation_match else ""
    improvement_text = improvement_match.group(1).strip() if improvement_match else ""

    # Print the results
    print("Response:", response_text,'\n\n')
    print("English Translation:", translation_text,'\n\n')    
    print("Improvement:", improvement_text,'\n\n')    

    # # Save the updated conversation history to the JSON file
    # with open(conversation_history_path, 'w', encoding='utf-8') as f:
    #     json.dump(conversation_history, f, ensure_ascii=False, indent=2)

    # Synthesize the generated response and return the response_audio
    synthesize_text(response_text, speaking_rate=playback_speed)
    response_audio = AudioSegment.from_mp3("output.mp3")
    # print('ADDITION: ',generated_response if not initial_conversation_history else conversation_history)
    # print('INITAL CONVO HISTORY: ',initial_conversation_history,'\n\n')
    # print(conversation_history)
    # print('NOT ICH: ',not initial_conversation_history,'\n\n')
    # print('GR: ',generated_response,'\n\n')

    if not initial_conversation_history:
        conversation_addition = conversation_history
    else:
        conversation_addition = conversation_history[-2:]

    # print('CA: ',conversation_addition,'\n\n')
    return response_audio, response_text, translation_text, improvement_text, transcript, conversation_addition
