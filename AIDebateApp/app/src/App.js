import React, { useState, useEffect } from "react";
import { fetchPersonas, moderatorTopic, participantResponse } from "./services/api";
import Transcript from "./components/Transcript";
import { AiOutlineAudio } from "react-icons/ai"; // For audio icon
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";

function App() {
  const [personas, setPersonas] = useState({});
  const [history, setHistory] = useState([]);
  const [topic, setTopic] = useState("");
  const [processing, setProcessing] = useState(false);
  const [isListening, setIsListening] = useState(false);

  useEffect(() => {
    const loadPersonas = async () => {
      try {
        const data = await fetchPersonas();
        setPersonas(data);
      } catch (error) {
        console.error("Failed to load personas:", error);
      }
    };
    loadPersonas();
  }, []);

  const startListening = () => {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = "en-US"; // Set the language
    recognition.interimResults = false; // Only get final results
    recognition.maxAlternatives = 1;

    setIsListening(true);

    recognition.onstart = () => {
      console.log("Listening for moderator input...");
    };

    recognition.onresult = async (event) => {
      const transcript = event.results[0][0].transcript;
      console.log("Transcription:", transcript);

      setIsListening(false);
      recognition.stop();

      // Set the topic and start participant responses
      await handleModeratorInput(transcript);
    };

    recognition.onerror = (event) => {
      console.error("Error in Speech Recognition:", event.error);
      setIsListening(false);
      recognition.stop();
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  const handleModeratorInput = async (transcript) => {
    setProcessing(true);
    try {
      const payload = {
        speaker: "Moderator",  // Required
        topic: transcript,     // Required
        message: ""            // Optional
      };
  
      console.log("Payload sent to /moderator-topic/:", payload);
  
      const response = await moderatorTopic(payload); // Send the correct payload
      if (response.conversation_history) {
        setHistory(response.conversation_history);
        setTopic(transcript);
        await handleParticipantResponses();
      }
    } catch (error) {
      console.error("Error processing moderator input:", error);
    } finally {
      setProcessing(false);
    }
  };

  const handleParticipantResponses = async () => {
    try {
      const response = await participantResponse();
      if (response.responses) {
        setHistory(response.conversation_history);

        // Sequentially play participant responses
        for (const res of response.responses) {
          const audio = new Audio(res.audio_file);
          await audio.play();
        }
      }
    } catch (error) {
      console.error("Error processing participant responses:", error);
    }
  };

  return (
    <div className="container-fluid">
      <div className="row">
        {/* Left Panel */}
        <div className="col-md-3 left-panel">
          <h2>Participants</h2>
          <ul>
            {Object.keys(personas).map((participant) => (
              <li key={participant}>
                <img
                  src={personas[participant]?.image || "/images/default-avatar.png"}
                  alt={personas[participant]?.name || participant}
                  className="avatar"
                  onError={(e) => {
                    e.target.src = "/images/default-avatar.png";
                  }}
                />
                <strong>{personas[participant]?.name || participant}</strong>
                <p>{personas[participant]?.description || "No description available"}</p>
              </li>
            ))}
          </ul>
        </div>

        {/* Main Panel */}
        <div className="col-md-9 main-panel">
          <h1>Interactive AI Debate</h1>
          {topic && <h2>Debate Topic: {topic}</h2>}
          <Transcript history={history} />

          <div className="moderator-input">
            {isListening ? (
              <div className="listening-loader">
                <p>Listening...</p>
                <div className="spinner-border text-primary" role="status">
                  <span className="visually-hidden">Loading...</span>
                </div>
              </div>
            ) : (
              <AiOutlineAudio
                className="start-listening-icon"
                size={50}
                onClick={startListening}
                title="Start Listening"
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;