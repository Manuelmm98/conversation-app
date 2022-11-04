from flask import Flask, request, jsonify
import os
# Modules for Bloom
from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed
# Modules for Database connection and manipulation
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import datetime
# Whisper libraries
import torch
import whisper

# Creating Flask backend
app = Flask(__name__)
app.config['DEBUG'] = True

# Database configurations and modules
# The URI should be changed to the database location (this is for Windows user and sqlite, for others check at:
# https://flask-sqlalchemy.palletsprojects.com/en/2.x/config/)
app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///db.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# To integrate SQLAlchemy to flask
db = SQLAlchemy(app)
# To serialize the data from SQL and transform it to be sent to the frontend
ma = Marshmallow(app)

# Loading Whisper and Bloom models to be more efficient while executing our app
# Loading Whisper model
device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model("tiny", device=device)
# # Load Model and Tokenizer
model_bloom = AutoModelForCausalLM.from_pretrained("bigscience/bloom-560m", use_cache=True)
tokenizer = AutoTokenizer.from_pretrained("bigscience/bloom-560m")
set_seed(424242)


# App route to take an audioblob and to transcribe it with Whisper
@app.route('/api/transcript', methods=['POST', 'GET'])
def convert_audio():
    """This method should take in audio as a blob and return a transcript."""
    # Save audio to file
    audio_file = 'audio.wav'
    audio_blob = request.files.get('audio')
    if audio_blob:
        audio_blob.save(audio_file)
        
#         # Loading Whisper and Bloom models to be more efficient while executing our app
#         # Loading Whisper model
#         device = "cuda" if torch.cuda.is_available() else "cpu"
#         model = whisper.load_model("base", device=device)
        
        # Import file into whisper and delete original file
        audio = whisper.load_audio(audio_file)
        os.remove(audio_file)

        # Load audio and pad/trim it to fit 30 seconds
        audio = whisper.pad_or_trim(audio)

        # make log-Mel spectrogram and move to the same device as the model
        mel = whisper.log_mel_spectrogram(audio).to(model.device)

        # detect the spoken language
        _, probs = model.detect_language(mel)

        # decode the audio
        options = whisper.DecodingOptions(fp16=False)
        result = whisper.decode(model, mel, options)

        return jsonify({
            'transcript': result.text
        }), 200
    return jsonify({'transcript': "the audio request has failed"})


# Bloom Model function to answer to the transcripts and questions
def answering(inp):

#     # Load Model and Tokenizer
#     model_bloom = AutoModelForCausalLM.from_pretrained("bigscience/bloom-1b1", use_cache=True)
#     tokenizer = AutoTokenizer.from_pretrained("bigscience/bloom-1b1")
#     set_seed(424242)
    
    # Tokenization of the input values
    device = "cuda" if torch.cuda.is_available() else "cpu"
    input_ids = tokenizer(inp, return_tensors='pt').to(device=device)

    # Model Inference
    sample = model_bloom.generate(**input_ids, max_length=100, top_k=0, temperature=0.7)

    # Decoding the generated sequence of tokens
    response = tokenizer.decode(sample[0], truncate_before_pattern=[r"\n\n^#", "^'''", "\n\n\n"])

    # # https://stackoverflow.com/questions/16816013/is-it-possible-to-print-using-different-colors-in-ipythons-notebook
    # # code to print in HTML with a certain style, it won't be used now
    # from IPython.display import HTML as html_print
    #
    # def cstr(s, color='black'):
    #     # return "<text style=color:{}>{}</text>".format(color, s)
    #     return "<text style=color:{}>{}</text>".format(color, s.replace('\n', '<br>'))
    #
    # def cstr_with_newlines(s, color='black'):
    #     return "<text style=color:{}>{}</text>".format(color, s.replace('\n', '<br>'))
    #
    # color_resp = html_print(cstr(inp, color='#f1f1c7') + cstr(response, color='#a1d8eb'))
    #
    # return response, color_resp
    return response


# App route to take a transcript and question and return the answer with the Bloom function above
@app.route('/api/question', methods=['POST', 'GET'])
def query():
    """This method should take in a transcript and query and return the answer."""
    # Requesting data to the frontend with the key:"transcript"
    transcript = request.form['transcript']

    # Requesting data to frontend with the key: "value" to get the question asked
    quest = request.form.get('question', 'Requested question failed')
    inter = """. Question: """
    ans = """ """
    inp = transcript + inter + quest + ans
    # Calling the Bloom function
    final_answer = answering(inp)
    
    add_question(transcript, quest, final_answer)

    return jsonify({
        'answer': final_answer
    }), 200


# App route to check that the app send data to the frontend
@app.route('/', methods=['GET'])
def prueba():
    work = False
    # if (final_answer != '') & (transcript != ''):
    #     work = True

    return{
        'Whisper and Bloom together': work,
    }


# Database Code


# Database Model, storing transcript, question and answer
class Whispering(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.datetime.now)
    transcript = db.Column(db.String(200), nullable=False)
    question = db.Column(db.String(200), nullable=False)
    answer = db.Column(db.String(200), nullable=False)

    def __init__(self, transcript, question, answer):
        self.transcript = transcript
        self.question = question
        self.answer = answer


# Schema to serialize the SQL data and transform it to the frontend with Marshmallow
class WhisperSchema(ma.Schema):
    class Meta:
        fields = ('id', 'date', 'transcript', 'question', 'answer')


# Initializing the Schemas, the first one to get one sequence and the other to get all the sequences
whisper_schema = WhisperSchema()
whispers_schema = WhisperSchema(many=True)


# Sending all the data stored in the database to the frontend
@app.route('/get', methods=["GET"])
def get_transcript():
    all_transcripts = Whispering.query.all()
    results = whispers_schema.dump(all_transcripts)
    return jsonify(results)


# Sending data specifying the id
@app.route('/get/<id>/', methods=['GET'])
def id_search(id):
    id_transcript = Whispering.query.get(id)
    return whisper_schema.jsonify(id_transcript)


# Function to test inserting data into the database
def add_question(transcript_flask, question_flask, answer_flask):
    transcript = transcript_flask
    question = question_flask
    answer = answer_flask

    save_transcript = Whispering(transcript, question, answer)
    db.session.add(save_transcript)
    db.session.commit()
    # return whisper_schema.jsonify()

# # This part of the code will include the data in the database
# @app.route('/alldata', methods=['GET'])
# def requesting_data():
#     # Requesting data to the frontend with the key:"transcript"
#     transcript_flask = request.args.get('transcript','The request method is not finding the transcript')
#     # Requesting data to frontend with the key: "value" to get the question asked
#     question_flask = request.args.get('value', 'Requested question failed')
#     # Requesting final answer
#     answer_flask = request.args.get('answer', 'Requested answer failed')
#     add_question(transcript_flask, question_flask, answer_flask)

# # This part of the code will include the data in the database, this is just a test with random values
# with app.app_context():
#     transcript_flask = 'This is an internship at Comed '
#     question_flask = 'What did you talk about? '
#     answer_flask = 'Test'
#
#     add_question(transcript_flask, question_flask, answer_flask)


# To initialize the app
if __name__ == '__main__':
    app.run(debug=True, host='localhost')
