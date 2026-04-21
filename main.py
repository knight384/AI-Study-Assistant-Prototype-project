"""
main.py
-------
AI Personal Study Assistant — built with the OpenAI Agents SDK.

Runs in two modes:
  1. Terminal mode  : python main.py
  2. Gradio UI mode : python main.py --ui
"""

import argparse
import os
import sys
import textwrap
from dotenv import load_dotenv

# ── Load environment variables from .env ─────────────────────────────────────
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    sys.exit(
        "ERROR: OPENAI_API_KEY is not set.\n"
        "Copy .env.example → .env and add your key."
    )

# ── OpenAI Agents SDK imports ─────────────────────────────────────────────────
from agents import Agent, Runner, function_tool

# ── Local module imports ──────────────────────────────────────────────────────
from tools import summarize_notes, generate_quiz, create_study_plan
from memory import (
    format_memory_summary,
    update_session,
    get_all_context,
    clear_memory,
)

# ─────────────────────────────────────────────────────────────────────────────
# 1.  Wrap each tool function with the @function_tool decorator so the
#     Agents SDK can expose it to the LLM as a callable tool.
# ─────────────────────────────────────────────────────────────────────────────

@function_tool
def tool_summarize_notes(text: str) -> str:
    """
    Summarize the provided study notes or topic description into clear,
    concise bullet points covering key concepts, definitions, and facts.
    Use this when the user wants a summary of notes or a topic.
    """
    return summarize_notes(text)


@function_tool
def tool_generate_quiz(topic: str, difficulty: str = "medium") -> str:
    """
    Generate quiz questions for the given topic.
    Difficulty must be one of: 'easy', 'medium', or 'hard'.
    Use this when the user asks for practice questions, a quiz, or wants to test themselves.
    """
    return generate_quiz(topic, difficulty)


@function_tool
def tool_create_study_plan(topic: str, exam_date: str, hours_per_day: float = 2.0) -> str:
    """
    Create a detailed day-by-day study plan for the topic.
    exam_date must be in YYYY-MM-DD format.
    hours_per_day is how many hours the user can study each day.
    Use this when the user asks for a study schedule, revision plan, or study timetable.
    """
    return create_study_plan(topic, exam_date, hours_per_day)


# ─────────────────────────────────────────────────────────────────────────────
# 2.  Build the specialized agents
# ─────────────────────────────────────────────────────────────────────────────

def build_study_assistant_agent(memory_context: str) -> Agent:
    """
    Build the Study Assistant agent for explaining topics and providing insights.
    """
    system_prompt = textwrap.dedent(f"""
        You are the Study Assistant Agent. Your role is to explain topics clearly
        and provide comprehensive learning resources and insights.

        {memory_context}

        When a user asks to explain, describe, or learn about a topic:
        1. Provide a clear explanation of the topic
        2. Break down complex concepts into simpler parts
        3. Offer examples and real-world applications
        4. Suggest related topics to explore
        5. Encourage further learning

        Be encouraging, clear, and student-friendly.
    """).strip()

    return Agent(
        name="StudyAssistant",
        instructions=system_prompt,
        tools=[tool_summarize_notes],
        model="gpt-4o-mini",
    )


def build_quiz_generator_agent(memory_context: str) -> Agent:
    """
    Build the Quiz Generator Agent for creating practice questions.
    """
    system_prompt = textwrap.dedent(f"""
        You are the Quiz Generator Agent. Your role is to create engaging
        practice questions that help students test their knowledge.

        {memory_context}

        When a user asks for quiz questions:
        1. Use the generate_quiz tool to create questions
        2. Vary question types (multiple choice, true/false, short answer)
        3. Adjust difficulty based on user preference
        4. Include clear explanations for correct answers
        5. Make questions engaging and relevant

        Format quiz questions clearly with options and explanations.
    """).strip()

    return Agent(
        name="QuizGenerator",
        instructions=system_prompt,
        tools=[tool_generate_quiz],
        model="gpt-4o-mini",
    )


def build_revision_planner_agent(memory_context: str) -> Agent:
    """
    Build the Revision Planner Agent for creating study schedules and plans.
    """
    system_prompt = textwrap.dedent(f"""
        You are the Revision Planner Agent. Your role is to create personalized
        study plans and revision schedules that help students prepare for exams.

        {memory_context}

        When a user asks for a study plan:
        1. Use the create_study_plan tool to generate a schedule
        2. Break topics into manageable daily chunks
        3. Include variety in study methods (reading, practice, review)
        4. Build in buffer time for complex topics
        5. Track progress towards the exam date

        Provide realistic, motivating study schedules.
    """).strip()

    return Agent(
        name="RevisionPlanner",
        instructions=system_prompt,
        tools=[tool_create_study_plan],
        model="gpt-4o-mini",
    )


# ─────────────────────────────────────────────────────────────────────────────
# 3.  Smart routing and execution
# ─────────────────────────────────────────────────────────────────────────────

def detect_request_type(user_input: str) -> str:
    """
    Detect what type of request the user is making based on keywords.
    
    Returns: 'summary', 'quiz', 'plan', or 'general'
    """
    text = user_input.lower()
    
    quiz_keywords = ['quiz', 'question', 'test', 'practice', 'exam question', 'problem']
    plan_keywords = ['plan', 'schedule', 'revision', 'timetable', 'when to study', 'exam date']
    summary_keywords = ['summarize', 'summary', 'explain', 'describe', 'define', 'what is']
    
    if any(word in text for word in quiz_keywords):
        return 'quiz'
    elif any(word in text for word in plan_keywords):
        return 'plan'
    elif any(word in text for word in summary_keywords):
        return 'summary'
    else:
        return 'general'


def run_study_assistant(
    user_input: str,
    topic: str = "",
    difficulty: str = "medium",
    study_style: str = "balanced",
) -> str:
    """
    Run the Study Assistant by routing to the appropriate tool based on user input.
    This version calls tools DIRECTLY without waiting for LLM processing.

    Args:
        user_input:  The user's full message/request.
        topic:       Optional explicit topic (used to update memory).
        difficulty:  Preferred difficulty level for quizzes.
        study_style: Preferred study style (e.g. 'visual', 'practice-heavy').

    Returns:
        The tool output as a string.
    """
    text = user_input.lower()
    
    # Quiz request - route to quiz generator
    quiz_keywords = ['quiz', 'question', 'test', 'practice', 'exam question', 'problem']
    if any(word in text for word in quiz_keywords):
        # Extract topic and difficulty from user input
        topic = topic or _extract_topic_hint(user_input)
        output = generate_quiz(topic, difficulty)
        
        # Persist session data
        update_session(topic=topic, difficulty=difficulty, study_style=study_style)
        return output
    
    # Study plan request - route to revision planner
    plan_keywords = ['plan', 'schedule', 'revision', 'timetable', 'when to study', 'exam date']
    if any(word in text for word in plan_keywords):
        # Try to extract exam date from user input
        exam_date = _extract_exam_date(user_input)
        if not exam_date:
            return "Error: Please provide an exam date in YYYY-MM-DD format.\nExample: 'Create a study plan for 2026-05-15 with 2 hours per day'"
        
        topic = topic or _extract_topic_hint(user_input)
        hours = _extract_hours_per_day(user_input)
        output = create_study_plan(topic, exam_date, hours)
        
        # Persist session data
        update_session(topic=topic, difficulty=difficulty, study_style=study_style)
        return output
    
    # Summary/explanation request - route to study assistant
    summary_keywords = ['summarize', 'summary', 'explain', 'describe', 'define', 'what is', 'tell me']
    if any(word in text for word in summary_keywords):
        # For summary, we need the actual content to summarize
        topic = topic or _extract_topic_hint(user_input)
        output = summarize_notes(user_input)
        
        # Persist session data
        update_session(topic=topic, difficulty=difficulty, study_style=study_style)
        return output
    
    # Default: Try to generate summary from the input
    topic = topic or _extract_topic_hint(user_input)
    output = summarize_notes(user_input)
    update_session(topic=topic, difficulty=difficulty, study_style=study_style)
    return output


def _extract_exam_date(text: str) -> str:
    """Extract YYYY-MM-DD format date from text."""
    import re
    match = re.search(r'\d{4}-\d{2}-\d{2}', text)
    return match.group(0) if match else None


def _extract_hours_per_day(text: str) -> float:
    """Extract hours per day from text."""
    import re
    match = re.search(r'(\d+\.?\d*)\s*hours?', text.lower())
    return float(match.group(1)) if match else 2.0


def _extract_topic_hint(text: str) -> str:
    """
    Very lightweight heuristic: grab up to the first 6 words of the user
    message as a topic hint when no explicit topic is provided.
    """
    words = text.strip().split()
    return " ".join(words[:6]) if words else "Unknown"


# ─────────────────────────────────────────────────────────────────────────────
# 4.  Terminal (CLI) interface
# ─────────────────────────────────────────────────────────────────────────────

BANNER = """
╔══════════════════════════════════════════════╗
║        AI Personal Study Assistant           ║
║        Powered by OpenAI Agents SDK          ║
╚══════════════════════════════════════════════╝
Commands:
  Type your study request and press Enter.
  'memory'  → show stored memory
  'clear'   → wipe memory
  'quit'    → exit
"""

def run_terminal() -> None:
    """Interactive terminal session."""
    print(BANNER)
    print(format_memory_summary())
    print()

    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye! Keep studying 📖")
            break

        if not user_input:
            continue

        if user_input.lower() == "quit":
            print("Goodbye! Keep studying 📖")
            break

        if user_input.lower() == "memory":
            print(format_memory_summary())
            continue

        if user_input.lower() == "clear":
            clear_memory()
            print("Memory cleared.")
            continue

        print("\nAssistant: thinking...\n")
        try:
            response = run_study_assistant(user_input)
            print(response)
        except Exception as exc:
            print(f"Error: {exc}")
        print("\n" + "─" * 60 + "\n")


# ─────────────────────────────────────────────────────────────────────────────
# 5.  Gradio UI  (optional — only imported when --ui flag is passed)
# ─────────────────────────────────────────────────────────────────────────────

def run_gradio_ui() -> None:
    """Launch the Gradio web interface."""
    try:
        import gradio as gr
    except ImportError:
        sys.exit(
            "Gradio is not installed. Run:  pip install gradio\n"
            "Or start without the --ui flag."
        )

    def gradio_handler(
        user_input: str,
        topic: str,
        difficulty: str,
        study_style: str,
        chat_history: list,
    ):
        """Called by Gradio on each submission."""
        if not user_input.strip():
            return chat_history, format_memory_summary()

        response = run_study_assistant(
            user_input=user_input,
            topic=topic,
            difficulty=difficulty,
            study_style=study_style,
        )

        chat_history.append((user_input, response))
        memory_display = format_memory_summary()
        return chat_history, memory_display

    # ── UI Layout ──────────────────────────────────────────────────────────
    with gr.Blocks(title="AI Study Assistant", theme=gr.themes.Soft()) as demo:
        gr.Markdown(
            "# 📚 AI Personal Study Assistant\n"
            "Powered by the OpenAI Agents SDK · Remembers your preferences across sessions"
        )

        with gr.Row():
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(
                    label="Study Assistant",
                    height=480,
                    bubble_full_width=False,
                )
                user_box = gr.Textbox(
                    label="Your request",
                    placeholder=(
                        "e.g. Summarize my notes on photosynthesis, "
                        "give me a hard quiz on World War II, "
                        "or create a study plan for Calculus with exam on 2025-08-01"
                    ),
                    lines=3,
                )
                with gr.Row():
                    submit_btn = gr.Button("Send", variant="primary")
                    clear_btn  = gr.Button("Clear Chat")

            with gr.Column(scale=1):
                gr.Markdown("### ⚙️ Session Preferences")
                topic_box = gr.Textbox(
                    label="Topic (optional)",
                    placeholder="e.g. Machine Learning",
                )
                difficulty_dd = gr.Dropdown(
                    label="Difficulty",
                    choices=["easy", "medium", "hard"],
                    value="medium",
                )
                style_dd = gr.Dropdown(
                    label="Study Style",
                    choices=["balanced", "visual", "practice-heavy", "reading-heavy"],
                    value="balanced",
                )
                memory_box = gr.Textbox(
                    label="🧠 Memory / Previous Context",
                    value=format_memory_summary(),
                    lines=8,
                    interactive=False,
                )
                clear_mem_btn = gr.Button("🗑️ Clear Memory", variant="stop")

        # ── Event handlers ─────────────────────────────────────────────────
        state = gr.State([])  # chat history state

        submit_btn.click(
            fn=gradio_handler,
            inputs=[user_box, topic_box, difficulty_dd, style_dd, state],
            outputs=[chatbot, memory_box],
        ).then(lambda: "", outputs=user_box)

        user_box.submit(
            fn=gradio_handler,
            inputs=[user_box, topic_box, difficulty_dd, style_dd, state],
            outputs=[chatbot, memory_box],
        ).then(lambda: "", outputs=user_box)

        clear_btn.click(lambda: ([], []), outputs=[chatbot, state])

        def wipe_memory():
            clear_memory()
            return format_memory_summary()

        clear_mem_btn.click(fn=wipe_memory, outputs=memory_box)

    demo.launch(share=False)


# ─────────────────────────────────────────────────────────────────────────────
# 6.  Entry point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AI Personal Study Assistant")
    parser.add_argument(
        "--ui",
        action="store_true",
        help="Launch the Gradio web interface instead of the terminal REPL.",
    )
    args = parser.parse_args()

    if args.ui:
        run_gradio_ui()
    else:
        run_terminal()
