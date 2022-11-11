import React, { Component } from 'react';
import './App.css';

interface AppState {
  loading: boolean;
  recording: boolean;
  transcript: string;
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
         <span>{props.loading ? "Waiting for response" : props.answer}</span>
     </label>
   </div>
 );
}

class ImportTranscript extends Component<{}, AppState> {
  mediaRecorder: MediaRecorder | undefined;
  audioChunks: Blob[] = [];
    
  constructor(props: any) {
    super(props);

    this.state = {
      loading: false,
      recording: false,
      transcript: "",
      answer: "", 
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

//             // Play back audio as a sanity check
//             const audioUrl = URL.createObjectURL(audioBlob);
//             const audio = new Audio(audioUrl);
//             audio.play();

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
    console.log('Here we are')
    fetch('/api/transcript', {
      method: 'POST',
      body: data
    }).then(response => response.json()
      ).then(data => {
        this.setState({
          transcript: data.transcript,
          answer: data.answer,  
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
        <div>
          <MediaController
            recording={this.state.recording}
            onClick={this.toggleRecording}
          />
          <Transcript
            transcript={this.state.transcript}
            loading={this.state.loading}
          />
          <ShowTranscript
            answer={this.state.answer}
            loading={this.state.loading}  
          />
        </div>
    );
  }
}

interface InspectionAPI {
    INSPECTION_ID: number,
    date?: string,
    transcript: string,
    POLE_ID: string,
    DAMAGED_EQUIPMENT: string,
    data: any
} 


const headers = [
     { key: "id", label: "INSPECTION_ID" },
     { key: "date", label: "date" },
     { key: "transcript", label: "TRANSCRIPT" },
     { key: "pole_id", label: "POLE_ID" },
     { key: "damaged_equipment", label: "DAMAGED_EQUIPMENT" },
     { key: "button", label: "" },    
];

const subheaders = [
     { key: "id", label: "integer" },
     { key: "date", label: "date" },
     { key: "transcript", label: "Text" },
     { key: "pole_id", label: "Text (9 digits)" },
     { key: "damaged_equipment", label: "Text (CROSSARM/ARRESTER/INSULATOR/NULL)" },
     { key: "button", label: "Edit/remove button" },    
]; 

class Importdatabase extends Component<{}, InspectionAPI> {

  constructor(props: any) {
    super(props);

    this.state = {
      INSPECTION_ID: 0,
      date: '',
      transcript: '',
      POLE_ID: '',
      DAMAGED_EQUIPMENT: '',
      data: []  
    }

  }

  componentDidMount() {
    // Getting the database data
    this.getDatabase(); 
  }

  async getDatabase() {
    fetch("/api/db", {
        method:"GET",
     })
      .then(response => {
        return response.json()
      })
      .then(response => {
            this.setState({ data: response})
      console.log(this.state.data)
      });
  } 

  render() {
    return (
          <div>
           <table>
             <thead>
               <tr>
                 {headers.map((row) => {
                   return <td key={row.key}>{row.label}</
                     td>;
                 })}
               </tr>  
             </thead>
             <thead>
               <tr>
                 {subheaders.map((row) => {
                   return <td key={row.key}>{row.label}</
                     td>;
                 })}
               </tr>  
             </thead>
               
             <tbody>     
               {this.state.data.map((ins:InspectionAPI) => {
                 return (      
                   <tr key={ins.INSPECTION_ID}>
                     <td>{ins.INSPECTION_ID}</td>
                     <td>{ins.date}</td>
                     <td>{ins.transcript}</td>
                     <td>{ins.POLE_ID}</td>
                     <td>{ins.DAMAGED_EQUIPMENT}</td>
                   </tr>
                 );
               })}     
             </tbody>
           </table>
          </div>
    );
  }
}

export default class App extends Component<{}, AppState> {

  handleClick(e: React.MouseEvent) {
    alert('Second Part is coming');
    e.preventDefault()
  }

  render() {
    return (
      <div className="App">
        <header className='App-header'>
          <span className="heading">Whisper</span>
          <ImportTranscript />
          <button onClick={this.handleClick.bind(this)}/>
          <Importdatabase />  
        </header>
      </div>
    );
  }
}
