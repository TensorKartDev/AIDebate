const Transcript = ({ history, personas }) => {
  return (
    <div className="transcript">
      {history.map((entry, index) => {
        // Safely retrieve the persona or use a fallback
        const persona = personas[entry.speaker] || {
          name: entry.speaker,
          image: "/images/default-avatar.png", // Fallback image
        };

        return (
          <div key={index} className="transcript-entry">
            <img
              src={persona.image}
              alt={persona.name || "Speaker"}
              className="avatar"
              onError={(e) => { e.target.src = "/images/default-avatar.png"; }} // Handle image loading errors
            />
            <div>
              <strong>{persona.name || "Unknown"}:</strong> {entry.message}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default Transcript;