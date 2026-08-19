"""Answer generation with evidence citing and abstention guards."""

from __future__ import annotations

import logging

from openai import OpenAI

from chronograph.config import get_config

logger = logging.getLogger(__name__)


class AnswerGenerator:
    def __init__(self):
        self.config = get_config()
        api_key = self.config.llm.openai_api_key or "mock-key"
        self.client = OpenAI(api_key=api_key)
        self.model = self.config.llm.synthesis_model

    def generate(self, question: str, context: str, should_abstain: bool = False) -> str:
        if should_abstain:
            return "I don't have enough information in my memory graph to answer this question accurately."

        system_prompt = (
            "You are ChronoGraph, an AI assistant answering questions based strictly on the retrieved temporal graph memory.\n"
            "Answer ONLY from the provided evidence. Cite session IDs where possible.\n"
            "If the provided evidence is insufficient or contradicts the question, clearly state so."
        )

        user_prompt = f"Context from HydraDB Graph:\n{context}\n\nQuestion: {question}"

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.0,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"Error generating answer with LLM: {e}")
            # Fallback answer directly from context
            if context.strip():
                return f"Based on retrieved memory:\n{context}"
            return "I don't have enough information in my memory graph to answer this question accurately."
