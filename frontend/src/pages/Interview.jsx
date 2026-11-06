import React, { useEffect, useRef, useState } from "react";
import { Navigate, useLocation, useNavigate } from "react-router-dom";
import { ArrowLeft, Bot, LoaderCircle, Play, Send, UserRound } from "lucide-react";
import {
  createChatSession,
  prefetchInterviewQuestions,
  sendChatMessage,
  startChatInterview,
} from "../services/api";

export default function Interview() {
  const { state } = useLocation();
  const navigate = useNavigate();
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);
  const wasSendingRef = useRef(false);
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState([]);
  const [hasStarted, setHasStarted] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");
  const [sessionId, setSessionId] = useState(state?.sessionId || null);

  const latestAssistantId = [...messages]
    .reverse()
    .find((message) => message.role === "assistant")?.id;

  useEffect(() => {
    if (!hasStarted || !latestAssistantId || !sessionId) return;
    prefetchInterviewQuestions(sessionId).catch(() => {});
  }, [hasStarted, latestAssistantId, sessionId]);

  const handleStart = async () => {
    if (isSending || hasStarted) return;

    setError("");
    setIsSending(true);
    try {
      const activeSessionId =+
        sessionId ||
        (
          await createChatSession(
            `${state.difficulty} Interview`,
            "interview_assessment",
            state.difficultyId,
          )
        ).id;
      setSessionId(activeSessionId);

      const response = await startChatInterview(activeSessionId);
      console.log("response : ",response)
      const opening = response.message?.assistant_content;
      if (!opening) {
        setError("The interview could not create its opening question.");
        return;
      }
      setMessages([{ id: response.message.id, role: "assistant", content: opening }]);
      setHasStarted(true);
    } catch (requestError) {
      setError(
        (requestError.response?.status === 401 &&
          "Your login has expired. Please log in and try starting the interview again.") ||
          requestError.response?.data?.error ||
          requestError.response?.data?.detail ||
          "The interview could not start right now. Please try again.",
      );
    } finally {
      setIsSending(false);
    }
  };

  useEffect(() => {
    const textarea = inputRef.current;
    if (!textarea) return;

    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, 144)}px`;
    textarea.style.overflowY = textarea.scrollHeight > 144 ? "auto" : "hidden";
  }, [input]);

  useEffect(() => {
    if (wasSendingRef.current && !isSending) {
      inputRef.current?.focus();
    }

    wasSendingRef.current = isSending;
  }, [isSending]);

  const handleSend = async (event) => {
    event.preventDefault();
    const content = input.trim();
    if (!content || isSending || !hasStarted) return;

    setMessages((current) => [...current, { id: `user-${Date.now()}`, role: "user", content }]);
    setInput("");
    setError("");
    setIsSending(true);

    try {
      const response = await sendChatMessage(content, sessionId);
      const assistantContent = response.message?.assistant_content;
      if (assistantContent) {
        setMessages((current) => [...current, {
          id: response.message.id || `assistant-${Date.now()}`,
          role: "assistant",
          content: assistantContent,
        }]);
      } else {
        setError(response.error || "The interview did not return a reply.");
      }
    } catch (requestError) {
      setError(requestError.response?.data?.error || "The interview could not respond right now. Please try again.");
    } finally {
      setIsSending(false);
    }
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  if (!state?.difficultyId) {
    return <Navigate to="/interview-setup" replace />;
  }

  return (
    <div className="interview-chat-page">
      <style>{`
        .interview-chat-page { height: calc(100vh - 68px); height: calc(100dvh - 68px); min-height: 0; overflow: hidden; box-sizing: border-box; padding: 28px 20px; color: #FBFAFF; background: radial-gradient(circle at 15% 10%, rgba(139,124,246,.25), transparent 32%), radial-gradient(circle at 90% 85%, rgba(69,224,208,.15), transparent 35%), #171A3A; font-family: Inter, Arial, sans-serif; }
        .interview-chat-shell { max-width: 900px; height: 100%; min-height: 0; margin: 0 auto; display: flex; flex-direction: column; }
        .interview-chat-top { display: flex; align-items: center; justify-content: space-between; padding-bottom: 24px; }
        .interview-chat-title { display: flex; align-items: center; gap: 10px; font-size: 20px; font-weight: 800; }
        .interview-chat-title span { color: #45E0D0; }
        .interview-chat-back { display: inline-flex; align-items: center; gap: 6px; border: 0; background: transparent; color: #C2C4EC; cursor: pointer; }
        .interview-chat-heading { margin: 22px 0 28px; flex-shrink: 0; }
        .interview-chat-heading p { margin: 6px 0 0; color: #C2C4EC; font-size: 14px; }
        .interview-chat-heading h1 { margin: 0; font-size: clamp(26px, 5vw, 38px); }
        .interview-transcript { flex: 1; min-height: 0; overflow-y: auto; padding: 24px 0; }
        .interview-empty { max-width: 570px; margin: 70px auto; text-align: center; color: #C2C4EC; line-height: 1.6; }
        .interview-empty strong { display: block; margin-bottom: 8px; color: #FBFAFF; font-size: 18px; }
        .interview-start { display: inline-flex; align-items: center; justify-content: center; gap: 8px; margin-top: 18px; padding: 11px 16px; border: 0; border-radius: 8px; background: #45E0D0; color: #10152B; font-weight: 700; cursor: pointer; }
        .interview-start:disabled { cursor: wait; opacity: .55; }
        .interview-message { display: flex; gap: 12px; margin: 0 0 18px; }
        .interview-message.user { justify-content: flex-end; }
        .interview-avatar { flex: 0 0 34px; height: 34px; display: grid; place-items: center; border-radius: 50%; background: #45E0D0; color: #10152B; }
        .interview-message.assistant .interview-avatar { order: -1; background: #8B7CF6; color: #10152B; }
        .interview-bubble { max-width: min(78%, 650px); padding: 13px 16px; border: 1px solid rgba(255,255,255,.12); border-radius: 16px; background: rgba(255,255,255,.08); line-height: 1.55; white-space: pre-wrap; }
        .interview-message.user .interview-bubble { background: rgba(69,224,208,.16); border-color: rgba(69,224,208,.25); }
        .interview-composer { display: flex; flex: 0 0 auto; align-items: flex-end; gap: 10px; padding-top: 18px; border-top: 1px solid rgba(255,255,255,.12); }
        .interview-input { flex: 1; min-width: 0; min-height: 52px; max-height: 144px; box-sizing: border-box; padding: 15px 17px; border: 1px solid rgba(255,255,255,.16); border-radius: 12px; outline: 0; resize: none; overflow-y: hidden; background: rgba(255,255,255,.08); color: #fff; font-size: 14px; line-height: 20px; }
        .interview-input:focus { border-color: #45E0D0; }
        .interview-send { display: inline-flex; align-items: center; justify-content: center; gap: 7px; min-width: 100px; border: 0; border-radius: 12px; background: #45E0D0; color: #10152B; font-weight: 700; cursor: pointer; }
        .interview-send:disabled { cursor: wait; opacity: .55; }
        .interview-error { margin: 14px 0 0; color: #F88B85; font-size: 13px; }
        .interview-loading { color: #45E0D0; animation: interview-spin 1s linear infinite; }
        @keyframes interview-spin { to { transform: rotate(360deg); } }
        @media (max-width: 560px) { .interview-chat-page { padding: 20px 15px; } .interview-send { min-width: 52px; } .interview-send-label { display: none; } }
      `}</style>

      <div className="interview-chat-shell">
        <header className="interview-chat-top">
          <button className="interview-chat-back" onClick={() => navigate("/interview-setup")}>
            <ArrowLeft size={15} /> Back
          </button>
          <div className="interview-chat-title">AI <span>INTERVIEW</span></div>
        </header> 

        <section className="interview-chat-heading">
          <h1>{state.difficulty || "Mock"} interview</h1>
          <p>{state.questionCount} questions · Interview assessment</p>
        </section>

        <main className="interview-transcript">
          {!messages.length && !isSending && (
            <div className="interview-empty">
              <strong>Ready when you are.</strong>
              <button
                className="interview-start"
                type="button"
                onClick={handleStart}
                disabled={isSending}
              >
                <Play size={16} /> Start interview
              </button>
            </div>
          )}
          {messages.map((message) => (
            <div className={`interview-message ${message.role}`} key={message.id}>
              <div className="interview-avatar">
                {message.role === "user" ? <UserRound size={16} /> : <Bot size={17} />}
              </div>
              <div className="interview-bubble">{message.content}</div>
            </div>
          ))}
          {isSending && <LoaderCircle className="interview-loading" size={20} />}
          <div ref={messagesEndRef} />
        </main>
        {hasStarted && (
        <form className="interview-composer" onSubmit={handleSend}>
          <textarea
            ref={inputRef}
            className="interview-input"
            rows={1}
            value={input}
            onChange={(event) => setInput(event.target.value)}
            onKeyDown={(event) => {
              if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                event.currentTarget.form.requestSubmit();
              }
            }}
            placeholder="Send a message..."
            disabled={isSending}
          />
          <button className="interview-send" type="submit" disabled={isSending || !input.trim()}>
            <Send size={16} /><span className="interview-send-label">Send</span>
          </button>
        </form>
        )}
        {error && <p className="interview-error">{error}</p>}
      </div>
    </div>
  );
}