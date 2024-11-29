import React, { useState } from "react";

const ModeratorInput = ({ onSetTopic }) => {
  const [topic, setTopic] = useState("");

  const handleSubmit = (e) => {
    e.preventDefault();
    if (topic.trim()) {
      onSetTopic(topic);
      setTopic("");
    }
  };

  return (
    <form onSubmit={handleSubmit} className="moderator-input">
      <input
        type="text"
        placeholder="Set the debate topic..."
        value={topic}
        onChange={(e) => setTopic(e.target.value)}
      />
      <button type="submit">Set Topic</button>
    </form>
  );
};

export default ModeratorInput;