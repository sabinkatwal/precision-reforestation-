import axios from "axios";

const API = axios.create({
  baseURL: "http://localhost:8001",
});

export const getEnvironment = (lat, lng) => API.get(`/environment?lat=${lat}&lng=${lng}`);

export const analyzePatch = (lat, lng) => API.post("/analyze", { lat, lng });

export const getSoil = (lat, lng) => API.get(`/soil?lat=${lat}&lng=${lng}`);

export const getElevation = (lat, lng) => API.get(`/elevation?lat=${lat}&lng=${lng}`);

export const getCropRecommendations = (lat, lng) => API.get(`/crops?lat=${lat}&lng=${lng}`);

export default API;