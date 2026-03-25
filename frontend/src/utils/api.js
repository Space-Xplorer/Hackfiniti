const RAW_API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api";
const API_BASE_URL = RAW_API_BASE_URL.replace(/\/+$/, "");

const requestJson = async (path, options = {}) => {
  const mergedHeaders = {
    "Content-Type": "application/json",
    ...(options.headers || {})
  };

  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: mergedHeaders
  });

  const text = await response.text();
  const data = text ? JSON.parse(text) : {};

  if (!response.ok) {
    // FastAPI 422 returns { detail: [{...}] } pattern
    const detail = data.detail;
    if (Array.isArray(detail)) {
      throw new Error(detail.map(e => `${e.loc?.slice(-1)[0] || 'Field'}: ${e.msg}`).join(", "));
    } else if (detail && typeof detail === "object" && detail.errors) {
      throw new Error(JSON.stringify(detail));
    }
    const message = (typeof detail === "string" ? detail : null) || data.message || data.error || "Request failed";
    throw new Error(message);
  }

  return data;
};

export const sendOtp = async (mobile) => {
  return requestJson("/auth/send-otp", {
    method: "POST",
    body: JSON.stringify({ mobile })
  });
};

export const verifyOtp = async (mobile, otp) => {
  return requestJson("/auth/verify-otp", {
    method: "POST",
    body: JSON.stringify({ mobile, otp })
  });
};

export const registerUser = async (payload) => {
  const response = await fetch(`${API_BASE_URL}/auth/register`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  const text = await response.text();
  const data = text ? JSON.parse(text) : {};

  if (response.status === 409) {
    return data;
  }

  if (!response.ok) {
    const detail = data.detail;
    if (Array.isArray(detail)) {
      throw new Error(detail.map(e => `${e.loc?.slice(-1)[0] || 'Field'}: ${e.msg}`).join(", "));
    }
    const message = (typeof detail === "string" ? detail : null) || data.error || data.message || "Request failed";
    throw new Error(message);
  }

  return data;
};

export const loginUser = async (payload) => {
  return requestJson("/auth/login", {
    method: "POST",
    body: JSON.stringify(payload)
  });
};

export const verifyKyc = async (token, payload) => {
  return requestJson("/workflow/verify-kyc", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  });
};

export const createApplication = async (token, payload) => {
  return requestJson("/applications/", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  });
};

export const previewOcr = async (token, payload) => {
  return requestJson("/workflow/preview-ocr", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`
    },
    body: JSON.stringify(payload)
  });
};

export const submitWorkflow = async (token, appId) => {
  return requestJson(`/workflow/submit/${appId}`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
};

export const getWorkflowStatus = async (token, appId) => {
  return requestJson(`/workflow/status/${appId}`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
};

export const getWorkflowResults = async (token, appId) => {
  return requestJson(`/workflow/results/${appId}`, {
    headers: {
      Authorization: `Bearer ${token}`
    }
  });
};
