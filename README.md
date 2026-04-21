# 📚 AI Personal Study Assistant

An AI-powered study companion built with the **OpenAI Agents SDK**.  
It summarizes notes, generates quiz questions, creates study plans, and
remembers your preferences across sessions.

---

## Project Overview

| Feature | Details |
| --- | --- |
| Framework | OpenAI Agents SDK |
| Model | `gpt-4o-mini` (configurable) |
| Tools | `summarize_notes`, `generate_quiz`, `create_study_plan` |
| Memory | JSON-based persistent memory (`memory.json`) |
| UI | Terminal REPL + optional Gradio web UI |

### How It Works

```text
User Input
    ↓
Agent (gpt-4o-mini) reads memory → decides which tool(s) to call
    ├── tool_summarize_notes(text)
    ├── tool_generate_quiz(topic, difficulty)
    └── tool_create_study_plan(topic, exam_date, hours_per_day)
    ↓
Structured response:  Topic / Summary / Quiz / Study Plan / Memory
    ↓
memory.py saves topic, difficulty, study style → memory.json
```

**Agent** — One `Agent` instance with a system prompt that includes the
current memory context. The agent autonomously decides which tools to call
based on the user's request.

**Tools** — Three `@function_tool`-decorated functions. The SDK serialises
their signatures into JSON Schema and passes them to the model as callable
tools.

**Memory** — `memory.py` reads/writes a local `memory.json` file. The
stored context (last topic, difficulty, study style, topic history) is
injected into the agent's system prompt at the start of each run, giving
the agent "memory" across sessions.

---

## Folder Structure

```text
study-assistant/
├── main.py           ← Agent setup, runner, Gradio UI
├── tools.py          ← All three tool functions
├── memory.py         ← Load/save conversation memory
├── requirements.txt  ← Python dependencies
├── .env.example      ← API key template
└── README.md         ← This file
```

---

## Setup & Installation

### 1. Clone / download the project

```bash
# If using git:
git clone <your-repo-url>
cd study-assistant

# Or just place all files in a folder called study-assistant/
```

### 2. Create and activate a virtual environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

To also use the Gradio UI:

```bash
pip install gradio
# Then uncomment the gradio line in requirements.txt
```

### 4. Add your OpenAI API key

```bash
# Copy the example file
cp .env.example .env

# Open .env in any editor and replace the placeholder:
OPENAI_API_KEY=sk-your-real-key-here
```

Get your key from: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)

---

## How to Run

### Terminal mode (default)

```bash
python main.py
```

### Gradio web UI

```bash
python main.py --ui
# Opens at http://127.0.0.1:7860
```

---

## Sample Input & Output

### Input (terminal)

```text
You: Summarize my notes on the water cycle. Also give me a medium quiz and
     create a study plan with my exam on 2025-08-15 and 2 hours per day.
```

### Output

```text
## 📚 Topic
The Water Cycle

## 📝 Summary
• Evaporation: Sun heats surface water → water vapour rises into atmosphere
• Condensation: Water vapour cools at altitude → forms clouds (water droplets / ice)
• Precipitation: Water falls as rain, snow, sleet, or hail
• Collection: Water collects in oceans, rivers, lakes, and groundwater
• Transpiration: Plants release water vapour (contributes ~10% of atmospheric moisture)
• The cycle is driven by solar energy and gravity

## ❓ Quiz Questions
1. (Multiple Choice) What process converts liquid water to water vapour?
   A) Condensation  B) Precipitation  C) Evaporation ✓  D) Transpiration
   Explanation: Evaporation occurs when solar energy gives water molecules enough
   energy to escape the liquid surface as vapour.
...

## 🗓️ Study Plan
Day 1  (2 hrs) — Evaporation & Transpiration: read textbook p.45–52, draw diagram
Day 2  (2 hrs) — Condensation & Cloud formation: watch YouTube explainer, make notes
Day 3  (2 hrs) — Precipitation types & Collection: flashcards + practice questions
Day 4  (2 hrs) — Full cycle revision: mind map + past paper questions
Day 5  (2 hrs) — Mock test + review weak areas
Day 6  (EXAM DAY) — Light review only, rest well 🎯

## 🧠 Memory / Previous Context
📋 Previous Session Context:
  • Last topic studied  : The Water Cycle
  • Preferred difficulty: medium
  • Study style         : balanced
  • Topics studied so far: The Water Cycle
  • Last session        : 2025-07-10T14:32:05
```

---

## Tips

- **Difficulty** — say "hard quiz" or "easy questions" and the agent will
  adjust automatically.
- **Study style** — mention "I prefer visual learning" or "practice-heavy"
  in your request; it gets saved to memory.
- **Clearing memory** — type `clear` in the terminal, or press
  *🗑️ Clear Memory* in the Gradio UI.
- **Better model** — change `model="gpt-4o-mini"` to `model="gpt-4o"` in
  `main.py` for higher quality (higher cost).

---

## Requirements

- Python 3.10+
- An OpenAI account with API access
- Dependencies listed in `requirements.txt`
