import React, { useState, useEffect } from "react";

function VoiceTester() {
  const [voices, setVoices] = useState([]);
  const [testText, setTestText] = useState("This is a voice test.");
  const [currentVoice, setCurrentVoice] = useState(null);

  useEffect(() => {
    const loadVoices = () => {
      const availableVoices = window.speechSynthesis.getVoices();
      console.log("Loaded voices:", availableVoices);
      if (availableVoices.length > 0) {
        setVoices(availableVoices);
      } else {
        console.warn("No voices available.");
      }
    };

    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }

    loadVoices(); // Load voices directly
  }, []);

  const playVoice = (voice) => {
    window.speechSynthesis.cancel(); // Stop any currently playing voice

    const utterance = new SpeechSynthesisUtterance(testText);
    utterance.voice = voice;

    setCurrentVoice(voice.name); // Track currently playing voice

    utterance.onend = () => setCurrentVoice(null);
    utterance.onerror = () => {
      console.error("Error during voice playback:", voice.name);
      setCurrentVoice(null);
    };

    window.speechSynthesis.speak(utterance);
  };

  const stopVoice = () => {
    window.speechSynthesis.cancel(); // Stop all ongoing speech
    setCurrentVoice(null);
  };

  return (
    <div style={{ padding: "20px", fontFamily: "Arial, sans-serif" }}>
      <h1>Voice Tester</h1>
      <textarea
        value={testText}
        onChange={(e) => setTestText(e.target.value)}
        rows="3"
        cols="50"
        placeholder="Enter test text here..."
        style={{ width: "100%", marginBottom: "10px" }}
      />
      <h2>Available Voices</h2>
      {voices.length > 0 ? (
        <ul style={{ listStyleType: "none", padding: 0 }}>
          {voices.map((voice, index) => (
            <li
              key={index}
              style={{
                marginBottom: "10px",
                padding: "10px",
                border: "1px solid #ddd",
                borderRadius: "5px",
                background: currentVoice === voice.name ? "#f0f8ff" : "#fff",
              }}
            >
              <strong>{voice.voiceURI}</strong> | <strong>{voice.name}</strong> ({voice.lang}){" "}
              {voice.default && <span style={{ color: "green" }}>Default</span>}
              <div style={{ marginTop: "5px" }}>
                <button
                  onClick={() => playVoice(voice)}
                  style={{
                    padding: "5px 10px",
                    marginRight: "10px",
                    background: "#007BFF",
                    color: "white",
                    border: "none",
                    cursor: "pointer",
                  }}
                  disabled={currentVoice === voice.name}
                  aria-label={`Play ${voice.name}`}
                >
                  Play
                </button>
                <button
                  onClick={stopVoice}
                  style={{
                    padding: "5px 10px",
                    background: "#FF4136",
                    color: "white",
                    border: "none",
                    cursor: "pointer",
                  }}
                  disabled={currentVoice !== voice.name}
                  aria-label={`Stop ${voice.name}`}
                >
                  Stop
                </button>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p>
          No voices available. Please check your browser settings or ensure that the Speech Synthesis API is
          supported.
        </p>
      )}
    </div>
  );
}

export default VoiceTester;