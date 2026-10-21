// Dynamic host detection so frontend works on localhost AND over LAN / Wi-Fi
const hostname = typeof window !== 'undefined' && window.location.hostname ? window.location.hostname : '127.0.0.1';

export const API_BASE_URL = `http://${hostname}:8000`;
export const WS_BASE_URL = `ws://${hostname}:8000`;
