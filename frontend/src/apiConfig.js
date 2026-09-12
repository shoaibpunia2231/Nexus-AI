// Centralized API configuration for Nexus AI
export const API_URL =
  import.meta.env.VITE_API_URL ||
  (import.meta.env.DEV
    ? `http://${window.location.hostname}:8000`
    : "https://nexusai-backend.onrender.com");

export default API_URL;
