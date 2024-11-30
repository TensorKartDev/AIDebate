import React, { useState } from "react";
import { submitTurn } from "./services/api";
import ModeratorInput from "./components/ModeratorInput";
import Transcript from "./components/Transcript";
import "./App.css";

function App() {
  const [history, setHistory] = useState([]); // Conversation history
  const [topic, setTopic] = useState(""); // Debate topic
  const [loading, setLoading] = useState(false); // Spinner for waiting
  const [currentParticipantIndex, setCurrentParticipantIndex] = useState(0); // Index of the current speaker
  const [participants] = useState([
    { name: "WizardLM2", image: "/images/Xi Jinping.jpg", description: "Xi Jinping, emphasizing collectivism." },
    { name: "LLaMA3", image: "/images/Joe_Biden.jpg", description: "Joe Biden, pragmatic and empathetic." },
    { name: "LLaMA2", image: "/images/Donald_Trump.jpg", description: "Donald Trump, bold and assertive." },
    { name: "Mistral", image: "/images/Angela_Merkel.jpg", description: "Angela Merkel, analytical and calm." },
  ]);

  const handleModeratorSubmit = async (content) => {
    if (!content.trim()) return;

    const payload = { speaker: "Moderator", topic: content, message: "" };
    setLoading(true);

    try {
      const data = await submitTurn(payload);

      // Add topic to history if not already added
      if (!history.some((entry) => entry.message === `Debate Topic: ${content}`)) {
        setTopic(content);
        setHistory((prevHistory) => [...prevHistory, ...data.conversation_history]);
      }

      // Start the debate flow
      setCurrentParticipantIndex(0);
      await startDebateFlow(content);
    } catch (error) {
      console.error("Error submitting topic:", error);
    } finally {
      setLoading(false);
    }
  };

  const startDebateFlow = async (content) => {
    for (let i = 0; i < participants.length; i++) {
      setCurrentParticipantIndex(i);
      await handleParticipantResponse(participants[i], content);
    }
  };

  const handleParticipantResponse = async (participant, content) => {
    const payload = { speaker: participant.name, topic: "", message: "" };
    setLoading(true);

    try {
      const data = await submitTurn(payload);
      setHistory((prevHistory) => [...prevHistory, ...data.conversation_history]);
    } catch (error) {
      console.error(`Error fetching response from ${participant.name}:`, error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="App">
      <div className="left-panel">
        <h2>Participants</h2>
        <ul>
          {participants.map((participant, index) => (
            <li key={index}>
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

        {/* Pass participants to Transcript */}
        <Transcript history={history} participants={participants} />

        <ModeratorInput onSubmit={handleModeratorSubmit} />

        {loading && (
          <div className="spinner">
            
          </div>
        )}
      </div>
    </div>
  );
}

export default App;