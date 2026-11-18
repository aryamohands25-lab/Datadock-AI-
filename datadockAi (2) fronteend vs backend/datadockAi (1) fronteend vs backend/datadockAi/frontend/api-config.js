const configuredApiUrl = window.DATADOCK_API_URL?.trim();
const apiHost = window.location.hostname || "localhost";

window.DATADOCK_API_URL = (
    configuredApiUrl ||
    (window.location.port === "8000"
        ? window.location.origin
        : `http://${apiHost}:8000`)
).replace(/\/+$/, "");

window.DATADOCK_GOOGLE_CLIENT_ID = window.DATADOCK_GOOGLE_CLIENT_ID || "";