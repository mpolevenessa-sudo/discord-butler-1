import os
from groq import Groq
from dotenv import load_dotenv
import database as db

load_dotenv(override=True)
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def process_user_message(discord_id, user_message, server_name="this community"):
    # Guardrails
    escalation_keywords = ["refund", "fraud", "scam", "human", "manager"]
    if any(word in user_message.lower() for word in escalation_keywords):
        db.update_user_status(discord_id, "escalated")
        return "**[ESCALATION]** I've notified a human admin to assist you with your request."

    if db.get_user_status(discord_id) == "escalated":
        return "A human admin is reviewing our chat. They will be with you shortly."

    db.save_message(discord_id, "user", user_message)
    history = db.get_chat_history(discord_id)

    system_prompt = f"You are the elite Butler for {server_name}. Be professional, concise, and helpful."

    messages = [{"role": "system", "content": system_prompt}] + history

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.5
        )
        ai_resp = completion.choices[0].message.content
        db.save_message(discord_id, "assistant", ai_resp)
        return ai_resp
    except Exception as e:
        return "I'm having a brief system hiccup. Please try again in a moment."