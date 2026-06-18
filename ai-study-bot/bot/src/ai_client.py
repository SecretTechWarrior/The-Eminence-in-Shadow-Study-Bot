import asyncio
import logging
import os

from openai import AsyncOpenAI
from groq import AsyncGroq

from config import (
    GEMINI_API_KEY,
    OPENROUTER_API_KEY,
    GROQ_API_KEY,
    GEMINI_MODEL,
    OPENROUTER_MODEL,
    GROQ_MODEL,
    MAX_TOKENS,
)

logger = logging.getLogger(__name__)

# Optional Gemini import
GEMINI_AVAILABLE = False
genai = None
genai_types = None
GEMINI_IMPORT_ERROR = None

try:
    import google.generativeai as genai
    from google.generativeai import types as genai_types
    if GEMINI_API_KEY:
        genai.configure(api_key=GEMINI_API_KEY)
        GEMINI_AVAILABLE = True
except Exception as e:
    GEMINI_IMPORT_ERROR = e
    logger.warning(f"Gemini unavailable: {e}")

# Lazy clients
_openrouter_client = None
_groq_client = None


def get_openrouter_client():
    global _openrouter_client
    if _openrouter_client is None:
        if not OPENROUTER_API_KEY:
            raise RuntimeError("OPENROUTER_API_KEY is not set")
        _openrouter_client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=OPENROUTER_API_KEY,
        )
    return _openrouter_client


def get_groq_client():
    global _groq_client
    if _groq_client is None:
        if not GROQ_API_KEY:
            raise RuntimeError("GROQ_API_KEY is not set")
        _groq_client = AsyncGroq(api_key=GROQ_API_KEY)
    return _groq_client


async def ask_gemini(prompt: str, system: str = None) -> str:
    if not GEMINI_AVAILABLE or genai is None or genai_types is None:
        raise RuntimeError(f"Gemini unavailable: {GEMINI_IMPORT_ERROR}")

    model = genai.GenerativeModel(GEMINI_MODEL)
    full_prompt = f"{system}\n\n{prompt}" if system else prompt

    response = await asyncio.to_thread(
        model.generate_content,
        full_prompt,
        generation_config=genai_types.GenerationConfig(
            max_output_tokens=MAX_TOKENS,
            temperature=0.7,
        ),
    )
    return (response.text or "").strip()


async def ask_openrouter(prompt: str, system: str = None) -> str:
    client = get_openrouter_client()

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = await client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=messages,
        max_tokens=MAX_TOKENS,
    )
    return (response.choices[0].message.content or "").strip()


async def ask_groq(prompt: str, system: str = None) -> str:
    client = get_groq_client()

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    response = await client.chat.completions.create(
        model=GROQ_MODEL,
        messages=messages,
        max_tokens=MAX_TOKENS,
    )
    return (response.choices[0].message.content or "").strip()


async def ask_ai(prompt: str, system: str = None, prefer: str = "gemini") -> str:
    errors = []

    if prefer == "gemini":
        order = [ask_gemini, ask_openrouter, ask_groq]
    elif prefer == "groq":
        order = [ask_groq, ask_openrouter, ask_gemini]
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
