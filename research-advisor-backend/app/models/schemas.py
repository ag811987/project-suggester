"""
Pydantic schemas for the Research Pivot Advisor System.

This module contains all data validation and serialization models used
throughout the application, following Pydantic V2 syntax.
"""

from typing import Literal
from pydantic import BaseModel, Field


# Supporting Enums and Types
NoveltyVerdict = Literal["SOLVED", "MARGINAL", "NOVEL", "UNCERTAIN"]
ImpactLevel = Literal["HIGH", "MEDIUM", "LOW", "UNCERTAIN"]
RecommendationType = Literal["CONTINUE", "PIVOT", "UNCERTAIN"]
MessageRole = Literal["user", "assistant", "system"]
GapMapSource = Literal["convergent", "homeworld", "wikenigma", "3ie", "encyclopedia"]


class Citation(BaseModel):
    """
    Citation for a research paper or source.

    Used in novelty assessments and recommendations to provide
    evidence and references.
    """
    title: str = Field(..., description="Title of the cited work")
    authors: list[str] | None = Field(default=None, description="List of authors")
    doi: str | None = Field(default=None, description="Digital Object Identifier")
    url: str | None = Field(default=None, description="URL to the source")
    year: int | None = Field(default=None, description="Publication year")
    fwci: float | None = Field(default=None, description="Field Weighted Citation Impact score")


class ChatMessage(BaseModel):
    """
    A message in the chat conversation.

    Compatible with OpenAI's chat message format for easy LLM integration.
    """
    role: MessageRole = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")


class ResearchDecomposition(BaseModel):
    """
    Decomposition of a research problem for novelty analysis.

    Extracted before OpenAlex query to understand core questions,
    motivations, and impact domains for better literature evaluation.
    """
    core_questions: list[str] = Field(
        default_factory=list,
        description="1-3 fundamental questions the research aims to answer"
    )
    core_motivations: list[str] = Field(
        default_factory=list,
        description="What drives this research (e.g., fundamental understanding, practical impact)"
    )
    potential_impact_domains: list[str] = Field(
        default_factory=list,
        description="Who/what benefits if this succeeds (e.g., clinicians, policy, basic science)"
    )
    key_concepts: list[str] = Field(
        default_factory=list,
        description="Key concepts/terms for search and similarity checks"
    )


class ResearchProfile(BaseModel):
    """
    Structured profile extracted from user input.

    This profile is built from chat messages and uploaded files to understand
    the researcher's background, interests, and current research direction.
    """
    research_question: str = Field(
        ...,
        description="The primary research question or problem the researcher is investigating"
    )
    problem_description: str | None = Field(
        default=None,
        description="Detailed description of the research problem or context"
    )
    skills: list[str] = Field(
        default_factory=list,
        description="Technical and research skills possessed by the researcher"
    )
    expertise_areas: list[str] = Field(
        default_factory=list,
        description="Domains or fields where the researcher has expertise"
    )
    motivations: list[str] = Field(
        default_factory=list,
        description="What drives the researcher's interest in this topic"
    )
    interests: list[str] = Field(
        default_factory=list,
        description="Broader research interests beyond the current question"
    )
    extracted_from_files: list[str] = Field(
        default_factory=list,
        description="Names of files used to build this profile"
    )


class NoveltyAssessment(BaseModel):
    """
    Novelty and impact analysis results.

    Determines whether the research question is already solved, marginal,
    or truly novel, using literature analysis and FWCI metrics.
    """
    score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Novelty score: 0.0 (solved/marginal) to 1.0 (novel)"
    )
    verdict: NoveltyVerdict = Field(
        ...,
        description="Categorical verdict on the novelty of the research"
    )
    evidence: list[Citation] = Field(
        default_factory=list,
        description="Citations of papers supporting the novelty assessment"
    )
    reasoning: str = Field(
        ...,
        description="Explanation of why this verdict was reached"
    )
    related_papers_count: int = Field(
        ...,
        ge=0,
        description="Number of related papers found in the literature"
    )

    # Impact metrics from OpenAlex FWCI
    average_fwci: float | None = Field(
        default=None,
        description="Average Field Weighted Citation Impact of related papers"
    )
    fwci_percentile: float | None = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Percentile of FWCI distribution"
    )
    citation_percentile_min: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Minimum citation percentile from cited_by_percentile_year"
    )
    citation_percentile_max: int | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Maximum citation percentile from cited_by_percentile_year"
    )
    # Literature/field impact (from FWCI of related papers)
    impact_assessment: ImpactLevel = Field(
        ...,
        description="Impact of existing literature in the field (from FWCI of related papers)"
    )
    impact_reasoning: str = Field(
        ...,
        description="Explanation of the field/literature impact based on FWCI and citations"
    )

    # Expected impact of THIS research if it goes through
    expected_impact_assessment: ImpactLevel = Field(
        ...,
        description="Predicted impact of the researcher's work if completed"
    )
    expected_impact_reasoning: str = Field(
        ...,
        description="Explanation of why we expect this impact for the researcher's work"
    )

    # Optional: research decomposition for traceability
    research_decomposition: ResearchDecomposition | None = Field(
        default=None,
        description="Decomposition of the research problem used for analysis"
    )


class GapMapEntry(BaseModel):
    """
    Normalized gap map entry from any source.

    Represents an identified research gap or unsolved problem from one of
    the gap map databases (Convergent, Homeworld, Wikenigma, etc.).
    """
    title: str = Field(..., description="Title of the research gap or problem")
    description: str = Field(..., description="Detailed description of the gap")
    source: GapMapSource = Field(..., description="Source database where this gap was found")
    source_url: str = Field(..., description="URL to the original entry")
    category: str | None = Field(default=None, description="Category or domain of the gap")
    tags: list[str] = Field(
        default_factory=list,
        description="Tags or keywords associated with this gap"
    )


class PivotSuggestion(BaseModel):
    """
    Suggested research pivot.

    A potential alternative research direction that better aligns with the
    researcher's skills and has higher impact potential.
    """
    gap_entry: GapMapEntry = Field(..., description="The gap map entry being suggested")
    relevance_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How well this gap matches the researcher's profile (0.0-1.0)"
    )
    impact_potential: ImpactLevel = Field(
        ...,
        description="Estimated impact potential of working on this gap"
    )
    match_reasoning: str = Field(
        ...,
        description="Why this gap matches the researcher's skills and motivations"
    )
    feasibility_for_researcher: str = Field(
        ...,
        description="Assessment of how feasible it is for this researcher to pivot to this gap"
    )
    impact_rationale: str = Field(
        ...,
        description="Why this problem has higher impact potential than the current research"
    )


class ReportSections(BaseModel):
    """Structured report sections returned from the LLM."""
    novelty_section: str = Field(
        ...,
        description="Markdown section analyzing whether the question is novel, marginal, or solved"
    )
    impact_section: str = Field(
        ...,
        description="Markdown section analyzing the expected impact of this research"
    )
    pivot_section: str = Field(
        default="",
        description="Markdown section with pivot suggestions (empty when not PIVOT)"
    )


class ResearchRecommendation(BaseModel):
    """
    Final recommendation report.

    The complete analysis including novelty assessment, recommendation,
    and potential pivot suggestions.
    """
    recommendation: RecommendationType = Field(
        ...,
        description="The primary recommendation: continue, pivot, or uncertain"
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence level in the recommendation (0.0-1.0)"
    )
    narrative_report: str = Field(
        ...,
        description="Detailed markdown-formatted report explaining the analysis and recommendation"
    )
    report_sections: ReportSections | None = Field(
        default=None,
        description="Structured report sections for frontend rendering"
    )
    novelty_assessment: NoveltyAssessment = Field(
        ...,
        description="The novelty and impact analysis results"
    )
    pivot_suggestions: list[PivotSuggestion] = Field(
        default_factory=list,
        description="Suggested alternative research directions (empty if CONTINUE recommended)"
    )
    evidence_citations: list[Citation] = Field(
        default_factory=list,
        description="All citations referenced in the report"
    )


# Request/Response Models for API
class AnalyzeRequest(BaseModel):
    """Request body for the /analyze endpoint."""
    messages: list[ChatMessage] = Field(
        ...,
        description="Chat messages to extract research profile from"
    )
    # Note: files are handled separately via multipart/form-data


class AnalyzeResponse(BaseModel):
    """Response from the /analyze endpoint."""
    session_id: str = Field(..., description="Unique session identifier for tracking")
    status: Literal["processing", "completed", "error"] = Field(
        ...,
        description="Current status of the analysis"
    )


class SessionStatusResponse(BaseModel):
    """Response for checking session status."""
    session_id: str = Field(..., description="Session identifier")
    status: Literal["processing", "completed", "error"] = Field(
        ...,
        description="Current status of the analysis"
    )
    result: ResearchRecommendation | None = Field(
        default=None,
        description="The completed recommendation (only present if status is 'completed')"
    )
    error_message: str | None = Field(
        default=None,
        description="Error details if status is 'error'"
    )
