import React from "react";
import ReactMarkdown from "react-markdown";

const Transcript = ({ history, participants }) => {
  return (
    <div className="transcript">
      {history.map((entry, index) => {
        // Find the participant matching the speaker's name
        const participant = participants.find((p) => p.name === entry.speaker) || {
          name: entry.speaker,
          image: entry.image,
        };

        return (
          <div key={index} className="transcript-entry">
            <img src={participant.image} alt={participant.name} className="avatar" />
            <div>
              <strong>{participant.name}:</strong>
              <ReactMarkdown>{entry.message}</ReactMarkdown>
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default Transcript;