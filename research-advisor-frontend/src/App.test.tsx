import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'

vi.mock('./hooks/useAnalysis', () => ({
  useAnalyzeResearch: () => ({
    mutate: vi.fn(),
    isPending: false,
    error: null,
  }),
  useGetAnalysis: () => ({
    data: null,
    error: null,
  }),
}))

function renderApp() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>,
  )
}

describe('App', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows landing view with hero on initial load', () => {
    renderApp()
    expect(
      screen.getByRole('heading', { name: /open thesis advisor/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /roast my research/i }),
    ).toBeInTheDocument()
  })

  it('transitions to chat view when CTA is clicked', async () => {
    const user = userEvent.setup()
    renderApp()

    await user.click(screen.getByRole('button', { name: /roast my research/i }))

    expect(
      screen.getByText(/we'll ask 3 quick questions to understand your research/i),
    ).toBeInTheDocument()
    expect(
      screen.getByText(
        /what are your research interests/i,
      ),
    ).toBeInTheDocument()
  })

  it('shows Research Pivot Advisor in header on landing', () => {
    renderApp()
    expect(screen.getByText('Research Pivot Advisor')).toBeInTheDocument()
  })
})
