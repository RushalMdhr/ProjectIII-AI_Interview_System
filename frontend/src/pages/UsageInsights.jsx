import { useEffect, useMemo, useState } from "react";
import { AlertCircle, BarChart3, CheckCircle2, Clock3, MessageSquare, RefreshCw } from "lucide-react";
import { getMyUsage } from "../services/api";

const colors = {
  panel: "#202449",
  border: "rgba(255,255,255,0.12)",
  text: "#FBFAFF",
  muted: "#C2C4EC",
  teal: "#45E0D0",
  gold: "#FFB35B",
  red: "#FF8D8D",
};

const number = (value) => Number(value || 0).toLocaleString();
const label = (value) =>
  String(value || "general_chat")
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
const windowLabel = (minutes) => {
  const hours = Number(minutes || 0) / 60;
  const days = Math.round(hours / 24);
  const roundedHours = Math.round(hours);
  return hours >= 24
    ? `${days} day${days === 1 ? "" : "s"}`
    : `${roundedHours} hour${roundedHours === 1 ? "" : "s"}`;
};

function Metric({ icon: Icon, title, value, detail }) {
  return (
    <div style={{ background: colors.panel, border: `1px solid ${colors.border}`, borderRadius: 16, padding: 20 }}>
      <div style={{ display: "flex", alignItems: "center", gap: 9, color: colors.muted, fontSize: 13, fontWeight: 700 }}>
        <Icon size={17} color={colors.teal} />
        {title}
      </div>
      <div style={{ color: colors.text, fontSize: 28, fontWeight: 700, marginTop: 12 }}>{value}</div>
      <div style={{ color: colors.muted, fontSize: 12, fontWeight: 500, marginTop: 5 }}>{detail}</div>
    </div>
  );
}

export default function UsageInsights() {
  const [usage, setUsage] = useState(null);
  const [days, setDays] = useState("30");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const loadUsage = async () => {
    setLoading(true);
    setError("");
    try {
      setUsage(await getMyUsage(days));
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Unable to load your usage right now.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadUsage();
  }, [days]);

  const maxDailyTokens = useMemo(
    () => Math.max(...(usage?.daily || []).map((day) => Number(day.total_tokens || 0)), 1),
    [usage],
  );

  if (loading) {
    return <main style={{ padding: 48, color: colors.muted }}>Loading your usage insights...</main>;
  }

  return (
    <main style={{ width: "100%", maxWidth: 1440, margin: "0 auto", padding: "48px clamp(24px, 4vw, 64px) 80px", boxSizing: "border-box", color: colors.text }}>
      <div style={{ display: "flex", justifyContent: "space-between", gap: 20, alignItems: "flex-start", marginBottom: 30 }}>
        <div>
          <div style={{ color: colors.teal, fontSize: 12, fontWeight: 800, letterSpacing: "0.14em", textTransform: "uppercase" }}>Personal overview</div>
          <h1 style={{ margin: "8px 0 8px", fontSize: 36, fontWeight: 800, letterSpacing: "-0.03em" }}>Usage Insights</h1>
          <p style={{ margin: 0, color: colors.muted }}>Review how you have been using AI Helper.</p>
        </div>
        <select value={days} onChange={(event) => setDays(event.target.value)} style={{ background: colors.panel, border: `1px solid ${colors.border}`, borderRadius: 10, color: colors.text, padding: "10px 12px", fontWeight: 700 }} aria-label="Usage period">
          <option value={7}>Last 7 days</option>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
          <option value="lifetime">Lifetime</option>
        </select>
      </div>

      {error ? (
        <div role="alert" style={{ background: "rgba(255,141,141,0.12)", border: `1px solid ${colors.red}`, borderRadius: 12, padding: 16, color: colors.red, display: "flex", gap: 10, alignItems: "center" }}>
          <AlertCircle size={18} /> {error}
          <button type="button" onClick={loadUsage} style={{ marginLeft: "auto", background: "none", border: 0, color: colors.text, cursor: "pointer" }} aria-label="Retry loading usage"><RefreshCw size={17} /></button>
        </div>
      ) : (
        <>
          <section style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(230px, 1fr))", gap: 18 }}>
            <Metric icon={BarChart3} title="Total tokens" value={number(usage.total_tokens)} detail={`${number(usage.requests)} requests`} />
            <Metric icon={MessageSquare} title="Input tokens" value={number(usage.input_tokens)} detail="Tokens sent" />
            <Metric icon={MessageSquare} title="Output tokens" value={number(usage.output_tokens)} detail="Tokens received" />
            <Metric icon={usage.failed_requests ? AlertCircle : CheckCircle2} title="Completed requests" value={number(usage.requests - usage.failed_requests)} detail={`${number(usage.failed_requests)} unsuccessful`} />
          </section>

          <section style={{ background: colors.panel, border: `1px solid ${colors.border}`, borderRadius: 18, padding: 26, marginTop: 20 }}>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 16, alignItems: "baseline", flexWrap: "wrap" }}>
              <div>
                <h2 style={{ margin: 0, fontSize: 18, fontWeight: 800 }}>Token limit</h2>
                <p style={{ margin: "6px 0 0", color: colors.muted, fontSize: 13 }}>
                  Rolling limit for your account
                </p>
              </div>
              <strong style={{ color: colors.teal, fontSize: 16 }}>
                {number(usage.tokens_remaining)} remaining
              </strong>
            </div>
            <div style={{ height: 10, marginTop: 20, background: "rgba(255,255,255,0.1)", borderRadius: 999 }}>
              <div
                style={{
                  width: `${Math.min((Number(usage.tokens_used_in_window || 0) / Math.max(Number(usage.token_limit || 0), 1)) * 100, 100)}%`,
                  height: "100%",
                  background: Number(usage.tokens_remaining) === 0 ? colors.red : colors.teal,
                  borderRadius: 999,
                }}
              />
            </div>
            <div style={{ display: "flex", justifyContent: "space-between", gap: 12, marginTop: 10, color: colors.muted, fontSize: 12 }}>
              <span>{number(usage.tokens_used_in_window)} used of {number(usage.token_limit)} tokens</span>
              <span>Resets continuously · {windowLabel(usage.window_minutes)} window</span>
            </div>
          </section>

          <section style={{ display: "grid", gridTemplateColumns: "minmax(0, 1.7fr) minmax(300px, 0.8fr)", gap: 20, marginTop: 20 }}>
            <div style={{ background: colors.panel, border: `1px solid ${colors.border}`, borderRadius: 18, padding: 26 }}>
              <h2 style={{ margin: "0 0 24px", fontSize: 18, fontWeight: 800 }}>Daily activity</h2>
              {usage.daily.length ? (
                <div style={{ display: "flex", alignItems: "flex-end", gap: 12, height: 230 }}>
                  {usage.daily.map((day) => (
                    <div key={day.day} title={`${day.day}: ${number(day.total_tokens)} tokens`} style={{ flex: 1, display: "flex", flexDirection: "column", alignItems: "center", gap: 8, height: "100%", justifyContent: "flex-end" }}>
                      <div style={{ width: "100%", maxWidth: 54, minHeight: 4, height: `${(Number(day.total_tokens || 0) / maxDailyTokens) * 180}px`, borderRadius: "7px 7px 2px 2px", background: "rgba(69,224,208,0.72)", boxShadow: "inset 0 1px 0 rgba(255,255,255,0.16)" }} />
                      <span style={{ color: colors.muted, fontSize: 10 }}>{String(day.day).slice(5)}</span>
                    </div>
                  ))}
                </div>
              ) : <p style={{ color: colors.muted }}>No activity in this period.</p>}
            </div>
            <div style={{ background: colors.panel, border: `1px solid ${colors.border}`, borderRadius: 18, padding: 26 }}>
              <h2 style={{ margin: "0 0 20px", fontSize: 18, fontWeight: 800 }}>By activity</h2>
              {usage.by_use_case.length ? usage.by_use_case.map((item) => (
                <div key={item.use_case} style={{ display: "flex", justifyContent: "space-between", gap: 12, padding: "11px 0", borderBottom: `1px solid ${colors.border}`, fontSize: 13 }}>
                  <span style={{ color: colors.muted, fontWeight: 600 }}>{label(item.use_case)}</span><strong style={{ color: colors.teal, fontWeight: 800 }}>{number(item.total_tokens)}</strong>
                </div>
              )) : <p style={{ color: colors.muted }}>No activity in this period.</p>}
            </div>
          </section>

          <section style={{ background: colors.panel, border: `1px solid ${colors.border}`, borderRadius: 18, padding: 26, marginTop: 20, overflowX: "auto" }}>
            <h2 style={{ margin: "0 0 20px", fontSize: 18, fontWeight: 800 }}>Recent requests</h2>
            {usage.recent.length ? (
              <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 13 }}>
                <thead><tr style={{ color: colors.muted, textAlign: "left", fontWeight: 800 }}><th style={{ padding: "8px 10px 12px 0" }}>Activity</th><th style={{ padding: "8px 10px" }}>Model</th><th style={{ padding: "8px 10px" }}>Tokens</th><th style={{ padding: "8px 0 12px 10px" }}>Status</th></tr></thead>
                <tbody>{usage.recent.map((request) => <tr key={request.id} style={{ borderTop: `1px solid ${colors.border}` }}><td style={{ padding: "12px 10px 12px 0", fontWeight: 700 }}>{label(request.use_case)}<div style={{ color: colors.muted, fontSize: 11, fontWeight: 400, marginTop: 3 }}><Clock3 size={11} style={{ verticalAlign: "middle", marginRight: 4 }} />{new Date(request.created_at).toLocaleString()}</div></td><td style={{ padding: 12, fontWeight: 600 }}>{request.model}</td><td style={{ padding: 12, color: colors.teal, fontWeight: 800 }}>{number(request.total_tokens)}</td><td style={{ padding: "12px 0 12px 10px", color: request.success ? colors.teal : colors.red, fontWeight: 800 }}>{request.success ? "Completed" : "Unsuccessful"}</td></tr>)}</tbody>
              </table>
            ) : <p style={{ color: colors.muted }}>Your recent requests will appear here.</p>}
          </section>
        </>
      )}
    </main>
  );
}
