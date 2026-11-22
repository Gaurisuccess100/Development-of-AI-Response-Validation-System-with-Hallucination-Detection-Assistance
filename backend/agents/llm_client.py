
import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq


# Load .env from the project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")


def get_groq_client():
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY not found. Check your project's .env file."
        )

    return Groq(api_key=api_key)


def ask_groq(prompt, system_prompt="You are a helpful AI assistant."):
    model = os.getenv("GROQ_MODEL")

    if not model:
        raise ValueError("GROQ_MODEL not found in .env file.")

    client = get_groq_client()

    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": system_prompt
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.2
    )

    return response.choices[0].message.content
