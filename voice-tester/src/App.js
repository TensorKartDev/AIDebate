import React, { useState, useEffect } from "react";

function App() {
  const [voices, setVoices] = useState([]);
  const [testText, setTestText] = useState("This is a voice test.");
  const [currentVoice, setCurrentVoice] = useState(null);
  const [currentUtterance, setCurrentUtterance] = useState(null);

  useEffect(() => {
    const loadVoices = () => {
      const availableVoices = speechSynthesis.getVoices();
      if (availableVoices.length > 0) {
        setVoices(availableVoices);
      } else {
        console.error("No voices available. Ensure your browser supports SpeechSynthesis.");
      }
    };

    if (speechSynthesis.onvoiceschanged !== undefined) {
      speechSynthesis.onvoiceschanged = loadVoices;
    } else {
      loadVoices();
    }
  }, []);

  const playVoice = (voice) => {
    stopVoice(); // Stop any currently playing voice before starting a new one
    const utterance = new SpeechSynthesisUtterance(testText);
    utterance.voice = voice;

    utterance.onstart = () => {
      setCurrentVoice(voice.name); // Highlight the playing voice
    };

    utterance.onend = () => {
      setCurrentVoice(null); // Remove highlight after playback
    };

    speechSynthesis.speak(utterance);
    setCurrentUtterance(utterance);
  };

  const stopVoice = () => {
    if (currentUtterance) {
      speechSynthesis.cancel(); // Stop current speech synthesis
      setCurrentVoice(null); // Remove highlight
      setCurrentUtterance(null); // Clear current utterance
    }
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
        style={{ width: "100%", marginBottom: "20px", padding: "10px" }}
      />
      <h2>Available Voices</h2>
      {voices.length === 0 ? (
        <p>No voices available. Please check your browser settings.</p>
      ) : (
        <ul style={{ listStyleType: "none", padding: 0 }}>
          {voices.map((voice, index) => (
            <li
              key={index}
              style={{
                marginBottom: "15px",
                padding: "10px",
                border: "1px solid #ccc",
                borderRadius: "5px",
                backgroundColor:
                  currentVoice === voice.name ? "#e0f7fa" : "#ffffff",
              }}
            >
              <strong>{voice.name}</strong> ({voice.lang}){" "}
              {voice.default && <span style={{ color: "green" }}>Default</span>}
              <div style={{ marginTop: "10px" }}>
                <button
                  onClick={() => playVoice(voice)}
                  style={{
                    marginRight: "10px",
                    padding: "5px 15px",
                    backgroundColor: "#007BFF",
                    color: "white",
                    border: "none",
                    cursor: "pointer",
                    borderRadius: "3px",
                  }}
                >
                  Play
                </button>
                <button
                  onClick={stopVoice}
                  style={{
                    padding: "5px 15px",
                    backgroundColor: "#FF3B3F",
                    color: "white",
                    border: "none",
                    cursor: "pointer",
                    borderRadius: "3px",
                  }}
                >
                  Stop
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

export default App;