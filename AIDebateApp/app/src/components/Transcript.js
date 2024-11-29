const Transcript = ({ history = [], personas }) => {
  if (!Array.isArray(history) || history.length === 0) {
    return <p>No conversation history yet.</p>;
  }

  return (
    <div className="transcript">
      {history.map((entry, index) => {
        const persona = personas[entry.speaker] || {
          name: entry.speaker,
          image: "/images/default-avatar.png", // Default avatar
        };

        return (
          <div key={index} className="transcript-entry">
            <img
              src={persona.image}
              alt={persona.name}
              className="avatar"
              onError={(e) => {
                e.target.src = "/images/default-avatar.png";
              }}
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