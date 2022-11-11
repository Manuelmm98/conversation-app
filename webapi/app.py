from flask import Flask, request, jsonify
import os
# Modules for Bloom
from transformers import AutoModelForCausalLM, AutoTokenizer, set_seed, AutoModelForSequenceClassification
from transformers import BloomForQuestionAnswering, BloomTokenizerFast, pipeline
# Modules for Database connection and manipulation
from flask_sqlalchemy import SQLAlchemy
from flask_marshmallow import Marshmallow
import datetime
# Whisper libraries
import torch
import whisper
import re

# # Importing models from local
# from localmodel import model, model_bloom, tokenizer

# Creating Flask backend
app = Flask(__name__)
app.config['DEBUG'] = True

# Database configurations and modules
# The URI should be changed to the database location (this is for Windows user and sqlite, for others check at:
# https://flask-sqlalchemy.palletsprojects.com/en/2.x/config/)
app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///newdb.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# To integrate SQLAlchemy to flask
db = SQLAlchemy(app)
# To serialize the data from SQL and transform it to be sent to the frontend
ma = Marshmallow(app)

# Loading Whisper and Bloom models to be more efficient while executing our app
# Loading Whisper model locally (Whisper model download with jupyter is stored in ~/.cache/whisper
device = "cuda" if torch.cuda.is_available() else "cpu"
model = whisper.load_model(name="base")
# Load Model and Tokenizer, from the directory saved in localmodel.py
model_bloom = AutoModelForCausalLM.from_pretrained("bigscience/bloom-560m", use_cache=True)
tokenizer = AutoTokenizer.from_pretrained("bigscience/bloom-560m")
set_seed(424242)

### THERE ARE FIVE DIFFERENT OPTIONS TO EXTRACT THE DESIRED INFORMATION:
### 1. USING REGEX MANUAL EXPRESSIONS
### 2. COMBINING BERT PARAPHRASING MODEL WITH REGEX MANUAL EXPRESSIONS
### 3. USING BLOOM LANGUAGE MODELING MODEL
### 4. USING BLOOM QUESTION ANSWERING MODEL
### 5. COMBINING BOTH BLOOM MODEL WITH REGEX MANUAL EXPRESSIONS

## THIS IS THE FIRST OPTION
# # App route to take an audioblob and to transcribe it with Whisper
# @app.route('/api/transcript', methods=['POST', 'GET'])
# def convert_audio():
#     """This method should take in audio as a blob and return a transcript."""
#     # Save audio to file
#     audio_file = 'audio.wav'
#     audio_blob = request.files.get('audio')
#     if audio_blob:
#         audio_blob.save(audio_file)
        
#         # Import file into whisper and delete original file
#         audio = whisper.load_audio(audio_file)
#         os.remove(audio_file)

#         # Load audio and pad/trim it to fit 30 seconds
#         audio = whisper.pad_or_trim(audio)

#         # make log-Mel spectrogram and move to the same device as the model
#         mel = whisper.log_mel_spectrogram(audio).to(model.device)

#         # detect the spoken language
#         _, probs = model.detect_language(mel)

#         # decode the audio
#         options = whisper.DecodingOptions(fp16=False)
#         result = whisper.decode(model, mel, options)
        
#         # Obtaining the transcript
#         transcript = result.text
#         # Obtaining the information needed using regex manual expressions from re library
#         first_answer = getting_pole_ID(transcript)
#         second_answer = getting_damaged_equipment(transcript)
        
#         # Adding our results to the database
#         add_inspection(transcript, first_answer, second_answer)
        
#         return jsonify({
#             'transcript': result.text,
#             'answer': 'POLE_ID: ' + first_answer + ', EQUIPMENT_DAMAGED: ' + second_answer
#         }), 200
#     return jsonify({'transcript': "the audio request has failed"})

# Extracting PoleID and Damaged Equipment with Re library
def getting_damaged_equipment(string):
    string = string.lower()
    print(string)
    words = ['crossarm','cross-arm','cross arm', 'insulator', 'arrester', 'arrestor']
    findbool = False
    for word in words:
        if re.search(word,string) is not None:
            start_index = re.search(word,string).start()
            len_word = len(word)
            extracted_word = string[start_index:start_index+len_word]
            if word in words[0:3]:
                extracted_word = words[0].upper()
            elif word in words [4:6]:
                extracted_word = words[4].upper()
            extracted_word = extracted_word.upper()
            findbool = True
    if findbool == False:
        extracted_word = 'NULL'
    return extracted_word

def getting_pole_ID(string):
    string = string.lower()
    print(string)
    pattern = "[0-9]{1,9}"
    findbool = False
    if re.findall(pattern,string) is not None:
        extracted_ID = re.findall(pattern,string)
        findbool = True
        len_ID = len(extracted_ID)
        ID=''
        for i in range(len_ID):
            ID = ID + extracted_ID[i]
    if findbool == False:
        ID = 'No ID provided'
    return ID

## THIS IS THE SECOND OPTION
# BERT paraphrasing to get the equipment we want from an audio and the regex to get the ID
# App route to take an audioblob and to transcribe it with Whisper
@app.route('/api/transcript', methods=['POST', 'GET'])
def convert_audio():
    """This method should take in audio as a blob and return a transcript and the information needed."""
    # Save audio to file
    audio_file = 'audio.wav'
    audio_blob = request.files.get('audio')
    if audio_blob:
        audio_blob.save(audio_file)
        
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
        
        # Obtaining the transcript
        transcript = result.text
        
        first_answer = getting_pole_ID(transcript)
        confidence, second_answer = BERT(transcript)
    
        add_inspection(transcript, first_answer, second_answer)

        return jsonify({
            'transcript': result.text,
            'answer': 'POLE_ID: ' + first_answer + ', EQUIPMENT_DAMAGED: ' + second_answer + "Confidence: " + confidence
        }), 200

# BERT function to obtain the ID and the equipment
def BERT(transcript):
        tokenizer = AutoTokenizer.from_pretrained("bert-base-cased-finetuned-mrpc")
        model = AutoModelForSequenceClassification.from_pretrained("bert-base-cased-finetuned-mrpc")


        classes = [ "insulator", "crossarm", "arrester", "no"]
        upper_classes = ["INSULATOR", "CROSSARM", "ARRESTER", 'NULL']

        sequence_0 = transcript
        sequence_1 = classes[0]
        sequence_2 = classes[1]
        sequence_3 = classes[2]
        sequence_4 = classes[3]

        # The tokenizer will automatically add any model specific separators (i.e. <CLS> and <SEP>) and tokens to
        # the sequence, as well as compute the attention masks.
        crossarm = tokenizer(sequence_0, sequence_2, return_tensors="pt")
        insulator = tokenizer(sequence_0, sequence_1, return_tensors="pt")
        arrester = tokenizer(sequence_0, sequence_3, return_tensors="pt")
        null = tokenizer(sequence_0, sequence_4, return_tensors="pt")

        insulator_logits = model(**insulator).logits
        crossarm_logits = model(**crossarm).logits
        arrester_logits = model(**arrester).logits
        null_logits = model(**null).logits

        insulator_results = torch.softmax(insulator_logits, dim=1).tolist()[0][1]
        crossarm_results = torch.softmax(crossarm_logits, dim=1).tolist()[0][1]
        arrester_results = torch.softmax(arrester_logits, dim=1).tolist()[0][1]
        null_results = torch.softmax(null_logits, dim=1).tolist()[0][1]
        results = [insulator_results, crossarm_results, arrester_results, null_results]
        total = sum(results)
        equipment = upper_classes[0]
        higher_value = results[0]
        for i in range(len(results)-1):
            if higher_value < results[i+1]:
                equipment =  upper_classes[i+1]
                higher_value = results[i+1]
                
        confidence = 100* higher_value / total        
        return confidence, equipment

## THIS IS THE THIRD OPTION
# # BLOOM LM MODEL to get the information we want from an audio.
# # App route to take an audioblob and to transcribe it with Whisper
# @app.route('/api/transcript', methods=['POST', 'GET'])
# def convert_audio():
#     """This method should take in audio as a blob and return a transcript and the information needed."""
#     # Save audio to file
#     audio_file = 'audio.wav'
#     audio_blob = request.files.get('audio')
#     if audio_blob:
#         audio_blob.save(audio_file)
        
#         # Import file into whisper and delete original file
#         audio = whisper.load_audio(audio_file)
#         os.remove(audio_file)

#         # Load audio and pad/trim it to fit 30 seconds
#         audio = whisper.pad_or_trim(audio)

#         # make log-Mel spectrogram and move to the same device as the model
#         mel = whisper.log_mel_spectrogram(audio).to(model.device)

#         # detect the spoken language
#         _, probs = model.detect_language(mel)

#         # decode the audio
#         options = whisper.DecodingOptions(fp16=False)
#         result = whisper.decode(model, mel, options)
        
#         # Obtaining the transcript
#         transcript = result.text
#         # recommended transcript: The pole, which ID is 11647383, has the arrester damaged  
#         pole = """\n Question: What is the ID?\n Answer: the ID is """
#         equipment = """\n Question: What is damaged? Answer: the pole damage is """
#         inp = transcript + pole
#         # Calling the Bloom function
#         first_answer = answering_pole(inp)
#         second_inp = transcript + equipment
#         second_answer = answering_equipment(second_inp)
    
#         add_inspection(transcript, first_answer, second_answer)

#         return jsonify({
#             'transcript': result.text,
#             'answer': 'POLE_ID: ' + first_answer + ', EQUIPMENT_DAMAGED: ' + second_answer
#         }), 200



    
    
# Bloom Model function to obtain the PoleID
def answering_pole(inp):
   
    # Tokenization of the input values
    device = "cuda" if torch.cuda.is_available() else "cpu"
    input_ids = tokenizer(inp, return_tensors='pt').to(device=device)
    
    # Model Inference
    max_length = input_ids['input_ids'].size(dim=1) + 4
    sample = model_bloom.generate(**input_ids, max_length=max_length, top_k=0, temperature=0.7)

    # Decoding the generated sequence of tokens
    transcript_size = input_ids['input_ids'].size(dim=1)
    answer_size = max_length
    response_size = sample[0,transcript_size:answer_size]
    response = tokenizer.decode(response_size, truncate_before_pattern=[r"\n\n^#", "^'''", "\n\n\n"])

    return response

# Bloom Model function to obtain the damaged equipment
def answering_equipment(inp):
    
    # Tokenization of the input values
    device = "cuda" if torch.cuda.is_available() else "cpu"
    input_ids = tokenizer(inp, return_tensors='pt').to(device=device)
    
    # Model Inference
    max_length = input_ids['input_ids'].size(dim=1) + 4
    sample = model_bloom.generate(**input_ids, max_length=max_length, top_k=0, temperature=0.7)

    # Decoding the generated sequence of tokens
    transcript_size = input_ids['input_ids'].size(dim=1)
    answer_size = max_length
    response_size = sample[0,transcript_size:answer_size]
    response = tokenizer.decode(response_size, truncate_before_pattern=[r"\n\n^#", "^'''", "\n\n\n"])
    
    return response

## THIS IS THE FOURTH OPTION
# # BLOOM QA MODEL to get the information we want from an audio.
# # App route to take an audioblob and to transcribe it with Whisper
# @app.route('/api/transcript', methods=['POST', 'GET'])
# def convert_audio():
#     """This method should take in audio as a blob and return a transcript and the information needed."""
#     # Save audio to file
#     audio_file = 'audio.wav'
#     audio_blob = request.files.get('audio')
#     if audio_blob:
#         audio_blob.save(audio_file)
        
#         # Import file into whisper and delete original file
#         audio = whisper.load_audio(audio_file)
#         os.remove(audio_file)

#         # Load audio and pad/trim it to fit 30 seconds
#         audio = whisper.pad_or_trim(audio)

#         # make log-Mel spectrogram and move to the same device as the model
#         mel = whisper.log_mel_spectrogram(audio).to(model.device)

#         # detect the spoken language
#         _, probs = model.detect_language(mel)

#         # decode the audio
#         options = whisper.DecodingOptions(fp16=False)
#         result = whisper.decode(model, mel, options)
        
#         # Obtaining the transcript
#         transcript = result.text
        
#         # Calling the Bloom function
#         first_answer, second_answer = BloomQA_pole_equipment(transcript)
    
#         add_inspection(transcript, first_answer, second_answer)

#         return jsonify({
#             'transcript': result.text,
#             'answer': 'POLE_ID: ' + first_answer + ', EQUIPMENT_DAMAGED: ' + second_answer
#         }), 200

# Bloom Question Answering Model function to obtain the PoleID and the equipment damaged
def BloomQA_pole_equipment(transcript):
   
    tokenizer = BloomTokenizerFast.from_pretrained("bigscience/bloom-560m")
    model = BloomForQuestionAnswering.from_pretrained("bigscience/bloom-560m")

    answerer = pipeline(task="question-answering", model=model, tokenizer=tokenizer)

    question = "What is the Pole ID?"

    result = answerer(question, transcript)
    first_response = result['answer']
    
    question2 = "What is damaged?"
    result = answerer(question2, transcript)
    
    second_response = result['answer']
    
    return first_response, second_response

## HERE IT IS THE LAST OPTION
# # App route to take an audioblob and to transcribe it with Whisper
# @app.route('/api/transcript', methods=['POST', 'GET'])
# def convert_audio():
#     """This method should take in audio as a blob and return a transcript and the information needed."""
#     # Save audio to file
#     audio_file = 'audio.wav'
#     audio_blob = request.files.get('audio')
#     if audio_blob:
#         audio_blob.save(audio_file)
        
#         # Import file into whisper and delete original file
#         audio = whisper.load_audio(audio_file)
#         os.remove(audio_file)

#         # Load audio and pad/trim it to fit 30 seconds
#         audio = whisper.pad_or_trim(audio)

#         # make log-Mel spectrogram and move to the same device as the model
#         mel = whisper.log_mel_spectrogram(audio).to(model.device)

#         # detect the spoken language
#         _, probs = model.detect_language(mel)

#         # decode the audio
#         options = whisper.DecodingOptions(fp16=False)
#         result = whisper.decode(model, mel, options)
        
#         # Obtaining the transcript
#         transcript = result.text
#         pole = """\n Question: What is the ID?\n Answer: the ID is """
#         equipment = """\n Question: What is damaged? Answer: the pole damage is """
#         inp = transcript + pole
#         # Calling the Bloom function
#         first_guess = answering_pole(inp)
#         second_inp = transcript + equipment
#         second_guess = answering_equipment(second_inp)
        
#         # Obtaining the information needed using regex manual expressions from re library
#         first_answer = getting_pole_ID(first_guess)
#         second_answer = getting_damaged_equipment(second_guess)
        
    
#         add_inspection(transcript, first_answer, second_answer)

#         return jsonify({
#             'transcript': result.text,
#             'answer': "the guess are: " + first_guess + ' ' + second_guess + 'POLE_ID: ' + first_answer + ', EQUIPMENT_DAMAGED: ' + second_answer
#         }), 200


### HERE IT IS THE CODE TO STORE IN THE DATABASE AND TO SEND TO THE FRONTEND IN A TABLE
## App route to take the database data and send it to the frontend
@app.route('/api/db', methods=['GET'])
def query():
    """This method should take the data from the database and send it to the frontend."""
    # Requesting data to the database
    all_transcripts = Inspections.query.all()
    results = Inspections_schema.dump(all_transcripts)
    return jsonify(results)

## Functions to create the database classes and schemas
# Database Model, storing transcript, PoleID and Equipment damaged
class Inspections(db.Model):
    INSPECTION_ID = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.DateTime, default=datetime.datetime.now)
    transcript = db.Column(db.String(200), nullable=False)
    POLE_ID = db.Column(db.String(10), nullable=True)
    DAMAGED_EQUIPMENT = db.Column(db.String(9), nullable=True)

    def __init__(self, transcript, POLE_ID, DAMAGED_EQUIPMENT):
        self.transcript = transcript
        self.POLE_ID = POLE_ID
        self.DAMAGED_EQUIPMENT = DAMAGED_EQUIPMENT        

# Schema to serialize the SQL data and transform it to the frontend with Marshmallow
class InspectionSchema(ma.Schema):
    class Meta:
        fields = ('INSPECTION_ID', 'date', 'transcript', 'POLE_ID', 'DAMAGED_EQUIPMENT')


# Initializing the Schemas, the first one to get one sequence and the other to get all the sequences
Inspection_schema = InspectionSchema()
Inspections_schema = InspectionSchema(many=True)

## Function to add the data from the frontend into the database
def add_inspection(transcript_flask, pole_id, damaged_equipment):
    transcript = transcript_flask
    POLE_ID = pole_id
    DAMAGED_EQUIPMENT = damaged_equipment

    save_transcript = Inspections(transcript, POLE_ID, DAMAGED_EQUIPMENT)
    db.session.add(save_transcript)
    db.session.commit()

## This is the last part of the database, where we should edit or remove data. It is not finished. Hope to finish sometime
# Sending data specifying the id
@app.route('/get/<INSPECTION_ID>/', methods=['GET'])
def id_search(INSPECTION_ID):
    id_transcript = Inspections.query.get(INSPECTION_ID)
    return Inspection_schema.jsonify(id_transcript)

# Adding the Edit/Delete option
# Editing existing inspection data
@app.route('/edit/<id>/', methods = ['PUT'])
def edit_inspection(INSPECTION_ID):
    inspection = Inspections.query.get(INSPECTION_ID)
    
    transcript = request.form
    pole_id = request.form
    damaged_equipment = request.form
    
    inspection.transcript = transcript
    inspection.POLE_ID = pole_id
    inspection.DAMAGED_EQUIPMENT = damaged_equipment
    
    db.session.commit()
    return Inspection_schema.jsonify(inspection)

# Deleting existing inspection 
@app.route('/delete/<id>/', methods = ['DELETE'])
def delete_inspection(INSPECTION_ID):
    inspection = Inspections.query.get(INSPECTION_ID)
    db.session.delete(inspection)
    db.session.commit()
    
    return Inspection_schema.jsonify(inspection)
    


# To initialize the app
if __name__ == '__main__':
    app.run(debug=True, host='localhost')
