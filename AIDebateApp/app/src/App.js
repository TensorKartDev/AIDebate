import React, { useState, useEffect } from "react";
import { submitTurn } from "./services/api"; // Updated API call
import ModeratorInput from "./components/ModeratorInput";
import Transcript from "./components/Transcript";
import "./App.css";

function App() {
  const [history, setHistory] = useState([]); // Conversation history
  const [topic, setTopic] = useState(""); // Debate topic
  const [loading, setLoading] = useState(false); // Loading state for spinner
  const [participants] = useState([
    { name: "WizardLM2", image: "/images/wizardlm2.png", description: "Xi Jinping, emphasizing collectivism." },
    { name: "LLaMA3", image: "/images/llama3.png", description: "Joe Biden, pragmatic and empathetic." },
    { name: "LLaMA2", image: "/images/llama2.png", description: "Donald Trump, bold and assertive." },
    { name: "Mistral", image: "/images/mistral.png", description: "Angela Merkel, analytical and calm." },
  ]);
  const [persona, setPersona] = useState({
    name: "Moderator",
    image: "/images/moderator.png",
    description: "You are moderating this debate.",
  });

  // Submit a topic or command from the moderator
  const handleModeratorSubmit = async (content) => {
    if (!content.trim()) return; // Prevent empty submissions

    const payload = {
      speaker: "Moderator",
      topic: content,
      message: "", // Moderator sets the topic
    };

    setLoading(true);
    try {
      const data = await submitTurn(payload);
      setTopic(content); // Set topic
      setHistory(data.conversation_history || []); // Update history
      setPersona(data.persona || {
        name: participants[0]?.name,
        image: "/images/default-avatar.png",
        description: "No description available.",
      });
    } catch (error) {
      console.error("Error submitting topic:", error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch a participant's response
  const fetchNextParticipant = async (speaker) => {
    const payload = { speaker, topic, message: "" };

    setLoading(true);
    try {
      const data = await submitTurn(payload);
      setHistory((prevHistory) => [...prevHistory, ...data.conversation_history]);
      setPersona(data.persona || {
        name: speaker,
        image: "/images/default-avatar.png",
        description: "No description available.",
      });
    } catch (error) {
      console.error("Error fetching participant response:", error);
    } finally {
      setLoading(false);
    }
  };

  // Fetch responses sequentially after the topic is set
  useEffect(() => {
    if (topic) {
      (async () => {
        for (const participant of participants) {
          await fetchNextParticipant(participant.name);
        }
      })();
    }
  }, [topic]);

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
        <Transcript
          history={history || []}
          personas={participants.reduce((acc, participant) => {
            acc[participant.name] = participant;
            return acc;
          }, {})}
        />

        {/* Moderator Input */}
        <ModeratorInput onSubmit={handleModeratorSubmit} />

        {/* Spinner */}
        {loading && <div className="spinner">Loading...</div>}
      </div>
    </div>
  );
}

export default App;