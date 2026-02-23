// TypeScript interfaces matching backend Pydantic models (schemas.py)

export type NoveltyVerdict = 'SOLVED' | 'MARGINAL' | 'NOVEL' | 'UNCERTAIN'
export type ImpactLevel = 'HIGH' | 'MEDIUM' | 'LOW' | 'UNCERTAIN'
export type RecommendationType = 'CONTINUE' | 'PIVOT' | 'UNCERTAIN'
export type MessageRole = 'user' | 'assistant' | 'system'
export type GapMapSource = 'convergent' | 'homeworld' | 'wikenigma' | '3ie' | 'encyclopedia'

export interface Citation {
  title: string
  authors: string[] | null
  doi: string | null
  url: string | null
  year: number | null
  fwci: number | null
}

export interface ChatMessage {
  role: MessageRole
  content: string
}

export interface ResearchProfile {
  research_question: string
  problem_description: string | null
  skills: string[]
  expertise_areas: string[]
  motivations: string[]
  interests: string[]
  extracted_from_files: string[]
}

export interface ResearchDecomposition {
  core_questions: string[]
  core_motivations: string[]
  potential_impact_domains: string[]
  key_concepts: string[]
}

export interface NoveltyAssessment {
  score: number
  verdict: NoveltyVerdict
  evidence: Citation[]
  reasoning: string
  related_papers_count: number
  average_fwci: number | null
  fwci_percentile: number | null
  citation_percentile_min: number | null
  citation_percentile_max: number | null
  impact_assessment: ImpactLevel
  impact_reasoning: string
  expected_impact_assessment: ImpactLevel
  expected_impact_reasoning: string
  research_decomposition?: ResearchDecomposition | null
}

export interface GapMapEntry {
  title: string
  description: string
  source: GapMapSource
  source_url: string
  category: string | null
  tags: string[]
}

export interface PivotSuggestion {
  gap_entry: GapMapEntry
  relevance_score: number
  impact_potential: ImpactLevel
  match_reasoning: string
  feasibility_for_researcher: string
  impact_rationale: string
}

export interface ReportSections {
  novelty_section: string
  impact_section: string
  real_world_impact_section?: string
  pivot_section: string
}

export interface ResearchRecommendation {
  recommendation: RecommendationType
  confidence: number
  narrative_report: string
  report_sections: ReportSections | null
  novelty_assessment: NoveltyAssessment
  pivot_suggestions: PivotSuggestion[]
  evidence_citations: Citation[]
}

// Request/Response types
export interface AnalyzeRequest {
  messages: ChatMessage[]
}

export interface AnalyzeResponse {
  session_id: string
  status: 'processing' | 'completed' | 'error'
}

export interface SessionStatusResponse {
  session_id: string
  status: 'processing' | 'completed' | 'error'
  result: ResearchRecommendation | null
  error_message: string | null
}
