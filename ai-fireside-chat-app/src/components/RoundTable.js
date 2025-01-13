import React from 'react';
import './RoundTable.css';

const RoundTable = ({ highlightedPersona }) => {
  const personas = [
    { id: 1, name: 'Persona 1', image: '/assets/images/persona1.png' },
    { id: 2, name: 'Persona 2', image: '/assets/images/persona2.png' },
    { id: 3, name: 'Persona 3', image: '/assets/images/persona3.png' },
    { id: 4, name: 'Persona 4', image: '/assets/images/persona4.png' },
  ];

  return (
    <div className="round-table">
      {personas.map((persona) => (
        <div
          key={persona.id}
          className={`persona ${highlightedPersona === persona.id ? 'highlight' : ''}`}
          style={{ backgroundImage: `url(${persona.image})` }}
        >
          <span>{persona.name}</span>
        </div>
      ))}
    </div>
  );
};

export default RoundTable;