const Transcript = ({ history, personas }) => {
  return (
    <div className="transcript">
      {history.map((entry, index) => {
        const persona = personas[entry.speaker] || {
          name: entry.speaker,
          image: "/images/default-avatar.png",
        };

        return (
          <div key={index} className="transcript-entry">
            <img
              src={persona.image}
              alt={persona.name}
              className="avatar"
              onError={(e) => {
                e.target.src = "/images/default-avatar.png"; // Fallback image
              }}
            />
            <div>
              <strong>{persona.name}:</strong> {entry.message}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default Transcript;