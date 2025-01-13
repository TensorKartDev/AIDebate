import React, { useState, useEffect } from "react";
import { fetchPersonas, participantResponse } from "./services/api";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";

function App() {
  const [personas, setPersonas] = useState({});
  const [currentSpeaker, setCurrentSpeaker] = useState(null);
  const [topic, setTopic] = useState("");
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
    console.log("Moderator mic clicked!");
    // Implement speech recognition or listening functionality here
  };

  const handleParticipantResponses = async (participants) => {
    try {
      for (const participant of participants) {
        setCurrentSpeaker(participant);
        try {
          const response = await participantResponse(participant, { topic });
          if (response.responses && response.responses.length > 0) {
            const { speaker, message } = response.responses[0];
            const voices = speechSynthesis.getVoices();
            const voice = voices.find(
              (v) => v.voiceURI === personas[speaker]?.voice_language
            );
            const utterance = new SpeechSynthesisUtterance(message);
            if (voice) utterance.voice = voice;
            await new Promise((resolve) => {
              utterance.onend = resolve;
              speechSynthesis.speak(utterance);
            });
          }
        } catch (error) {
          console.error(`Error with participant ${participant}:`, error);
        }
      }
    } finally {
      setCurrentSpeaker(null);
    }
  };

  return (
    <div className="round-table-container">
      <div className="round-table">
        {Object.keys(personas).map((participant, index) => (
          <div
            key={participant}
            className={`chair ${
              currentSpeaker === participant ? "highlight" : ""
            } chair-${index + 1}`}
          >
            <div
              className="avatar"
              style={{
                backgroundImage: `url(${personas[participant]?.image || "/images/default-avatar.png"})`,
              }}
            ></div>
            <span className="name">{personas[participant]?.name || participant}</span>
            {currentSpeaker === participant && (
              <p className="speaking-label">Speaking...</p>
            )}
          </div>
        ))}

        <div className="mic-icon" onClick={startListening}>
          🎤
        </div>
      </div>
    </div>
  );
}

export default App;