import React, { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";
import { AiOutlineAudio } from "react-icons/ai";

const Transcript = ({ history, personas, highlightedTextId, speakMessage }) => {
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

  return (
    <div className="transcript" ref={transcriptRef}>
      {history.map((entry, index) => {
        // Fallback handling if persona is missing
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
  );
};

export default Transcript;