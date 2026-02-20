import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import { ResultsView } from './results-view'
import type { ResearchRecommendation } from '@/types'

const mockRecommendation: ResearchRecommendation = {
  recommendation: 'CONTINUE',
  confidence: 0.85,
  narrative_report:
    '# Analysis\n\nYour research on **quantum computing** shows strong novelty.',
  report_sections: null,
  novelty_assessment: {
    score: 0.78,
    verdict: 'NOVEL',
    evidence: [
      {
        title: 'Quantum Advances 2024',
        authors: ['Smith, J.', 'Lee, K.'],
        doi: '10.1234/qa2024',
        url: 'https://example.com/paper1',
        year: 2024,
        fwci: 2.5,
      },
    ],
    reasoning:
      'The research question addresses a gap in quantum error correction.',
    related_papers_count: 42,
    average_fwci: 1.85,
    fwci_percentile: 82.5,
    citation_percentile_min: 65,
    citation_percentile_max: 95,
    impact_assessment: 'HIGH',
    impact_reasoning:
      'High FWCI indicates strong impact potential in this research area.',
    expected_impact_assessment: 'HIGH',
    expected_impact_reasoning:
      'The researcher has strong skills and the field has room for novel contributions.',
  },
  pivot_suggestions: [
    {
      gap_entry: {
        title: 'Topological Quantum Codes',
        description:
          'Research gap in topological approaches to quantum error correction.',
        source: 'convergent',
        source_url: 'https://example.com/gap1',
        category: 'Quantum Computing',
        tags: ['quantum', 'topology', 'error-correction'],
      },
      relevance_score: 0.92,
      impact_potential: 'HIGH',
      match_reasoning:
        'Your skills in quantum computing align well with this gap.',
      feasibility_for_researcher:
        'High feasibility given your background in error correction.',
      impact_rationale:
        'This gap represents a high-impact opportunity due to growing industry interest.',
    },
  ],
  evidence_citations: [
    {
      title: 'Quantum Advances 2024',
      authors: ['Smith, J.', 'Lee, K.'],
      doi: '10.1234/qa2024',
      url: 'https://example.com/paper1',
      year: 2024,
      fwci: 2.5,
    },
    {
      title: 'Error Correction Survey',
      authors: null,
      doi: null,
      url: null,
      year: 2023,
      fwci: null,
    },
  ],
}

describe('ResultsView', () => {
  it('renders the results view container', () => {
    render(<ResultsView data={mockRecommendation} />)
    expect(screen.getByTestId('results-view')).toBeInTheDocument()
  })

  it('displays the recommendation badge with correct type', () => {
    render(<ResultsView data={mockRecommendation} />)
    const badge = screen.getByTestId('recommendation-badge')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveTextContent('CONTINUE')
  })

  it('shows confidence percentage', () => {
    render(<ResultsView data={mockRecommendation} />)
    expect(screen.getByText('Confidence: 85%')).toBeInTheDocument()
  })

  it('displays novelty assessment section', () => {
    render(<ResultsView data={mockRecommendation} />)
    const section = screen.getByTestId('novelty-section')
    expect(section).toBeInTheDocument()
    expect(section).toHaveTextContent('NOVEL')
    expect(section).toHaveTextContent('78%')
  })

  it('shows FWCI metrics', () => {
    render(<ResultsView data={mockRecommendation} />)
    const fwci = screen.getByTestId('fwci-metric')
    expect(fwci).toBeInTheDocument()
    expect(fwci).toHaveTextContent('1.85')
  })

  it('displays related papers count', () => {
    render(<ResultsView data={mockRecommendation} />)
    expect(screen.getByText('42')).toBeInTheDocument()
  })

  it('displays expected impact section', () => {
    render(<ResultsView data={mockRecommendation} />)
    const section = screen.getByTestId('expected-impact-section')
    expect(section).toBeInTheDocument()
    expect(section).toHaveTextContent('Expected Impact')
  })

  it('shows field impact as secondary context', () => {
    render(<ResultsView data={mockRecommendation} />)
    expect(
      screen.getByText(
        'High FWCI indicates strong impact potential in this research area.',
      ),
    ).toBeInTheDocument()
  })

  it('does not show pivot suggestions for CONTINUE recommendation', () => {
    render(<ResultsView data={mockRecommendation} />)
    expect(screen.queryByTestId('pivot-suggestions')).not.toBeInTheDocument()
  })

  it('displays evidence citations with links', () => {
    render(<ResultsView data={mockRecommendation} />)
    const citations = screen.getAllByTestId('citation-item')
    expect(citations).toHaveLength(2)

    const firstCitation = screen.getByText('Quantum Advances 2024 (2024)')
    expect(firstCitation.closest('a')).toHaveAttribute(
      'href',
      'https://example.com/paper1',
    )
  })

  it('renders citation without link when no url/doi', () => {
    render(<ResultsView data={mockRecommendation} />)
    const noLinkCitation = screen.getByText('Error Correction Survey (2023)')
    expect(noLinkCitation.tagName).toBe('SPAN')
  })

  it('shows FWCI on citations when available', () => {
    render(<ResultsView data={mockRecommendation} />)
    expect(screen.getByText('FWCI: 2.50')).toBeInTheDocument()
  })

  describe('with PIVOT recommendation', () => {
    it('displays PIVOT badge and pivot suggestions', () => {
      const pivotData: ResearchRecommendation = {
        ...mockRecommendation,
        recommendation: 'PIVOT',
      }
      render(<ResultsView data={pivotData} />)
      expect(screen.getByTestId('recommendation-badge')).toHaveTextContent(
        'PIVOT',
      )
      const cards = screen.getAllByTestId('pivot-card')
      expect(cards).toHaveLength(1)
      expect(cards[0]).toHaveTextContent('Topological Quantum Codes')
    })

    it('shows pivot suggestion details', () => {
      const pivotData: ResearchRecommendation = {
        ...mockRecommendation,
        recommendation: 'PIVOT',
      }
      render(<ResultsView data={pivotData} />)
      expect(
        screen.getByText(
          'Research gap in topological approaches to quantum error correction.',
        ),
      ).toBeInTheDocument()
      const card = screen.getByTestId('pivot-card')
      expect(card).toHaveTextContent('Relevance:')
      expect(card).toHaveTextContent('92')
    })

    it('renders pivot suggestion source link', () => {
      const pivotData: ResearchRecommendation = {
        ...mockRecommendation,
        recommendation: 'PIVOT',
      }
      render(<ResultsView data={pivotData} />)
      const link = screen.getByText('View source')
      expect(link).toHaveAttribute('href', 'https://example.com/gap1')
      expect(link).toHaveAttribute('target', '_blank')
    })
  })

  describe('with UNCERTAIN recommendation', () => {
    it('displays UNCERTAIN badge', () => {
      const uncertainData: ResearchRecommendation = {
        ...mockRecommendation,
        recommendation: 'UNCERTAIN',
      }
      render(<ResultsView data={uncertainData} />)
      expect(screen.getByTestId('recommendation-badge')).toHaveTextContent(
        'UNCERTAIN',
      )
    })
  })

  describe('with no pivot suggestions and PIVOT', () => {
    it('does not render pivot cards but shows pivot section', () => {
      const noPivotData: ResearchRecommendation = {
        ...mockRecommendation,
        recommendation: 'PIVOT',
        pivot_suggestions: [],
      }
      render(<ResultsView data={noPivotData} />)
      expect(screen.queryByTestId('pivot-card')).not.toBeInTheDocument()
    })
  })

  describe('with no citations', () => {
    it('does not render citations section', () => {
      const noCitationsData: ResearchRecommendation = {
        ...mockRecommendation,
        evidence_citations: [],
      }
      render(<ResultsView data={noCitationsData} />)
      expect(
        screen.queryByTestId('citations-section'),
      ).not.toBeInTheDocument()
    })
  })

  describe('with null FWCI metrics', () => {
    it('does not render FWCI metric when null', () => {
      const noFwciData: ResearchRecommendation = {
        ...mockRecommendation,
        novelty_assessment: {
          ...mockRecommendation.novelty_assessment,
          average_fwci: null,
          fwci_percentile: null,
          citation_percentile_min: null,
          citation_percentile_max: null,
        },
      }
      render(<ResultsView data={noFwciData} />)
      expect(screen.queryByTestId('fwci-metric')).not.toBeInTheDocument()
    })
  })
})
