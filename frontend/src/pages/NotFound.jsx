import { Link } from "react-router-dom";

export default function NotFound() {
  return (
    <section
      style={{
        minHeight: "70vh",
        display: "grid",
        placeItems: "center",
        padding: 32,
        textAlign: "center",
      }}
    >
      <div>
        <p style={{ color: "#45E0D0", fontSize: 13, fontWeight: 700, letterSpacing: "0.16em" }}>
          ERROR 404
        </p>
        <h1 style={{ margin: "12px 0", color: "#FBFAFF", fontSize: 42 }}>
          Page not found
        </h1>
        <p style={{ margin: "0 auto 24px", maxWidth: 420, color: "#C2C4EC" }}>
          The page you are looking for does not exist or the address was typed incorrectly.
        </p>
        <Link
          to="/"
          style={{
            display: "inline-block",
            padding: "12px 18px",
            borderRadius: 10,
            background: "#45E0D0",
            color: "#191C36",
            fontWeight: 700,
            textDecoration: "none",
          }}
        >
          Return home
        </Link>
      </div>
    </section>
  );
}
