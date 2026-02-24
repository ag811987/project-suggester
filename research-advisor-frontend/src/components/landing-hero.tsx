interface LandingHeroProps {
  onStart: () => void
}

export function LandingHero({ onStart }: LandingHeroProps) {
  return (
    <section
      className="flex min-h-[60vh] flex-col items-center justify-center px-5 py-12 animate-fade-in sm:min-h-[70vh] sm:px-6 sm:py-16"
      data-testid="landing-hero"
    >
      <h1 className="text-center text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl md:text-4xl">
        Open Thesis Advisor.
      </h1>
      <p className="mt-3 max-w-2xl text-center text-sm text-slate-600 sm:mt-4 sm:text-base md:text-lg">
        Drop your proposal. We’ll tell you if it’s novel, impactful, and worth
        your time.
      </p>
      <button
        onClick={onStart}
        className="mt-6 touch-target rounded-xl bg-blue-600 px-8 py-3.5 text-base font-medium text-white shadow-lg shadow-blue-500/25 transition-all hover:scale-[1.02] hover:bg-blue-700 hover:shadow-xl hover:shadow-blue-500/30 active:scale-[0.98] sm:mt-8 sm:px-6 sm:py-3"
        data-testid="landing-cta"
      >
        Roast my research
      </button>
      <p className="mt-5 text-center text-xs text-slate-500 sm:mt-6 sm:text-sm">
        Powered by OpenAlex · Citations included · No sign-up required
      </p>
    </section>
  )
}
