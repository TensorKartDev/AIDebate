import React, { useEffect, useRef } from "react";

const Transcript = ({ history, participants }) => {
  const transcriptEndRef = useRef(null); // Reference to the end of the transcript

  // Scroll to the last message when history updates
  useEffect(() => {
    if (transcriptEndRef.current) {
      transcriptEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [history]);

  return (
    <div className="transcript">
      {history.map((entry, index) => {
        const participant = participants.find((p) => p.name === entry.speaker) || {
          name: entry.speaker,
          image: "/images/default-avatar.png",
        };

        return (
          <div key={index} className="transcript-entry">
            <img src={participant.image} alt={participant.name} className="avatar" />
            <div>
              <strong>{participant.name}:</strong>
              <p>{entry.message}</p>
            </div>
          </div>
        );
      })}
      {/* Invisible div for auto-scrolling */}
      <div ref={transcriptEndRef} />
    </div>
  );
};

export default Transcript;