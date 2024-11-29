import React, { useState, useEffect } from "react";
import { fetchNextTurn, submitTurn } from "./services/api";
import ModeratorInput from "./components/ModeratorInput";
import Transcript from "./components/Transcript";
import "./App.css";

function App() {
  const [history, setHistory] = useState([]);
  const [topic, setTopic] = useState("");
  const [isDebateStarted, setIsDebateStarted] = useState(false);
  const [participants] = useState([
    { name: "WizardLM2", image: "/images/wizardlm2.png", description: "Xi Jinping, emphasizing collectivism." },
    { name: "LLaMA3", image: "/images/llama3.png", description: "Joe Biden, pragmatic and empathetic." },
    { name: "LLaMA2", image: "/images/llama2.png", description: "Donald Trump, bold and assertive." },
    { name: "Mistral", image: "/images/mistral.png", description: "Angela Merkel, analytical and calm." },
  ]);
  const [currentParticipantIndex, setCurrentParticipantIndex] = useState(0);
  const [persona, setPersona] = useState({
    name: "Moderator",
    image: "/images/moderator.png", // Default fallback image
    description: "You are moderating this debate."
  });
  
  // Handle setting the debate topic
  const handleSetTopic = async (content) => {
    setTopic(content);
    setIsDebateStarted(true);
    setHistory([{ speaker: "Moderator", message: `Debate Topic: ${content}` }]);
    fetchNextParticipant(); // Trigger the first participant
  };

  // Fetch the next participant's response
  const fetchNextParticipant = async () => {
    if (currentParticipantIndex < participants.length) {
      const currentParticipant = participants[currentParticipantIndex];
      const data = await submitTurn(currentParticipant.name, "", topic);
      setHistory(data.conversation_history);
      setPersona(data.persona);
      setCurrentParticipantIndex((prevIndex) => prevIndex + 1);
    }
  };

  useEffect(() => {
    if (isDebateStarted && currentParticipantIndex < participants.length) {
      fetchNextParticipant();
    }
  }, [currentParticipantIndex, isDebateStarted]);

  return (
    <div className="App">
      <div className="left-panel">
        <h2>Participants</h2>
        <ul>
          {participants.map((participant, index) => (
            <li key={index} className="participant">
              <img src={participant.image} alt={participant.name} className="avatar" />
              <div>
                <strong>{participant.name}</strong>
                <p>{participant.description}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>
      <div className="main-panel">
  <h1>Interactive AI Debate</h1>
  {topic && <h2>Debate Topic: {topic}</h2>}

  {/* Next Speaker Section */}
  <div className="next-speaker">
    {persona?.image ? (
      <img
        src={persona.image}
        alt={persona.name || "Speaker"}
        className="avatar"
        onError={(e) => { e.target.src = "/images/moderator.png"; }} // Fallback for missing image
      />
    ) : (
      <p>No speaker avatar available</p>
    )}
    <p>
      <strong>Next Speaker:</strong> {persona?.name || "Unknown"}
    </p>
    <p>{persona?.description || "No description available"}</p>
  </div>

  {/* Full-width "Set Topic" Input */}
  {!isDebateStarted && (
    <div className="full-width-input">
      <ModeratorInput onSetTopic={handleSetTopic} />
    </div>
  )}

  <Transcript history={history} personas={{}} />

  {isDebateStarted && currentParticipantIndex >= participants.length && (
    <p>All participants have responded to the topic.</p>
  )}
</div>
      
    </div>
  );
}

export default App;