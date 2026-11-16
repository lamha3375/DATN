
import json
from typing import Any, Dict, List

from google import genai
from google.genai import types

from app.core.config import settings
from app.prompts.answer_prompt import AnswerPrompt
from app.schemas.answer import (
    AnswerResponse,
    AnswerSource,
    GeneratedAnswer
)


class AnswerGenerationService:

    def __init__(self):
        self.client = genai.Client(
            api_key=settings.GEMINI_API_KEY,
            http_options=types.HttpOptions(
                timeout=settings.GEMINI_TIMEOUT
            )
        )

        self.model = settings.GEMINI_MODEL

    def _build_sources(
        self,
        vector_context: List[Dict[str, Any]]
    ) -> List[AnswerSource]:

        sources = []
        seen = set()

        for item in vector_context:

            document_name = item.get("document_name")

            if not document_name:
                continue

            page_number = item.get("page_number")
            chunk_id = item.get("chunk_id")

            source_key = (
                document_name,
                page_number
            )

            if source_key in seen:
                continue

            seen.add(source_key)

            sources.append(
                AnswerSource(
                    document_name=document_name,
                    page_number=page_number,
                    chunk_id=chunk_id
                )
            )

        return sources

    def generate(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> AnswerResponse:

        query = query.strip() if query else ""

        if not query:
            raise ValueError("Câu hỏi không được để trống.")

        if not isinstance(context, dict):
            raise ValueError("Context phải có kiểu dữ liệu dict.")

        combined_context = context.get(
            "combined_context", ""
        )

        vector_context = context.get(
            "vector_context", []
        )

        if not isinstance(vector_context, list):
            vector_context = []

        sources = self._build_sources(vector_context)

        # Không gọi Gemini nếu không có dữ liệu truy xuất.
        if not combined_context.strip():

            return AnswerResponse(
                query=query,
                answer=(
                    "Hiện tại hệ thống chưa tìm thấy "
                    "dữ liệu lịch sử phù hợp để trả lời câu hỏi."
                ),
                sources=sources,
                has_sufficient_context=False
            )

        prompt = AnswerPrompt.build_prompt(
            query=query,
            context=combined_context
        )

        try:

            response = self.client.models.generate_content(
                model=self.model,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    response_mime_type="application/json",
                    response_schema=GeneratedAnswer
                )
            )

            if not response.text:
                raise RuntimeError(
                    "Gemini không trả về nội dung."
                )

            generated_data = GeneratedAnswer.model_validate(
                json.loads(response.text)
            )

            return AnswerResponse(
                query=query,
                answer=generated_data.answer,
                sources=sources,
                has_sufficient_context=(
                    generated_data.has_sufficient_context
                )
            )

        except Exception as exc:

            raise RuntimeError(
                f"Lỗi khi tạo câu trả lời bằng Gemini: {exc}"
            ) from exc


answer_generation_service = AnswerGenerationService()
