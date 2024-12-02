import axios from 'axios'
const API_BASE_URL = "http://localhost:10000"; // Replace with your FastAPI backend URL
export const fetchNextTurn = async () => {
    console.log('ok')
    const response = await axios.get(`${API_BASE_URL}/next-turn`);
    return response.data; // Includes next_speaker and persona
  };
  
  export const fetchHistory = async () => {
    const response = await axios.get(`${API_BASE_URL}/history/`);
    return response.data;
  };
  export const submitTurn = async ({ speaker, topic, message }) => {
    const payload = { speaker, topic, message };
    console.log("Payload sent to /submit-turn/:", payload);
    const response = await axios.post(`${API_BASE_URL}/submit-turn/`, payload);
    console.log("Response from /submit-turn/:", response.data);
    return response.data;
  };
  export const fetchPersonas = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/personas/`);
      if (!response.ok) {
        throw new Error(`Error fetching personas: ${response.statusText}`);
      }
      return await response.json();
    } catch (error) {
      console.error("Error in fetchPersonas:", error);
      throw error;
    }
  };