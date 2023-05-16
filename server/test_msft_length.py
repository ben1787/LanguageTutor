import pyttsx3

# Initialize the pyttsx3 engine
engine = pyttsx3.init()

# Get a list of available voices
voices = engine.getProperty('voices')

# Print the voice ID and name of each available voice
for voice in voices:
    print("Voice:")
    print(" - ID: %s" % voice.id)
    print(" - Name: %s" % voice.name)

engine = pyttsx3.init()
engine.setProperty('rate', 200) 
engine.setProperty('voice', 'HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\Speech\Voices\Tokens\TTS_MS_EN-US_ZIRA_11.0')
engine.say('שלום, איך היום?')
# engine.say("Hello, I'm Jarvis, your personal assistant. Say my name and ask me anything:")
engine.runAndWait()