import React, { Component } from 'react';
import './App.css';

interface AppState {
  loading: boolean;
  recording: boolean;
  transcript: string;
  value: string;
  enter: boolean;
  answer: string;
}

interface MediaControllerProps extends Partial<AppState> {
  onClick: React.MouseEventHandler;
}

function MediaController(props: MediaControllerProps) {
  return (
    <div>
      <button onClick={props.onClick} className="record-button">
        <span>{props.recording ? "Stop recording" : "Start recording"}</span>
      </button>
    </div>
  );
}

function Transcript(props: Partial<AppState>) {
  return (
    <div>
      <p>{props.loading ? "Processing..." : props.transcript}</p>
    </div>
  );
}

function ShowTranscript(props: Partial<AppState>) {
 return (
   <div>
     <label>
     Answer:
       <span>{props.answer}</span>
     </label>
   </div>
 );
}

export default class App extends Component<{}, AppState> {
  static displayName = App.name;

  mediaRecorder: MediaRecorder | undefined;
  audioChunks: Blob[] = [];
  value: string | undefined;

  constructor(props: any) {
    super(props);

    this.state = {
      loading: false,
      recording: false,
      transcript: "",
      value: "",
      enter: false,
      answer: "",
    }

    this.handleChange = this.handleChange.bind(this);
    this.handleSubmit = this.handleSubmit.bind(this);
    this.handleEnter = this.handleEnter.bind(this);

    this.toggleRecording = this.toggleRecording.bind(this);
  }

  componentDidMount() {
    // Set up media controls
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
      navigator.mediaDevices
        .getUserMedia({ audio: true })
        .then((stream) => {
          this.mediaRecorder = new MediaRecorder(stream);
          this.mediaRecorder.ondataavailable = (e) => {
            this.audioChunks.push(e.data);
          }
          this.mediaRecorder.onstop = (e) => {
            // Send audio to backend
            const audioBlob = new Blob(this.audioChunks, { type: "audio/wav" });
            let data = new FormData();
            data.append('audio', audioBlob, 'audio');
            this.setState({ loading: true });
            this.generateTranscript(data);

            // Play back audio as a sanity check
            const audioUrl = URL.createObjectURL(audioBlob);
            const audio = new Audio(audioUrl);
            audio.play();

            // Clear audio chunks
            this.audioChunks = [];
          }
        })
        .catch((err) => {
          console.error(`getUserMedia error: ${err}`);
        });
    } else {
      alert("getUserMedia is not supported in this browser");
    }
  }
  componentDidUpdate() {
    // Setting up the question
    if (this.state.enter) {
      console.log('here we are again');
      let newData = new FormData();
      newData.append('transcript', this.state.transcript);
      newData.append('question', this.state.value);
      this.generateAnswer(newData);
    }
  }

  async generateTranscript(data: FormData) {
    console.log('Here we are')
    fetch('/api/transcript', {
      method: 'POST',
      body: data
    }).then(response => response.json()
    ).then(data => {
      this.setState({
        transcript: data.transcript,
        loading: false,
      })
    });
  }


  toggleRecording(e: React.MouseEvent) {
    e.preventDefault();

    if (!this.state.recording) {
      this.mediaRecorder?.start();
    } else {
      this.mediaRecorder?.stop();
    }

    this.setState({
      recording: !this.state.recording,
    })
  }

  handleChange(event: any) {
    this.setState({
    value: event.target.value,
    });
  }

  handleEnter(e: React.MouseEvent) {
    e.preventDefault();

    this.setState({
      enter: !this.state.enter,
    });
  }

  handleSubmit(event: any) {
    alert('A question was submitted: ' + this.state.value);
    event.preventDefault()
  }

  async generateAnswer(newData: FormData) {
    fetch("/api/question", {
        method:"POST",
        body:newData
     })
      .then(response => {
        console.log(response)
        return response.json()
      })
      .then(newData => {
      this.setState({
        answer: newData.answer,
        enter: false,
      })
      console.log(newData)
    })
  }

  render() {
    return (
      <div className="App">
        <header className='App-header'>
          <span className="heading">Whisper</span>
          <MediaController
            recording={this.state.recording}
            onClick={this.toggleRecording}
          />
          <Transcript
            transcript={this.state.transcript}
            loading={this.state.loading}
          />
          <div>
            <form onSubmit={this.handleSubmit}>
              <label>
              Question:
                <input type="text" value={this.state.value} onChange={this.handleChange}/>
              </label>
              <input type="submit" value="Submit" onClick={this.handleEnter}/>
            </form>
          </div>
          <ShowTranscript
            answer={this.state.answer}
          />
        </header>
      </div>
    );
  }
}

