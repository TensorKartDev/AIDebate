import axios from 'axios'
const API_BASE_URL = "http://localhost:10000"; // Replace with your FastAPI backend URL
export const fetchNextTurn = async () => {
    console.log('ok')
    const response = await axios.get(`${API_BASE_URL}/next-turn`);
    return response.data; // Includes next_speaker and persona
  };
  
  export const submitTurn = async ({ speaker, topic, message }) => {
    const payload = { speaker, topic, message };
    console.log("Submitting payload:", payload); // Debug log
    const response = await axios.post(`${API_BASE_URL}/submit-turn/`, payload);
    return response.data;
  };

  export const fetchHistory = async () => {
    const response = await axios.get(`${API_BASE_URL}/history/`);
    return response.data;
  };