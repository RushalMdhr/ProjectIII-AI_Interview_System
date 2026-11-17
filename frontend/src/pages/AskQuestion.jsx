import React, { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Bot,
  ChevronLeft,
  ChevronRight,
  LoaderCircle,
  Menu,
  MessageSquarePlus,
  Send,
  Trash2,
} from "lucide-react";
import {
  deleteChatSession,
  getChatMessages,
  getChatSessions,
  sendChatMessage,
} from "../services/api";
import ReactMarkdown from "react-markdown";

export default function AskQuestion() {
  const navigate = useNavigate();
  const [input, setInput] = useState("");
  const inputRef = useRef(null);
  const wasSendingRef = useRef(false);
  const [messages, setMessages] = useState([]);
  const [sessionId, setSessionId] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isLoadingSessions, setIsLoadingSessions] = useState(true);
  const [isLoadingMessages, setIsLoadingMessages] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState("");
  const [contextMenu, setContextMenu] = useState(null);
  const [deletingSessionId, setDeletingSessionId] = useState(null);
  const messagesEndRef = useRef(null);

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

  useEffect(() => {
    const loadSessions = async () => {
      try {
        const sessionList = await getChatSessions();
        setSessions(Array.isArray(sessionList) ? sessionList : []);
      } catch (requestError) {
        setError(
          requestError.response?.data?.detail ||
            "Could not load chat sessions.",
        );
      } finally {
        setIsLoadingSessions(false);
      }
    };

    loadSessions();
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isSending]);

  useEffect(() => {
    const closeContextMenu = () => setContextMenu(null);

    document.addEventListener("click", closeContextMenu);
    document.addEventListener("scroll", closeContextMenu, true);

    return () => {
      document.removeEventListener("click", closeContextMenu);
      document.removeEventListener("scroll", closeContextMenu, true);
    };
  }, []);

  const handleSelectSession = async (session) => {
    if (session.id === sessionId || isLoadingMessages || isSending) return;

    setSessionId(session.id);
    setMessages([]);
    setError("");
    setIsLoadingMessages(true);

    try {
      const history = await getChatMessages(session.id);
      const formattedMessages = history
        .flatMap((message) => [
          message.user_content && {
            id: `user-${message.id}`,
            role: "user",
            content: message.user_content,
          },
          message.assistant_content && {
            id: `assistant-${message.id}`,
            role: "assistant",
            content: message.assistant_content,
          },
        ])
        .filter(Boolean);

      setMessages(formattedMessages);
    } catch (requestError) {
      setError(
        requestError.response?.data?.error ||
          "Could not load this conversation.",
      );
    } finally {
      setIsLoadingMessages(false);
    }
  };

  const handleNewChat = () => {
    if (isSending) return;

    setContextMenu(null);
    setSessionId(null);
    setMessages([]);
    setInput("");
    setError("");
  };

  const handleDeleteSession = async (session) => {
    setContextMenu(null);

    if (
      isSending ||
      deletingSessionId ||
      !window.confirm(`Delete "${session.title || "New Chat Session"}"?`)
    ) {
      return;
    }

    setDeletingSessionId(session.id);
    setError("");

    try {
      await deleteChatSession(session.id);
      setSessions((current) =>
        current.filter((currentSession) => currentSession.id !== session.id),
      );

      if (session.id === sessionId) {
        setSessionId(null);
        setMessages([]);
        setInput("");
      }
    } catch (requestError) {
      setError(
        requestError.response?.data?.error ||
          "Could not delete this conversation.",
      );
    } finally {
      setDeletingSessionId(null);
    }
  };

  const handleSend = async () => {
    const question = input.trim();

    if (!question || isSending) return;

    setMessages((current) => [
      ...current,
      {
        id: `user-${Date.now()}`,
        role: "user",
        content: question,
      },
    ]);

    setInput("");
    setError("");
    setIsSending(true);

    try {
      // sessionId can be null for a new chat
      const response = await sendChatMessage(question, sessionId);

      // Get the session returned by Django
      if (response.session) {
        setSessionId(response.session.id);

        setSessions((current) => {
          const exists = current.some(
            (session) => session.id === response.session.id,
          );

          if (exists) {
            return current.map((session) =>
              session.id === response.session.id ? response.session : session,
            );
          }

          return [response.session, ...current];
        });
      }

      const message = response.message;

      if (message?.assistant_content) {
        setMessages((current) => [
          ...current,
          {
            id: message.id || `assistant-${Date.now()}`,
            role: "assistant",
            content: message.assistant_content,
          },
        ]);
      } else {
        setError(
          response.error || "The backend did not return an assistant reply.",
        );
      }
    } catch (requestError) {
      const message = requestError.response?.data?.error;

      setError(
        message ||
          "The assistant could not answer right now. Please try again.",
      );
    } finally {
      setIsSending(false);
    }
  };

  return (
    <div
      className={`ask-page ${isSidebarOpen ? "sidebar-open" : "sidebar-closed"}`}
    >
      <aside className="chat-sidebar" aria-label="Chat sessions">
        <div className="chat-sidebar-header">
          {isSidebarOpen && <span>Chats</span>}
          <button
            className="chat-sidebar-toggle"
            onClick={() => setIsSidebarOpen((current) => !current)}
            aria-label={
              isSidebarOpen ? "Collapse chat sessions" : "Expand chat sessions"
            }
            title={
              isSidebarOpen ? "Collapse chat sessions" : "Expand chat sessions"
            }
          >
            {isSidebarOpen ? (
              <ChevronLeft size={17} />
            ) : (
              <ChevronRight size={17} />
            )}
          </button>
        </div>

        <button
          className="chat-new-button"
          onClick={handleNewChat}
          disabled={isSending}
          title="Start a new chat"
        >
          <MessageSquarePlus size={17} />
          {isSidebarOpen && <span>New chat</span>}
        </button>

        {isSidebarOpen && (
          <div className="chat-session-list">
            {isLoadingSessions && (
              <div className="chat-sidebar-status">Loading chats...</div>
            )}
            {!isLoadingSessions && !sessions.length && (
              <div className="chat-sidebar-status">No chats yet</div>
            )}
            {sessions.map((session) => (
              <div className="chat-session-wrapper" key={session.id}>
                <button
                  className={`chat-session-item ${
                    session.id === sessionId ? "selected" : ""
                  }`}
                  onClick={() => handleSelectSession(session)}
                  onContextMenu={(event) => {
                    event.preventDefault();
                    event.stopPropagation();

                    const rect = event.currentTarget.getBoundingClientRect();

                    const menuWidth = 140;
                    const menuHeight = 42;
                    const gap = 6;

                    setContextMenu({
                      session,
                      top: Math.max(
                        gap,
                        Math.min(
                          rect.top,
                          window.innerHeight - menuHeight - gap,
                        ),
                      ),
                      left: Math.min(
                        rect.right + gap,
                        window.innerWidth - menuWidth - gap
                      ),
                    });
                  }}
                  disabled={
                    isLoadingMessages ||
                    isSending ||
                    deletingSessionId === session.id
                  }
                >
                  <Menu size={14} />
                  <span>{session.title || "New Chat Session"}</span>
                </button>

                {contextMenu?.session.id === session.id && (
                  createPortal(
                    <div
                      className="
                        fixed z-[9999]
                        w-[140px] p-1
                        rounded-lg
                        border border-slate-700
                        bg-slate-800
                        shadow-xl shadow-black/30
                        animate-in fade-in slide-in-from-left-1
                        duration-150
                      "
                      style={{
                        position: "fixed",
                        zIndex: 9999,
                        top: contextMenu.top,
                        left: contextMenu.left,
                      }}
                      role="menu"
                      onClick={(event) => event.stopPropagation()}
                    >
                      <button
                        type="button"
                        role="menuitem"
                        onClick={() => handleDeleteSession(session)}
                        disabled={isSending || Boolean(deletingSessionId)}
                        className="
                          flex w-full items-center gap-2
                          rounded-md px-2.5 py-2
                          text-sm text-red-400
                          transition-colors
                          hover:bg-red-400/10 hover:text-red-300
                          disabled:cursor-not-allowed disabled:opacity-50
                        "
                      >
                        <Trash2 size={14} />
                        Delete
                      </button>
                    </div>,
                    document.body,
                  )
                )}
              </div>
            ))}
          </div>
        )}
      </aside>

      {/* =========================
          TOP BAR
      ========================= */}

      <div className="ask-topbar">
        <button className="ask-back" onClick={() => navigate("/")}>
          <ArrowLeft size={16} />
          Back to Home
        </button>
      </div>

      {/* =========================
          MAIN AREA
      ========================= */}

      <main className="ask-main">
        {!messages.length && !sessionId && !isLoadingMessages && (
          <div className="ask-welcome">
            <div className="ask-welcome-icon">
              <Bot size={25} />
            </div>
            <p className="ask-eyebrow">Career companion</p>
            <h1>Talk through your next move.</h1>
            <p>
              Practical guidance for resumes, interviews, and the search ahead.
            </p>
          </div>
        )}

        <section
          className={`ask-messages ${messages.length ? "has-messages" : ""}`}
          aria-live="polite"
        >
          {!messages.length && !isLoadingMessages && (
            <div className="ask-empty">
              <Bot size={18} />
              <span>
                {sessionId
                  ? "This conversation has no messages yet."
                  : "Start a new conversation."}
              </span>
            </div>
          )}

          {isLoadingMessages && (
            <div className="ask-empty">
              <LoaderCircle className="ask-loading-icon" size={18} />
              <span>Loading conversation...</span>
            </div>
          )}

          {messages.map((message) => (
            <div className={`ask-message-row ${message.role}`} key={message.id}>
              {message.role === "assistant" && (
                <div className="ask-avatar">
                  <Bot size={16} />
                </div>
              )}
              <div className="ask-bubble">
                <ReactMarkdown>{message.content}</ReactMarkdown>
              </div>
            </div>
          ))}

          {isSending && (
            <div className="ask-message-row assistant">
              <div className="ask-avatar">
                <Bot size={16} />
              </div>
              <div className="ask-bubble ask-typing">
                <LoaderCircle size={15} /> Thinking...
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </section>

        {error && (
          <div className="ask-error" role="alert">
            {error}
          </div>
        )}

        <div className="ask-input-area">
          <div className="ask-input-box">
            <textarea
              ref={inputRef}
              rows={1}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              placeholder="Ask about your next career move..."
              disabled={isSending}
            />

            <button
              className={`ask-send ${input.trim() ? "active" : ""}`}
              onClick={handleSend}
              disabled={!input.trim() || isSending}
              aria-label="Send question"
            >
              <Send size={17} />
            </button>
          </div>

          <div className="ask-disclaimer">
            {/* <Sparkles size={11} /> */}
            <span>
              AI Helper can make mistakes. Verify important information.
            </span>
          </div>
        </div>
      </main>
    </div>
  );
}
// h