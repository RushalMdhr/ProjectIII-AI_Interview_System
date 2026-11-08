import axios from "axios";

// =====================================================
// AXIOS CLIENT
// =====================================================

const baseURL = import.meta.env.VITE_API_URL || "http://localhost:8000";
const client = axios.create({ baseURL });
let refreshRequest = null;


// =====================================================
// JWT INTERCEPTOR
// =====================================================

client.interceptors.request.use(
  (config) => {

    const token = localStorage.getItem("accessToken");

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },

  (error) => {
    return Promise.reject(error);
  }
);


client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (
      error.response?.status !== 401 ||
      !originalRequest ||
      originalRequest._retry
    ) {
      return Promise.reject(error);
    }

    const requestUrl = originalRequest.url;

    const isAuthRequest =
      requestUrl === "/accounts/login/" ||
      requestUrl === "/accounts/register/" ||
      requestUrl === "/accounts/token/refresh/" ||
      requestUrl === "/accounts/password-reset/" ||
      requestUrl === "/accounts/password-reset/confirm/";

    if (isAuthRequest) {
      return Promise.reject(error);
    }

    const refreshToken = localStorage.getItem("refreshToken");

    if (!refreshToken) {
      logout();
      window.location.assign("/login");
      return Promise.reject(error);
    }

    originalRequest._retry = true;

    try {
      refreshRequest ||= axios
        .post(`${baseURL}/accounts/token/refresh/`, {
          refresh: refreshToken,
        })
        .then((response) => response.data.access)
        .finally(() => {
          refreshRequest = null;
        });

      const accessToken = await refreshRequest;

      localStorage.setItem("accessToken", accessToken);
      originalRequest.headers.Authorization = `Bearer ${accessToken}`;

      return client(originalRequest);
    } catch (refreshError) {
      logout();
      window.location.assign("/login");

      return Promise.reject(refreshError);
    }
  },
);



// =====================================================
// ASK QUESTION
// =====================================================

export async function askQuestion(question) {
  const res = await client.post(
    "/interview/",
    {
      message: question,
    }
  );

  return res.data;
}


// =====================================================
// CHAT SESSIONS
// =====================================================

export async function createChatSession(
  title = "New Chat Session",
  useCase = "general_chat",
  interviewDifficulty = "medium",
) {
  const res = await client.post(
    "/chats/session/",
    {
      title,
      use_case: useCase,
      interview_difficulty: interviewDifficulty,
    }
  );

  return res.data;
}


export async function getChatSessions() {
  const res = await client.get(
    "/chats/session/"
  );

  return res.data;
}


export async function sendChatMessage(userContent, sessionId = null) {
  const payload = {
    user_content: userContent,
  };

  if (sessionId) {
    payload.session = sessionId;
  }

  const res = await client.post(
    "/chats/message/",
    payload
  );

  return res.data;
}

export async function getAnalyticsSummary(days = 30) {
  const res = await client.get(`/ai/analytics/summary/?days=${days}`);
  return res.data;
}

export async function getAnalyticsTimeseries(days = 30) {
  const res = await client.get(`/ai/analytics/timeseries/?days=${days}`);
  return res.data;
}

export async function getUserActivity(days = 30) {
  const res = await client.get(`/ai/analytics/users/?days=${days}`);
  return res.data;
}

export async function getModelPricing() {
  const res = await client.get("/ai/analytics/pricing/");
  return res.data;
}

export async function saveModelPricing(payload) {
  const res = await client.post("/ai/analytics/pricing/", payload);
  return res.data;
}

export async function getUseCaseConfigs() {
  const res = await client.get("/ai/analytics/use-case-config/");
  return res.data;
}

export async function saveUseCaseConfig(payload) {
  const res = await client.post("/ai/analytics/use-case-config/", payload);
  return res.data;
}


export async function startChatInterview(sessionId) {
  const res = await client.post(`/chats/session/${sessionId}/start-interview/`);
  return res.data;
}


export async function prefetchInterviewQuestions(sessionId) {
  const res = await client.post(`/chats/session/${sessionId}/prefetch-questions/`);
  return res.data;
}

export async function generateInterviewAnswerSuggestion(sessionId, draft) {
  const res = await client.post(
    `/chats/session/${sessionId}/suggest-answer/`,
    { draft },
  );
  return res.data;
}

export async function getInterviewResults(sessionId, includeReview = false) {
  const res = await client.get(`/chats/session/${sessionId}/results/`, {
    params: includeReview ? { include: "review" } : undefined,
  });
  return res.data;
}


export async function getChatMessages(sessionId) {
  const res = await client.get(
    `/chats/session/${sessionId}/messages`
  );

  return res.data;
}


// =====================================================
// START INTERVIEW
// =====================================================

export async function startInterview(level) {
  const res = await client.post(
    "/interview/start",
    {
      level: level,
    }
  );

  return res.data;
}


// =====================================================
// SUBMIT ANSWER
// =====================================================

export async function submitAnswer(
  sessionId,
  answer
) {
  const res = await client.post(
    `/interview/${sessionId}/answer`,
    {
      answer: answer,
    }
  );

  return res.data;
}


// =====================================================
// REGISTER
// =====================================================

export async function register(
  name,
  email,
  password
) {
  const res = await client.post(
    "/accounts/register/",
    {
      first_name: name,
      email: email,
      password: password,
    }
  );

  return res.data;
}


// =====================================================
// LOGIN
// =====================================================

export async function login(
  email,
  password
) {
  const res = await client.post(
    "/accounts/login/",
    {
      email: email,
      password: password,
    }
  );

  return res.data;
}

export async function requestPasswordReset(email) {
  const res = await client.post("/accounts/password-reset/", { email });
  return res.data;
}

export async function confirmPasswordReset(uid, token, password) {
  const res = await client.post("/accounts/password-reset/confirm/", {
    uid,
    token,
    password,
  });
  return res.data;
}


// =====================================================
// GET CURRENT USER
// =====================================================

export async function getCurrentUser() {

  const res = await client.get(
    "/accounts/me/"
  );

  return res.data;
}


// =====================================================
// LOGOUT
// =====================================================

export function logout() {

  localStorage.removeItem("accessToken");
  localStorage.removeItem("refreshToken");
  localStorage.removeItem("currentUser");
}


// =====================================================
// TEST CONNECTION
// =====================================================

export async function testConnection(message) {
  const response = await client.post(
    "/test_connect",
    { message }
  );

  return response.data;
}