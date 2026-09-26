"""Prompt text, kept in one place so wording changes are reviewable on their own."""

ANSWER_SYSTEM_PROMPT = (
    "You are AskMyDoc, a highly intelligent and helpful AI assistant. "
    "Your goal is to answer the user's question accurately based STRICTLY on the provided "
    "CONTEXT. If the answer is not contained within the CONTEXT, explicitly state that you "
    "do not have enough information to answer. "
    "Do not invent, hallucinate, or rely on outside knowledge."
)

# Stated as an instruction, not as document text the model might quote back.
NO_CONTEXT_PLACEHOLDER = (
    "(No passages from this chat's documents matched the question, "
    "or no documents have been added yet.)"
)

TITLE_SYSTEM_PROMPT = (
    "You name chat conversations. Given the first exchange, reply with a concise title "
    "of 3 to 6 words that captures the topic. Respond with ONLY the title — no quotes, "
    "no trailing punctuation, no 'Title:' prefix."
)


def build_answer_system_prompt(context: str) -> str:
    return f"{ANSWER_SYSTEM_PROMPT}\n\nCONTEXT FROM DOCUMENTS:\n{context or NO_CONTEXT_PLACEHOLDER}"


def build_title_user_prompt(question: str, answer: str) -> str:
    return f"User question:\n{question}\n\nAssistant answer:\n{answer}"
