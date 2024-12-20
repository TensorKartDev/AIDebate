import axios from 'axios';

const API_BASE_URL = "http://localhost:1000"; // Replace with your FastAPI backend URL

// Fetch the next turn (next speaker and persona)
export const fetchNextTurn = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/next-turn`);
    return response.data; // Includes next_speaker and persona
  } catch (error) {
    console.error("Error fetching next turn:", error);
    throw error;
  }
};

// Fetch conversation history
export const fetchHistory = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/history/`);
    return response.data;
  } catch (error) {
    console.error("Error fetching history:", error);
    throw error;
  }
};

// Submit a turn (speaker, topic, message)
export const submitTurn = async ({ speaker, topic, message }) => {
  const payload = { speaker, topic, message };
  console.log("Payload sent to /submit-turn/:", payload);
  try {
    const response = await axios.post(`${API_BASE_URL}/submit-turn/`, payload);
    console.log("Response from /submit-turn/:", response.data);
    return response.data;
  } catch (error) {
    console.error("Error submitting turn:", error);
    throw error;
  }
};

// Fetch personas
export const fetchPersonas = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/personas/`);
    return response.data;
  } catch (error) {
    console.error("Error fetching personas:", error);
    throw error;
  }
};

// Submit the moderator's topic (with voice input as audio file)
export const moderatorTopic = async (formData) => {
  try {
    const response = await axios.post(`${API_BASE_URL}/moderator-topic/`, formData, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return response.data;
  } catch (error) {
    console.error("Error submitting moderator topic:", error);
    throw error;
  }
};

// Fetch participant responses
export const participantResponse = async () => {
  try {
    const response = await axios.post(`${API_BASE_URL}/participant-response/`);
    return response.data;
  } catch (error) {
    console.error("Error fetching participant responses:", error);
    throw error;
  }
};