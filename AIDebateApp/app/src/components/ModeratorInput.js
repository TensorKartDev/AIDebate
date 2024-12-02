import React, { useState } from "react";
import "./ModeratorInput.css";

const ModeratorInput = ({ onSetTopic }) => {
  const [input, setInput] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim()) {
      onSetTopic(input);
      setInput(""); // Clear the input after submission
    }
  };

  return (
    <form className="moderator-input" onSubmit={handleSubmit}>
      <input
        type="text"
        placeholder="Enter debate topic..."
        value={input}
        onChange={(e) => setInput(e.target.value)}
      />
      <button type="submit">Set Topic</button>
    </form>
  );
};

export default ModeratorInput;