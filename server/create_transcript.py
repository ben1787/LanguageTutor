import openai
openai.api_key = "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"

audio_file_path = 'C:/Users/Ben/Downloads/shalom_imma.m4a'

audio_file= open(audio_file_path, "rb")

# Transcribe the audio using the Whisper ASR model
transcript = openai.Audio.transcribe(
    file=audio_file,
    model="whisper-1",
    response_format="text",
    temperature=0,
    language="en",
    prompt="The audio may contain both Hebrew and English. האודיו מכיל אדם המקבל שיעורים ומשוחח עם המורה שלו."
)

print(transcript)