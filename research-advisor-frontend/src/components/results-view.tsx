import { useState } from 'react'
import { Link, Check } from 'lucide-react'
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
  sessionId: string
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
        'inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold sm:px-3 sm:py-1 sm:text-sm',
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

/* Final Verdict -- appears at the very top of results */
function VerdictSection({
  sections,
  recommendation,
}: {
  sections: ReportSections | null
  recommendation: RecommendationType
}) {
  const content = sections?.verdict_section
  if (!content) return null

  const borderColor = {
    CONTINUE: 'border-l-green-500',
    PIVOT: 'border-l-amber-500',
    UNCERTAIN: 'border-l-gray-400',
  }[recommendation]

  return (
    <div
      className={cn(
        'rounded-lg border border-l-4 bg-white p-4 sm:p-6',
        borderColor,
      )}
      data-testid="verdict-section"
    >
      <h3 className="mb-2 text-base font-semibold sm:text-lg">
        Final Verdict
      </h3>
      <div
        className="prose prose-sm max-w-none text-gray-700"
        dangerouslySetInnerHTML={{
          __html: renderMarkdown(content),
        }}
      />
    </div>
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
    <div className="rounded-lg border bg-white p-4 sm:p-6" data-testid="novelty-section">
      <h3 className="mb-3 text-base font-semibold sm:mb-4 sm:text-lg">Novelty of Your Question</h3>

      <div className="mb-3 flex flex-wrap items-center gap-2 sm:gap-3">
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
          <div className="mt-4 rounded-md bg-gray-50 p-3 sm:p-4">
            <h4 className="mb-2 text-sm font-medium text-gray-700">
              Related Literature
            </h4>
            <ul className="space-y-1.5 sm:space-y-1">
              {assessment.evidence.slice(0, 5).map((citation, i) => (
                <CitationLink key={i} citation={citation} />
              ))}
            </ul>
          </div>
        )}

      {/* Secondary FWCI metrics */}
      <div className="mt-4 grid grid-cols-2 gap-2 text-sm sm:gap-3 md:grid-cols-4">
        <div>
          <span className="text-xs text-gray-500 sm:text-sm">Related Papers</span>
          <p className="font-medium">{assessment.related_papers_count}</p>
        </div>
        {assessment.average_fwci != null && (
          <div data-testid="fwci-metric">
            <span className="text-xs text-gray-500 sm:text-sm">Avg FWCI</span>
            <p className="font-medium">{assessment.average_fwci.toFixed(2)}</p>
          </div>
        )}
        {assessment.fwci_percentile != null && (
          <div>
            <span className="text-xs text-gray-500 sm:text-sm">FWCI Percentile</span>
            <p className="font-medium">
              {assessment.fwci_percentile.toFixed(1)}%
            </p>
          </div>
        )}
        {assessment.citation_percentile_min != null &&
          assessment.citation_percentile_max != null && (
            <div>
              <span className="text-xs text-gray-500 sm:text-sm">Citation Range</span>
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

/* Section 2: Impact on the field */
function ExpectedImpactSection({
  assessment,
  sections,
}: {
  assessment: NoveltyAssessment
  sections: ReportSections | null
}) {
  return (
    <div
      className="rounded-lg border bg-white p-4 sm:p-6"
      data-testid="expected-impact-section"
    >
      <h3 className="mb-3 text-base font-semibold sm:mb-4 sm:text-lg">
        Impact on the field
      </h3>
      <p className="mb-3 text-sm text-gray-500">
        How this research affects the discipline, methods, or tools
      </p>

      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="text-sm text-gray-500">Impact on the field:</span>
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
        <div className="flex flex-wrap items-center gap-2 text-sm">
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

/* Section 3: Global impact */
function RealWorldImpactSection({
  sections,
  assessment,
}: {
  sections: ReportSections | null
  assessment: NoveltyAssessment
}) {
  const content = sections?.real_world_impact_section
  if (!content) return null

  return (
    <div
      className="rounded-lg border bg-white p-4 sm:p-6"
      data-testid="real-world-impact-section"
    >
      <h3 className="mb-3 text-base font-semibold sm:mb-4 sm:text-lg">
        Global impact
      </h3>
      <p className="mb-3 text-sm text-gray-500">
        Effect on society, policy, and population
      </p>

      {assessment.real_world_impact_assessment && (
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <span className="text-sm text-gray-500">Global impact:</span>
          <ImpactBadge level={assessment.real_world_impact_assessment} />
        </div>
      )}

      <div
        className="prose prose-sm max-w-none text-gray-700"
        dangerouslySetInnerHTML={{
          __html: renderMarkdown(content),
        }}
      />
    </div>
  )
}

/* Section 4: Pivot Suggestions / Alternative Direction */
function PivotSection({
  suggestions,
  sections,
  recommendation,
}: {
  suggestions: PivotSuggestion[]
  sections: ReportSections | null
  recommendation: RecommendationType
}) {
  const heading =
    recommendation === 'PIVOT' ? 'Pivot Suggestions' : 'Alternative Direction'

  return (
    <div data-testid="pivot-suggestions">
      <h3 className="mb-3 text-base font-semibold sm:mb-4 sm:text-lg">{heading}</h3>

      {suggestions.length > 0 ? (
        <div className="space-y-3 sm:space-y-4">
          {suggestions.map((suggestion, i) => (
            <PivotCard key={i} suggestion={suggestion} />
          ))}
        </div>
      ) : (
        sections?.pivot_section && (
          <div
            className="prose prose-sm max-w-none text-sm text-gray-600"
            dangerouslySetInnerHTML={{
              __html: renderMarkdown(sections.pivot_section),
            }}
          />
        )
      )}
    </div>
  )
}

function PivotCard({ suggestion }: { suggestion: PivotSuggestion }) {
  return (
    <div className="rounded-lg border bg-white p-4 sm:p-5" data-testid="pivot-card">
      <div className="mb-2 flex items-start justify-between gap-2">
        <h4 className="text-sm font-semibold sm:text-base">{suggestion.gap_entry.title}</h4>
        <ImpactBadge level={suggestion.impact_potential} />
      </div>
      <p className="mb-3 text-sm text-gray-600">
        {suggestion.gap_entry.description}
      </p>
      <div className="mb-2 flex flex-wrap items-center gap-2 text-xs text-gray-500">
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
          className="mt-3 inline-flex touch-target items-center text-sm text-blue-600 hover:underline active:text-blue-800"
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
    <li className="text-sm leading-relaxed" data-testid="citation-item">
      {citation.url || citation.doi ? (
        <a
          href={citation.url ?? `https://doi.org/${citation.doi}`}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-600 hover:underline active:text-blue-800"
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

function XIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z" />
    </svg>
  )
}

function FacebookIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
    </svg>
  )
}

function LinkedInIcon() {
  return (
    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
      <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433a2.062 2.062 0 01-2.063-2.065 2.064 2.064 0 112.063 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z" />
    </svg>
  )
}

function ShareBar({ data, sessionId }: { data: ResearchRecommendation; sessionId: string }) {
  const [copied, setCopied] = useState(false)

  const shareUrl = `${window.location.origin}${window.location.pathname}?session=${sessionId}`
  const shareText = `I analyzed my research with Research Pivot Advisor \u2014 verdict: ${data.novelty_assessment.verdict}, recommendation: ${data.recommendation}. Check it out!`

  const shareLinks = {
    x: `https://x.com/intent/tweet?text=${encodeURIComponent(shareText)}&url=${encodeURIComponent(shareUrl)}`,
    facebook: `https://www.facebook.com/sharer/sharer.php?u=${encodeURIComponent(shareUrl)}`,
    linkedin: `https://www.linkedin.com/sharing/share-offsite/?url=${encodeURIComponent(shareUrl)}`,
  }

  // Use native share sheet on mobile (iOS/Android)
  const handleNativeShare = async () => {
    if (navigator.share) {
      try {
        await navigator.share({
          title: 'Research Analysis Results',
          text: shareText,
          url: shareUrl,
        })
        return
      } catch {
        // User cancelled — do nothing
      }
    }
  }

  const handleCopyLink = async () => {
    await navigator.clipboard.writeText(shareUrl)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const supportsNativeShare = typeof navigator !== 'undefined' && !!navigator.share

  return (
    <div className="flex flex-wrap items-center gap-1 sm:gap-1.5">
      <span className="mr-0.5 text-xs text-gray-500 sm:text-sm">Share:</span>

      {/* Native share button — shown on mobile devices that support Web Share API */}
      {supportsNativeShare && (
        <button
          onClick={handleNativeShare}
          className="touch-target flex items-center gap-1 rounded-lg p-2 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-700 active:bg-gray-200"
          aria-label="Share via system share sheet"
        >
          <NativeShareIcon />
          <span className="text-xs sm:hidden">Share</span>
        </button>
      )}

      {/* Social share links — hidden on small screens when native share is available */}
      <div className={cn(
        'flex items-center gap-0.5',
        supportsNativeShare ? 'hidden sm:flex' : 'flex',
      )}>
        <a
          href={shareLinks.x}
          target="_blank"
          rel="noopener noreferrer"
          className="touch-target flex items-center justify-center rounded-lg p-2 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-700 active:bg-gray-200"
          aria-label="Share on X"
        >
          <XIcon />
        </a>
        <a
          href={shareLinks.facebook}
          target="_blank"
          rel="noopener noreferrer"
          className="touch-target flex items-center justify-center rounded-lg p-2 text-gray-400 transition-colors hover:bg-blue-50 hover:text-blue-600 active:bg-blue-100"
          aria-label="Share on Facebook"
        >
          <FacebookIcon />
        </a>
        <a
          href={shareLinks.linkedin}
          target="_blank"
          rel="noopener noreferrer"
          className="touch-target flex items-center justify-center rounded-lg p-2 text-gray-400 transition-colors hover:bg-blue-50 hover:text-blue-700 active:bg-blue-100"
          aria-label="Share on LinkedIn"
        >
          <LinkedInIcon />
        </a>
      </div>

      <button
        onClick={handleCopyLink}
        className="touch-target flex items-center gap-1 rounded-lg px-2 py-1.5 text-xs text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-700 active:bg-gray-200 sm:gap-1.5 sm:px-2.5 sm:text-sm"
      >
        {copied ? <Check size={16} /> : <Link size={16} />}
        <span className="hidden sm:inline">{copied ? 'Copied!' : 'Copy link'}</span>
        <span className="sm:hidden">{copied ? 'Copied!' : 'Copy'}</span>
      </button>
    </div>
  )
}

function NativeShareIcon() {
  return (
    <svg
      className="h-4 w-4"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
      />
    </svg>
  )
}

export function ResultsView({ data, sessionId }: ResultsViewProps) {
  const sections = data.report_sections ?? null
  const showPivot =
    data.pivot_suggestions.length > 0 || !!sections?.pivot_section

  return (
    <div className="space-y-4 sm:space-y-6" data-testid="results-view">
      {/* Recommendation badge + share at top */}
      <div className="rounded-lg border bg-white p-4 sm:p-6">
        <div className="flex items-start justify-between gap-2">
          <div className="min-w-0">
            <h2 className="text-lg font-bold sm:text-xl">Research Analysis</h2>
            <p className="mt-1 text-sm text-gray-500">
              Confidence: {(data.confidence * 100).toFixed(0)}%
            </p>
          </div>
          <RecommendationBadge type={data.recommendation} />
        </div>
        <div className="mt-3 border-t pt-3">
          <ShareBar data={data} sessionId={sessionId} />
        </div>
      </div>

      {/* Final Verdict -- top of report */}
      <VerdictSection sections={sections} recommendation={data.recommendation} />

      {/* Section 1: Novelty */}
      <NoveltySection assessment={data.novelty_assessment} sections={sections} />

      {/* Section 2: Expected Impact */}
      <ExpectedImpactSection
        assessment={data.novelty_assessment}
        sections={sections}
      />

      {/* Section 3: Real-World Impact */}
      <RealWorldImpactSection sections={sections} assessment={data.novelty_assessment} />

      {/* Section 4: Pivot Suggestions / Alternative Direction */}
      {showPivot && (
        <PivotSection
          suggestions={data.pivot_suggestions}
          sections={sections}
          recommendation={data.recommendation}
        />
      )}

      {/* References */}
      {data.evidence_citations.length > 0 && (
        <div
          className="rounded-lg border bg-white p-4 sm:p-6"
          data-testid="citations-section"
        >
          <h3 className="mb-3 text-base font-semibold sm:text-lg">References</h3>
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
