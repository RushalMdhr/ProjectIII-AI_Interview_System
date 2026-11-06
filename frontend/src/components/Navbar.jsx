import { useEffect, useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { logout } from "../services/api";

const tokens = {
  gold: "#FFB35B",
  teal: "#45E0D0",
  text: "#FBFAFF",
};

function Logo() {
  const navigate = useNavigate();

  return (
    <button
      onClick={() => navigate("/")}
      aria-label="Go to homepage"
      style={{
        display: "flex",
        alignItems: "center",
        gap: 10,
        background: "none",
        border: "none",
        padding: 0,
        cursor: "pointer",
      }}
    >
      <svg width="34" height="34" viewBox="0 0 40 40" fill="none">
        <circle
          cx="20"
          cy="20"
          r="17.5"
          stroke="rgba(255,255,255,0.2)"
          strokeWidth="3"
        />

        <path
          d="M20 2.5 A17.5 17.5 0 0 1 35.4 28.7"
          stroke={tokens.gold}
          strokeWidth="3"
          strokeLinecap="round"
        />

        <circle cx="20" cy="20" r="6" fill={tokens.teal} />
      </svg>

      <span
        className="cp-display"
        style={{
          fontSize: 18,
          fontWeight: 700,
          color: tokens.text,
        }}
      >
        AI
        <span style={{ color: tokens.teal }}>HELPER</span>
      </span>
    </button>
  );
}

export default function Navbar() {
  const navigate = useNavigate();
  const location = useLocation();
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem("currentUser")) || null;
    } catch {
      return null;
    }
  });

  useEffect(() => {
    try {
      setCurrentUser(JSON.parse(localStorage.getItem("currentUser")) || null);
    } catch {
      setCurrentUser(null);
    }
  }, [location.pathname]);

  const displayName = currentUser?.first_name || currentUser?.name || "Guest";
  const initials = displayName
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
  const profilePicture =
    currentUser?.profile_picture || currentUser?.profile_picture_url;

  const handleLogout = () => {
    logout();
    setCurrentUser(null);
    setAccountMenuOpen(false);
    navigate("/");
  };

  return (
    <nav
      className="cp-navbar"
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        padding: "22px 48px",
        width: "100%",
        boxSizing: "border-box",

        position: "sticky",
        top: 0,
        zIndex: 1000,

        background: "#191C36",
        borderBottom: "1px solid rgba(255,255,255,0.08)",
      }}
    >
      {/* LOGO */}
      <Logo />

      {/* PROFILE */}
      <div
        style={{
          position: "relative",
          display: "flex",
          alignItems: "center",
          gap: 14,
        }}
      >
        <button
          type="button"
          aria-expanded={accountMenuOpen}
          aria-haspopup="menu"
          onClick={() => setAccountMenuOpen((isOpen) => !isOpen)}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 14,
            background: "none",
            border: "none",
            padding: 0,
            cursor: "pointer",
            color: "inherit",
          }}
        >
          <span
            style={{
              fontSize: 13.5,
              color: "#C2C4EC",
            }}
          >
            Hi, {displayName}
          </span>

          <span
            style={{
              width: 34,
              height: 34,
              borderRadius: "50%",
              background: `linear-gradient(135deg, ${tokens.gold}, ${tokens.teal})`,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: 13,
              fontWeight: 700,
              color: "#191C36",
              overflow: "hidden",
            }}
          >
            {profilePicture ? (
              <img
                src={profilePicture}
                alt={`${displayName} profile`}
                style={{
                  width: "100%",
                  height: "100%",
                  objectFit: "cover",
                }}
              />
            ) : (
              initials
            )}
          </span>
        </button>

        {accountMenuOpen && (
          <div
            role="menu"
            style={{
              position: "absolute",
              top: 46,
              right: 0,
              zIndex: 20,
              minWidth: 170,
              padding: 8,
              borderRadius: 12,
              background: "#202449",
              border: "1px solid rgba(255,255,255,0.16)",
              boxShadow: "0 18px 36px rgba(0,0,0,0.28)",
            }}
          >
            {currentUser ? (
              <>
                <div
                  style={{
                    padding: "9px 12px 10px",
                    color: "#C2C4EC",
                    fontSize: 12,
                    borderBottom: "1px solid rgba(255,255,255,0.12)",
                  }}
                >
                  {currentUser.email}
                </div>

                <button
                  type="button"
                  role="menuitem"
                  onClick={handleLogout}
                  style={{
                    display: "block",
                    width: "100%",
                    padding: "10px 12px",
                    marginTop: 4,
                    border: "none",
                    borderRadius: 8,
                    background: "none",
                    color: tokens.text,
                    textAlign: "left",
                    fontSize: 13.5,
                    cursor: "pointer",
                  }}
                >
                  Log out
                </button>
              </>
            ) : (
              <>
                <Link
                  to="/login"
                  role="menuitem"
                  onClick={() => setAccountMenuOpen(false)}
                  style={{
                    display: "block",
                    padding: "10px 12px",
                    borderRadius: 8,
                    color: tokens.text,
                    textDecoration: "none",
                    fontSize: 13.5,
                  }}
                >
                  Login
                </Link>

                <Link
                  to="/register"
                  role="menuitem"
                  onClick={() => setAccountMenuOpen(false)}
                  style={{
                    display: "block",
                    padding: "10px 12px",
                    borderRadius: 8,
                    color: tokens.text,
                    textDecoration: "none",
                    fontSize: 13.5,
                  }}
                >
                  Create account
                </Link>
              </>
            )}
          </div>
        )}
      </div>
    </nav>
  );
}

export { Logo };
