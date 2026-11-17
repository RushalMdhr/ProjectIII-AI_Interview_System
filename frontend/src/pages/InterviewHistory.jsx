import { useEffect, useMemo, useState } from "react";
import { ArrowLeft, ArrowRight, LoaderCircle, Star } from "lucide-react";
import { Link, useNavigate } from "react-router-dom";
import { getInterviewSessions } from "../services/api";
import "./InterviewHistory.css";

const scoreOf = (session) => {
  const score = session.average_overall_score;
  return typeof score === "number" && Number.isFinite(score) ? score : null;
};

const scoreTone = (score) => {
  if (score === null) return "unscored";
  if (score < 5) return "low";
  if (score <= 7) return "middle";
  return "high";
};

const formatDate = (value) => {
  if (!value) return "Date unavailable";
  const date = new Date(value);
  return Number.isNaN(date.getTime())
    ? "Date unavailable"
    : date.toLocaleDateString(undefined, {
        year: "numeric",
        month: "short",
        day: "numeric",
      });
};

export default function InterviewHistory() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError("");
    getInterviewSessions()
      .then((data) => {
        if (active) setSessions(data);
      })
      .catch((requestError) => {
        if (active) {
          setError(
            requestError.response?.data?.error ||
              "Your interview history could not be loaded. Please try again.",
          );
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [reloadKey]);

  const highestScore = useMemo(
    () => sessions.reduce((highest, session) => {
      const score = scoreOf(session);
      return score === null ? highest : Math.max(highest, score);
    }, -Infinity),
    [sessions],
  );
  const scoredSessions = sessions.filter((session) => scoreOf(session) !== null);
  const averageScore = scoredSessions.length
    ? scoredSessions.reduce((total, session) => total + scoreOf(session), 0) /
      scoredSessions.length
    : null;

  return (
    <div className="interview-history-page">
      <main className="interview-history-content">
        <Link className="interview-history-back" to="/profile">
          <ArrowLeft size={16} /> Profile
        </Link>
        <header className="interview-history-header">
          <span className="interview-history-eyebrow">YOUR PRACTICE, IN FOCUS</span>
          <h1>Interview history</h1>
          <p>Track your progress and revisit the feedback from every interview.</p>
        </header>

        {loading ? (
          <div className="interview-history-state" role="status">
            <LoaderCircle className="interview-history-spinner" size={26} />
            <span>Loading your interview history…</span>
          </div>
        ) : error ? (
          <div className="interview-history-state interview-history-error" role="alert">
            <p>{error}</p>
            <button type="button" onClick={() => setReloadKey((key) => key + 1)}>
              Try again
            </button>
          </div>
        ) : sessions.length === 0 ? (
          <div className="interview-history-empty">
            <h2>No interview history yet</h2>
            <p>Your completed and in-progress interviews will appear here.</p>
            <button
              type="button"
              onClick={() => navigate("/interview-setup")}
            >
              Start an interview <ArrowRight size={16} />
            </button>
          </div>
        ) : (
          <>
            <section className="interview-history-overview" aria-label="Interview score summary">
              <article className="interview-history-stat">
                <span className="interview-history-stat-label">INTERVIEWS</span>
                <strong>{sessions.length}</strong>
                <span className="interview-history-stat-note">Practice sessions</span>
              </article>
              <article className="interview-history-stat">
                <span className="interview-history-stat-label">AVERAGE SCORE</span>
                <strong>{averageScore === null ? "—" : averageScore.toFixed(1)}<small>/ 10</small></strong>
                <span className="interview-history-stat-note">
                  Across {scoredSessions.length} scored {scoredSessions.length === 1 ? "interview" : "interviews"}
                </span>
              </article>
              <article className="interview-history-stat interview-history-stat-best">
                <span className="interview-history-stat-label">PERSONAL BEST</span>
                <strong>
                  {highestScore === -Infinity ? "—" : highestScore.toFixed(1)}
                  {highestScore !== -Infinity && <small>/ 10</small>}
                  {highestScore !== -Infinity && <Star size={17} fill="currentColor" aria-hidden="true" />}
                </strong>
                <span className="interview-history-stat-note">Your highest overall score</span>
              </article>
            </section>

            <section className="interview-history-section" aria-label="Interview history">
              <div className="interview-history-section-heading">
                <div>
                  <span className="interview-history-eyebrow">YOUR SESSIONS</span>
                  <h2>All interviews <span>{sessions.length}</span></h2>
                </div>
                <div className="interview-history-legend" aria-label="Score colors">
                  <span><i className="low" /> Below 5</span>
                  <span><i className="middle" /> 5–7</span>
                  <span><i className="high" /> Above 7</span>
                </div>
              </div>
              <div className="interview-history-list">
                {sessions.map((session) => {
                  const score = scoreOf(session);
                  const tone = scoreTone(score);
                  const isHighest = score !== null && score === highestScore;
                  const hasEnded = session.halted || session.archived;
                  const statusLabel = hasEnded
                    ? session.question_count >= session.max_questions
                      ? "Completed"
                      : "Halted"
                    : "In progress";
                  const headline = session.interview_role || session.title || "Interview";
                  return (
                    <button
                      type="button"
                      className={`interview-history-row interview-history-row-${tone}`}
                      key={session.id}
                      onClick={() => navigate(`/results?session=${session.id}`, {
                        state: { fromHistory: true },
                      })}
                    >
                      <span className="interview-history-row-main">
                        <span className="interview-history-row-title">{headline}</span>
                        <span className="interview-history-row-meta">
                          {formatDate(session.updated_at || session.created_at)}
                          <span className="interview-history-meta-divider" aria-hidden="true" />
                          {session.interview_difficulty || "Interview"} round
                          <span
                            className={`interview-history-status ${
                              hasEnded ? "interview-history-ended" : "interview-history-in-progress"
                            }`}
                          >
                            {statusLabel}
                          </span>
                        </span>
                      </span>
                      <span className={`interview-history-score ${tone}`}>
                        <span className="interview-history-score-label">OVERALL</span>
                        <span className="interview-history-score-value">
                          {score === null ? "—" : score.toFixed(1)}
                          <small>/ 10</small>
                        </span>
                      </span>
                      {isHighest && (
                        <span
                          className="interview-history-star"
                          role="img"
                          aria-label="Highest score"
                          title="Highest score"
                        >
                          <Star size={19} fill="currentColor" aria-hidden="true" />
                        </span>
                      )}
                      <ArrowRight className="interview-history-arrow" size={19} aria-hidden="true" />
                    </button>
                  );
                })}
              </div>
            </section>
          </>
        )}
      </main>
    </div>
  );
}
