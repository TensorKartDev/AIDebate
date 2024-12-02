import React, { useState, useEffect } from "react";
import { fetchPersonas, submitTurn } from "./services/api";
import ModeratorInput from "./components/ModeratorInput";
import Transcript from "./components/Transcript";
import "bootstrap/dist/css/bootstrap.min.css"; // Import Bootstrap CSS
import "./App.css";

function App() {
  const [personas, setPersonas] = useState({});
  const [participants, setParticipants] = useState([]);
  const [history, setHistory] = useState([]);
  const [topic, setTopic] = useState("");
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [currentSpeaker, setCurrentSpeaker] = useState(null);

  useEffect(() => {
    const loadPersonas = async () => {
      try {
        const data = await fetchPersonas();
        setPersonas(data);
        setParticipants(Object.keys(data));
      } catch (error) {
        console.error("Failed to load personas:", error);
      } finally {
        setLoading(false);
      }
    };
    loadPersonas();
  }, []);

  const handleSetTopic = async (newTopic) => {
    setProcessing(true);
    try {
      setTopic(newTopic);

      const topicPayload = { speaker: "Moderator", message: "", topic: newTopic };
      const topicResponse = await submitTurn(topicPayload);

      if (topicResponse?.conversation_history) {
        setHistory(topicResponse.conversation_history);
      }

      for (const participant of participants) {
        setCurrentSpeaker(participant);
        const responsePayload = { speaker: participant, message: "" };
        const response = await submitTurn(responsePayload);

        if (response?.conversation_history) {
          setHistory((prevHistory) => [...prevHistory, ...response.conversation_history]);
        } else {
          console.error(`Invalid response for participant ${participant}:`, response);
        }
      }
    } catch (error) {
      console.error("Error handling topic and responses:", error);
    } finally {
      setProcessing(false);
      setCurrentSpeaker(null);
    }
  };

  return (
    <div className="container-fluid">
      <div className="row">
        {/* Left Panel */}
        <div className="col-md-3 left-panel">
          <h2>Participants</h2>
          <ul>
            {participants.map((participant) => (
              <li key={participant}>
                <img
                  src={personas[participant]?.image || "/images/default-avatar.png"}
                  alt={personas[participant]?.name || participant}
                  className="avatar"
                  onError={(e) => {
                    e.target.src = "/images/default-avatar.png";
                  }}
                />
                <div>
                  <strong>{personas[participant]?.name || participant}</strong>
                  <p>{personas[participant]?.description || "No description available"}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>

        <div className="main-panel">
  {/* Scrollable Transcript Section */}
  <div className="transcript-container">
    <h1>Interactive AI Debate</h1>
    {topic && <h2>Debate Topic: {topic}</h2>}
    <Transcript history={history} participants={participants} personas={personas} />
  </div>

  {/* Spinner Section */}
  {processing && currentSpeaker && (
    <div className="bottom-spinner-container">
      {/* Speaker's Avatar */}
      <img
        src={personas[currentSpeaker]?.image || "/images/default-avatar.png"}
        alt={personas[currentSpeaker]?.name || "Current Speaker"}
        className="spinner-avatar"
        onError={(e) => {
          e.target.src = "/images/default-avatar.png"; // Fallback for missing images
        }}
      />

      {/* Spinner Animation */}
      <div className="spinner"></div>

      {/* Speaker's Name */}
      <p className="spinner-text">
        Processing response from {personas[currentSpeaker]?.name || currentSpeaker}...
      </p>
    </div>
  )}

  {/* Fixed Textbox Section */}
  <ModeratorInput onSetTopic={handleSetTopic} />
</div>
      </div>
    </div>
  );
}

export default App;