import os
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
MODEL = "llama-3.3-70b-versatile"

def ask_groq(question: str, data_summary: str, chat_history: list = []):
    """
    Sends a question to Groq AI with the sales data as context.
    Returns the AI response as a string.
    """

    system_prompt = f"""You are ARIA, an intelligent AI sales analyst assistant for a homeopathic company.
You have been given the company's sales data summary below.
Answer all questions based on this data only. Be clear, concise, and helpful.
Format numbers with Indian currency style (₹ and commas).
If you don't know something from the data, say so honestly.

=== SALES DATA CONTEXT ===
{data_summary}
=== END OF DATA ===
"""

    messages = [{"role": "system", "content": system_prompt}]

    # Add chat history
    for msg in chat_history:
        messages.append(msg)

    # Add current question
    messages.append({"role": "user", "content": question})

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 1024
    }

    try:
        response = requests.post(GROQ_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error connecting to ARIA: {str(e)}"