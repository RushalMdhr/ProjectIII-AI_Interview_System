import React, { useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  MessageCircleQuestion,
  Mic,
  ArrowRight,
  Sparkles,
  Zap,
  FileText,
  BarChart3,
  ArrowLeft,
  ArrowDown,
  Target,
  TrendingUp,
} from "lucide-react";

import HomeBackground from "../components/HomeBackground";

const tokens = {
  bg: "#2B2F63",
  bgLo: "#232752",

  glass: "rgba(255,255,255,0.06)",
  glassHi: "rgba(255,255,255,0.10)",
  border: "rgba(255,255,255,0.14)",

  violet: "#8B7CF6",
  gold: "#FFB35B",
  goldSoft: "#FFB35B2b",
  goldLine: "#FFB35B70",

  teal: "#45E0D0",
  tealSoft: "#45E0D02b",
  tealLine: "#45E0D070",

  text: "#FBFAFF",
  textMuted: "#C2C4EC",
};

/* =========================================
   GLOBAL STYLE
========================================= */

function GlobalStyle() {
  return (
    <style>{`

      .cp-root * {
        box-sizing: border-box;
      }

      .cp-root {
        font-family: Inter, Arial, sans-serif;
      }

      .cp-display {
        font-family: "Space Grotesk", Inter, sans-serif;
      }

      .cp-mono {
        font-family: "JetBrains Mono", monospace;
      }

      .cp-navlink {
        color: ${tokens.textMuted};
        text-decoration: none;
        font-size: 13.5px;
        transition: color 0.2s ease;
      }

      .cp-navlink:hover {
        color: ${tokens.text};
      }

      .cp-card-wrap {
        transition: transform 0.3s cubic-bezier(.22,1,.36,1);
      }

      .cp-card-wrap:hover {
        transform: translateY(-8px);
      }

      .cp-card-wrap:hover .cp-card {
        background: var(--hover-bg) !important;

        box-shadow:
          0 30px 60px -20px var(--hover-glow),
          inset 0 1px 0 rgba(255,255,255,0.16);
      }

      .cp-card-wrap:hover .cp-arrow {
        transform: translateX(6px);
      }

      .cp-card-wrap:hover .cp-cta {
        color: var(--hover-color);
      }

      .cp-card-wrap:hover .cp-ring-fg {
        stroke-dashoffset: var(--ring-hover) !important;
      }

      .cp-arrow {
        transition: transform 0.25s ease;
      }

      @keyframes cp-pulse {
        0%,100% {
          opacity: 0.4;
        }

        50% {
          opacity: 1;
        }
      }

      @keyframes cp-drift1 {
        0%,100% {
          transform: translate(0,0) scale(1);
        }

        50% {
          transform: translate(40px,-30px) scale(1.12);
        }
      }

      @keyframes cp-drift2 {
        0%,100% {
          transform: translate(0,0) scale(1);
        }

        50% {
          transform: translate(-35px,30px) scale(1.08);
        }
      }

      @keyframes cp-drift3 {
        0%,100% {
          transform: translate(0,0) scale(1);
        }

        50% {
          transform: translate(20px,25px) scale(1.06);
        }
      }

      @keyframes cp-spin-cw {
        to {
          transform: rotate(360deg);
        }
      }

      @keyframes cp-spin-ccw {
        to {
          transform: rotate(-360deg);
        }
      }

      @keyframes cp-core-pulse {

        0%,100% {
          box-shadow:
            0 0 0 0 ${tokens.goldSoft},
            0 0 60px 10px rgba(255,179,91,0.25);
        }

        50% {
          box-shadow:
            0 0 0 14px rgba(255,179,91,0),
            0 0 80px 18px rgba(255,179,91,0.4);
        }
      }

      @keyframes cp-bob {

        0%,100% {
          transform: translateY(0);
        }

        50% {
          transform: translateY(-6px);
        }
      }

      @keyframes cp-bounce-y {

        0%,100% {
          transform: translateY(0);
        }

        50% {
          transform: translateY(4px);
        }
      }

      @keyframes cp-fade-scale-out {

        from {
          opacity: 1;
          transform: scale(1);
        }

        to {
          opacity: 0;
          transform: scale(0.85);
        }
      }

      @keyframes cp-reveal-up {

        from {
          opacity: 0;
          transform: translateY(26px);
        }

        to {
          opacity: 1;
          transform: translateY(0);
        }
      }

      .cp-dot {
        animation: cp-pulse 2.6s ease-in-out infinite;
      }

      .cp-orbit-cw {
        animation: cp-spin-cw 18s linear infinite;
      }

      .cp-orbit-ccw {
        animation: cp-spin-ccw 24s linear infinite;
      }

      .cp-core {
        animation:
          cp-core-pulse 2.8s ease-in-out infinite,
          cp-bob 4.5s ease-in-out infinite;
      }

      .cp-bounce {
        animation: cp-bounce-y 1.6s ease-in-out infinite;
      }

      .cp-circle-leaving {
        animation: cp-fade-scale-out 0.35s ease forwards;
      }

      .cp-cards-enter {
        animation: cp-reveal-up 0.55s cubic-bezier(.22,1,.36,1) both;
      }

      .cp-back-link {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        background: none;
        border: none;
        cursor: pointer;
        color: ${tokens.textMuted};
        font-size: 13px;
        font-family: Inter, Arial, sans-serif;
        padding: 8px 0;
      }

      .cp-back-link:hover {
        color: ${tokens.text};
      }

      @media (max-width: 760px) {

        .cp-nav {
          padding: 18px 20px !important;
        }

        .cp-navlinks {
          display: none !important;
        }

        .cp-hero {
          padding: 56px 24px 10px !important;
        }

        .cp-hero-title {
          font-size: 34px !important;
        }

        .cp-cards {
          flex-direction: column;
        }

        .cp-divider {
          display: none !important;
        }

        .cp-steps {
          flex-direction: column;
        }

        .cp-content {
          padding-left: 24px !important;
          padding-right: 24px !important;
        }

        .cp-stats {
          padding-left: 24px !important;
          padding-right: 24px !important;
        }

        .cp-footer {
          padding-left: 24px !important;
          padding-right: 24px !important;
        }
      }

    `}</style>
  );
}

/* =========================================
   LOGO
========================================= */

function Logo() {
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
      }}
    >
      <div
        style={{
          width: 32,
          height: 32,
          borderRadius: 10,
          background: `linear-gradient(135deg, ${tokens.violet}, ${tokens.teal})`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          boxShadow: `0 8px 24px rgba(69,224,208,0.18)`,
        }}
      >
        <Sparkles size={17} color={tokens.text} />
      </div>

      <span
        className="cp-display"
        style={{
          fontSize: 17,
          fontWeight: 700,
          color: tokens.text,
          letterSpacing: "-0.02em",
        }}
      >
        AI HELPER
      </span>
    </div>
  );
}

/* =========================================
   CONSTELLATION
========================================= */

function Constellation() {
  const dots = [
    [8, 15],
    [22, 55],
    [92, 10],
    [80, 60],
    [50, 8],
    [96, 85],
    [4, 80],
    [60, 92],
    [35, 35],
    [70, 30],
  ];

  return (
    <svg
      viewBox="0 0 100 100"
      preserveAspectRatio="none"
      style={{
        position: "absolute",
        inset: 0,
        width: "100%",
        height: "100%",
        opacity: 0.5,
        pointerEvents: "none",
      }}
    >
      {dots.map((d, i) => (
        <circle
          key={i}
          cx={d[0]}
          cy={d[1]}
          r={i % 3 === 0 ? 0.55 : 0.32}
          fill={i % 2 === 0 ? tokens.gold : tokens.teal}
          className="cp-dot"
          style={{
            animationDelay: `${i * 0.25}s`,
          }}
        />
      ))}
    </svg>
  );
}

/* =========================================
   READINESS RING
========================================= */

function ReadinessRing({ icon: Icon, accent, pct, hoverPct, size = 76 }) {
  const r = size === 76 ? 30 : 22;
  const c = 2 * Math.PI * r;

  const offset = c - (pct / 100) * c;
  const hoverOffset = c - (hoverPct / 100) * c;

  const sw = size === 76 ? 5 : 4;

  return (
    <div
      style={{
        position: "relative",
        width: size,
        height: size,
      }}
    >
      <svg
        width={size}
        height={size}
        viewBox={`0 0 ${size} ${size}`}
        style={{
          transform: "rotate(-90deg)",
        }}
      >
        <circle
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke="rgba(255,255,255,0.12)"
          strokeWidth={sw}
        />

        <circle
          className="cp-ring-fg"
          cx={size / 2}
          cy={size / 2}
          r={r}
          fill="none"
          stroke={accent}
          strokeWidth={sw}
          strokeLinecap="round"
          strokeDasharray={c}
          strokeDashoffset={offset}
          style={{
            "--ring-hover": hoverOffset,
            transition: "stroke-dashoffset 0.4s ease",
          }}
        />
      </svg>

      <div
        style={{
          position: "absolute",
          inset: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
        }}
      >
        <Icon size={size === 76 ? 26 : 18} color={accent} />
      </div>
    </div>
  );
}

/* =========================================
   AI INTERVIEW CIRCLE
========================================= */

function AiInterviewCircle({ onClick, leaving }) {
  return (
    <button
      onClick={onClick}
      className={`cp-circle-btn${leaving ? " cp-circle-leaving" : ""}`}
      aria-label="Choose Ask a Question or Mock Interview"
      style={{
        background: "none",
        border: "none",
        cursor: "pointer",
        padding: 24,
        position: "relative",
      }}
    >
      <div
        style={{
          position: "relative",
          width: 300,
          height: 300,
        }}
      >
        {/* OUTER ORBIT */}

        <svg
          className="cp-orbit-cw"
          width="300"
          height="300"
          viewBox="0 0 300 300"
          style={{
            position: "absolute",
            inset: 0,
          }}
        >
          <circle
            cx="150"
            cy="150"
            r="145"
            fill="none"
            stroke={tokens.tealLine}
            strokeWidth="1.5"
            strokeDasharray="2 10"
            strokeLinecap="round"
          />
        </svg>

        {/* MIDDLE ORBIT */}

        <svg
          className="cp-orbit-ccw"
          width="300"
          height="300"
          viewBox="0 0 300 300"
          style={{
            position: "absolute",
            inset: 0,
          }}
        >
          <circle
            cx="150"
            cy="150"
            r="122"
            fill="none"
            stroke={tokens.border}
            strokeWidth="1.5"
            strokeDasharray="1 8"
          />

          <path
            d="M150 28 A122 122 0 0 1 250 92"
            fill="none"
            stroke={tokens.gold}
            strokeWidth="2.5"
            strokeLinecap="round"
          />

          <path
            d="M150 272 A122 122 0 0 1 50 208"
            fill="none"
            stroke={tokens.teal}
            strokeWidth="2.5"
            strokeLinecap="round"
          />
        </svg>

        {/* GOLD SATELLITE */}

        <div
          className="cp-orbit-cw"
          style={{
            position: "absolute",
            inset: 0,
          }}
        >
          <div
            style={{
              position: "absolute",
              top: 2,
              left: "50%",
              width: 8,
              height: 8,
              marginLeft: -4,
              borderRadius: "50%",
              background: tokens.gold,
              boxShadow: `0 0 12px 2px ${tokens.gold}`,
            }}
          />
        </div>

        {/* TEAL SATELLITE */}

        <div
          className="cp-orbit-ccw"
          style={{
            position: "absolute",
            inset: 0,
          }}
        >
          <div
            style={{
              position: "absolute",
              bottom: 26,
              right: 26,
              width: 6,
              height: 6,
              borderRadius: "50%",
              background: tokens.teal,
              boxShadow: `0 0 10px 2px ${tokens.teal}`,
            }}
          />
        </div>

        {/* MAIN CIRCLE */}

        <div
          className="cp-core"
          style={{
            position: "absolute",
            inset: 40,
            borderRadius: "50%",
            background: `linear-gradient(150deg, ${tokens.violet}, #6f5fe0 45%, ${tokens.bgLo})`,
            border: "1.5px solid rgba(255,255,255,0.25)",
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            textAlign: "center",
            gap: 6,
          }}
        >
          <Sparkles size={22} color={tokens.gold} />

          <span
            className="cp-display"
            style={{
              fontSize: 22,
              fontWeight: 700,
              color: tokens.text,
            }}
          >
            AI Interview
          </span>

          <span
            className="cp-mono"
            style={{
              fontSize: 10.5,
              color: "rgba(255,255,255,0.75)",
              letterSpacing: "0.06em",
              textTransform: "uppercase",
            }}
          >
            Tap to begin
          </span>

          <ArrowDown size={14} color={tokens.gold} className="cp-bounce" />
        </div>
      </div>
    </button>
  );
}

/* =========================================
   OPTION CARD
========================================= */

function OptionCard({
  icon: Icon,
  tag,
  title,
  desc,
  accent,
  accentSoft,
  accentLine,
  hoverBg,
  pct,
  hoverPct,
  bullets,
  onClick,
}) {
  return (
    <div
      className="cp-card-wrap"
      style={{
        "--hover-glow": accentSoft,
        "--hover-color": accent,
        "--hover-bg": hoverBg,
        flex: 1,
        minWidth: 300,
      }}
    >
      <button
        onClick={onClick}
        className="cp-card"
        style={{
          textAlign: "left",
          width: "100%",
          height: "100%",
          background: tokens.glass,
          backdropFilter: "blur(18px)",
          WebkitBackdropFilter: "blur(18px)",
          border: `1.5px solid ${tokens.border}`,
          borderRadius: 26,
          padding: "34px 32px",
          cursor: "pointer",
          display: "flex",
          flexDirection: "column",
          gap: 22,
          position: "relative",
          overflow: "hidden",
          transition: "background 0.3s ease, box-shadow 0.3s ease",
          boxShadow:
            "0 20px 40px -28px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.08)",
        }}
      >
        {/* GLOW */}

        <div
          style={{
            position: "absolute",
            top: -50,
            right: -50,
            width: 150,
            height: 150,
            borderRadius: "50%",
            background: `radial-gradient(circle, ${accentSoft}, transparent 70%)`,
          }}
        />

        {/* TOP */}

        <div
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            position: "relative",
          }}
        >
          <ReadinessRing
            icon={Icon}
            accent={accent}
            pct={pct}
            hoverPct={hoverPct}
          />

          <span
            className="cp-mono"
            style={{
              fontSize: 10.5,
              letterSpacing: "0.08em",
              color: accent,
              textTransform: "uppercase",
              border: `1px solid ${accentLine}`,
              borderRadius: 999,
              padding: "5px 12px",
              background: `${accent}17`,
            }}
          >
            {tag}
          </span>
        </div>

        {/* TITLE */}

        <div
          style={{
            position: "relative",
          }}
        >
          <h3
            className="cp-display"
            style={{
              fontSize: 23,
              fontWeight: 700,
              color: tokens.text,
              margin: "0 0 9px",
            }}
          >
            {title}
          </h3>

          <p
            style={{
              fontSize: 14,
              color: tokens.textMuted,
              lineHeight: 1.65,
              margin: 0,
            }}
          >
            {desc}
          </p>
        </div>

        {/* BULLETS */}

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 10,
            position: "relative",
          }}
        >
          {bullets.map((b, i) => (
            <div
              key={i}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 9,
              }}
            >
              <div
                style={{
                  width: 16,
                  height: 16,
                  borderRadius: 6,
                  background: accentSoft,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  flexShrink: 0,
                }}
              >
                <div
                  style={{
                    width: 5,
                    height: 5,
                    borderRadius: "50%",
                    background: accent,
                  }}
                />
              </div>

              <span
                style={{
                  fontSize: 12.8,
                  color: tokens.textMuted,
                }}
              >
                {b}
              </span>
            </div>
          ))}
        </div>

        {/* CTA */}

        <div
          className="cp-cta"
          style={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            color: tokens.text,
            fontSize: 14,
            fontWeight: 600,
            marginTop: 4,
            position: "relative",
          }}
        >
          Get started
          <ArrowRight size={16} className="cp-arrow" />
        </div>
      </button>
    </div>
  );
}

/* =========================================
   STEP CARD
========================================= */

function StepCard({ icon: Icon, step, title, desc, accent, accentSoft }) {
  return (
    <div
      style={{
        flex: 1,
        background: tokens.glass,
        backdropFilter: "blur(12px)",
        border: `1px solid ${tokens.border}`,
        borderRadius: 18,
        padding: 24,
        position: "relative",
      }}
    >
      <span
        className="cp-mono"
        style={{
          position: "absolute",
          top: 18,
          right: 20,
          fontSize: 11,
          color: tokens.textMuted,
        }}
      >
        {step}
      </span>

      <div
        style={{
          width: 42,
          height: 42,
          borderRadius: 12,
          background: accentSoft,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          marginBottom: 16,
        }}
      >
        <Icon size={19} color={accent} />
      </div>

      <h4
        className="cp-display"
        style={{
          fontSize: 15.5,
          fontWeight: 700,
          color: tokens.text,
          margin: "0 0 6px",
        }}
      >
        {title}
      </h4>

      <p
        style={{
          fontSize: 12.8,
          color: tokens.textMuted,
          lineHeight: 1.6,
          margin: 0,
        }}
      >
        {desc}
      </p>
    </div>
  );
}

/* =========================================
   HOMEPAGE
========================================= */

export default function HomePage() {
  const navigate = useNavigate();

  const [showOptions, setShowOptions] = useState(false);
  const [leaving, setLeaving] = useState(false);

  /* =========================================
     OPEN OPTIONS
  ========================================= */

  const handleCircleClick = () => {
    setLeaving(true);

    setTimeout(() => {
      setShowOptions(true);
      setLeaving(false);
    }, 320);
  };

  /* =========================================
     RENDER
========================================= */

  return (
    <div
      className="cp-root"
      style={{
        minHeight: "100vh",
        position: "relative",
        background: tokens.bg,
        color: tokens.text,
      }}
    >
      <GlobalStyle />

      <HomeBackground tokens={tokens} />

      <div
        style={{
          position: "relative",
          zIndex: 1,
        }}
      >
        {/* =====================================
            HERO
        ===================================== */}

        <div
          className="cp-hero"
          style={{
            padding: "56px 24px 8px",
            textAlign: "center",
            position: "relative",
            overflow: "hidden",
          }}
        >
          <Constellation />

          <div
            style={{
              position: "relative",
              zIndex: 1,
              maxWidth: 650,
              margin: "0 auto",
            }}
          >
            {/* BADGE */}

            <div
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                background: tokens.glassHi,
                backdropFilter: "blur(10px)",
                border: `1px solid ${tokens.goldLine}`,
                borderRadius: 999,
                padding: "7px 16px",
                marginBottom: 22,
              }}
            >
              <Zap size={13} color={tokens.gold} />

              <span
                className="cp-mono"
                style={{
                  fontSize: 11,
                  color: tokens.gold,
                  letterSpacing: "0.05em",
                }}
              >
                YOUR AI CAREER COACH
              </span>
            </div>

            {/* TITLE */}

            <h1
              className="cp-hero-title cp-display"
              style={{
                fontSize: 42,
                fontWeight: 700,
                lineHeight: 1.18,
                margin: "0 0 14px",
                letterSpacing: "-0.01em",
                backgroundImage: `linear-gradient(100deg, ${tokens.text} 30%, ${tokens.teal} 65%, ${tokens.gold} 100%)`,
                WebkitBackgroundClip: "text",
                backgroundClip: "text",
                color: "transparent",
              }}
            >
              What are we working on today?
            </h1>

            {/* DESCRIPTION */}

            <p
              style={{
                fontSize: 15.5,
                color: tokens.textMuted,
                lineHeight: 1.6,
                margin: 0,
              }}
            >
              Ask a career question or step into a realistic mock interview —
              pick a path to begin.
            </p>
          </div>
        </div>

        {/* =====================================
            AI ORB / OPTIONS
        ===================================== */}

        {!showOptions ? (
          <div
            style={{
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              padding: "24px 24px 32px",
              position: "relative",
            }}
          >
            <AiInterviewCircle onClick={handleCircleClick} leaving={leaving} />

            <p
              style={{
                fontSize: 13,
                color: tokens.textMuted,
                margin: "4px 0 0",
              }}
            >
              One tap away from your question — or your next mock interview.
            </p>
          </div>
        ) : (
          <div
            className="cp-content"
            style={{
              maxWidth: 1000,
              margin: "0 auto",
              padding: "24px 48px 28px",
            }}
          >
            {/* START OVER */}

            <button
              className="cp-back-link"
              onClick={() => setShowOptions(false)}
            >
              <ArrowLeft size={14} />
              Start over
            </button>

            {/* OPTIONS */}

            <div
              className="cp-cards cp-cards-enter"
              style={{
                display: "flex",
                alignItems: "stretch",
                gap: 0,
                marginTop: 8,
                position: "relative",
              }}
            >
              {/* ASK A QUESTION */}

              <OptionCard
                icon={MessageCircleQuestion}
                tag="Guidance"
                title="Ask a Question"
                desc="Get instant, tailored answers on resumes, career switches, negotiation, and more."
                accent={tokens.teal}
                accentSoft={tokens.tealSoft}
                accentLine={tokens.tealLine}
                hoverBg="rgba(69,224,208,0.10)"
                pct={62}
                hoverPct={90}
                bullets={[
                  "Career-path planning",
                  "Guidance",
                  "Chat with AI",
                ]}
                onClick={() => navigate("/ask-question")}
              />

              {/* DIVIDER */}

              <div
                className="cp-divider"
                style={{
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  width: 64,
                  flexShrink: 0,
                }}
              >
                <div
                  style={{
                    width: 1,
                    flex: 1,
                    background:
                      "linear-gradient(transparent, " +
                      tokens.border +
                      ", transparent)",
                  }}
                />

                <span
                  className="cp-mono"
                  style={{
                    fontSize: 11,
                    color: tokens.textMuted,
                    padding: "12px 0",
                  }}
                >
                  OR
                </span>

                <div
                  style={{
                    width: 1,
                    flex: 1,
                    background:
                      "linear-gradient(transparent, " +
                      tokens.border +
                      ", transparent)",
                  }}
                />
              </div>

              {/* MOCK INTERVIEW */}

              <OptionCard
                icon={Mic}
                tag="Practice"
                title="Mock Interview"
                desc="Run a realistic, role-specific interview and get scored feedback right after."
                accent={tokens.gold}
                accentSoft={tokens.goldSoft}
                accentLine={tokens.goldLine}
                hoverBg="rgba(255,179,91,0.10)"
                pct={48}
                hoverPct={85}
                bullets={[
                  "Behavioral & technical rounds",
                  "Live AI interviewer",
                  "Instant readiness score",
                ]}
                onClick={() => navigate("/interview-setup")}
              />
            </div>
          </div>
        )}

        {/* =====================================
            STATS STRIP
        ===================================== */}

        <div
          className="cp-stats"
          style={{
            display: "flex",
            justifyContent: "center",
            gap: 20,
            padding: "20px 24px 60px",
            flexWrap: "wrap",
          }}
        >
          {[
            {
              icon: Target,
              label: "Mock interviews run",
              value: "128K+",
              accent: tokens.violet,
              soft: "rgba(139,124,246,0.16)",
            },

            {
              icon: TrendingUp,
              label: "Avg. readiness lift",
              value: "+34%",
              accent: tokens.teal,
              soft: tokens.tealSoft,
            },

            {
              icon: Sparkles,
              label: "Questions answered",
              value: "540K+",
              accent: tokens.gold,
              soft: tokens.goldSoft,
            },
          ].map((s, i) => {
            const Icon = s.icon;

            return (
              <div
                key={i}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  background: tokens.glass,
                  backdropFilter: "blur(12px)",
                  border: `1px solid ${tokens.border}`,
                  borderRadius: 16,
                  padding: "14px 20px",
                }}
              >
                <div
                  style={{
                    width: 36,
                    height: 36,
                    borderRadius: 11,
                    background: s.soft,
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <Icon size={17} color={s.accent} />
                </div>

                <div>
                  <div
                    className="cp-display"
                    style={{
                      fontSize: 18,
                      fontWeight: 700,
                      color: tokens.text,
                    }}
                  >
                    {s.value}
                  </div>

                  <div
                    style={{
                      fontSize: 11.5,
                      color: tokens.textMuted,
                    }}
                  >
                    {s.label}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* =====================================
            HOW IT WORKS
        ===================================== */}

        <div
          className="cp-content"
          style={{
            maxWidth: 1000,
            margin: "0 auto",
            padding: "0 48px 72px",
          }}
        >
          <div
            style={{
              textAlign: "center",
              marginBottom: 30,
            }}
          >
            <span
              className="cp-mono"
              style={{
                fontSize: 11,
                color: tokens.gold,
                letterSpacing: "0.08em",
                textTransform: "uppercase",
              }}
            >
              How it works
            </span>

            <h2
              className="cp-display"
              style={{
                fontSize: 24,
                fontWeight: 700,
                color: tokens.text,
                margin: "8px 0 0",
              }}
            >
              Two steps to walk in ready
            </h2>
          </div>

          <div
            className="cp-steps"
            style={{
              display: "flex",
              gap: 18,
            }}
          >
            <StepCard
              icon={FileText}
              step="01"
              title="Choose your path"
              accent={tokens.teal}
              accentSoft={tokens.tealSoft}
              desc="Ask a career question or choose a mock interview based on your target role."
            />

            <StepCard
              icon={BarChart3}
              step="02"
              title="See your score"
              accent={tokens.gold}
              accentSoft={tokens.goldSoft}
              desc="Walk away with useful answers, interview feedback, and a readiness score."
            />
          </div>
        </div>

        {/* =====================================
            FOOTER
        ===================================== */}

        <div
          className="cp-footer"
          style={{
            borderTop: `1px solid ${tokens.border}`,
            padding: "24px 48px",
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            flexWrap: "wrap",
            gap: 12,
          }}
        >
          <Logo />

          <span
            style={{
              fontSize: 12,
              color: tokens.textMuted,
            }}
          >
            © 2026 AI HELPER — Career Intelligence
          </span>
        </div>
      </div>
    </div>
  );
}
