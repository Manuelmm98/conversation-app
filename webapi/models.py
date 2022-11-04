

# Database Model, storing transcript, question and answer
class Whisper(db.Model):
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