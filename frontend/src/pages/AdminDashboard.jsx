
import { useEffect, useMemo, useState } from "react";
import { Navigate } from "react-router-dom";
import {
  AlertTriangle,
  Activity,
  BarChart3,
  Clock3,
  Cpu,
  LayoutDashboard,
  LogOut,
  RefreshCw,
  Settings2,
  ShieldCheck,
  Users,
  Zap,
  Database,
  TrendingUp,
} from "lucide-react";

import {
  getAnalyticsSummary,
  getAnalyticsTimeseries,
  getModelPricing,
  getUseCaseConfigs,
  getUserActivity,
  saveModelPricing,
  saveUseCaseConfig,
} from "../services/api";

// ----------------------------------
// Helpers
// ----------------------------------

const currentUser = () => {
  try {
    return JSON.parse(localStorage.getItem("currentUser") || "null");
  } catch {
    return null;
  }
};

const number = (value) =>
  Number(value || 0).toLocaleString();

const currency = (value) =>
  Number(value || 0).toLocaleString(undefined, {
    style: "currency",
    currency: "USD",
    minimumFractionDigits: 4,
    maximumFractionDigits: 8,
  });

const DEFAULT_PRICED_MODELS = [
  { provider: "ollama", model: "llama3.2:latest" },
  { provider: "groq", model: "openai/gpt-oss-120b" },
];

const formatDate = (date) =>
  new Date(date).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
  });

// ----------------------------------
// Metric Card
// ----------------------------------

function Metric({ label, value, icon: Icon, description, danger = false, success = false }) {
  const stateClass = danger
    ? "border-red-400/30 bg-red-400/10 hover:border-red-300/60 hover:bg-red-400/15"
    : success
      ? "border-[#42DCC6]/30 bg-[#42DCC6]/10 hover:border-[#42DCC6]/60 hover:bg-[#42DCC6]/15"
      : "border-[#253247] bg-[#111A29] hover:border-[#42DCC6]/40 hover:bg-[#141F30]";
  const iconClass = danger
    ? "bg-red-400/15 text-red-300 group-hover:bg-red-400/25"
    : success
      ? "bg-[#42DCC6]/15 text-[#42DCC6] group-hover:bg-[#42DCC6]/25"
      : "bg-[#42DCC6]/10 text-[#42DCC6] group-hover:bg-[#42DCC6]/15";
  const valueClass = danger ? "text-red-200" : success ? "text-[#42DCC6]" : "text-[#F1F5F9]";
  const descriptionClass = danger ? "text-red-200/70" : success ? "text-[#42DCC6]/70" : "text-[#64748B]";

  return (
    <article className={`group rounded-xl border p-5 transition-all duration-200 ${stateClass}`}>
      <div className="mb-5 flex items-center justify-between">
        <span className="text-sm font-medium text-[#94A3B8]">
          {label}
        </span>

        <div className={`grid h-10 w-10 place-items-center rounded-lg transition-colors ${iconClass}`}>
          <Icon size={19} />
        </div>
      </div>

      <strong className={`block text-2xl font-semibold tracking-tight ${valueClass}`}>
        {value}
      </strong>

      {description && (
        <p className={`mt-2 text-xs ${descriptionClass}`}>
          {description}
        </p>
      )}
    </article>
  );
}

// ----------------------------------
// Breakdown Component
// ----------------------------------

function Breakdown({ title, rows, labelKey, icon: Icon, showCost = false }) {
  const max = Math.max(
    ...rows.map((row) => Number(row.total_tokens || 0)),
    1
  );

  return (
    <section className="min-h-[260px] rounded-xl border border-[#253247] bg-[#111A29] p-6">
      <div className="mb-7 flex items-center gap-3">
        <div className="grid h-9 w-9 place-items-center rounded-lg bg-[#42DCC6]/10 text-[#42DCC6]">
          <Icon size={18} />
        </div>

        <h2 className="text-base font-semibold text-[#F1F5F9]">
          {title}
        </h2>
      </div>

      {rows.length === 0 ? (
        <div className="flex min-h-[140px] items-center justify-center text-sm text-[#8492A8]">
          No request data yet.
        </div>
      ) : (
        <div className="space-y-6">
          {rows.map((row) => (
            <div key={`${row[labelKey]}-${row.provider || ""}`}>
              <div className="mb-2 flex justify-between gap-3 text-sm">
                <span className="truncate text-[#A1AEC1]">
                  {row[labelKey]}
                </span>

                <span className="shrink-0 font-medium text-[#E2E8F0]">
                  {number(row.total_tokens)} tokens
                  {showCost && <span className="ml-3 text-[#42DCC6]">{currency(row.estimated_cost)}</span>}
                </span>
              </div>

              <div className="h-2 overflow-hidden rounded-full bg-[#253247]">
                <div
                  className="h-full rounded-full bg-[#42DCC6] transition-all duration-500"
                  style={{
                    width: `${(Number(row.total_tokens || 0) / max) * 100}%`,
                  }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </section>
  );
}

// ----------------------------------
// Daily Usage Chart
// ----------------------------------

function DailyUsageChart({ daily, maxDaily }) {
  return (
    <section className="col-span-2 rounded-xl border border-[#253247] bg-[#111A29] p-6 max-[760px]:col-span-1">
      <div className="mb-8 flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-semibold text-[#F1F5F9]">
            Daily token usage
          </h2>

          <p className="mt-1 text-xs text-[#8492A8]">
            Token consumption over time
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs text-[#8492A8]">
          <span className="h-2 w-2 rounded-full bg-[#42DCC6]" />
          Total tokens
        </div>
      </div>

      {daily.length === 0 ? (
        <div className="flex h-[190px] items-center justify-center text-sm text-[#8492A8]">
          No daily usage data available.
        </div>
      ) : (
        <div className="flex h-[190px] items-end gap-3 overflow-x-auto border-b border-[#253247] px-2 pt-3">
          {daily.map((row) => {
            const percentage =
              (Number(row.total_tokens || 0) / maxDaily) * 100;

            return (
              <div
                className="flex h-full min-w-[34px] flex-1 flex-col items-center justify-end"
                key={row.day}
                title={`${number(row.total_tokens)} tokens`}
              >
                <div
                  className="group relative flex w-full flex-1 items-end justify-center"
                >
                  <div
                    className="min-h-[3px] w-[22px] rounded-t-md bg-[#42DCC6] transition-all duration-300 hover:bg-[#66E8D5]"
                    style={{
                      height: `${percentage}%`,
                    }}
                  />
                </div>

                <span className="mt-3 whitespace-nowrap text-[10px] text-[#8492A8]">
                  {formatDate(row.day)}
                </span>
              </div>
            );
          })}
        </div>
      )}
    </section>
  );
}

function UserActivity({ activity }) {
  return (
    <div className="space-y-5">
      <section className="rounded-xl border border-[#253247] bg-[#111A29] p-6">
        <h2 className="mb-5 text-base font-semibold">Usage by user</h2>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[620px] text-left text-sm">
            <thead className="text-xs uppercase tracking-wide text-[#64748B]">
              <tr><th className="pb-3">User</th><th className="pb-3">Requests</th><th className="pb-3">Input tokens</th><th className="pb-3">Output tokens</th><th className="pb-3">Tokens</th><th className="pb-3">Failures</th><th className="pb-3">Last request</th></tr>
            </thead>
            <tbody className="divide-y divide-[#253247]">
              {(activity?.users || []).map((row) => (
                <tr key={row.user_id || row["user__email"]}>
                  <td className="py-3 text-[#E2E8F0]">{row["user__email"] || "Deleted user"}</td>
                  <td className="py-3 text-[#A1AEC1]">{number(row.requests)}</td>
                  <td className="py-3 text-[#A1AEC1]">{number(row.input_tokens)}</td>
                  <td className="py-3 text-[#A1AEC1]">{number(row.output_tokens)}</td>
                  <td className="py-3 text-[#A1AEC1]">{number(row.total_tokens)}</td>
                  <td className="py-3 text-[#A1AEC1]">{number(row.failed_requests)}</td>
                  <td className="py-3 text-[#8492A8]">{row.last_request ? formatDate(row.last_request) : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!activity?.users?.length && <p className="text-sm text-[#8492A8]">No user activity in this period.</p>}
        </div>
      </section>
      <section className="rounded-xl border border-[#253247] bg-[#111A29] p-6">
        <h2 className="mb-5 text-base font-semibold">Recent AI requests</h2>
        <div className="space-y-3">
          {(activity?.recent || []).map((row) => (
            <div key={row.id} className="flex flex-wrap items-center justify-between gap-3 border-b border-[#253247] pb-3 text-sm">
              <span className="text-[#E2E8F0]">{row["user__email"] || "Deleted user"}</span>
              <span className="text-[#8492A8]">{row.provider} / {row.model}</span>
              <span className="text-[#A1AEC1]">{number(row.total_tokens)} tokens</span>
              <span className={row.success ? "text-[#42DCC6]" : "text-red-300"}>{row.success ? "Success" : "Failed"}</span>
            </div>
          ))}
        </div>
      </section>
      <section className="rounded-xl border border-[#253247] bg-[#111A29] p-6">
        <h2 className="mb-5 text-base font-semibold">Usage by chat session</h2>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[900px] text-left text-sm">
            <thead className="text-xs uppercase tracking-wide text-[#64748B]">
              <tr><th className="pb-3">User</th><th className="pb-3">Session</th><th className="pb-3">Use case</th><th className="pb-3">Requests</th><th className="pb-3">Input tokens</th><th className="pb-3">Output tokens</th><th className="pb-3">Tokens</th><th className="pb-3">Last request</th></tr>
            </thead>
            <tbody className="divide-y divide-[#253247]">
              {(activity?.sessions || []).map((row) => (
                <tr key={`${row.session_id || "unassigned"}-${row.user_id || "deleted"}-${row.use_case}`}>
                  <td className="py-3 text-[#E2E8F0]">{row["user__email"] || "Deleted user"}</td>
                  <td className="max-w-[220px] truncate py-3 text-[#A1AEC1]" title={row["session__title"] || undefined}>{row["session__title"] || "Unassigned session"}</td>
                  <td className="py-3 text-[#A1AEC1]">{row.use_case}</td>
                  <td className="py-3 text-[#A1AEC1]">{number(row.requests)}</td>
                  <td className="py-3 text-[#A1AEC1]">{number(row.input_tokens)}</td>
                  <td className="py-3 text-[#A1AEC1]">{number(row.output_tokens)}</td>
                  <td className="py-3 text-[#A1AEC1]">{number(row.total_tokens)}</td>
                  <td className="py-3 text-[#8492A8]">{row.last_request ? formatDate(row.last_request) : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!activity?.sessions?.length && <p className="text-sm text-[#8492A8]">No session activity in this period.</p>}
        </div>
      </section>
    </div>
  );
}

function SettingsPanel({ pricing, configs, onSave, onSaveConfig }) {
  const pricedModels = DEFAULT_PRICED_MODELS;
  const [form, setForm] = useState({
    provider: "ollama",
    model: "llama3.2:latest",
    input_cost_per_million_tokens: "",
    output_cost_per_million_tokens: "",
  });
  const [saving, setSaving] = useState(false);
  const useCases = [
    { value: "general_chat", label: "General Chat" },
    { value: "career_guidance", label: "Career Guidance" },
    { value: "interview_assessment", label: "Interview Assessment" },
  ];
  const defaultModels = {
    ollama: "llama3.2:latest",
    groq: "openai/gpt-oss-120b",
  };
  const [routingForms, setRoutingForms] = useState({
    general_chat: { provider: "ollama", model: "llama3.2:latest" },
    career_guidance: { provider: "groq", model: "openai/gpt-oss-120b" },
    interview_assessment: { provider: "ollama", model: "llama3.2:latest" },
  });
  const [savingConfig, setSavingConfig] = useState("");

  useEffect(() => {
    if (!configs?.length) return;
    setRoutingForms((current) => {
      const next = { ...current };
      configs.forEach((config) => {
        next[config.use_case] = {
          provider: config.provider,
          model: config.model,
        };
      });
      return next;
    });
  }, [configs]);

  const submit = async (event) => {
    event.preventDefault();
    if (!form.model.trim()) return;
    setSaving(true);
    try {
      await onSave(form);
      setForm({ ...form, model: "", input_cost_per_million_tokens: "", output_cost_per_million_tokens: "" });
    } finally {
      setSaving(false);
    }
  };

  const modelsForProvider = pricedModels.filter((row) => row.provider === form.provider);

  const submitConfig = async (event, useCase) => {
    event.preventDefault();
    const configForm = routingForms[useCase];
    if (!configForm.model.trim()) return;
    setSavingConfig(useCase);
    try {
      await onSaveConfig({ ...configForm, use_case: useCase });
    } finally {
      setSavingConfig("");
    }
  };

  return (
    <div className="space-y-5">
      <section className="rounded-xl border border-[#253247] bg-[#111A29] p-6">
        <h2 className="mb-2 text-base font-semibold">Use-case routing</h2>
        <p className="mb-6 text-sm text-[#8492A8]">Choose the provider and model for each use case. Changes apply to new requests.</p>
        <div className="space-y-4">
          {useCases.map(({ value, label }) => {
            const configForm = routingForms[value];
            const availableModels = (pricing || [])
              .filter((row) => row.provider === configForm.provider)
              .map((row) => row.model);
            const models = availableModels.includes(configForm.model)
              ? availableModels
              : [configForm.model, ...availableModels];

            return (
              <form key={value} onSubmit={(event) => submitConfig(event, value)} className="grid gap-3 rounded-lg border border-[#253247] p-4 md:grid-cols-[1.2fr_1fr_1.5fr_auto] md:items-center">
                <strong className="text-sm text-[#E2E8F0]">{label}</strong>
                <select value={configForm.provider} onChange={(e) => {
                  const provider = e.target.value;
                  const providerModels = (pricing || [])
                    .filter((row) => row.provider === provider)
                    .map((row) => row.model);
                  setRoutingForms({
                    ...routingForms,
                    [value]: {
                      provider,
                      model: providerModels[0] || defaultModels[provider],
                    },
                  });
                }} className="rounded-lg border border-[#253247] bg-[#0D1422] p-3 text-sm text-[#E2E8F0]">
                  <option value="ollama">Ollama</option>
                  <option value="groq">Groq</option>
                </select>
                <select value={configForm.model} onChange={(e) => setRoutingForms({ ...routingForms, [value]: { ...configForm, model: e.target.value } })} className="rounded-lg border border-[#253247] bg-[#0D1422] p-3 text-sm text-[#E2E8F0]">
                  {models.map((model) => <option key={model} value={model}>{model}</option>)}
                </select>
                <button disabled={savingConfig === value} className="rounded-lg bg-[#42DCC6] px-4 py-3 text-sm font-bold text-[#09131C]">{savingConfig === value ? "Saving..." : "Save"}</button>
              </form>
            );
          })}
        </div>
      </section>
      <section className="rounded-xl border border-[#253247] bg-[#111A29] p-6">
        <h2 className="mb-2 text-base font-semibold">Model pricing manager</h2>
        <p className="mb-6 text-sm text-[#8492A8]">Set input and output pricing for the two active models. Costs apply to new requests.</p>
        <form onSubmit={submit} className="grid gap-3 md:grid-cols-4">
          <select value={form.provider} onChange={(e) => {
            const provider = e.target.value;
            const nextModel = pricedModels.find((row) => row.provider === provider)?.model || form.model;
            setForm({ ...form, provider, model: nextModel });
          }} className="rounded-lg border border-[#253247] bg-[#0D1422] p-3 text-sm text-[#E2E8F0]">
            <option value="ollama">Ollama</option><option value="groq">Groq</option>
          </select>
          <select required value={form.model} onChange={(e) => setForm({ ...form, model: e.target.value })} className="rounded-lg border border-[#253247] bg-[#0D1422] p-3 text-sm text-[#E2E8F0]">
            {modelsForProvider.map((row) => <option key={row.model} value={row.model}>{row.model}</option>)}
          </select>
          <input type="number" step="0.00000001" min="0" max="9999.99999999" placeholder="Input $ / 1M" value={form.input_cost_per_million_tokens} onChange={(e) => setForm({ ...form, input_cost_per_million_tokens: e.target.value })} className="rounded-lg border border-[#253247] bg-[#0D1422] p-3 text-sm text-[#E2E8F0]" />
          <div className="flex gap-2"><input type="number" step="0.00000001" min="0" max="9999.99999999" placeholder="Output $ / 1M" value={form.output_cost_per_million_tokens} onChange={(e) => setForm({ ...form, output_cost_per_million_tokens: e.target.value })} className="min-w-0 flex-1 rounded-lg border border-[#253247] bg-[#0D1422] p-3 text-sm text-[#E2E8F0]" /><button disabled={saving} className="rounded-lg bg-[#42DCC6] px-4 text-sm font-bold text-[#09131C]">Save</button></div>
        </form>
      </section>
      <section className="rounded-xl border border-[#253247] bg-[#111A29] p-6">
        <h2 className="mb-5 text-base font-semibold">Configured models</h2>
        <div className="grid gap-3 md:grid-cols-2">
          {pricedModels.map((model) => {
            const row = (pricing || []).find((item) => item.provider === model.provider && item.model === model.model);
            return <div key={`${model.provider}-${model.model}`} className="rounded-lg border border-[#253247] p-4 text-sm"><div className="flex justify-between"><b>{model.provider} / {model.model}</b><span className={row ? "text-[#42DCC6]" : "text-[#8492A8]"}>{row ? "configured" : "not priced"}</span></div><p className="mt-2 text-[#8492A8]">Input ${row?.input_cost_per_million_tokens || "0"} · Output ${row?.output_cost_per_million_tokens || "0"} per 1M</p></div>;
          })}
        </div>
      </section>
    </div>
  );
}

// ----------------------------------
// Sidebar Navigation
// ----------------------------------

function Sidebar({ onLogout, section, onSectionChange }) {
  const navigation = [
    {
      label: "Overview",
      icon: LayoutDashboard,
      key: "overview",
    },
    {
      label: "AI Analytics",
      icon: BarChart3,
      key: "analytics",
    },
    {
      label: "User Activity",
      icon: Users,
      key: "users",
    },
    {
      label: "Settings",
      icon: Settings2,
      key: "settings",
    },
  ];

  return (
    <aside className="fixed inset-y-0 left-0 z-20 hidden w-[250px] border-r border-[#253247] bg-[#0D1422] p-5 lg:flex lg:flex-col">
      {/* Branding */}

      <div className="flex items-center gap-3 border-b border-[#253247] pb-7">
        <div className="grid h-10 w-10 shrink-0 place-items-center rounded-xl bg-[#42DCC6] text-[#09131C]">
          <ShieldCheck size={22} />
        </div>

        <div>
          <strong className="block text-sm font-bold tracking-wide text-[#F1F5F9]">
            AI Interview 
          </strong>

          <span className="text-[10px] font-semibold tracking-[.16em] text-[#8492A8]">
            ADMIN CONSOLE
          </span>
        </div>
      </div>

      {/* Navigation */}

      <div className="mt-8">
        <p className="mb-3 px-4 text-[10px] font-bold uppercase tracking-[.15em] text-[#64748B]">
          Workspace
        </p>

        <nav className="space-y-1">
          {navigation.map(({ label, icon: Icon, key }) => (
            <button
              key={label}
              onClick={() => onSectionChange(key)}
              className={`flex cursor-pointer items-center gap-3 rounded-lg px-4 py-3 text-sm transition-colors ${
                section === key
                  ? "bg-[#42DCC6]/10 font-semibold text-[#42DCC6]"
                  : "text-[#8492A8] hover:bg-white/5 hover:text-[#F1F5F9]"
              }`}
            >
              <Icon size={18} />
              {label}
            </button>
          ))}
        </nav>
      </div>

      {/* System Status */}

      <div className="mt-auto">
        <div className="mb-5 rounded-xl border border-[#253247] bg-[#111A29] p-4">
          <div className="mb-2 flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-[#42DCC6]" />
            <span className="text-xs font-semibold text-[#E2E8F0]">
              System status
            </span>
          </div>

          <p className="text-[11px] leading-relaxed text-[#8492A8]">
            Analytics dashboard is connected.
          </p>
        </div>

        <button
          onClick={onLogout}
          className="flex w-full items-center gap-3 rounded-lg px-4 py-3 text-sm text-[#8492A8] transition-colors hover:bg-red-400/10 hover:text-red-400"
        >
          <LogOut size={18} />
          Sign out
        </button>
      </div>
    </aside>
  );
}

// ----------------------------------
// Main Dashboard
// ----------------------------------

export default function AdminDashboard() {
  const user = currentUser();

  const [summary, setSummary] = useState(null);
  const [daily, setDaily] = useState([]);
  const [activity, setActivity] = useState(null);
  const [pricing, setPricing] = useState([]);
  const [useCaseConfigs, setUseCaseConfigs] = useState([]);
  const [section, setSection] = useState("overview");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    setError("");

    try {
      const [summaryData, timeseriesData] = await Promise.all([
        getAnalyticsSummary(),
        getAnalyticsTimeseries(),
      ]);

      setSummary(summaryData);
      setDaily(timeseriesData.daily || []);
    } catch (requestError) {
      setError(
        requestError.response?.data?.detail ||
        "Unable to load analytics."
      );
    } finally {
      setLoading(false);
    }
  };

  const loadActivity = async () => {
    try {
      setActivity(await getUserActivity());
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Unable to load user activity.");
    }
  };

  const loadPricing = async () => {
    try {
      const [pricingResult, configResult] = await Promise.all([
        getModelPricing(),
        getUseCaseConfigs(),
      ]);
      setPricing(pricingResult.pricing || []);
      setUseCaseConfigs(configResult.configs || []);
    } catch (requestError) {
      setError(requestError.response?.data?.detail || "Unable to load settings.");
    }
  };

  const savePricing = async (payload) => {
    await saveModelPricing(payload);
    await loadPricing();
  };

  const saveConfig = async (payload) => {
    await saveUseCaseConfig(payload);
    await loadPricing();
  };

  useEffect(() => {
    if (user?.is_superuser) {
      load();
      loadActivity();
      loadPricing();
    }
  }, []);

  const maxDaily = useMemo(
    () =>
      Math.max(
        ...daily.map((row) => Number(row.total_tokens || 0)),
        1
      ),
    [daily]
  );

  const logout = () => {
    localStorage.clear();
    window.location.assign("/login");
  };

  if (!localStorage.getItem("accessToken")) {
    return <Navigate to="/login" replace />;
  }

  if (!user?.is_superuser) {
    return <Navigate to="/" replace />;
  }

  return (
    <div className="min-h-screen bg-[#090D18] text-[#F1F5F9]">
      <Sidebar onLogout={logout} section={section} onSectionChange={setSection} />

      <div className="lg:ml-[250px]">
        {/* Header */}

        <header className="sticky top-0 z-10 flex min-h-[76px] items-center justify-between gap-4 border-b border-[#253247] bg-[#0D1422]/95 px-5 py-4 backdrop-blur-xl lg:px-10">
          <div>
            <p className="text-[10px] font-bold uppercase tracking-[.16em] text-[#42DCC6]">
              Operations center
            </p>

            <h1 className="mt-1 text-lg font-bold text-[#F1F5F9] sm:text-xl">
              {section === "users" ? "User Activity" : section === "settings" ? "Settings" : "AI Usage Overview"}
            </h1>
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <p className="text-sm font-medium text-[#E2E8F0]">
                {user.email}
              </p>

              <p className="text-[10px] text-[#8492A8]">
                Superuser
              </p>
            </div>

            <button
              onClick={load}
              disabled={loading}
              className="flex items-center gap-2 rounded-lg bg-[#42DCC6] px-3 py-2.5 text-xs font-bold text-[#09131C] transition-colors hover:bg-[#66E8D5] disabled:cursor-not-allowed disabled:opacity-50 sm:px-4 sm:text-sm"
            >
              <RefreshCw
                size={15}
                className={loading ? "animate-spin" : ""}
              />
              <span className="hidden sm:inline">Refresh</span>
            </button>
          </div>
        </header>

        {/* Main Content */}

        <main className="mx-auto max-w-[1440px] px-5 pb-12 pt-8 lg:px-10">
          {/* Page Introduction */}

          <div className="mb-8 flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-[.12em] text-[#42DCC6]">
                <ShieldCheck size={16} />
                Superuser analytics
              </div>

              <p className="mt-2 text-sm text-[#8492A8]">
                {section === "analytics"
                  ? "Compare model pricing, token usage, providers, and use cases."
                  : "Review overall requests, token usage, latency, and total pricing."}
              </p>
            </div>

            <div className="flex items-center gap-2 rounded-lg border border-[#253247] bg-[#111A29] px-3 py-2">
              <Activity size={15} className="text-[#42DCC6]" />

              <span className="text-xs text-[#A1AEC1]">
                Live analytics
              </span>
            </div>
          </div>

          {error && (
            <div className="mb-6 flex items-center gap-3 rounded-xl border border-red-400/20 bg-red-400/10 px-4 py-4 text-sm text-red-300">
              <AlertTriangle size={19} className="shrink-0" />
              {error}
            </div>
          )}

          {section === "users" ? (
            <UserActivity activity={activity} />
          ) : section === "settings" ? (
            <SettingsPanel pricing={pricing} configs={useCaseConfigs} onSave={savePricing} onSaveConfig={saveConfig} />
          ) : (
          <>
          {/* Loading */}

          {loading && !summary ? (
            <div className="flex min-h-[300px] flex-col items-center justify-center gap-4">
              <RefreshCw
                size={26}
                className="animate-spin text-[#42DCC6]"
              />

              <p className="text-sm text-[#8492A8]">
                Loading analytics...
              </p>
            </div>
          ) : (
            <>
              {section === "overview" ? (
                <div>
                  <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-3">
                  <Metric label="Total requests" value={number(summary?.requests)} icon={Activity} description="Total AI API requests" />
                  <Metric label="Total tokens" value={number(summary?.total_tokens)} icon={Database} description="Combined token consumption" />
                  <Metric label="Total estimated cost" value={currency(summary?.estimated_cost)} icon={TrendingUp} description="Overall provider usage cost" />
                  <Metric label="Input tokens" value={number(summary?.input_tokens)} icon={Zap} description="Tokens sent to AI models" />
                  <Metric label="Output tokens" value={number(summary?.output_tokens)} icon={Cpu} description="Tokens generated by AI models" />
                  <Metric label="Failed requests" value={number(summary?.failed_requests)} icon={AlertTriangle} description="Unsuccessful API requests" danger={Number(summary?.failed_requests || 0) > 0} success={Number(summary?.failed_requests || 0) === 0} />
                  <Metric label="Average latency" value={`${Math.round(summary?.average_response_time_ms || 0)} ms`} icon={Clock3} description="Average response time" />
                  </div>
                  <div className="mt-6">
                    <DailyUsageChart daily={daily} maxDaily={maxDaily} />
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-5 max-[760px]:grid-cols-1">
                  <DailyUsageChart daily={daily} maxDaily={maxDaily} />
                  <Breakdown title="Usage by provider" rows={summary?.by_provider || []} labelKey="provider" icon={Zap} />
                  <Breakdown title="Pricing and usage by model" rows={summary?.by_model || []} labelKey="model" icon={Cpu} showCost />
                  <Breakdown title="Usage by use case" rows={summary?.by_use_case || []} labelKey="use_case" icon={TrendingUp} />
                </div>
              )}
            </>
          )}
          </>
          )}

          {/* Footer */}

          <footer className="mt-10 border-t border-[#253247] pt-5">
            <div className="flex flex-wrap items-center justify-between gap-3 text-xs text-[#64748B]">
              <span>
                AI Interview Helper
              </span>

              <span>
                Administrative dashboard
              </span>
            </div>
          </footer>
        </main>
      </div>
    </div>
  );
}
