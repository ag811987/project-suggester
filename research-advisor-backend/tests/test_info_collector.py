"""Tests for the information collector service."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.schemas import ChatMessage, ResearchProfile
from app.services.info_collector import InfoCollectionService


class TestInfoCollectionService:
    """Test suite for InfoCollectionService."""

    def setup_method(self):
        self.service = InfoCollectionService(api_key="test-key")

    # --- extract_from_chat tests ---

    @pytest.mark.asyncio
    async def test_extract_from_chat_returns_research_profile(self, mock_openai_response):
        """LLM extraction from chat should return a valid ResearchProfile."""
        messages = [
            ChatMessage(role="user", content="I'm researching quantum computing for NP-complete problems"),
        ]

        with patch.object(self.service, "_call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_openai_response["choices"][0]["message"]["content"]
            result = await self.service.extract_from_chat(messages)

        assert isinstance(result, ResearchProfile)
        assert result.research_question != ""
        assert len(result.skills) > 0

    @pytest.mark.asyncio
    async def test_extract_from_chat_with_multiple_messages(self, mock_openai_response):
        """Should handle multi-turn conversations."""
        messages = [
            ChatMessage(role="user", content="I study quantum computing"),
            ChatMessage(role="assistant", content="What specific aspects?"),
            ChatMessage(role="user", content="Quantum algorithms for NP-complete problems"),
        ]

        with patch.object(self.service, "_call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_openai_response["choices"][0]["message"]["content"]
            result = await self.service.extract_from_chat(messages)

        assert isinstance(result, ResearchProfile)
        # Verify the LLM was called with all messages
        mock_call.assert_called_once()

    @pytest.mark.asyncio
    async def test_extract_from_chat_empty_messages(self):
        """Should raise ValueError when given empty message list."""
        with pytest.raises(ValueError, match="No messages provided"):
            await self.service.extract_from_chat([])

    @pytest.mark.asyncio
    async def test_extract_from_chat_handles_llm_error(self):
        """Should raise RuntimeError when OpenAI call fails."""
        messages = [ChatMessage(role="user", content="Hello")]

        with patch.object(self.service, "_call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.side_effect = Exception("API rate limit exceeded")
            with pytest.raises(RuntimeError, match="Failed to extract research profile"):
                await self.service.extract_from_chat(messages)

    @pytest.mark.asyncio
    async def test_extract_from_chat_handles_invalid_json(self):
        """Should raise RuntimeError when LLM returns invalid JSON."""
        messages = [ChatMessage(role="user", content="Research question")]

        with patch.object(self.service, "_call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = "This is not valid JSON at all"
            with pytest.raises(RuntimeError, match="Failed to extract research profile"):
                await self.service.extract_from_chat(messages)

    @pytest.mark.asyncio
    async def test_extract_from_chat_handles_incomplete_json(self):
        """Should handle LLM response with missing optional fields gracefully."""
        messages = [ChatMessage(role="user", content="Research question")]
        minimal_response = json.dumps({
            "research_question": "Can we improve solar cell efficiency?",
        })

        with patch.object(self.service, "_call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = minimal_response
            result = await self.service.extract_from_chat(messages)

        assert isinstance(result, ResearchProfile)
        assert result.research_question == "Can we improve solar cell efficiency?"
        assert result.skills == []  # Default empty list

    # --- extract_from_text tests ---

    @pytest.mark.asyncio
    async def test_extract_from_text_returns_profile(self, mock_openai_response):
        """Should extract a ResearchProfile from plain text."""
        text = "My research focuses on quantum algorithms for optimization."

        with patch.object(self.service, "_call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_openai_response["choices"][0]["message"]["content"]
            result = await self.service.extract_from_text(text)

        assert isinstance(result, ResearchProfile)

    @pytest.mark.asyncio
    async def test_extract_from_text_empty_string(self):
        """Should raise ValueError for empty text."""
        with pytest.raises(ValueError, match="No text provided"):
            await self.service.extract_from_text("")

    @pytest.mark.asyncio
    async def test_extract_from_text_with_file_context(self, mock_openai_response):
        """Should include file name context when provided."""
        text = "Research on protein folding using deep learning."

        with patch.object(self.service, "_call_openai", new_callable=AsyncMock) as mock_call:
            mock_call.return_value = mock_openai_response["choices"][0]["message"]["content"]
            result = await self.service.extract_from_text(
                text, source_filename="proposal.pdf"
            )

        assert isinstance(result, ResearchProfile)

    # --- merge_profiles tests ---

    def test_merge_profiles_combines_fields(self):
        """Should merge multiple profiles, combining list fields."""
        profile1 = ResearchProfile(
            research_question="Quantum computing for NP problems",
            skills=["Python", "Qiskit"],
            expertise_areas=["Computer Science"],
            motivations=["Curiosity"],
            interests=["Quantum algorithms"],
        )
        profile2 = ResearchProfile(
            research_question="Quantum optimization techniques",
            skills=["C++", "Linear Algebra"],
            expertise_areas=["Mathematics"],
            motivations=["Impact"],
            interests=["Optimization"],
        )

        result = self.service.merge_profiles([profile1, profile2])

        assert isinstance(result, ResearchProfile)
        # First profile's question takes priority
        assert result.research_question == "Quantum computing for NP problems"
        # Skills merged and deduplicated
        assert "Python" in result.skills
        assert "C++" in result.skills
        assert "Qiskit" in result.skills

    def test_merge_profiles_single_profile(self):
        """Should return the single profile unchanged."""
        profile = ResearchProfile(
            research_question="Solar energy research",
            skills=["MATLAB"],
        )
        result = self.service.merge_profiles([profile])
        assert result.research_question == "Solar energy research"
        assert result.skills == ["MATLAB"]

    def test_merge_profiles_empty_list(self):
        """Should raise ValueError when given empty list."""
        with pytest.raises(ValueError, match="No profiles to merge"):
            self.service.merge_profiles([])

    def test_merge_profiles_deduplicates_skills(self):
        """Should not produce duplicate entries in list fields."""
        profile1 = ResearchProfile(
            research_question="AI research",
            skills=["Python", "TensorFlow"],
        )
        profile2 = ResearchProfile(
            research_question="ML research",
            skills=["Python", "PyTorch"],
        )

        result = self.service.merge_profiles([profile1, profile2])
        assert result.skills.count("Python") == 1

    # --- _call_openai tests ---

    @pytest.mark.asyncio
    async def test_call_openai_sends_correct_payload(self):
        """Should call OpenAI with proper message format and model."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = '{"research_question": "test"}'
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        self.service._client = mock_client

        result = await self.service._call_openai("Extract research profile from: test input")

        assert result == '{"research_question": "test"}'
        mock_client.chat.completions.create.assert_called_once()

    # --- Integration-style test with sample_research_profile fixture ---

    def test_research_profile_fixture_valid(self, sample_research_profile):
        """Verify the sample_research_profile fixture is a valid ResearchProfile."""
        assert isinstance(sample_research_profile, ResearchProfile)
        assert sample_research_profile.research_question != ""
        assert len(sample_research_profile.skills) > 0
        assert len(sample_research_profile.expertise_areas) > 0
