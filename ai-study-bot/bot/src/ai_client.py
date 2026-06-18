import asyncio
from google import genai
from google.genai import types as genai_types
from openai import AsyncOpenAI
from groq import AsyncGroq
import logging
from config import (
    GEMINI_API_KEY, OPENROUTER_API_KEY, GROQ_API_KEY,
    GEMINI_MODEL, OPENROUTER_MODEL, GROQ_MODEL, MAX_TOKENS
)

logger = logging.getLogger(__name__)

# Configure clients
gemini_client = genai.Client(api_key=GEMINI_API_KEY)

openrouter_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

groq_client = AsyncGroq(api_key=GROQ_API_KEY)


async def ask_gemini(prompt: str, system: str = None) -> str:
    try:
        config = genai_types.GenerateContentConfig(
            max_output_tokens=MAX_TOKENS,
            temperature=0.7,
            system_instruction=system or "You are an expert AI study assistant. Always respond clearly and in a structured way.",
        )
        response = await asyncio.to_thread(
            gemini_client.models.generate_content,
            model=GEMINI_MODEL,
            contents=prompt,
            config=config,
        )
        return response.text
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        raise


async def ask_openrouter(prompt: str, system: str = None) -> str:
    try:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await openrouter_client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"OpenRouter error: {e}")
        raise


async def ask_groq(prompt: str, system: str = None) -> str:
    try:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=MAX_TOKENS,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq error: {e}")
        raise


async def ask_ai(prompt: str, system: str = None, prefer: str = "gemini") -> str:
    """
    Try AI models in order with fallback:
    gemini -> openrouter -> groq
    """
    errors = []

    if prefer == "gemini":
        order = [ask_gemini, ask_openrouter, ask_groq]
    elif prefer == "groq":
        order = [ask_groq, ask_gemini, ask_openrouter]
    else:
        order = [ask_openrouter, ask_gemini, ask_groq]

    for fn in order:
        try:
            result = await fn(prompt, system)
            if result and result.strip():
                return result
        except Exception as e:
            errors.append(str(e))
            logger.warning(f"AI fallback triggered: {e}")

    raise RuntimeError(f"All AI providers failed: {errors}")
