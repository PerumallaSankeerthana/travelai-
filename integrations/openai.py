import time

from google import genai
from google.genai import types

from backend.core.config import settings


def _get_gemini_client():
    if not settings.gemini_api_key:
        raise RuntimeError(
            "GEMINI_API_KEY is not configured"
        )

    return genai.Client(
        api_key=settings.gemini_api_key
    )


def generate_json(
    system_prompt: str,
    user_message: str,
    response_schema: dict | None = None,
) -> str:

    if settings.llm_provider.lower() != "gemini":
        raise RuntimeError(
            f"Unsupported LLM provider: "
            f"{settings.llm_provider}"
        )

    client = _get_gemini_client()

    config = types.GenerateContentConfig(
        system_instruction=system_prompt,
        response_mime_type="application/json",
        response_schema=response_schema,
        temperature=0.2,
        max_output_tokens=4096,
    )

    models_to_try = [
        settings.gemini_model,
        "gemini-3.7-flash",
        "gemini-3.5-flash",
    ]

    last_error = None

    for model in models_to_try:

        for attempt in range(3):

            try:

                print(
                    f"\nCalling Gemini model: {model} "
                    f"(attempt {attempt + 1}/3)"
                )

                response = client.models.generate_content(
                    model=model,
                    contents=user_message,
                    config=config,
                )

                if not response.text:
                    raise RuntimeError(
                        f"Gemini returned empty response "
                        f"from {model}"
                    )

                return response.text

            except Exception as exc:

                last_error = exc

                error_text = str(exc)

                print(
                    f"Gemini error from {model}: "
                    f"{error_text}"
                )

                if "503" not in error_text:
                    raise

                if attempt < 2:
                    time.sleep(2)

        print(
            f"\nModel {model} unavailable. "
            f"Trying next model..."
        )

    raise RuntimeError(
        "All configured Gemini models are currently "
        "unavailable."
    ) from last_error