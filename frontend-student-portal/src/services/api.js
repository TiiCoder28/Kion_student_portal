import axios from "axios";

const API_URL = "http://127.0.0.1:5000"; // Flask server URL

export const sendMessage = async (message) => {
  try {
    const response = await axios.post(`${API_URL}/api/chat`, { message });
    return response.data.response;
  } catch (error) {
    console.error("Error:", error);
    return "Error communicating with AI";
  }
};
