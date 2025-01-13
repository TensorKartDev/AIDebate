import React from 'react';

const ModeratorPanel = ({ onMicClick }) => {
  return (
    <div className="moderator-panel">
      <button id="mic-button" onClick={onMicClick}>
        🎤 Add Moderator Input
      </button>
    </div>
  );
};

export default ModeratorPanel;