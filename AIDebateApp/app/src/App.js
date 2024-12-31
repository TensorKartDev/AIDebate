import React, { useState, useEffect } from "react";
import { fetchPersonas, moderatorTopic, participantResponse } from "./services/api";
import Transcript from "./components/Transcript";
import { AiOutlineAudio } from "react-icons/ai";
import "bootstrap/dist/css/bootstrap.min.css";
import "./App.css";

function App() {
  const [personas, setPersonas] = useState({});
  const [history, setHistory] = useState([]);
  const [topic, setTopic] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [isListening, setIsListening] = useState(false);
  const [currentSpeaker, setCurrentSpeaker] = useState(null);

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
    const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    setIsListening(true);

    recognition.onresult = async (event) => {
      const transcript = event.results[0][0].transcript;
      setIsListening(false);
      recognition.stop();
      await handleModeratorInput(transcript);
    };

    recognition.onerror = (event) => {
      console.error("Speech recognition error:", event.error);
      setIsListening(false);
      recognition.stop();
    };

    recognition.onend = () => {
      setIsListening(false);
    };

    recognition.start();
  };

  const handleModeratorInput = async (transcript) => {
    setIsProcessing(true);
    try {
      const payload = { speaker: "Moderator", topic: transcript, message: "" };
      const response = await moderatorTopic(payload);

      if (response.conversation_history) {
        setHistory(response.conversation_history);
        setTopic(transcript);
        await handleParticipantResponses(Object.keys(personas)); // Start participant responses
      }
    } catch (error) {
      console.error("Error handling moderator input:", error);
      alert("Failed to set the debate topic.");
    } finally {
      setIsProcessing(false);
    }
  };

  const handleParticipantResponses = async (participants) => {
    try {
      for (const participant of participants) {
        setCurrentSpeaker(participant);
        try {
          const formData = { topic }; // Use topic to send with API
          const response = await participantResponse(participant, formData);
  
          if (response.responses && response.responses.length > 0) {
            const { speaker, message } = response.responses[0];
            setHistory((prevHistory) => [...prevHistory, { speaker, message }]); // Update transcript
  
            // Use voice_language from personas to select the appropriate voice
          const voiceLanguage = personas[speaker]?.voice_language || "en-US";
          console.log("persona voicez",voiceLanguage)
          const voices = speechSynthesis.getVoices();
          console.log(voices)
          const selectedVoice = voices.find((v) => v.voiceURI === voiceLanguage);

          const utterance = new SpeechSynthesisUtterance(message);
          if (selectedVoice) {
            utterance.voice = selectedVoice; // Assign the selected voice
          } else {
            console.warn(`Voice for language "${voiceLanguage}" not found, using default.`);
          }
          speechSynthesis.speak(utterance);
  
            // Delay between participants
            await new Promise((resolve) => setTimeout(resolve, 1000));
          }
        } catch (error) {
          console.error(`Error fetching response for ${participant}:`, error);
        }
      }
    } catch (error) {
      console.error("Error handling participant responses:", error);
      alert("Failed to fetch participant responses.");
    } finally {
      setCurrentSpeaker(null); // Clear spinner after all responses are processed
    }
  };

  const playAudio = (audio) => {
    return new Promise((resolve, reject) => {
      audio
        .play()
        .then(() => {
          console.log("Audio playback started");
          audio.onended = resolve; // Resolve when audio ends
        })
        .catch((error) => {
          console.warn("Autoplay blocked or error occurred:", error);
  
          // Show a manual player as a fallback
          const playerContainer = document.createElement("div");
          const player = document.createElement("audio");
          player.src = audio.src;
          player.controls = true;
          player.autoplay = true;
  
          player.onended = () => {
            playerContainer.remove(); // Remove the player after playback ends
            resolve();
          };
  
          player.onerror = (err) => {
            console.error("Error with manual playback:", err);
            playerContainer.remove();
            reject(err);
          };
  
          playerContainer.appendChild(player);
          document.body.appendChild(playerContainer);
        });
    });
  };

  return (
    <div className="container-fluid">
      <div className="row">
        {/* Left Panel: Participants */}
        <div className="col-md-3 left-panel">
          <h2>Participants</h2>
          {Object.keys(personas).length > 0 ? (
            <ul>
              {Object.keys(personas).map((participant) => (
                <li key={participant}>
                  <img
                    src={personas[participant]?.image || "/images/default-avatar.png"}
                    alt={personas[participant]?.name || participant}
                    className="avatar"
                  />
                  <strong>{personas[participant]?.name || participant}</strong>
                  <p>{personas[participant]?.description || "No description available"}</p>
                </li>
              ))}
            </ul>
          ) : (
            <p>Loading participants...</p>
          )}
        </div>

        {/* Main Panel */}
        <div className="col-md-9 main-panel">
          <h1>Interactive AI Debate</h1>
          {topic && <h2>Debate Topic: {topic}</h2>}
          <Transcript history={history} personas={personas} />

          {/* Spinner Popup */}
          {isProcessing && (
            <div className="popup-spinner">
              <div className="spinner-content">
                {currentSpeaker ? (
                  <>
                    <img
                      src={personas[currentSpeaker]?.image || "/images/default-avatar.png"}
                      alt={personas[currentSpeaker]?.name || "Processing"}
                      className="spinner-avatar"
                    />
                    <p className="spinner-text">
                      Processing response from {personas[currentSpeaker]?.name || currentSpeaker}...
                    </p>
                  </>
                ) : (
                  <p className="spinner-text">Processing topic...</p>
                )}
                <div className="spinner"></div>
              </div>
            </div>
          )}

          {/* Moderator Input Section */}
          <div className="moderator-input">
            {isListening ? (
              <div className="listening-loader">
                <p>Listening...</p>
                <div className="spinner-border text-primary" role="status">
                  <span className="visually-hidden">Loading...</span>
                </div>
              </div>
            ) : (
              <AiOutlineAudio
                className="start-listening-icon"
                size={50}
                onClick={startListening}
                title="Start Listening"
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;