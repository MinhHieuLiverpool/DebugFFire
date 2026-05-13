import { Outlet } from 'react-router-dom'

const AppLayout = () => (
  <div className="min-h-screen bg-ink font-body text-white">
    <div className="relative overflow-hidden">
      <div className="pointer-events-none absolute -left-32 top-0 h-72 w-72 rounded-full bg-magenta/50 blur-[140px]" />
      <div className="pointer-events-none absolute right-0 top-24 h-80 w-80 rounded-full bg-electric/40 blur-[160px]" />

      <div className="mx-auto flex max-w-6xl flex-col gap-10 px-6 py-10">
        <header className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <p className="text-xs uppercase tracking-[0.5em] text-white/50">Zone Tracker</p>
            <h1 className="font-display text-2xl font-semibold text-white md:text-3xl">
              Free Fire Zone Analyzer
            </h1>
          </div>
          <nav className="flex items-center gap-3 text-xs uppercase tracking-[0.3em] text-white/60">
            <span className="rounded-full border border-white/10 px-3 py-1">Analyzer</span>
          </nav>
        </header>

        <Outlet />
      </div>
    </div>
  </div>
)

export default AppLayout
