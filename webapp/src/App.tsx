import React, { Component } from 'react';
import './App.css';

interface AppState {
  loading: boolean;
  recording: boolean;
  transcript: string;
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

export default class App extends Component<{}, AppState> {
  static displayName = App.name;

  mediaRecorder: MediaRecorder | undefined;
  audioChunks: Blob[] = [];

  constructor(props: any) {
    super(props);

    this.state = {
      loading: false,
      recording: false,
      transcript: "",
    }

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

            // // Play back audio as a sanity check
            // const audioUrl = URL.createObjectURL(audioBlob);
            // const audio = new Audio(audioUrl);
            // audio.play();

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

  async generateTranscript(data: FormData) {
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

  render() {
    return (
      <div className="App">
        <header className="App-header">
          <MediaController
            recording={this.state.recording}
            onClick={this.toggleRecording}
          />
          <Transcript
            transcript={this.state.transcript}
            loading={this.state.loading}
          />
        </header>
      </div>
    );
  }
}
