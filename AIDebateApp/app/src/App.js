import React, { useState, useEffect } from "react";
import { fetchPersonas, moderatorTopic, participantResponse } from "./services/api";
import Transcript from "./components/Transcript";
import { AiOutlineAudio } from "react-icons/ai";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";

function App() {
  const [personas, setPersonas] = useState({});
  const [history, setHistory] = useState([]);
  const [topic, setTopic] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [currentSpeaker, setCurrentSpeaker] = useState(null);

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
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    setIsListening(true);

    recognition.onresult = async (event) => {
      const transcript = event.results[0][0].transcript;
      setIsListening(false);
      recognition.stop();
      await handleModeratorInput(transcript);
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      setIsListening(false);
      recognition.stop();
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  const handleModeratorInput = async (transcript) => {
    setIsProcessing(true);
    try {
      const payload = { speaker: "Moderator", topic: transcript, message: "" };
      const response = await moderatorTopic(payload);

      if (response.conversation_history) {
        setHistory(response.conversation_history);
        setTopic(transcript);
        await handleParticipantResponses();
      }
    } catch (error) {
      console.error("Error handling moderator input:", error);
      alert("Failed to set the debate topic.");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleParticipantResponses = async () => {
    try {
      const response = await participantResponse();

      if (response.responses) {
        setHistory(response.conversation_history);

        for (const res of response.responses) {
          setCurrentSpeaker(res.speaker);

          try {
            const audio = new Audio(res.audio_file);
            await playAudioSequentially(audio);
          } catch (error) {
            console.error(`Error playing audio for ${res.speaker}:`, error);
          }

          // Add a slight delay for better user experience
          await new Promise((resolve) => setTimeout(resolve, 500));
        }
      }
    } catch (error) {
      console.error("Error handling participant responses:", error);
      alert("Failed to fetch participant responses.");
    } finally {
      setCurrentSpeaker(null);
    }
  };

  const playAudioSequentially = (audio) => {
    return new Promise((resolve, reject) => {
      audio.onended = resolve;
      audio.onerror = (error) => reject(`Audio playback error: ${error.message}`);
      audio.play().catch((error) => {
        console.error("Error during playback:", error);
        reject(error);
      });
    });
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
          <h1>Interactive AI Debate</h1>
          {topic && <h2>Debate Topic: {topic}</h2>}
          <Transcript history={history} personas={personas} />

          {/* Spinner Popup */}
          {isProcessing && (
            <div className="popup-spinner">
              <div className="spinner-content">
                {currentSpeaker ? (
                  <>
                    <img
                      src={personas[currentSpeaker]?.image || "/images/default-avatar.png"}
                      alt={personas[currentSpeaker]?.name || "Processing"}
                      className="spinner-avatar"
                    />
                    <p className="spinner-text">
                      Processing response from {personas[currentSpeaker]?.name || currentSpeaker}...
                    </p>
                  </>
                ) : (
                  <p className="spinner-text">Processing topic...</p>
                )}
                <div className="spinner"></div>
              </div>
            </div>
          )}

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