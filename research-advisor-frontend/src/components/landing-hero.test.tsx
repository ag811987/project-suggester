import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LandingHero } from './landing-hero'

describe('LandingHero', () => {
  it('renders headline', () => {
    render(<LandingHero onStart={vi.fn()} />)
    expect(
      screen.getByRole('heading', { name: /open thesis advisor/i }),
    ).toBeInTheDocument()
  })

  it('renders subheadline', () => {
    render(<LandingHero onStart={vi.fn()} />)
    expect(
      screen.getByText(/drop your proposal/i),
    ).toBeInTheDocument()
  })

  it('renders CTA button', () => {
    render(<LandingHero onStart={vi.fn()} />)
    expect(
      screen.getByRole('button', { name: /roast my research/i }),
    ).toBeInTheDocument()
  })

  it('renders trust line', () => {
    render(<LandingHero onStart={vi.fn()} />)
    expect(screen.getByText(/powered by OpenAlex/i)).toBeInTheDocument()
  })

  it('calls onStart when CTA is clicked', async () => {
    const onStart = vi.fn()
    const user = userEvent.setup()
    render(<LandingHero onStart={onStart} />)

    await user.click(screen.getByRole('button', { name: /roast my research/i }))

    expect(onStart).toHaveBeenCalledTimes(1)
  })

  it('has landing-hero data-testid', () => {
    render(<LandingHero onStart={vi.fn()} />)
    expect(screen.getByTestId('landing-hero')).toBeInTheDocument()
  })

  it('CTA has landing-cta data-testid', () => {
    render(<LandingHero onStart={vi.fn()} />)
    expect(screen.getByTestId('landing-cta')).toBeInTheDocument()
  })
})
