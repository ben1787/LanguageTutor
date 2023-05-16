# Import required libraries
from pydub import AudioSegment

import openai
openai.api_key = "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"

import io

def load_m4a_file(file_path):
    """
    This function takes a file path to an .m4a file and returns an AudioSegment object.
    
    Args:
        file_path (str): The path to the .m4a file.
        
    Returns:
        audio_segment (AudioSegment): The loaded audio segment.
    """
    # Load the .m4a file using the from_file method of AudioSegment
    # The format parameter is set to 'm4a' to indicate the file format
    audio_segment = AudioSegment.from_file(file_path, format='m4a')
    
    return audio_segment

# Replace 'path/to/your/audio_file.m4a' with the actual file path of the .m4a file you want to load
audio_file_path = 'C:/Users/Ben/Downloads/shalom_imma.m4a'

# Call the load_m4a_file function and store the returned AudioSegment object
loaded_audio = load_m4a_file(audio_file_path)

# Print the loaded_audio object to confirm successful loading of the .m4a file
print(loaded_audio)

def transcribe_audio(audio_segment):
    """
    This function takes a Pydub AudioSegment object and transcribes it using the Whisper ASR model.

    Args:
        audio_segment (pydub.audio_segment.AudioSegment): The audio segment to transcribe.

    Returns:
        transcript (str): The transcription of the audio segment.
    """

    # Export the audio segment to a BytesIO object in .mp3 format
    audio_data = io.BytesIO()
    audio_segment.export(audio_data, format="mp3")
    audio_data.seek(0)

    # Transcribe the audio using the Whisper ASR model
    transcript_response = openai.Audio.transcribe(
        file=audio_data,
        model="whisper-1",
        response_format="text",
        language="en",
    )

    # Extract the transcript text from the response
    transcript = transcript_response["data"]["transcript"]

    return transcript

# Call the transcribe_audio function with the loaded audio and print the transcript
transcription = transcribe_audio(loaded_audio)
print(transcription)
