from flask import Flask, request, jsonify
import os

# Load whisper
# TODO: Check if there's a better way to Dockerize this so the model
#       isn't re-downloaded each time the image is started
import torch
import whisper
Device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("tiny", device=Device)

app = Flask(__name__)


@app.route('/api/transcript', methods=['POST'])
def convert_audio():
    """This method should take in audio as a blob and return a transcript."""
    # Save audio to file (if there's a way to import this directly into whisper that would be better)
    audio_file = 'audio.wav'
    audio_blob = request.files.get('audio')
    audio_blob.save(audio_file)

    # Import file into whisper and delete original file
    audio = whisper.load_audio(audio_file)
    os.remove(audio_file)  # Warning: This file will linger if there's an error with the import

    # Pad/trim audio to fit 30 seconds
    audio = whisper.pad_or_trim(audio)

    # make log-Mel spectrogram and move to the same device as the model
    mel = whisper.log_mel_spectrogram(audio).to(model.device)

    # decode the audio
    options = whisper.DecodingOptions(fp16=False)
    result = whisper.decode(model, mel, options)

    return jsonify({
        'transcript': result.text
    }), 200


@app.route('/api/query', methods=['GET'])
def query():
    """This method should take in a transcript and query and return the answer."""
    transcript = request.args.get('transcript')
    query = request.args.get('query')
    return jsonify({
        'text': "This should return an answer."
    }), 200
