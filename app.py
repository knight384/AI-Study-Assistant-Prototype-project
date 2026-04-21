"""
app.py
------
Gradio Web UI for AI Personal Study Assistant
Provides a modern, interactive web interface
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

# ── Import tools and memory
from tools import summarize_notes, generate_quiz, create_study_plan
from memory import format_memory_summary, update_session, clear_memory

try:
    import gradio as gr
except ImportError:
    sys.exit("Gradio is not installed. Run: pip install gradio")


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
    remove_patterns = [
        r'generate\s+a\s+\w+\s+quiz\s+on\s+',
        r'create\s+a\s+study\s+plan\s+for\s+',
        r'tell\s+me\s+about\s+',
        r'summarize\s+',
        r'explain\s+',
        r'quiz\s+on\s+',
        r'test\s+on\s+',
        r'with\s+exam\s+on\s+\d{4}-\d{2}-\d{2}',
        r'\d{4}-\d{2}-\d{2}',
        r'with\s+\d+\s*hours?',
    ]
    
    cleaned = text
    for pattern in remove_patterns:
        cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)
    
    cleaned = re.sub(r'\b(easy|medium|hard)\b', '', cleaned, flags=re.IGNORECASE)
    
    words = [w.strip() for w in cleaned.split() if w.strip() and len(w.strip()) > 2]
    topic = " ".join(words[:4]).strip()
    
    return topic if topic else "General Topic"


def route_request(user_input: str) -> str:
    """Route user request to appropriate tool."""
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
            return "❌ Please provide an exam date in YYYY-MM-DD format.\n\nExample: 'Create a study plan for photosynthesis with exam on 2026-05-15 with 2 hours per day'"
        
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


def chat_interface(message, chat_history):
    """Handle chat interactions."""
    if not message.strip():
        return chat_history
    
    try:
        response = route_request(message)
        chat_history.append({
            "role": "user",
            "content": message
        })
        chat_history.append({
            "role": "assistant",
            "content": response
        })
        return chat_history
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        chat_history.append({
            "role": "user",
            "content": message
        })
        chat_history.append({
            "role": "assistant",
            "content": error_msg
        })
        return chat_history


def get_memory():
    """Get current memory context."""
    return format_memory_summary()


def clear_mem():
    """Clear all memory."""
    clear_memory()
    return "✓ Memory cleared!"


# ── Create Gradio Interface ──

with gr.Blocks(title="AI Study Assistant") as demo:
    gr.Markdown(
        """
        # 📚 AI Personal Study Assistant
        **Powered by OpenAI Agents SDK**
        
        Three specialized agents to help you study:
        - 📖 **Study Assistant** - Explains topics and provides insights
        - ❓ **Quiz Generator** - Creates practice questions of any difficulty
        - 🗓️ **Revision Planner** - Plans your study schedule with exam dates
        """
    )
    
    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                label="Study Assistant Chat",
                height=500,
            )
            
            with gr.Row():
                message_input = gr.Textbox(
                    label="Your request",
                    placeholder="e.g. 'Generate a hard quiz on photosynthesis' or 'Create a study plan for exam on 2026-05-20'",
                    lines=2,
                    scale=4,
                )
                send_btn = gr.Button("Send", variant="primary", scale=1)
            
            with gr.Row():
                clear_chat_btn = gr.Button("Clear Chat", variant="secondary")
                memory_btn = gr.Button("View Memory", variant="secondary")
                clear_mem_btn = gr.Button("Clear Memory", variant="stop")
        
        with gr.Column(scale=1):
            gr.Markdown("### 💡 Examples")
            gr.Markdown(
                """
                **Quiz:**
                - "Generate a hard quiz on photosynthesis"
                - "Easy test on world history"
                
                **Study Plan:**
                - "Create a study plan for exam on 2026-05-20 with 2 hours per day"
                - "Plan for calculus revision, exam 2026-06-01"
                
                **Explanation:**
                - "Explain the water cycle"
                - "Summarize photosynthesis"
                """
            )
            
            memory_display = gr.Textbox(
                label="🧠 Memory Context",
                value=get_memory(),
                lines=8,
                interactive=False,
            )
    
    # ── Event Handlers ──
    
    def update_memory():
        return get_memory()
    
    def clear_chat():
        return []
    
    send_btn.click(
        fn=chat_interface,
        inputs=[message_input, chatbot],
        outputs=chatbot,
    ).then(
        lambda: "",
        outputs=message_input
    )
    
    message_input.submit(
        fn=chat_interface,
        inputs=[message_input, chatbot],
        outputs=chatbot,
    ).then(
        lambda: "",
        outputs=message_input
    )
    
    clear_chat_btn.click(
        fn=clear_chat,
        outputs=chatbot
    )
    
    memory_btn.click(
        fn=update_memory,
        outputs=memory_display
    )
    
    clear_mem_btn.click(
        fn=clear_mem,
        outputs=memory_display
    ).then(
        fn=update_memory,
        outputs=memory_display
    )


if __name__ == "__main__":
    demo.launch(
        server_name="127.0.0.1",
        server_port=7860,
        share=False,
        show_error=True,
        theme=gr.themes.Soft(),
    )
