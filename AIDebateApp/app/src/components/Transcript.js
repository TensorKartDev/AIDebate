import React, { useEffect, useRef } from "react";
import ReactMarkdown from "react-markdown";

const Transcript = ({ history, participants, personas }) => {
  const transcriptRef = useRef(null);

  useEffect(() => {
    if (transcriptRef.current) {
      // Automatically scroll to the bottom when history updates
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
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
          <div key={index} className="transcript-entry">
            {/* Display speaker's avatar */}
            <img
              src={persona.image}
              alt={persona.name}
              className="avatar"
              onError={(e) => {
                e.target.src = "/images/default-avatar.png"; // Fallback for broken image
              }}
            />

            {/* Speaker's message */}
            <div>
              <strong>{persona.name}:</strong>
              <ReactMarkdown className="markdown-message">
                {entry.message || "No message available"}
              </ReactMarkdown>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default Transcript;