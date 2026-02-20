"""Information collection service for extracting research profiles.

Uses OpenAI's GPT models to extract structured research profile data
from chat messages and document text.
"""

import json

from openai import AsyncOpenAI

from app.models.schemas import ChatMessage, ResearchProfile


EXTRACTION_SYSTEM_PROMPT = """You are a research profile extractor. Given the user's messages or text about their research, extract a structured JSON profile.

Return ONLY valid JSON with these fields:
- research_question (string, required): The primary research question
- problem_description (string, optional): Detailed description of the research problem
- skills (list of strings): Technical and research skills
- expertise_areas (list of strings): Domains of expertise
- motivations (list of strings): What drives the researcher
- interests (list of strings): Broader research interests
- extracted_from_files (list of strings): File names if mentioned

Return ONLY the JSON object, no markdown formatting or extra text."""


class InfoCollectionService:
    """Extracts structured research profiles from user input using LLMs."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4-0125-preview",
        temperature: float = 0.7,
        max_tokens: int = 2000,
    ):
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    async def extract_from_chat(self, messages: list[ChatMessage]) -> ResearchProfile:
        """Extract a ResearchProfile from chat messages.

        Args:
            messages: List of chat messages from the conversation.

        Returns:
            A structured ResearchProfile.

        Raises:
            ValueError: If no messages are provided.
            RuntimeError: If extraction fails.
        """
        if not messages:
            raise ValueError("No messages provided")

        try:
            prompt = "Extract the research profile from this conversation:\n\n"
            for msg in messages:
                prompt += f"{msg.role}: {msg.content}\n"

            raw = await self._call_openai(prompt)
            return self._parse_profile(raw)
        except (ValueError, RuntimeError):
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to extract research profile: {e}") from e

    async def extract_from_text(
        self, text: str, source_filename: str | None = None
    ) -> ResearchProfile:
        """Extract a ResearchProfile from plain text.

        Args:
            text: Document or input text to analyze.
            source_filename: Optional filename for context.

        Returns:
            A structured ResearchProfile.

        Raises:
            ValueError: If text is empty.
            RuntimeError: If extraction fails.
        """
        if not text.strip():
            raise ValueError("No text provided")

        try:
            prompt = "Extract the research profile from this text"
            if source_filename:
                prompt += f" (from file: {source_filename})"
            prompt += f":\n\n{text}"

            raw = await self._call_openai(prompt)
            profile = self._parse_profile(raw)

            if source_filename and source_filename not in profile.extracted_from_files:
                profile.extracted_from_files.append(source_filename)

            return profile
        except (ValueError, RuntimeError):
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to extract research profile: {e}") from e

    def merge_profiles(self, profiles: list[ResearchProfile]) -> ResearchProfile:
        """Merge multiple ResearchProfiles into one.

        The first profile's research_question takes priority.
        List fields are combined and deduplicated.

        Args:
            profiles: List of profiles to merge.

        Returns:
            A merged ResearchProfile.

        Raises:
            ValueError: If no profiles are provided.
        """
        if not profiles:
            raise ValueError("No profiles to merge")

        if len(profiles) == 1:
            return profiles[0]

        merged_skills: list[str] = []
        merged_expertise: list[str] = []
        merged_motivations: list[str] = []
        merged_interests: list[str] = []
        merged_files: list[str] = []

        for p in profiles:
            for s in p.skills:
                if s not in merged_skills:
                    merged_skills.append(s)
            for e in p.expertise_areas:
                if e not in merged_expertise:
                    merged_expertise.append(e)
            for m in p.motivations:
                if m not in merged_motivations:
                    merged_motivations.append(m)
            for i in p.interests:
                if i not in merged_interests:
                    merged_interests.append(i)
            for f in p.extracted_from_files:
                if f not in merged_files:
                    merged_files.append(f)

        return ResearchProfile(
            research_question=profiles[0].research_question,
            problem_description=profiles[0].problem_description,
            skills=merged_skills,
            expertise_areas=merged_expertise,
            motivations=merged_motivations,
            interests=merged_interests,
            extracted_from_files=merged_files,
        )

    async def _call_openai(self, user_prompt: str) -> str:
        """Call OpenAI chat completion API.

        Args:
            user_prompt: The user message to send.

        Returns:
            The assistant's response content.
        """
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": EXTRACTION_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=self._temperature,
            max_tokens=self._max_tokens,
        )
        return response.choices[0].message.content

    def _parse_profile(self, raw_json: str) -> ResearchProfile:
        """Parse raw JSON string into a ResearchProfile.

        Args:
            raw_json: JSON string from LLM response.

        Returns:
            A validated ResearchProfile.

        Raises:
            RuntimeError: If parsing or validation fails.
        """
        try:
            data = json.loads(raw_json)
            return ResearchProfile(**data)
        except (json.JSONDecodeError, TypeError, Exception) as e:
            raise RuntimeError(f"Failed to extract research profile: {e}") from e
