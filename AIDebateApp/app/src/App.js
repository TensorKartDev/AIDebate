import React, { useState, useEffect, useRef } from "react";
import { fetchPersonas } from "./services/api";
import Transcript from "./components/Transcript";
import { AiOutlineAudio } from "react-icons/ai";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";

function App() {
  const [personas, setPersonas] = useState({});
  const [history, setHistory] = useState([]);
  const [isListening, setIsListening] = useState(false);
  const wsRef = useRef(null);
  const speakMessage = (message, speaker) => {
    if (!("speechSynthesis" in window)) {
      console.error("Text-to-speech is not supported in this browser.");
      return;
    }

    const utterance = new SpeechSynthesisUtterance(message);

    // Retrieve persona properties for the speaker
    const voices = speechSynthesis.getVoices();
    const selectedVoice = voices.find(
      (v) => v.voiceURI === personas[speaker]?.voice_language
    );

    if (selectedVoice) {
      utterance.voice = selectedVoice;
      console.log(`Using voice: ${selectedVoice.name} (${selectedVoice.lang})`);
    } else {
      console.warn(
        `No matching voice found for speaker: ${speaker}. Using default voice.`
      );
    }

    utterance.pitch = personas[speaker]?.pitch || 1; // Optional pitch customization
    utterance.rate = personas[speaker]?.rate || 1;   // Optional rate customization

    speechSynthesis.cancel(); // Stop any ongoing speech
    speechSynthesis.speak(utterance);
  };
  useEffect(() => {
    // Load personas on component mount
    const loadPersonas = async () => {
      try {
        const data = await fetchPersonas();
        setPersonas(data);
      } catch (error) {
        console.error("Failed to load personas:", error);
      }
    };
    loadPersonas();

    // Establish WebSocket connection
    if (!wsRef.current) {
      wsRef.current = new WebSocket("ws://localhost:1000/ws");

      wsRef.current.onopen = () => console.log("WebSocket connection established")
      
    }
    wsRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log("WebSocket message received:", data);
        setHistory((prev) => [...prev, data]);
        speakMessage(data.message, data.speaker);
      } catch (e) {
        console.error("Failed to process WebSocket message:", e);
        alert("An error occurred while processing a message.");
      }
    };

    wsRef.current.onerror = (error) => console.error("WebSocket error:", error);

    wsRef.current.onclose = (event) => {
      console.log(
        `WebSocket connection closed with code ${event.code} and reason: ${event.reason}`
      );
    };

    // Cleanup WebSocket on component unmount
    return () => {
      if (wsRef.current) {
        wsRef.current.close(1000, "Component unmounting");
        wsRef.current = null;
      }
    };
  }, []);


  const startListening = () => {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    setIsListening(true);

    recognition.onresult = async (event) => {
      const transcript = event.results[0][0].transcript;
      setIsListening(false);
      recognition.stop();

      // Send the transcript via WebSocket
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        const messagePayload = { speaker: "Moderator", message: transcript };
        console.log("Sending transcript to WebSocket:", messagePayload);
        wsRef.current.send(JSON.stringify(messagePayload));
      } else {
        console.error("WebSocket is not open. Unable to send transcript.");
      }
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      setIsListening(false);
      recognition.stop();

      // Provide feedback to the user
      if (event.error === "no-speech") {
        alert("No speech detected. Please try again.");
      }
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  return (
    <div className="container-fluid">
      <div className="row">
        {/* Left Panel: Participants */}
        <div className="col-md-3 left-panel">
          <h2>Participants</h2>
          {Object.keys(personas).length > 0 ? (
            <ul>
              {Object.keys(personas).map((participant) => (
                <li key={participant}>
                  <img
                    src={personas[participant]?.image || "/images/default-avatar.png"}
                    alt={personas[participant]?.name || participant}
                    className="avatar"
                  />
                  <strong>{personas[participant]?.name || participant}</strong>
                  <p>{personas[participant]?.description || "No description available"}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p>Loading participants...</p>
          )}
        </div>

        {/* Main Panel */}
        <div className="col-md-9 main-panel">
          <h1>AI Fireside Chat</h1>
          <Transcript history={history} personas={personas} />

          {/* Moderator Input Section */}
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