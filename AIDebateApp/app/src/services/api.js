import axios from 'axios'
const API_BASE_URL = "http://localhost:10000"; // Replace with your FastAPI backend URL
export const fetchNextTurn = async () => {
    console.log('ok')
    const response = await axios.get(`${API_BASE_URL}/next-turn`);
    return response.data; // Includes next_speaker and persona
  };
  
  export const submitTurn = async (speaker, message) => {
    const payload = { speaker, message };
    const response = await axios.post(`${API_BASE_URL}/submit-turn/`, payload);
    return response.data; // Includes conversation_history, next_speaker, and persona
  };