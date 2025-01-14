import React, { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import { AiOutlineAudio } from "react-icons/ai";
import "./Transcript.css";

const Transcript = ({ history, personas, highlightedTextId, speakMessage, isListening, startListening }) => {
  const transcriptRef = useRef(null);

  useEffect(() => {
    if (transcriptRef.current) {
      // Smooth scroll to the bottom when history updates
      transcriptRef.current.scrollTo({
        top: transcriptRef.current.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [history]);

  const currentPersona =
    highlightedTextId !== null && history[highlightedTextId]
      ? personas[history[highlightedTextId].speaker] || { name: "Unknown Speaker" }
      : null;

  return (
    <div className="transcript-wrapper">
      {/* Left Panel: Animation or Moderator Placeholder */}
      <div className="transcript-column transcript-left">
        {currentPersona ? (
          <iframe
            src={`/animations/${currentPersona.name
              .replace(" ", "_")
              .toLowerCase()}/${currentPersona.name
              .replace(" ", "_")
              .toLowerCase()}.html`}
            title={`${currentPersona.name} Animation`}
            className="persona-animation-frame"
            frameBorder="0"
            onLoad={() => {
              const iframe = document.querySelector(".persona-animation-frame");
              if (iframe?.contentWindow?.resizeCanvas) {
                iframe.contentWindow.resizeCanvas();
              }
            }}
          ></iframe>
        ) : (
          <div className="placeholder">
            <img
              src="/images/moderator.png"
              alt="Moderator"
              className="moderator-image"
            />
            <div className="overlay">
              <AiOutlineAudio
                className={`start-listening-icon ${isListening ? "active" : ""}`}
                onClick={startListening}
                title="Start Listening"
                size={60} // Larger icon for better visual
              />
            </div>
          </div>
        )}
      </div>

      {/* Right Panel: Transcript */}
      <div className="transcript-column transcript-right" ref={transcriptRef}>
        {history.map((entry, index) => {
          const persona = personas[entry.speaker] || {
            name: entry.speaker || "Unknown Speaker",
            image: "/images/default-avatar.png",
            description: "No description available",
          };

          return (
            <div
              key={index}
              className={`transcript-entry ${
                highlightedTextId === index ? "highlighted-text" : ""
              }`}
            >
              {/* Speaker's Avatar */}
              <div className="avatar-container">
                <img
                  src={persona.image}
                  alt={persona.name}
                  className="avatar"
                  onError={(e) => {
                    e.target.src = "/images/default-avatar.png"; // Fallback for broken image
                  }}
                />
              </div>

              {/* Speaker's Message */}
              <div className="message-container">
                <div className="message-header">
                  <strong>{persona.name}</strong>
                  <span className="message-timestamp">
                    {new Date(entry.timestamp || Date.now()).toLocaleTimeString([], {
                      hour: "2-digit",
                      minute: "2-digit",
                    })}
                  </span>
                </div>
                <ReactMarkdown className="markdown-message">
                  {entry.message || "No message available"}
                </ReactMarkdown>
              </div>

              {/* Speaker Button */}
              <div className="hear-again-button-container">
                <button
                  className="hear-again-button"
                  onClick={() => speakMessage(entry.message, entry.speaker, index)}
                  title="Hear Again"
                >
                  <AiOutlineAudio size={20} />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default Transcript;