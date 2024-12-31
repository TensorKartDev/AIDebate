import React, { useState, useEffect } from "react";

function VoiceTester() {
  const [voices, setVoices] = useState([]);
  const [testText, setTestText] = useState("This is a voice test.");
  const [currentVoice, setCurrentVoice] = useState(null);

  useEffect(() => {
    const loadVoices = () => {
      const availableVoices = window.speechSynthesis.getVoices();
      console.log("Loaded voices:", availableVoices);
      setVoices(availableVoices);
    };

    if (window.speechSynthesis.onvoiceschanged !== undefined) {
      window.speechSynthesis.onvoiceschanged = loadVoices;
    }

    loadVoices(); // Call directly in case voices are already loaded
  }, []);

  const playVoice = (voice) => {
    // Stop any currently playing voice
    window.speechSynthesis.cancel();

    // Create a new utterance
    const utterance = new SpeechSynthesisUtterance(testText);
    utterance.voice = voice;

    // Track the currently playing voice
    setCurrentVoice(voice.name);

    utterance.onend = () => {
      setCurrentVoice(null);
    };

    utterance.onerror = () => {
      console.error("Error during voice playback:", voice.name);
      setCurrentVoice(null);
    };

    // Speak the text
    window.speechSynthesis.speak(utterance);
  };

  const stopVoice = () => {
    // Cancel all ongoing speech
    window.speechSynthesis.cancel();
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
              <strong>{voice.name}</strong> ({voice.lang}){" "}
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
                >
                  Stop
                </button>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p>No voices available. Please check your browser settings.</p>
      )}
    </div>
  );
}

export default VoiceTester;