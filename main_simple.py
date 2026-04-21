"""
main_simple.py
--------------
Simplified AI Personal Study Assistant.
Direct tool calls - no LLM processing delays.
"""

import os
import sys
import re
from dotenv import load_dotenv

# ── Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    sys.exit("ERROR: OPENAI_API_KEY not set in .env file")

# ── Import our tools and memory
from tools import summarize_notes, generate_quiz, create_study_plan
from memory import (
    format_memory_summary,
    update_session,
    clear_memory,
)


def extract_exam_date(text: str) -> str:
    """Extract YYYY-MM-DD format date from text."""
    match = re.search(r'\d{4}-\d{2}-\d{2}', text)
    return match.group(0) if match else None


def extract_hours_per_day(text: str) -> float:
    """Extract hours per day from text."""
    match = re.search(r'(\d+\.?\d*)\s*hours?', text.lower())
    return float(match.group(1)) if match else 2.0


def extract_difficulty(text: str) -> str:
    """Extract difficulty level from text."""
    text_lower = text.lower()
    if 'hard' in text_lower:
        return 'hard'
    elif 'easy' in text_lower:
        return 'easy'
    else:
        return 'medium'


def extract_topic_hint(text: str) -> str:
    """Extract topic from user input - removes keywords and cleans up."""
    text_lower = text.lower()
    
    # Remove question words and keywords
    remove_patterns = [
        r'generate\s+a\s+\w+\s+quiz\s+on\s+',  # "generate a hard quiz on"
        r'create\s+a\s+study\s+plan\s+for\s+',  # "create a study plan for"
        r'tell\s+me\s+about\s+',
        r'summarize\s+',
        r'explain\s+',
        r'quiz\s+on\s+',
        r'test\s+on\s+',
        r'with\s+exam\s+on\s+\d{4}-\d{2}-\d{2}',
        r'\d{4}-\d{2}-\d{2}',  # dates
        r'with\s+\d+\s*hours?',  # hours
    ]
    
    cleaned = text
    for pattern in remove_patterns:
        cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)
    
    # Remove difficulty words
    cleaned = re.sub(r'\b(easy|medium|hard)\b', '', cleaned, flags=re.IGNORECASE)
    
    # Get first few meaningful words
    words = [w.strip() for w in cleaned.split() if w.strip() and len(w.strip()) > 2]
    topic = " ".join(words[:4]).strip()
    
    return topic if topic else "General Topic"


def route_request(user_input: str) -> str:
    """
    Route user request to appropriate tool.
    Returns immediate result without LLM processing.
    """
    text = user_input.lower()
    
    # ── QUIZ REQUEST ──
    quiz_keywords = ['quiz', 'question', 'test', 'practice', 'exam question', 'problem']
    if any(word in text for word in quiz_keywords):
        topic = extract_topic_hint(user_input)
        difficulty = extract_difficulty(user_input)
        result = generate_quiz(topic, difficulty)
        update_session(topic=topic, difficulty=difficulty, study_style="balanced")
        return result
    
    # ── STUDY PLAN REQUEST ──
    plan_keywords = ['plan', 'schedule', 'revision', 'timetable', 'when to study', 'exam date', 'prep']
    if any(word in text for word in plan_keywords):
        exam_date = extract_exam_date(user_input)
        if not exam_date:
            return "❌ Please provide an exam date in YYYY-MM-DD format.\nExample: 'Create a study plan for photosynthesis with exam on 2026-05-15'"
        
        topic = extract_topic_hint(user_input)
        hours = extract_hours_per_day(user_input)
        result = create_study_plan(topic, exam_date, hours)
        update_session(topic=topic, difficulty="medium", study_style="balanced")
        return result
    
    # ── SUMMARY/EXPLANATION REQUEST ──
    summary_keywords = ['summarize', 'summary', 'explain', 'describe', 'define', 'what is', 'tell me about']
    if any(word in text for word in summary_keywords):
        topic = extract_topic_hint(user_input)
        result = summarize_notes(user_input)
        update_session(topic=topic, difficulty="medium", study_style="balanced")
        return result
    
    # ── DEFAULT: TREAT AS SUMMARY ──
    topic = extract_topic_hint(user_input)
    result = summarize_notes(user_input)
    update_session(topic=topic, difficulty="medium", study_style="balanced")
    return result


BANNER = """
╔═══════════════════════════════════════════════╗
║   📚 AI Personal Study Assistant             ║
║   Three Agents: Study, Quiz, Revision        ║
║   Tools: summarize, generate_quiz, plan      ║
╚═══════════════════════════════════════════════╝

Commands:
  • Type your study request and press Enter
  • Type 'memory' to view your session history
  • Type 'clear' to reset memory
  • Type 'quit' to exit

Examples:
  ✓ "Summarize photosynthesis for me"
  ✓ "Generate a hard quiz on calculus"
  ✓ "Create a study plan for exam on 2026-05-15"
"""


def main():
    """Run the interactive study assistant."""
    print(BANNER)
    print(format_memory_summary())
    print()

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n✨ Goodbye! Keep studying 📖\n")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("\n✨ Goodbye! Keep studying 📖\n")
            break

        if user_input.lower() == "memory":
            print(f"\n{format_memory_summary()}\n")
            continue

        if user_input.lower() == "clear":
            clear_memory()
            print("✓ Memory cleared.\n")
            continue

        print()
        try:
            response = route_request(user_input)
            print(response)
        except Exception as exc:
            print(f"❌ Error: {exc}")
        print("\n" + "─" * 60 + "\n")


if __name__ == "__main__":
    main()
