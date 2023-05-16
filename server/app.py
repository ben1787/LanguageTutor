from flask import Flask, request, jsonify
from flask_wtf import FlaskForm
from flask_wtf.file import FileField
from wtforms.validators import DataRequired
from audio_processing import process_audio, play_welcome_message
import io
import os
import base64
import json

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a-very-secret-key'

conversation_history_file = "conversation_history.json"
if os.path.exists(conversation_history_file):
    os.remove(conversation_history_file)

class AudioUploadForm(FlaskForm):
    audio_data = FileField(validators=[DataRequired()])

# Custom BytesIO class with a name attribute since the openai whisper API requires a name attribute
class NamedBytesIO(io.BytesIO):
    def __init__(self, *args, **kwargs):
        self._name = kwargs.pop("name", "temp.wav")
        super().__init__(*args, **kwargs)

    @property
    def name(self):
        return self._name
    
@app.route('/play_welcome_message', methods=['POST'])
def play_welcome_message_route():
    playback_speed = float(request.form.get('playback_speed', 1.0))
    response_audio, welcome_message = play_welcome_message(playback_speed)

    response_audio_bytes = io.BytesIO()
    response_audio.export(response_audio_bytes, format="mp3")
    response_audio_bytes.seek(0)
    response_audio_base64 = base64.b64encode(response_audio_bytes.read()).decode('utf-8')
    return jsonify({"response_audio": response_audio_base64, 
                    "welcome_message": welcome_message})


@app.route('/process_audio', methods=['POST'])
def process_audio_route():
    print("Received files:", request.files)

    if 'audio_data' not in request.files:
        return jsonify({'error': 'Missing audio_data field'}), 400

    audio_data = request.files['audio_data']
    audio_buffer = NamedBytesIO(audio_data.read())

    # Get the playback rate from the request
    playback_speed = float(request.form.get('playback_speed', 1.0))
    level = int(request.form.get('level', 1)) # Get the level parameter from the request
    language = request.form.get('language')
    conversation_history = json.loads(request.form.get('conversation_history', '[]'))

    response_audio, generated_response, english_translation, improvement, transcript, conversation_addition, suggestion_text, full_story = process_audio(audio_buffer, playback_speed, level, language, conversation_history)

    print("Convo Addition: ",conversation_addition)

    response_audio_bytes = io.BytesIO()
    response_audio.export(response_audio_bytes, format="mp3")
    response_audio_bytes.seek(0)
    response_audio_base64 = base64.b64encode(response_audio_bytes.read()).decode('utf-8')
    return jsonify({"response_audio": response_audio_base64, 
                    "generated_response": generated_response, 
                    "english_translation": english_translation, 
                    "improvement": improvement, 
                    "transcript": transcript,
                    "conversation_addition": conversation_addition,
                    "suggestion_text": suggestion_text,
                    "full_story": full_story})

if __name__ == '__main__':
    app.run(host='192.168.1.137', debug=True)