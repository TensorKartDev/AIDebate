import React, { useEffect, useRef } from "react";

const Transcript = ({ history, participants, personas }) => {
  const transcriptRef = useRef(null);

  useEffect(() => {
    if (transcriptRef.current) {
      // Scroll to the bottom when history updates
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [history]);

  return (
    <div className="transcript" ref={transcriptRef}>
      {history.map((entry, index) => {
        const persona = personas[entry.speaker];
        return (
          <div key={index} className="transcript-entry">
            <img
              src={persona?.image || "/images/default-avatar.png"}
              alt={persona?.name || entry.speaker}
              className="avatar"
              onError={(e) => {
                e.target.src = "/images/default-avatar.png";
              }}
            />
            <div>
              <strong>{persona?.name || entry.speaker}:</strong>
              <p>{entry.message}</p>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default Transcript;