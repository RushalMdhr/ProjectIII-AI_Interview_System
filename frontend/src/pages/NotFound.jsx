import { Link, useLocation } from "react-router-dom";

export default function NotFound() {
  const location = useLocation();
  const isAdminRoute = location.pathname.startsWith("/admin");

  return (
    <section className={`relative grid min-h-screen place-items-center overflow-hidden px-6 py-16 text-center text-[#FBFAFF] ${isAdminRoute ? "bg-[#090D18]" : "bg-[#191C36]"}`}>
      <div className="pointer-events-none absolute -left-24 top-16 h-48 w-48 rounded-full bg-[#45E0D0]/10 blur-3xl" />

      <div className="relative max-w-lg">
        <div className="mx-auto mb-6 flex h-20 w-20 rotate-[-6deg] items-center justify-center rounded-2xl border border-[#45E0D0]/30 bg-[#202449] text-3xl font-bold text-[#45E0D0] shadow-2xl shadow-[#45E0D0]/10">
          404
        </div>

        <p className="mb-3 text-xs font-bold uppercase tracking-[0.2em] text-[#45E0D0]">
          Navigation hiccup
        </p>
        <h1 className="text-4xl font-bold tracking-tight sm:text-5xl">
          This page took a wrong turn.
        </h1>
        <p className="mx-auto mt-5 max-w-md text-sm leading-7 text-[#C2C4EC] sm:text-base">
          We checked the usual places, but this address is not on the map. Even our AI helper is pretending it knows where it went.
        </p>

        <Link
          to="/"
          className="mt-8 inline-flex items-center rounded-xl bg-[#45E0D0] px-5 py-3 text-sm font-bold text-[#191C36] shadow-lg shadow-[#45E0D0]/20 transition hover:-translate-y-0.5 hover:bg-[#6BE9DC]"
        >
          Take me home
        </Link>
      </div>
    </section>
  );
}
