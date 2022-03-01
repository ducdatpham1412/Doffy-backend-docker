import axios from "axios";
import env from "./env.js";

export const request = axios.create({
    baseURL: env.API_URL,
    timeout: 5000,
    headers: {
        Accept: "*/*",
    },
});

request.interceptors.response.use((response) => response.data);
