import { cn } from '@/lib/utils'
import type {
  ResearchRecommendation,
  RecommendationType,
  NoveltyAssessment,
  PivotSuggestion,
  Citation,
  ImpactLevel,
  ReportSections,
} from '@/types'

interface ResultsViewProps {
  data: ResearchRecommendation
}

const badgeStyles: Record<RecommendationType, string> = {
  CONTINUE: 'bg-green-100 text-green-800 border-green-300',
  PIVOT: 'bg-amber-100 text-amber-800 border-amber-300',
  UNCERTAIN: 'bg-gray-100 text-gray-800 border-gray-300',
}

const impactStyles: Record<ImpactLevel, string> = {
  HIGH: 'bg-red-100 text-red-700',
  MEDIUM: 'bg-yellow-100 text-yellow-700',
  LOW: 'bg-blue-100 text-blue-700',
  UNCERTAIN: 'bg-gray-100 text-gray-700',
}

const verdictStyles: Record<string, string> = {
  NOVEL: 'bg-green-100 text-green-800 border-green-300',
  MARGINAL: 'bg-yellow-100 text-yellow-800 border-yellow-300',
  SOLVED: 'bg-red-100 text-red-800 border-red-300',
  UNCERTAIN: 'bg-gray-100 text-gray-800 border-gray-300',
}

function RecommendationBadge({ type }: { type: RecommendationType }) {
  return (
    <span
      data-testid="recommendation-badge"
      className={cn(
        'inline-flex items-center rounded-full border px-3 py-1 text-sm font-semibold',
        badgeStyles[type],
      )}
    >
      {type}
    </span>
  )
}

function ImpactBadge({ level }: { level: ImpactLevel }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium',
        impactStyles[level],
      )}
    >
      {level}
    </span>
  )
}

function VerdictBadge({ verdict }: { verdict: string }) {
  return (
    <span
      className={cn(
        'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold',
        verdictStyles[verdict] || verdictStyles.UNCERTAIN,
      )}
    >
      {verdict}
    </span>
  )
}

/* Section 1: Novelty of Your Question */
function NoveltySection({
  assessment,
  sections,
}: {
  assessment: NoveltyAssessment
  sections: ReportSections | null
}) {
  return (
    <div className="rounded-lg border bg-white p-6" data-testid="novelty-section">
      <h3 className="mb-4 text-lg font-semibold">Novelty of Your Question</h3>

      <div className="mb-3 flex items-center gap-3">
        <VerdictBadge verdict={assessment.verdict} />
        <span className="text-sm text-gray-500">
          Score: {(assessment.score * 100).toFixed(0)}%
        </span>
      </div>

      {sections?.novelty_section ? (
        <div
          className="prose prose-sm max-w-none text-gray-700"
          dangerouslySetInnerHTML={{
            __html: renderMarkdown(sections.novelty_section),
          }}
        />
      ) : (
        <p className="mb-4 text-sm text-gray-700">{assessment.reasoning}</p>
      )}

      {/* Related literature when MARGINAL/SOLVED */}
      {(assessment.verdict === 'MARGINAL' || assessment.verdict === 'SOLVED') &&
        assessment.evidence.length > 0 && (
          <div className="mt-4 rounded-md bg-gray-50 p-4">
            <h4 className="mb-2 text-sm font-medium text-gray-700">
              Related Literature
            </h4>
            <ul className="space-y-1">
              {assessment.evidence.slice(0, 5).map((citation, i) => (
                <CitationLink key={i} citation={citation} />
              ))}
            </ul>
          </div>
        )}

      {/* Secondary FWCI metrics */}
      <div className="mt-4 grid grid-cols-2 gap-3 text-sm md:grid-cols-4">
        <div>
          <span className="text-gray-500">Related Papers</span>
          <p className="font-medium">{assessment.related_papers_count}</p>
        </div>
        {assessment.average_fwci != null && (
          <div data-testid="fwci-metric">
            <span className="text-gray-500">Avg FWCI</span>
            <p className="font-medium">{assessment.average_fwci.toFixed(2)}</p>
          </div>
        )}
        {assessment.fwci_percentile != null && (
          <div>
            <span className="text-gray-500">FWCI Percentile</span>
            <p className="font-medium">
              {assessment.fwci_percentile.toFixed(1)}%
            </p>
          </div>
        )}
        {assessment.citation_percentile_min != null &&
          assessment.citation_percentile_max != null && (
            <div>
              <span className="text-gray-500">Citation Range</span>
              <p className="font-medium">
                {assessment.citation_percentile_min}–
                {assessment.citation_percentile_max}
              </p>
            </div>
          )}
      </div>
    </div>
  )
}

/* Section 2: Expected Impact of Your Research */
function ExpectedImpactSection({
  assessment,
  sections,
}: {
  assessment: NoveltyAssessment
  sections: ReportSections | null
}) {
  return (
    <div
      className="rounded-lg border bg-white p-6"
      data-testid="expected-impact-section"
    >
      <h3 className="mb-4 text-lg font-semibold">
        Expected Impact of Your Research
      </h3>

      <div className="mb-3 flex items-center gap-2">
        <span className="text-sm text-gray-500">Expected Impact:</span>
        <ImpactBadge level={assessment.expected_impact_assessment} />
      </div>

      {sections?.impact_section ? (
        <div
          className="prose prose-sm max-w-none text-gray-700"
          dangerouslySetInnerHTML={{
            __html: renderMarkdown(sections.impact_section),
          }}
        />
      ) : (
        <p className="text-sm text-gray-700">
          {assessment.expected_impact_reasoning}
        </p>
      )}

      {/* Field impact as secondary context */}
      <div className="mt-4 rounded-md bg-gray-50 p-3">
        <div className="flex items-center gap-2 text-sm">
          <span className="text-gray-500">Field Impact (from literature):</span>
          <ImpactBadge level={assessment.impact_assessment} />
        </div>
        <p className="mt-1 text-xs text-gray-500">
          {assessment.impact_reasoning}
        </p>
      </div>
    </div>
  )
}

/* Section 3: Pivot Suggestions (only when PIVOT) */
function PivotSection({
  suggestions,
  sections,
}: {
  suggestions: PivotSuggestion[]
  sections: ReportSections | null
}) {
  return (
    <div data-testid="pivot-suggestions">
      <h3 className="mb-4 text-lg font-semibold">Pivot Suggestions</h3>

      {sections?.pivot_section && (
        <div
          className="prose prose-sm mb-4 max-w-none rounded-lg border bg-white p-6 text-gray-700"
          dangerouslySetInnerHTML={{
            __html: renderMarkdown(sections.pivot_section),
          }}
        />
      )}

      {suggestions.length > 0 && (
        <div className="space-y-4">
          {suggestions.map((suggestion, i) => (
            <PivotCard key={i} suggestion={suggestion} />
          ))}
        </div>
      )}
    </div>
  )
}

function PivotCard({ suggestion }: { suggestion: PivotSuggestion }) {
  return (
    <div className="rounded-lg border bg-white p-5" data-testid="pivot-card">
      <div className="mb-2 flex items-start justify-between">
        <h4 className="font-semibold">{suggestion.gap_entry.title}</h4>
        <ImpactBadge level={suggestion.impact_potential} />
      </div>
      <p className="mb-3 text-sm text-gray-600">
        {suggestion.gap_entry.description}
      </p>
      <div className="mb-2 flex items-center gap-2 text-xs text-gray-500">
        <span className="rounded bg-gray-100 px-2 py-0.5">
          {suggestion.gap_entry.source}
        </span>
        <span>
          Relevance: {(suggestion.relevance_score * 100).toFixed(0)}%
        </span>
      </div>
      <div className="space-y-2 text-sm">
        <div>
          <span className="font-medium text-gray-700">Why this matches: </span>
          <span className="text-gray-600">{suggestion.match_reasoning}</span>
        </div>
        <div>
          <span className="font-medium text-gray-700">Feasibility: </span>
          <span className="text-gray-600">
            {suggestion.feasibility_for_researcher}
          </span>
        </div>
        <div>
          <span className="font-medium text-gray-700">Impact: </span>
          <span className="text-gray-600">{suggestion.impact_rationale}</span>
        </div>
      </div>
      {suggestion.gap_entry.source_url && (
        <a
          href={suggestion.gap_entry.source_url}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-block text-sm text-blue-600 hover:underline"
        >
          View source
        </a>
      )}
    </div>
  )
}

function CitationLink({ citation }: { citation: Citation }) {
  const display = `${citation.title}${citation.year ? ` (${citation.year})` : ''}`
  return (
    <li className="text-sm" data-testid="citation-item">
      {citation.url || citation.doi ? (
        <a
          href={citation.url ?? `https://doi.org/${citation.doi}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline"
        >
          {display}
        </a>
      ) : (
        <span>{display}</span>
      )}
      {citation.fwci != null && (
        <span className="ml-2 text-xs text-gray-500">
          FWCI: {citation.fwci.toFixed(2)}
        </span>
      )}
    </li>
  )
}

export function ResultsView({ data }: ResultsViewProps) {
  const sections = data.report_sections ?? null
  const showPivot =
    data.recommendation === 'PIVOT' &&
    (data.pivot_suggestions.length > 0 || sections?.pivot_section)

  return (
    <div className="space-y-6" data-testid="results-view">
      {/* Recommendation badge at top */}
      <div className="rounded-lg border bg-white p-6">
        <div className="flex items-center justify-between">
          <h2 className="text-xl font-bold">Research Analysis</h2>
          <RecommendationBadge type={data.recommendation} />
        </div>
        <p className="mt-1 text-sm text-gray-500">
          Confidence: {(data.confidence * 100).toFixed(0)}%
        </p>
      </div>

      {/* Section 1: Novelty */}
      <NoveltySection assessment={data.novelty_assessment} sections={sections} />

      {/* Section 2: Expected Impact */}
      <ExpectedImpactSection
        assessment={data.novelty_assessment}
        sections={sections}
      />

      {/* Section 3: Pivot Suggestions (only when PIVOT) */}
      {showPivot && (
        <PivotSection suggestions={data.pivot_suggestions} sections={sections} />
      )}

      {/* References */}
      {data.evidence_citations.length > 0 && (
        <div
          className="rounded-lg border bg-white p-6"
          data-testid="citations-section"
        >
          <h3 className="mb-3 text-lg font-semibold">References</h3>
          <ul className="space-y-2">
            {data.evidence_citations.map((citation, i) => (
              <CitationLink key={i} citation={citation} />
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

/**
 * Basic markdown to HTML conversion for narrative reports.
 * Handles headings, bold, italic, links, lists, and paragraphs.
 */
function renderMarkdown(md: string): string {
  return md
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    .replace(
      /\[([^\]]+)\]\(([^)]+)\)/g,
      '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>',
    )
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
    .replace(/\n\n/g, '</p><p>')
    .replace(/^(?!<[h|p|u|o|l])/, '<p>')
    .replace(/$/, '</p>')
}
