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
  const [isLoading, setIsLoading] = useState(false);
  const [activeSpeaker, setActiveSpeaker] = useState(null);
  const [highlightedTextId, setHighlightedTextId] = useState(null);
  const wsRef = useRef(null);
  const speechQueue = useRef([]);
  const isSpeakingRef = useRef(false);

  const speakMessage = (message, speaker, index) => {
    if (speaker === "Moderator") {
      console.log("Skipping reading aloud for Moderator.");
      return;
    }

    if (!("speechSynthesis" in window)) {
      console.error("Text-to-speech is not supported in this browser.");
      return;
    }

    // Add the message to the speech queue
    speechQueue.current.push({ message, speaker, index });
    processSpeechQueue();
  };

  const processSpeechQueue = () => {
    if (isSpeakingRef.current || speechQueue.current.length === 0) return;

    const { message, speaker, index } = speechQueue.current.shift();
    isSpeakingRef.current = true;

    setActiveSpeaker(speaker);
    setHighlightedTextId(index);

    const utterance = new SpeechSynthesisUtterance(message);
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

    utterance.pitch = personas[speaker]?.pitch || 1;
    utterance.rate = personas[speaker]?.rate || 1;

    utterance.onend = () => {
      isSpeakingRef.current = false;
      setActiveSpeaker(null);
      setHighlightedTextId(null);
      processSpeechQueue(); // Process the next item in the queue
    };

    utterance.onerror = (error) => {
      console.error("Speech synthesis error:", error);
      isSpeakingRef.current = false;
      setActiveSpeaker(null);
      setHighlightedTextId(null);
      processSpeechQueue(); // Process the next item in the queue
    };

    speechSynthesis.speak(utterance);
  };

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

    if (!wsRef.current) {
      wsRef.current = new WebSocket("ws://localhost:1000/ws");

      wsRef.current.onopen = () => console.log("WebSocket connection established");

      wsRef.current.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          console.log("WebSocket message received:", data);
          setHistory((prev) => [...prev, data]);
          if (data.speaker !== "Moderator") {
            speakMessage(data.message, data.speaker, history.length);
          }
          setIsLoading(false);
        } catch (e) {
          console.error("Failed to process WebSocket message:", e);
          alert("An error occurred while processing a message.");
          setIsLoading(false);
        }
      };

      wsRef.current.onerror = (error) => {
        setIsLoading(false);
        console.error("WebSocket error:", error);
      };

      wsRef.current.onclose = (event) => {
        console.log(
          `WebSocket connection closed with code ${event.code} and reason: ${event.reason}`
        );
      };
    }

    return () => {
      if (wsRef.current) {
        wsRef.current.close(1000, "Component unmounting");
        wsRef.current = null;
      }
    };
  }, [history]);

  const startListening = () => {
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    setIsListening(true);
    setActiveSpeaker("Moderator");

    recognition.onresult = async (event) => {
      const transcript = event.results[0][0].transcript;
      setIsListening(false);
      recognition.stop();
      setActiveSpeaker(null);

      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        const messagePayload = { speaker: "Moderator", message: transcript };
        console.log("Sending transcript to WebSocket:", messagePayload);
        wsRef.current.send(JSON.stringify(messagePayload));
        setIsLoading(true);
      } else {
        console.error("WebSocket is not open. Unable to send transcript.");
      }
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      setIsListening(false);
      recognition.stop();

      if (event.error === "no-speech") {
        alert("No speech detected. Please try again.");
      }
    };

    recognition.onend = () => {
      setIsListening(false);
      setActiveSpeaker(null);
    };

    recognition.start();
  };

  return (
    <div className="container-fluid d-flex flex-column vh-100">
      {/* Main Panel */}
      <div className="flex-grow-1 overflow-auto">
        <h1 className="text-center">AI Fireside Chat</h1>
        <div className="scrollable-transcript">
          <Transcript
            history={history}
            personas={personas}
            highlightedTextId={highlightedTextId}
          />
        </div>
      </div>

      {/* Bottom Panel: Participants */}
      <div className="bottom-panel bg-light border-top w-100">
        <div className="d-flex align-items-center justify-content-between px-3 py-2">
          <h4>Participants</h4>
          <AiOutlineAudio
            className={`start-listening-icon ${isListening ? "active" : ""}`}
            size={40}
            onClick={startListening}
            title="Start Listening"
          />
        </div>
        <div className="participants-list d-flex flex-wrap overflow-auto px-3 py-2">
          {Object.keys(personas).length > 0 ? (
            Object.keys(personas).map((participant) => (
              <div
                key={participant}
                className={`participant-card ${
                  participant === activeSpeaker ? "highlight" : ""
                } ${
                  isListening && participant === "Moderator" ? "highlight" : ""
                }`}
              >
                <img
                  src={personas[participant]?.image || "/images/default-avatar.png"}
                  alt={personas[participant]?.name || participant}
                  className="avatar mb-2"
                />
                <strong>{personas[participant]?.name || participant}</strong>
                <p className="small text-muted">
                  {personas[participant]?.description || "No description available"}
                </p>
              </div>
            ))
          ) : (
            <p>Loading participants...</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;