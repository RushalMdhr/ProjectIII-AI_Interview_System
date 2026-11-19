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

const SCORE_CHART = {
  width: 800,
  height: 270,
  left: 52,
  right: 756,
  top: 18,
  bottom: 220,
};

function ScoreTrendChart({ sessions, range, onRangeChange }) {
  const chartSessions = useMemo(() => {
    const now = Date.now();
    const lastWeek = now - 7 * 24 * 60 * 60 * 1000;

    return sessions
      .map((session, index) => {
        const dateValue = session.updated_at || session.created_at;
        const date = dateValue ? new Date(dateValue) : null;
        const score = scoreOf(session);
        return {
          session,
          index,
          date,
          score,
        };
      })
      .filter(({ date, score }) =>
        date &&
        !Number.isNaN(date.getTime()) &&
        score !== null &&
        (range === "all" || (date.getTime() >= lastWeek && date.getTime() <= now)),
      )
      .sort((left, right) =>
        left.date.getTime() - right.date.getTime() || left.index - right.index,
      );
  }, [sessions, range]);

  const plotWidth = SCORE_CHART.right - SCORE_CHART.left;
  const plotHeight = SCORE_CHART.bottom - SCORE_CHART.top;
  const points = chartSessions.map((item, index) => ({
    ...item,
    x: chartSessions.length === 1
      ? SCORE_CHART.left + plotWidth / 2
      : SCORE_CHART.left + (index / (chartSessions.length - 1)) * plotWidth,
    y: SCORE_CHART.top + ((10 - item.score) / 10) * plotHeight,
  }));
  const pointLabels = new Set(
    Array.from(
      { length: Math.min(5, points.length) },
      (_, index) => points.length === 1
        ? 0
        : Math.round((index * (points.length - 1)) / (Math.min(5, points.length) - 1)),
    ),
  );
  const linePoints = points.map(({ x, y }) => `${x},${y}`).join(" ");

  return (
    <section className="interview-history-chart" aria-labelledby="interview-score-chart-title">
      <div className="interview-history-chart-heading">
        <div>
          <span className="interview-history-eyebrow">YOUR PROGRESS</span>
          <h2 id="interview-score-chart-title">Interview scores</h2>
          <p>Overall score for each scored interview, out of 10.</p>
        </div>
        <div className="interview-history-chart-range" role="group" aria-label="Score chart range">
          <button
            type="button"
            aria-pressed={range === "week"}
            onClick={() => onRangeChange("week")}
          >
            Last 7 days
          </button>
          <button
            type="button"
            aria-pressed={range === "all"}
            onClick={() => onRangeChange("all")}
          >
            All time
          </button>
        </div>
      </div>

      {points.length ? (
        <div className="interview-history-chart-plot">
          <svg
            viewBox={`0 0 ${SCORE_CHART.width} ${SCORE_CHART.height}`}
            role="img"
            aria-labelledby="interview-score-chart-title interview-score-chart-description"
          >
            <desc id="interview-score-chart-description">
              {points.length} scored {points.length === 1 ? "interview" : "interviews"} shown from oldest to newest.
            </desc>
            {[0, 2, 4, 6, 8, 10].map((score) => {
              const y = SCORE_CHART.top + ((10 - score) / 10) * plotHeight;
              return (
                <g key={score}>
                  <line
                    className="interview-history-chart-grid"
                    x1={SCORE_CHART.left}
                    x2={SCORE_CHART.right}
                    y1={y}
                    y2={y}
                  />
                  <text
                    className="interview-history-chart-y-label"
                    x={SCORE_CHART.left - 13}
                    y={y + 4}
                    textAnchor="end"
                  >
                    {score}
                  </text>
                </g>
              );
            })}
            {points.length > 1 && (
              <polyline
                className="interview-history-chart-line"
                points={linePoints}
              />
            )}
            {points.map(({ session, date, score, x, y }, index) => (
              <g key={session.id}>
                <circle
                  className="interview-history-chart-point"
                  cx={x}
                  cy={y}
                  r="5"
                >
                  <title>
                    {`${session.interview_role || session.title || "Interview"} · ${score.toFixed(1)}/10 · ${date.toLocaleString()}`}
                  </title>
                </circle>
                {pointLabels.has(index) && (
                  <text
                    className="interview-history-chart-x-label"
                    x={x}
                    y={SCORE_CHART.bottom + 27}
                    textAnchor="middle"
                  >
                    {date.toLocaleDateString(undefined, {
                      month: "short",
                      day: "numeric",
                      ...(range === "all" ? { year: "2-digit" } : {}),
                    })}
                  </text>
                )}
              </g>
            ))}
          </svg>
        </div>
      ) : (
        <p className="interview-history-chart-empty">
          {range === "week"
            ? "No scored interviews in the last 7 days. Switch to all time to see your full progress."
            : "Your score trend will appear here after an interview has been scored."}
        </p>
      )}
    </section>
  );
}

export default function InterviewHistory() {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reloadKey, setReloadKey] = useState(0);
  const [scoreRange, setScoreRange] = useState("all");

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
            <ScoreTrendChart
              sessions={sessions}
              range={scoreRange}
              onRangeChange={setScoreRange}
            />

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
                    ? score !== null
                      ? "Completed"
                      : "Incomplete"
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
