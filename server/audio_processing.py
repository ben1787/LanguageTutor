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
    
def synthesize_text(text,speaking_rate,language_code="he-IL"):
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

def getStoryFromConversation(conversation_history):
    full_story = ''
    for elem in conversation_history:
    # Extract all content enclosed in double backticks
        if elem['role'] == 'user':
            match = re.search(r'``([^`]+)``', elem['content'])
            if match:
                full_story += ' ' + match.group(1).rstrip('\n')
    # Extract all sentences that start with "YOUR SENTENCE" and end in a newline character
        if elem['role'] == 'assistant':
            match = re.search(r'YOUR SENTENCE:\s*(.+)\n', elem['content'])
            if match:
                full_story += ' ' + match.group(1).rstrip('\n')
        
    return full_story
                
def update_conversation_history(initial_conversation_history, transcript, level):
    if not initial_conversation_history:
        conversation_history = []
        conversation_history.append({"role": "system", "content": f"""You are a Hebrew language tutor conversing with a student, and you are colaborating on creating a story with your student. On a scale of 1 to 10, 1 being the simplest Hebrew and 10 being the most difficult Hebrew, speak at level {level}."""})
        conversation_history.append({"role": "user", "content": f"""My suggestion for the next sentence(s) in the story is delimited below using double backticks:

``{transcript}``

Suggest an improvement in vocabulary and grammar for the text in double backticks.

Then suggest a next sentence in the story. On a scale of 1 to 10, 1 being the simplest Hebrew and 10 being the most difficult Hebrew, use level {level}.

Then suggest a hebrew word for me to use in my next sentence that will come after your continuation of the story.

Structure your response EXACTLY as follows:

IMPROVEMENT: <provide an improved version of the sentence in Hebrew if needed>

YOUR SENTENCE: <choose a next Hebrew sentence for the story to come after the text in double backticks, this should only be in Hebrew. Translation does not belong here, it belongs in the next line.>

TRANSLATION: <translate YOUR SENTENCE into english>

WORD SUGGESTION: <write your word suggestion here along with its english translation>


Below I will provide an example prompt in triple backticks and below that an ideal response:

```היה איש, ושמעו היה בן.```

IMPROVEMENT: היה איש, ושמו היה בן.

YOUR SENTENCE: הוא היה חקלאי צעיר וגר בכפר קטן.

TRANSLATION: He was a young farmer who lived in a small village.

WORD SUGGESTION: שדה (sadeh) - field"""})
    else:
        conversation_history = initial_conversation_history
        conversation_history.append({"role": "user", "content": f"""My suggestion for the next sentence(s) in the story is delimited below using double backticks:

``{transcript}``

Suggest an improvement in vocabulary and grammar for the text in double backticks.

Then suggest a next sentence in the story. On a scale of 1 to 10, 1 being the simplest Hebrew and 10 being the most difficult Hebrew, use level {level}.

Then suggest a hebrew word for me to use in my next sentence that will come after your continuation of the story.

Structure your response EXACTLY as follows:

IMPROVEMENT: <provide an improved version of the sentence in Hebrew if needed>

YOUR SENTENCE: <choose a next Hebrew sentence for the story to come after the text in double backticks, this should only be in Hebrew>

TRANSLATION: <translate YOUR SENTENCE into english>

WORD SUGGESTION: <write your word suggestion here along with its english translation>


Below I will provide an example prompt in triple backticks and below that an ideal response:

```היה איש, ושמעו היה בן.```

IMPROVEMENT: היה איש, ושמו היה בן.

YOUR SENTENCE: הוא היה חקלאי צעיר וגר בכפר קטן.

TRANSLATION: He was a young farmer who lived in a small village.

WORD SUGGESTION: שדה (sadeh) - field
"""})
    
    return conversation_history

def getGPTMessages(conversation_history, just_story):
    copy_conversation_history = conversation_history.copy()
    if just_story:
        gpt_messages = []
        gpt_messages.append(copy_conversation_history.pop(0))
        last_message = copy_conversation_history.pop()
        gpt_messages.append({"role": "user", "content": f"""The story so far is below delimited by single backticks:
    
`{getStoryFromConversation(copy_conversation_history)}`"""})
        gpt_messages.append(last_message)
    else:
        gpt_messages = conversation_history

    return gpt_messages

def play_welcome_message(playback_speed):
    welcome_message = "Hi! My name is Tamar and I will be your Hebrew tutor today. Right now I am an expert at one particular game called Tale Tag, so let's play it! Here's how it works. Our goal is to write a story together. I will say the first sentence. Then I will give you a word for you to use in the next sentence. Then I will make up a third sentence and so forth. At the end we will have written a great story together."
    synthesize_text(welcome_message, speaking_rate=playback_speed, language_code="en-IL")
    response_audio = AudioSegment.from_mp3("output.mp3")
    return response_audio, welcome_message

def translateToLearningLanguage(text):
    request_text = []
    request_text.append({"role": "user", "content": f"Translate the text delimited by double backticks into Hebrew: ``{text}``"})
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=request_text
    )

    # Extract the generated response
    return response['choices'][0]['message']['content']

def process_audio(audio_buffer, playback_speed, level, language, initial_conversation_history):

    # convert language to ISO-639-1 
    if language == "hebrew":
        language_code = "iw"
    else:
        language_code = "en"

    # Transcribe the audio using the Whisper ASR model
    raw_transcript = openai.Audio.transcribe(
        file=audio_buffer,
        model="whisper-1",
        response_format="text",
        temperature=0,
        language=language_code, #"he-il",
        prompt="זה הזמן לחגוג, אנחנו עשינו זאת!" if language_code == 'iw' else "It's time to celebrate, we did it!"
    )
    print("Raw Transcript:\n",raw_transcript)
    if language_code == "en":
        transcript = translateToLearningLanguage(raw_transcript).strip('\n`')
    else:
        transcript = raw_transcript.strip('\n`')

    # print("Convo History:", initial_conversation_history,'\n\n')
    print("Transcript:", transcript,'\n\n')

    if transcript == '':
        return None

    # Update conversation history
    conversation_history = update_conversation_history(initial_conversation_history, transcript, level)

    # Make sure the conversation history json is not getting too long
    conversation_history_limit = 3000
    conversation_history_token_count = sum(len(message["content"].split()) for message in conversation_history if message["role"] != "system")
    print('Token Count 1: ',conversation_history_token_count)
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

    conversation_history_token_count = sum(len(message["content"].split()) for message in conversation_history if message["role"] != "system")
    print('Token Count 2: ',conversation_history_token_count)

    just_story = True
    print(conversation_history)
    gpt_messages = getGPTMessages(conversation_history, just_story)
    print(conversation_history)
    print('GPT Messages:\n', gpt_messages)

    # Feed the conversation history to the GPT model using the Chat API
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=gpt_messages
    )

    # Extract the generated response and its English translation
    generated_response = response['choices'][0]['message']['content']
    # print(conversation_history)
    conversation_history.append({"role": "assistant", "content": generated_response})
    # print(conversation_history)
    print("Generated Response:", generated_response,'\n\n')
    
    # Assume the generated_response variable contains the full response string

    response_pattern = r"YOUR SENTENCE:(.*?)(?=\n|$)"
    translation_pattern = r"TRANSLATION:(.*?)(?=\n|$)"
    improvement_pattern = r"IMPROVEMENT:(.*?)(?=\n|$)"
    suggestion_pattern = r"WORD SUGGESTION:(.*?)(?=\n|$)"

    response_match = re.search(response_pattern, generated_response, re.DOTALL)
    translation_match = re.search(translation_pattern, generated_response, re.DOTALL)
    improvement_match = re.search(improvement_pattern, generated_response, re.DOTALL)
    suggestion_match = re.search(suggestion_pattern, generated_response, re.DOTALL)

    response_text = response_match.group(1).strip('\n` ') if response_match else ""
    translation_text = translation_match.group(1).strip('\n` ') if translation_match else ""
    improvement_text = improvement_match.group(1).strip('\n` ') if improvement_match else ""
    suggestion_text = suggestion_match.group(1).strip('\n` ') if suggestion_match else ""

    # Print the results
    print("Response:", response_text,'\n\n')
    print("English Translation:", translation_text,'\n\n')    
    print("Improvement:", improvement_text,'\n\n')    
    print("Suggestion:", suggestion_text,'\n\n')    

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

    # Get full story
    full_story = getStoryFromConversation(conversation_history)

    print("Full Story: ",full_story)


    # print('CA: ',conversation_addition,'\n\n')
    return response_audio, response_text, translation_text, improvement_text, transcript, conversation_addition, suggestion_text, full_story
