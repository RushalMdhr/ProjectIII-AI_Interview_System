import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowLeft,
  Flame,
  Wind,
  Zap,
} from "lucide-react";

export const MAX_QUESTIONS_BY_DIFFICULTY = {
  easy: 5,
  medium: 8,
  hard: 10,
};

const DIFFICULTIES = [
  {
    id: "easy",
    label: "Easy",
    questions: MAX_QUESTIONS_BY_DIFFICULTY.easy,
    icon: Wind,
    color: "#45E0D0",
    soft: "rgba(69,224,208,0.14)",
    line: "rgba(69,224,208,0.35)",
    desc: "Warm-up round. Common questions, relaxed pace.",
  },
  {
    id: "medium",
    label: "Medium",
    questions: MAX_QUESTIONS_BY_DIFFICULTY.medium,
    icon: Zap,
    color: "#FFB35B",
    soft: "rgba(255,179,91,0.14)",
    line: "rgba(255,179,91,0.35)",
    desc: "Standard round. Real follow-ups, timed answers.",
  },
  {
    id: "hard",
    label: "Hard",
    questions: MAX_QUESTIONS_BY_DIFFICULTY.hard,
    icon: Flame,
    color: "#F4615B",
    soft: "rgba(244,97,91,0.14)",
    line: "rgba(244,97,91,0.35)",
    desc: "Advanced round. Rapid-fire, curveball follow-ups.",
  },
];

function DifficultyCircle({
  difficulty,
  hovered,
  onHover,
  onLeave,
  onClick,
  disabled,
}) {
  const Icon = difficulty.icon;
  const isHovered = hovered === difficulty.id;

  return (
    <button
      type="button"
      onClick={onClick}
      onMouseEnter={onHover}
      onMouseLeave={onLeave}
      disabled={disabled}
      className="difficulty-button"
      style={{
        transform: isHovered
          ? "translateY(-6px) scale(1.03)"
          : "translateY(0) scale(1)",
      }}
    >
      <div
        className="difficulty-outer"
        style={{
          background: `radial-gradient(circle at 35% 30%, ${difficulty.color}55, ${difficulty.color}1a 60%, transparent 75%)`,
          borderColor: difficulty.line,
          boxShadow: isHovered
            ? `0 0 44px ${difficulty.color}55`
            : `0 0 22px ${difficulty.color}22`,
        }}
      >
        <div
          className="difficulty-inner"
          style={{
            background: `linear-gradient(150deg, ${difficulty.color}dd, ${difficulty.color}88)`,
          }}
        >
          <Icon size={22} color="#0E1024" strokeWidth={2.2} />

          <span className="difficulty-name">
            {difficulty.label}
          </span>

          <span className="difficulty-count">
            {difficulty.questions} QUESTIONS
          </span>
        </div>
      </div>

      <p className="difficulty-description">
        {difficulty.desc}
      </p>
    </button>
  );
}

export default function InterviewSetup() {
  const navigate = useNavigate();

  const [role, setRole] = useState("");
  const [hovered, setHovered] = useState(null);

  const handleDifficulty = (difficulty) => {
    navigate("/interview", {
      state: {
        role,
        difficulty: difficulty.label,
        difficultyId: difficulty.id,
        questionCount: difficulty.questions,
      },
    });
  };

  return (
    <div className="interview-page">
      <style>{`
        * {
          box-sizing: border-box;
        }

        .interview-page {
          min-height: 100vh;
          width: 100%;
          background:
            radial-gradient(
              circle at 15% 20%,
              rgba(139, 124, 246, 0.25),
              transparent 35%
            ),
            radial-gradient(
              circle at 85% 70%,
              rgba(69, 224, 208, 0.16),
              transparent 35%
            ),
            #2B2F63;
          color: #FBFAFF;
          font-family: Inter, Arial, sans-serif;
          overflow-x: hidden;
        }

        .interview-content {
          width: 100%;
          max-width: 900px;
          margin: 0 auto;
          padding: 34px 24px 50px;
        }

        .difficulty-container {
          max-width: 900px;
          margin: 0 auto;
          text-align: center;
        }

        .difficulty-header {
          margin-bottom: 40px;
        }

        .difficulty-header h1 {
          margin: 0 0 10px;
          font-size: 34px;
          font-weight: 700;
        }

        .difficulty-header p {
          max-width: 480px;
          margin: 0 auto;
          color: #C2C4EC;
          font-size: 14px;
          line-height: 1.6;
        }

        .difficulty-back {
          display: flex;
          align-items: center;
          gap: 6px;
          border: none;
          background: transparent;
          color: #C2C4EC;
          cursor: pointer;
          font-size: 13px;
          margin-bottom: 30px;
        }

        .difficulty-options {
          display: flex;
          justify-content: center;
          gap: 48px;
          flex-wrap: wrap;
        }

        .difficulty-button {
          display: flex;
          flex-direction: column;
          align-items: center;
          padding: 0;
          border: none;
          background: transparent;
          cursor: pointer;
          transition: transform 0.25s ease;
        }

        .difficulty-button:disabled {
          cursor: wait;
          opacity: 0.65;
        }

        .setup-error {
          margin: 28px auto 0;
          color: #F88B85;
          font-size: 13px;
        }

        .difficulty-outer {
          width: 168px;
          height: 168px;
          border-radius: 50%;
          position: relative;
          display: flex;
          align-items: center;
          justify-content: center;
          border: 1.5px solid;
          transition: box-shadow 0.25s ease;
        }

        .difficulty-inner {
          width: 128px;
          height: 128px;
          border-radius: 50%;
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          gap: 4px;
        }

        .difficulty-name {
          font-size: 17px;
          font-weight: 800;
          color: #0E1024;
        }

        .difficulty-count {
          font-size: 9px;
          letter-spacing: 0.04em;
          color: #0E1024;
          opacity: 0.75;
        }

        .difficulty-description {
          max-width: 190px;
          margin: 15px 0 0;
          color: #C2C4EC;
          font-size: 12px;
          line-height: 1.5;
        }

        @media (max-width: 700px) {
          .interview-content {
            padding: 25px 18px 40px;
          }

          .setup-header h1 {
            font-size: 28px;
          }

          .type-grid {
            grid-template-columns: 1fr;
          }

          .difficulty-header h1 {
            font-size: 29px;
          }

          .difficulty-options {
            gap: 35px;
          }
        }
      `}</style>

      <div className="interview-content">
        <div className="difficulty-container">

            <button
              className="difficulty-back"
              onClick={() => navigate("/")}
            >
              <ArrowLeft size={14} />
              Back
            </button>

          <div className="difficulty-header">

              <h1>
                Choose your difficulty
              </h1>

              <p>
                Same interview, different pressure. Pick the
                level that matches how you want to practice.
              </p>

          </div>

          <div className="difficulty-options">

              {DIFFICULTIES.map((difficulty) => (
                <DifficultyCircle
                  key={difficulty.id}
                  difficulty={difficulty}
                  hovered={hovered}
                  onHover={() => setHovered(difficulty.id)}
                  onLeave={() => setHovered(null)}
                  onClick={() => handleDifficulty(difficulty)}
                />
              ))}

          </div>

        </div>

      </div>
    </div>
  );
}