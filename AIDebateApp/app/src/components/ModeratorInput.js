import React, { useState } from "react";

const ModeratorInput = ({ onSubmit }) => {
  const [input, setInput] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim()) {
      onSubmit(input); // Pass input to parent handler
      setInput(""); // Clear input field
    }
  };

  return (
    <form className="moderator-input" onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Enter a topic or message..."
        value={input}
        onChange={(e) => setInput(e.target.value)}
        className="moderator-input-box"
      />
      <button type="submit" className="moderator-submit-button">Send</button>
    </form>
  );
};

export default ModeratorInput;