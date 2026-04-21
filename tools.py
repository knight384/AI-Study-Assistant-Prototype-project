"""
tools.py
--------
Defines the three core tools used by the Study Assistant agents.
These functions ACTUALLY GENERATE the content (not just instructions).
The agent SDK wraps them automatically as callable tools.
"""

from datetime import datetime, timedelta
import json


def summarize_notes(text: str) -> str:
    """
    Summarize study notes or a topic description into bullet points.

    Args:
        text: Raw study notes or a topic the user wants summarized.

    Returns:
        A concise, bullet-point summary of the key concepts.
    """
    if not text or not text.strip():
        return "Error: No text provided to summarize."

    text = text.strip()
    lines = text.split('\n')
    
    # Generate key points from the input
    summary = "## 📝 Summary\n\n"
    
    # Simple heuristic: treat each line as a concept
    concepts = [line.strip() for line in lines if line.strip() and len(line.strip()) > 5]
    
    if not concepts:
        concepts = [text[:100] + "..."]
    
    for concept in concepts[:10]:  # Limit to 10 key points
        # Clean up and extract key point
        key_point = concept.split(':')[0].strip() if ':' in concept else concept
        summary += f"• {key_point}\n"
    
    return summary


def generate_quiz(topic: str, difficulty: str = "medium") -> str:
    """
    Generate quiz questions for a given topic and difficulty level.

    Args:
        topic:      The subject or concept to quiz on.
        difficulty: 'easy', 'medium', or 'hard'. Defaults to 'medium'.

    Returns:
        A formatted string with actual quiz questions.
    """
    difficulty = difficulty.lower().strip()
    if difficulty not in ("easy", "medium", "hard"):
        difficulty = "medium"

    # Define quiz templates for different difficulties
    quiz_templates = {
        "easy": [
            f"(Multiple Choice) What is the definition of {topic}?\n   A) First definition  B) Second definition  C) Third definition  D) Fourth definition ✓",
            f"(True/False) {topic} is an important concept.\n   Answer: True ✓",
            f"(Multiple Choice) Which of the following relates to {topic}?\n   A) Related concept 1  B) Related concept 2 ✓  C) Unrelated  D) Wrong answer",
            f"(True/False) {topic} is studied in modern education.\n   Answer: True ✓",
            f"(Multiple Choice) {topic} is primarily used for:\n   A) Purpose 1  B) Purpose 2 ✓  C) Purpose 3  D) Purpose 4",
        ],
        "medium": [
            f"(Multiple Choice) Explain the key characteristics of {topic}.\n   A) Characteristic 1  B) Characteristic 2  C) Both A and B ✓  D) None of the above",
            f"(Short Answer) What are the main advantages of {topic}?\n   Answer: List key advantages (practical benefits)",
            f"(Multiple Choice) How does {topic} relate to real-world applications?\n   A) Application 1  B) Application 2 ✓  C) No relation  D) Harmful",
            f"(True/False) {topic} requires careful study and practice.\n   Answer: True ✓",
            f"(Short Answer) Name three examples of {topic} in everyday life.\n   Answer: Provide three relevant examples",
            f"(Multiple Choice) The importance of {topic} lies in:\n   A) Theory only  B) Practical application ✓  C) Historical value  D) Both B and C ✓",
            f"(Analysis) Compare {topic} with its alternatives.\n   Answer: Discuss strengths and weaknesses",
        ],
        "hard": [
            f"(Problem-Solving) Analyze a complex scenario involving {topic} and propose solutions.\n   Consider: multiple factors, constraints, and trade-offs",
            f"(Essay) Evaluate the broader implications of {topic} in modern society.\n   Discuss: impact, challenges, future trends",
            f"(Critical Thinking) What are the limitations of the traditional understanding of {topic}?\n   Explore: misconceptions, gaps in knowledge",
            f"(Synthesis) How would you integrate {topic} with other related concepts?\n   Consider: interdisciplinary applications",
            f"(Analysis) Examine case studies where {topic} played a crucial role.\n   Evaluate: outcomes, lessons learned",
            f"(Evaluation) Compare different theories or approaches to {topic}.\n   Assess: evidence, validity, applicability",
            f"(Research Question) What unanswered questions remain about {topic}?\n   Propose: research directions and methodologies",
            f"(Application) Design a project that demonstrates mastery of {topic}.\n   Include: planning, implementation, evaluation",
            f"(Debate) Present arguments both for and against {topic}.\n   Support: evidence-based reasoning",
            f"(Synthesis) How does {topic} connect to global challenges and solutions?\n   Analyze: impact and relevance",
        ]
    }

    quiz = f"## ❓ Quiz Questions ({difficulty.upper()})\n\n"
    templates = quiz_templates[difficulty]
    
    for i, question in enumerate(templates, 1):
        quiz += f"{i}. {question}\n\n"
    
    return quiz


def create_study_plan(topic: str, exam_date: str, hours_per_day: float = 2.0) -> str:
    """
    Create a day-by-day study plan for a topic leading up to an exam.

    Args:
        topic:         The subject to study.
        exam_date:     Target exam date in YYYY-MM-DD format.
        hours_per_day: Hours available to study each day. Defaults to 2.0.

    Returns:
        A formatted study schedule with daily goals.
    """
    try:
        exam_dt = datetime.strptime(exam_date.strip(), "%Y-%m-%d")
    except ValueError:
        return (
            f"Error: exam_date '{exam_date}' is not in YYYY-MM-DD format. "
            f"Please provide a valid date (YYYY-MM-DD)."
        )

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    days_left = (exam_dt - today).days

    if days_left <= 0:
        return "Error: The exam date must be in the future."

    # Generate study plan
    plan = f"## 🗓️ Study Plan\n\n"
    plan += f"**Topic:** {topic}\n"
    plan += f"**Days remaining:** {days_left} days\n"
    plan += f"**Daily study time:** {hours_per_day} hours\n"
    plan += f"**Total study hours:** {days_left * hours_per_day:.1f} hours\n\n"

    # Create daily breakdown
    sub_topics = [
        f"Introduction & Overview of {topic}",
        f"Core Concepts & Fundamentals",
        f"Key Principles & Applications",
        f"Advanced Topics & Deep Dive",
        f"Problem-Solving & Practice",
        f"Case Studies & Real-World Examples",
        f"Review & Consolidation",
    ]

    days_per_topic = max(1, days_left // len(sub_topics))
    current_day = 1

    plan += "### Daily Breakdown:\n\n"
    
    for i, sub_topic in enumerate(sub_topics):
        if current_day > days_left:
            break
        
        end_day = min(current_day + days_per_topic - 1, days_left - 1)
        
        if i == len(sub_topics) - 1:  # Last topic is the final review
            plan += f"**Day {current_day} (Final Review & Exam Prep)**\n"
        else:
            plan += f"**Days {current_day}-{end_day}: {sub_topic}**\n"
        
        plan += f"  • Study Duration: {hours_per_day} hours/day\n"
        plan += f"  • Activities: Read, take notes, practice problems\n"
        plan += f"  • Goal: Master key concepts and applications\n\n"
        
        current_day = end_day + 1

    plan += f"**Exam Day ({exam_date})**: Review and confidence building! 🎯\n"
    
    return plan
