import { useEffect, useMemo, useRef, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import {
  ArrowDown,
  ArrowLeft,
  ArrowUp,
  Check,
  ChevronDown,
  LoaderCircle,
  Sparkles,
  Target,
} from "lucide-react";
import { getInterviewResults } from "../services/api";
import "./Results.css";

const CATEGORIES = [
  { key: "introduction", label: "Introduction", color: "#45E0D0" },
  { key: "experience", label: "Experience", color: "#8B7CF6" },
  { key: "behavioral", label: "Behavioral", color: "#FFB35B" },
  { key: "situational", label: "Situational", color: "#F4615B" },
  { key: "technical", label: "Technical", color: "#6EA8FE" },
];

const scoreValue = (value) =>
  typeof value === "number" && Number.isFinite(value)
    ? Math.max(0, Math.min(10, value))
    : null;

const formatScore = (value) =>
  scoreValue(value) === null ? "—" : scoreValue(value).toFixed(1);

function RadarChart({ session }) {
  const centerX = 250;
  const centerY = 205;
  const radius = 130;
  const pointsAt = (scale) =>
    CATEGORIES.map((category, index) => {
      const angle = (-Math.PI / 2) + (index * 2 * Math.PI) / CATEGORIES.length;
      return [
        centerX + Math.cos(angle) * radius * scale,
        centerY + Math.sin(angle) * radius * scale,
      ];
    });
  const scorePoints = CATEGORIES.map((category, index) => {
    const angle = (-Math.PI / 2) + (index * 2 * Math.PI) / CATEGORIES.length;
    const score = scoreValue(session[`average_${category.key}_score`]) || 0;
    return [
      centerX + Math.cos(angle) * radius * (score / 10),
      centerY + Math.sin(angle) * radius * (score / 10),
    ];
  });
  const polygonPoints = (points) => points.map((point) => point.join(",")).join(" ");

  return (
    <div className="results-radar-wrap">
      <svg
        className="results-radar"
        viewBox="0 0 500 410"
        role="img"
        aria-label="Radar chart showing average performance across five interview categories"
      >
        {[0.25, 0.5, 0.75, 1].map((scale) => (
          <polygon
            key={scale}
            points={polygonPoints(pointsAt(scale))}
            className="results-radar-grid"
          />
        ))}
        {CATEGORIES.map((category, index) => {
          const angle = (-Math.PI / 2) + (index * 2 * Math.PI) / CATEGORIES.length;
          const endX = centerX + Math.cos(angle) * radius;
          const endY = centerY + Math.sin(angle) * radius;
          const labelX = centerX + Math.cos(angle) * 178;
          const labelY = centerY + Math.sin(angle) * 178;
          const score = session[`average_${category.key}_score`];
          return (
            <g key={category.key}>
              <line
                x1={centerX}
                y1={centerY}
                x2={endX}
                y2={endY}
                className="results-radar-axis"
              />
              <text
                x={labelX}
                y={labelY}
                className="results-radar-label"
                textAnchor="middle"
                dominantBaseline="middle"
              >
                {category.label}
              </text>
              <text
                x={labelX}
                y={labelY + 17}
                className="results-radar-score"
                textAnchor="middle"
                dominantBaseline="middle"
              >
                {formatScore(score)}/10
              </text>
            </g>
          );
        })}
        <polygon
          points={polygonPoints(scorePoints)}
          className="results-radar-value"
        />
        {scorePoints.map(([x, y], index) => (
          <circle
            key={CATEGORIES[index].key}
            cx={x}
            cy={y}
            r="4.5"
            fill={CATEGORIES[index].color}
            className="results-radar-dot"
          />
        ))}
      </svg>
      <p className="results-chart-note">
        {CATEGORIES.some((item) => scoreValue(session[`average_${item.key}_score`]) !== null)
          ? "A wider shape means stronger performance across more areas."
          : "Category scores will appear here when rated answers are available."}
      </p>
    </div>
  );
}

function ScoreBar({ label, score, color }) {
  const numericScore = scoreValue(score);
  return (
    <div className="results-score-row">
      <div className="results-score-row-heading">
        <span>{label}</span>
        <span>{numericScore === null ? "Not scored" : `${numericScore.toFixed(1)} / 10`}</span>
      </div>
      <div
        className="results-score-track"
        role="progressbar"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={10}
        aria-valuenow={numericScore ?? 0}
      >
        <span
          className="results-score-fill"
          style={{
            width: `${numericScore === null ? 0 : numericScore * 10}%`,
            background: color,
          }}
        />
      </div>
    </div>
  );
}

function ScoreComparison({ current, previous, baselineCaptured }) {
  const currentScore = scoreValue(current);
  const previousScore = scoreValue(previous);
  const firstScore = currentScore !== null && previousScore === null && baselineCaptured;
  const isNewBest = currentScore !== null && previousScore !== null && currentScore > previousScore;
  const isLower = currentScore !== null && previousScore !== null && currentScore < previousScore;
  const difference = currentScore === null || previousScore === null
    ? null
    : Math.abs(currentScore - previousScore);

  let tone = "matched";
  let Icon = Check;
  let message = currentScore === null
    ? "No scored answers yet"
    : baselineCaptured ? "Matches your best" : "Previous best unavailable";
  if (firstScore || isNewBest) {
    tone = "new-best";
    Icon = ArrowUp;
    message = firstScore ? "Your first recorded score" : `New best · +${difference.toFixed(1)}`;
  } else if (isLower) {
    tone = "below-best";
    Icon = ArrowDown;
    message = `Down by ${difference.toFixed(1)} from your best`;
  }

  return (
    <section className={`results-kpi-card ${tone}`}>
      {(firstScore || isNewBest) && (
        <div className="results-celebration" aria-hidden="true">
          <div className="results-balloons"><i /><i /><i /></div>
          {Array.from({ length: 28 }, (_, index) => (
            <i
              key={index}
              className="results-confetti"
              style={{
                "--x": `${(index * 37) % 100}%`,
                "--delay": `${(index % 8) * -0.37}s`,
                "--color": ["#45e0d0", "#ffb35b", "#8b7cf6", "#f4615b", "#6ea8fe"][index % 5],
              }}
            />
          ))}
        </div>
      )}
      <div className="results-kpi-top">
        <span className="results-kpi-label">Overall interview score</span>
        <span className="results-kpi-icon"><Icon size={18} /></span>
      </div>
      <div className="results-kpi-score">
        {currentScore === null ? "—" : currentScore.toFixed(1)}
        <span>/ 10</span>
      </div>
      <div className="results-kpi-comparison">
        <strong>{message}</strong>
        {previousScore !== null && (
          <span>Previous best: {previousScore.toFixed(1)} / 10</span>
        )}
      </div>
    </section>
  );
}

function QuestionReview({ questions }) {
  if (!questions.length) {
    return <p className="results-empty-review">No answered questions were found for this session.</p>;
  }

  return (
    <div className="results-question-list">
      {questions.map((question, index) => {
        const dimensions = question.rating?.dimension_scores;
        const hasDimensions = dimensions && typeof dimensions === "object" &&
          Object.keys(dimensions).length > 0;
        return (
          <article className="results-question-card" key={question.id}>
            <div className="results-question-top">
              <span className="results-question-number">QUESTION {index + 1}</span>
              <span className="results-category-pill">{question.category || "Interview"}</span>
            </div>
            <h3>{question.question_text || "Interview question"}</h3>
            <div className="results-answer-block">
              <span>Your answer</span>
              <p>{question.candidate_answer || "No answer recorded."}</p>
            </div>
            {question.expected_answer && (
              <details className="results-expected">
                <summary>View reference answer</summary>
                <p>{question.expected_answer}</p>
              </details>
            )}
            <div className="results-bars">
              <ScoreBar
                label="Overall answer score"
                score={question.rating?.overall_score}
                color="#45E0D0"
              />
              {hasDimensions && Object.entries(dimensions).map(([name, value], dimensionIndex) => (
                <ScoreBar
                  key={name}
                  label={name.replaceAll("_", " ")}
                  score={value?.score}
                  color={CATEGORIES[dimensionIndex % CATEGORIES.length].color}
                />
              ))}
            </div>
            {question.feedback && (
              <div className="results-feedback">
                <Sparkles size={16} />
                <p>{typeof question.feedback === "string"
                  ? question.feedback
                  : question.feedback.feedback_text || "Feedback available."}</p>
              </div>
            )}
          </article>
        );
      })}
    </div>
  );
}

export default function Results() {
  const [searchParams] = useSearchParams();
  const sessionId = searchParams.get("session");
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [showReview, setShowReview] = useState(false);
  const [reviewLoading, setReviewLoading] = useState(false);
  const [reviewError, setReviewError] = useState("");
  const [reviewQuestions, setReviewQuestions] = useState(null);
  const reviewRef = useRef(null);
  const overviewRef = useRef(null);

  useEffect(() => {
    if (!sessionId) {
      setLoading(false);
      setError("Choose an interview session to view its results.");
      return;
    }
    let active = true;
    setLoading(true);
    setError("");
    getInterviewResults(sessionId)
      .then((data) => {
        if (active) setResults(data);
      })
      .catch((requestError) => {
        if (active) {
          setError(
            requestError.response?.data?.error ||
              "Your interview results could not be loaded. Please try again.",
          );
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [sessionId]);

  useEffect(() => {
    if (results) {
      overviewRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }
  }, [results]);

  const previousOverall = results?.previous_high_scores?.highest_score;
  const baselineCaptured = Object.hasOwn(
    results?.previous_high_scores || {},
    "highest_score",
  );
  const session = results?.session;
  const focusCategory = useMemo(() => {
    if (!session) return null;
    return CATEGORIES
      .map((category) => ({
        ...category,
        score: scoreValue(session[`average_${category.key}_score`]),
      }))
      .filter((category) => category.score !== null)
      .sort((left, right) => left.score - right.score)[0] || null;
  }, [session]);

  const handleReview = async () => {
    if (showReview) {
      setShowReview(false);
      return;
    }
    if (!reviewQuestions) {
      setShowReview(true);
      setReviewLoading(true);
      setReviewError("");
      try {
        const review = await getInterviewResults(sessionId, true);
        setReviewQuestions(review.questions || []);
      } catch (requestError) {
        setReviewError(
          requestError.response?.data?.error ||
            "The question review could not be loaded. Please try again.",
        );
        setReviewLoading(false);
        window.setTimeout(() => {
          reviewRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
        }, 80);
        return;
      }
      setReviewLoading(false);
    }
    setShowReview(true);
    window.setTimeout(() => {
      reviewRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 80);
  };

  if (loading) {
    return (
      <div className="results-page results-state">
        <LoaderCircle className="results-spinner" size={28} />
        <p>Putting your results together…</p>
      </div>
    );
  }

  if (error || !session) {
    return (
      <div className="results-page results-state">
        <p className="results-error">{error || "No results are available."}</p>
        <Link className="results-secondary-button" to="/interview-setup">
          <ArrowLeft size={16} /> Back to interview setup
        </Link>
      </div>
    );
  }

  return (
    <div className="results-page">
      <main className="results-content">
        <Link className="results-back" to="/interview-setup">
          <ArrowLeft size={16} /> Start another interview
        </Link>
        <header className="results-header">
          <span className="results-eyebrow">INTERVIEW COMPLETE</span>
          <h1>Your performance, at a glance.</h1>
          <p>
            {session.interview_role || "Interview assessment"} ·{" "}
            {session.question_count} questions · {session.interview_difficulty} round
          </p>
        </header>

        <div className="results-overview" ref={overviewRef}>
          <section className="results-panel results-radar-panel">
            <div className="results-panel-heading">
              <div>
                <span className="results-eyebrow">FIVE DIMENSIONS</span>
                <h2>Performance breakdown</h2>
              </div>
              <Target size={20} aria-hidden="true" />
            </div>
            <RadarChart session={session} />
          </section>

          <div className="results-side-column">
            <ScoreComparison
              current={session.average_overall_score}
              previous={previousOverall}
              baselineCaptured={baselineCaptured}
            />
            <section className="results-focus-card">
              <span className="results-focus-icon"><Target size={18} /></span>
              <div>
                <span className="results-eyebrow">NEXT FOCUS</span>
                {focusCategory ? (
                  <>
                    <h2>{focusCategory.label}</h2>
                    <p>
                      Your lowest rated area at {focusCategory.score.toFixed(1)}/10.
                      A little practice here can round out your profile.
                    </p>
                  </>
                ) : (
                  <>
                    <h2>Keep practicing</h2>
                    <p>Category guidance will appear as soon as rated answers are available.</p>
                  </>
                )}
              </div>
            </section>
            <button
              type="button"
              className="results-review-button"
              onClick={handleReview}
              disabled={reviewLoading}
              aria-expanded={showReview}
              aria-controls="question-review"
            >
              {reviewLoading
                ? "Loading your answers…"
                : showReview ? "Hide question review" : "Dive into your answers"}
              {reviewLoading
                ? <LoaderCircle size={18} className="results-spinner" />
                : <ChevronDown size={18} className={showReview ? "is-rotated" : ""} />}
            </button>
          </div>
        </div>

        {showReview && (
          <section className="results-review-section" id="question-review" ref={reviewRef}>
            <div className="results-review-heading">
              <span className="results-eyebrow">ANSWER BY ANSWER</span>
              <h2>Interview review</h2>
              <p>See your answer, score, and feedback for every question.</p>
            </div>
            {reviewError
              ? <p className="results-error">{reviewError}</p>
              : <QuestionReview questions={reviewQuestions || []} />}
          </section>
        )}
      </main>
    </div>
  );
}
