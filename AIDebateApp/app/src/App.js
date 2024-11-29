import React, { useState, useEffect } from "react";
import { submitTurn } from "./services/api"; // Updated API call
import ModeratorInput from "./components/ModeratorInput";
import Transcript from "./components/Transcript";
import "./App.css";

function App() {
  const [history, setHistory] = useState([]); // Conversation history
  const [topic, setTopic] = useState(""); // Debate topic
  const [isDebateStarted, setIsDebateStarted] = useState(false); // Debate state
  const [participants] = useState([
    { name: "WizardLM2", image: "/images/wizardlm2.png", description: "Xi Jinping, emphasizing collectivism." },
    { name: "LLaMA3", image: "/images/llama3.png", description: "Joe Biden, pragmatic and empathetic." },
    { name: "LLaMA2", image: "/images/llama2.png", description: "Donald Trump, bold and assertive." },
    { name: "Mistral", image: "/images/mistral.png", description: "Angela Merkel, analytical and calm." },
  ]);
  const [currentParticipantIndex, setCurrentParticipantIndex] = useState(0);
  const [persona, setPersona] = useState({
    name: "Moderator",
    image: "/images/moderator.png",
    description: "You are moderating this debate.",
  });

  // Debug history updates
  useEffect(() => {
    console.log("History updated:", history);
  }, [history]);

  // Handle moderator submission
  const handleModeratorSubmit = async (content) => {
    if (!content.trim()) return; // Prevent empty submissions

    try {
      // Send the topic to the backend API
      const data = await submitTurn("Moderator", content, topic || content); // Pass topic if already set, else use input
      setTopic(data.topic || content);
      setHistory(data.conversation_history || []);
      setPersona(data.persona || {
        name: participants[0]?.name,
        image: "/images/default-avatar.png",
        description: "No description available.",
      });
      setIsDebateStarted(true); // Start the debate if topic is set
      setCurrentParticipantIndex(0); // Reset participant index
    } catch (error) {
      console.error("Error sending topic to API:", error);
    }
  };

  // Fetch the next participant's response
  const fetchNextParticipant = async () => {
    if (currentParticipantIndex < participants.length) {
      const currentParticipant = participants[currentParticipantIndex];
      try {
        const data = await submitTurn(currentParticipant.name, "", topic);
        setHistory(data.conversation_history || []);
        setPersona(data.persona || {
          name: currentParticipant.name,
          image: "/images/default-avatar.png",
          description: "No description available.",
        });
        setCurrentParticipantIndex((prevIndex) => prevIndex + 1);
      } catch (error) {
        console.error("Error fetching participant response:", error);
      }
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

        {/* Transcript */}
        <Transcript history={history || []} personas={participants.reduce((acc, participant) => {
          acc[participant.name] = participant;
          return acc;
        }, {})} />

        {/* Always-visible Moderator Input */}
        <div className="moderator-input-container">
          <ModeratorInput onSubmit={handleModeratorSubmit} />
        </div>

        {/* Display Next Speaker */}
        {isDebateStarted && currentParticipantIndex < participants.length && (
          <div className="next-speaker">
            <img
              src={persona.image}
              alt={persona.name || "Speaker"}
              className="avatar"
              onError={(e) => { e.target.src = "/images/default-avatar.png"; }}
            />
            <p>
              <strong>Next Speaker:</strong> {persona.name || "Unknown"}
            </p>
            <p>{persona.description || "No description available."}</p>
          </div>
        )}

        {/* All Participants Responded */}
        {isDebateStarted && currentParticipantIndex >= participants.length && (
          <p>All participants have responded to the topic.</p>
        )}
      </div>
    </div>
  );
}

export default App;