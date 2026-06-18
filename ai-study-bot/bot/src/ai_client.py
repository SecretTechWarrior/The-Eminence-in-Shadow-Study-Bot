import asyncio
import logging
import google.generativeai as genai

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

# ---------------------------
# GEMINI SETUP (FIXED)
# ---------------------------
genai.configure(api_key=GEMINI_API_KEY)

# ---------------------------
# OPENROUTER
# ---------------------------
openrouter_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# ---------------------------
# GROQ
# ---------------------------
groq_client = AsyncGroq(api_key=GROQ_API_KEY)


# ---------------------------
# GEMINI
# ---------------------------
async def ask_gemini(prompt: str, system: str = None) -> str:
    try:
        model = genai.GenerativeModel(GEMINI_MODEL)

        full_prompt = (
            f"{system}\n\n{prompt}"
            if system
            else prompt
        )

        response = await asyncio.to_thread(
            model.generate_content,
            full_prompt,
            generation_config={
                "max_output_tokens": MAX_TOKENS,
                "temperature": 0.7,
            },
        )

        return response.text or ""

    except Exception as e:
        logger.error(f"Gemini error: {e}")
        raise


# ---------------------------
# OPENROUTER
# ---------------------------
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


# ---------------------------
# GROQ
# ---------------------------
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


# ---------------------------
# AI ROUTER (FALLBACK SYSTEM)
# ---------------------------
async def ask_ai(prompt: str, system: str = None, prefer: str = "gemini") -> str:
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
