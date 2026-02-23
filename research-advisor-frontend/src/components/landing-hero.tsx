interface LandingHeroProps {
  onStart: () => void
}

export function LandingHero({ onStart }: LandingHeroProps) {
  return (
    <section
      className="flex min-h-[70vh] flex-col items-center justify-center px-4 py-16 animate-fade-in"
      data-testid="landing-hero"
    >
      <h1 className="text-center text-3xl font-bold tracking-tight text-slate-900 md:text-4xl">
        Open Thesis Advisor.
      </h1>
      <p className="mt-4 max-w-2xl text-center text-base text-slate-600 md:text-lg">
        Drop your proposal. We’ll tell you if it’s novel, impactful, and worth
        your time.
      </p>
      <button
        onClick={onStart}
        className="mt-8 rounded-xl bg-blue-600 px-6 py-3 font-medium text-white shadow-lg shadow-blue-500/25 transition-all hover:scale-[1.02] hover:bg-blue-700 hover:shadow-xl hover:shadow-blue-500/30"
        data-testid="landing-cta"
      >
        Roast my research
      </button>
      <p className="mt-6 text-center text-sm text-slate-500">
        Powered by OpenAlex · Citations included · No sign-up required
      </p>
    </section>
  )
}
