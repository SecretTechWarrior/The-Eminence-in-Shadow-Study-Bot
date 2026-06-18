SYSTEM_STUDY = """You are an expert AI study assistant. You help students understand complex topics by breaking them down clearly. Always structure your output with clear headings, bullet points, and examples. Be thorough but concise."""

SYSTEM_QUIZ = """You are an expert quiz generator for students. Create clear, well-structured quizzes that test understanding. Always follow the exact format requested."""

SYSTEM_ELI10 = """You are a master at explaining complex topics in simple terms. You use everyday analogies, relatable examples, and simple language that a 10-year-old can understand. Never use jargon without explaining it immediately."""


def notes_prompt(transcript: str, title: str) -> str:
    return f"""You are creating comprehensive study notes from this YouTube lecture transcript.

VIDEO TITLE: {title}

TRANSCRIPT:
{transcript[:10000]}

Generate DETAILED STUDY NOTES in this exact structure:

# {title} — Complete Notes

## 📖 Overview
(2-3 sentence summary of the entire lecture)

## 🎯 Key Concepts
(List and explain each major concept covered)

### Concept 1: [Name]
- Explanation
- Key points
- Examples

### Concept 2: [Name]
- Explanation
- Key points
- Examples

(Continue for all concepts)

## 📝 Important Definitions
- **Term**: Definition
(List all important terms and their definitions)

## ⚡ Key Formulas & Equations
(If applicable — list all formulas with explanation of variables)

## 💡 Important Points to Remember
1. Point 1
2. Point 2
(List 10-15 most important points)

## 🔗 Applications & Real-world Examples
(Where these concepts are used in real life)

## ❓ Common Mistakes to Avoid
- Mistake 1
- Mistake 2

## 📌 Quick Revision Summary
(5-7 bullet points summarizing the entire lecture)

Be thorough, accurate, and student-friendly."""


def short_notes_prompt(transcript: str, title: str) -> str:
    return f"""Create SHORT REVISION NOTES from this lecture transcript.

VIDEO: {title}
TRANSCRIPT: {transcript[:8000]}

Generate CONCISE SHORT NOTES (1-2 pages equivalent):

# {title} — Short Notes

## Key Points
• Point 1
• Point 2
(20-25 essential bullet points only)

## Must-Know Definitions
- Term: Quick definition
(Only the most critical terms)

## Important Formulas
(If applicable)

## Quick Summary
(3-4 sentences max)

Keep it brief, bulleted, and revision-ready."""


def quiz_prompt(transcript: str, title: str, quiz_type: str = "mixed", difficulty: str = "medium") -> str:
    type_instruction = {
        "mcq": "Generate ONLY Multiple Choice Questions (MCQs) with 4 options each.",
        "subjective": "Generate ONLY Short-Answer and Long-Answer questions.",
        "mixed": "Generate a MIX of MCQs and subjective questions.",
    }.get(quiz_type, "Generate a mix of MCQs and subjective questions.")

    difficulty_instruction = {
        "easy": "Focus on basic recall and understanding. Keep questions straightforward.",
        "medium": "Include application and analysis questions. Moderate difficulty.",
        "hard": "Focus on analysis, evaluation, and problem-solving. Include tricky questions.",
        "exam": "Exam-oriented questions similar to board/competitive exams. Include all levels.",
    }.get(difficulty, "Moderate difficulty.")

    return f"""Create a comprehensive quiz from this lecture.

VIDEO: {title}
DIFFICULTY: {difficulty.upper()} — {difficulty_instruction}
TYPE: {type_instruction}

TRANSCRIPT: {transcript[:8000]}

QUIZ FORMAT:

# {title} — {difficulty.title()} Quiz

## Part A: Multiple Choice Questions
(If MCQ or mixed — 10 MCQs)

Q1. [Question]
A) Option A
B) Option B
C) Option C
D) Option D

Q2. [Question]
...

## Part B: Short Answer Questions
(5 questions, 2-3 sentence answers expected)

Q11. [Question]
Q12. [Question]
...

## Part C: Long Answer Questions
(3 questions, detailed answers expected)

Q16. [Question]
Q17. [Question]
Q18. [Question]

---
ANSWER KEY:

# Answer Key

## MCQ Answers
Q1 → [Correct Option] | Explanation: [Brief explanation]
Q2 → [Correct Option] | Explanation: [Brief explanation]
...

## Short Answer Guidelines
Q11: [Expected answer points]
...

## Long Answer Guidelines
Q16: [Key points to cover]
...

Separate the QUIZ section and ANSWER KEY section clearly with ---"""


def summary_prompt(transcript: str, title: str, mode: str = "detailed") -> str:
    modes = {
        "quick": f"""Create a QUICK SUMMARY of this lecture in exactly 10 bullet points.

VIDEO: {title}
TRANSCRIPT: {transcript[:8000]}

# Quick Summary — {title}

## 10 Key Takeaways
1. 
2. 
3. 
4. 
5. 
6. 
7. 
8. 
9. 
10. 

## One-Line Verdict
(What this lecture is fundamentally about in one sentence)""",

        "5min": f"""Create a 5-MINUTE REVISION summary of this lecture (about 1 page of reading).

VIDEO: {title}
TRANSCRIPT: {transcript[:8000]}

# 5-Minute Revision — {title}

## What This Lecture Covers
(2-3 sentences)

## Core Concepts
(Paragraph-style explanation of each main concept, 3-5 concepts)

## Key Points
• 
• 
•

## Remember This
(Most critical takeaway in bold)""",

        "ultra": f"""Summarize this lecture in EXACTLY 100 WORDS. No more, no less.

VIDEO: {title}
TRANSCRIPT: {transcript[:6000]}

Write a 100-word summary:""",

        "detailed": f"""Create a DETAILED CHAPTER-LEVEL SUMMARY of this lecture.

VIDEO: {title}
TRANSCRIPT: {transcript[:10000]}

# Detailed Summary — {title}

## Introduction
(What the lecture starts with)

## Main Sections
(Break down each major section/topic covered, with 2-3 paragraph explanations)

## Conclusions & Key Takeaways
(What was concluded)

## Study Notes
(Important points for revision)"""
    }
    return modes.get(mode, modes["detailed"])


def chapters_prompt(transcript_list: list, title: str) -> str:
    # Build timestamped text
    timestamped = ""
    for i, entry in enumerate(transcript_list):
        if i % 5 == 0:  # Every 5th entry to keep context manageable
            mins = int(entry['start'] // 60)
            secs = int(entry['start'] % 60)
            timestamped += f"[{mins:02d}:{secs:02d}] "
        timestamped += entry['text'] + " "

    return f"""Analyze this lecture transcript and identify distinct chapters/topics with timestamps.

VIDEO: {title}
TIMESTAMPED TRANSCRIPT:
{timestamped[:10000]}

Create a CHAPTER BREAKDOWN:

# Chapter Breakdown — {title}

## Chapters Identified

### Chapter 1: [Topic Name]
- **Timestamp**: [MM:SS] - [MM:SS]
- **Summary**: (2-3 sentences about this chapter)
- **Key Points**:
  • Point 1
  • Point 2

### Chapter 2: [Topic Name]
- **Timestamp**: [MM:SS] - [MM:SS]
- **Summary**: (2-3 sentences)
- **Key Points**:
  • Point 1
  • Point 2

(Continue for all chapters — typically 4-8 chapters)

## Quick Navigation
00:00 Introduction
[MM:SS] Chapter 2 Topic
[MM:SS] Chapter 3 Topic
...

## Lecture Overview
(Brief paragraph about the overall lecture structure)

Identify REAL topic transitions based on content, not arbitrary splits."""


def revision_prompt(transcript: str, title: str) -> str:
    return f"""Create a ONE-DAY REVISION SHEET for this lecture. It should be readable in 15 minutes.

VIDEO: {title}
TRANSCRIPT: {transcript[:8000]}

# One-Day Revision Sheet — {title}

## 📌 Top 20 Most Important Concepts
1. 
2. 
... (list all 20)

## 🔢 Key Formulas (if applicable)
| Formula | What it means | When to use |
(Table format)

## ⚠️ 5 Common Mistakes Students Make
1. 
2. 
3. 
4. 
5. 

## ❓ Frequently Asked Questions
Q: ?
A: 

Q: ?
A: 

Q: ?
A: 

## ✅ Final Revision Checklist
- [ ] I understand...
- [ ] I can explain...
- [ ] I know the difference between...
(10 checklist items)

## 🚀 One-Liner Revision
(Each concept in one line — rapid fire revision)

Make this sheet comprehensive enough to replace re-watching the lecture."""


def formulas_prompt(transcript: str, title: str) -> str:
    return f"""Extract ALL formulas, equations, and mathematical expressions from this lecture.

VIDEO: {title}
TRANSCRIPT: {transcript[:8000]}

# Formula Sheet — {title}

## All Formulas

### Formula 1: [Name]
**Formula**: [Write the formula]
**Variables**:
- Variable 1 = Description (Unit)
- Variable 2 = Description (Unit)
**Meaning**: What this formula calculates
**Conditions**: When to use / Assumptions
**Common Mistake**: What students often get wrong
**Category**: ⭐ Important / ⭐⭐ Very Important / ⭐⭐⭐ Must Memorize

---

### Formula 2: [Name]
(Same structure)

---

## Quick Reference Table
| Formula | Variables | Units | Category |
|---------|-----------|-------|----------|
| F = ma  | F,m,a     | N,kg,m/s² | ⭐⭐⭐ |

## Derivation Tips
(Any derivations mentioned in the lecture)

If this lecture has NO formulas, respond with: "No mathematical formulas found in this lecture. This appears to be a conceptual/theoretical topic." """


def explain_eli10_prompt(topic: str, transcript: str = "") -> str:
    context = f"\nFor context, here's some relevant information: {transcript[:3000]}" if transcript else ""

    return f"""Explain "{topic}" in a way that a 10-year-old can understand.{context}

# Understanding {topic} — Simplified!

## 🌟 The Simple Version
(Explain in the most basic, everyday language possible — no jargon)

## 🎯 The Main Idea
(One clear sentence that captures the whole concept)

## 🏠 Real-Life Analogy
(Use a relatable, everyday comparison — like comparing electricity to water in pipes)

**It's like this:**
[Analogy explanation]

Just like [everyday thing], {topic} works by...

## 📚 Step by Step
1. First...
2. Then...
3. Finally...

## 🌍 Real Examples You've Seen
- Example 1 (something from daily life)
- Example 2
- Example 3

## 🤔 Why Does This Matter?
(Why should a 10-year-old care about this?)

## ✅ The Textbook Version
(Now the proper definition, after they understand the concept)

## 🧪 Quick Test
Q: [Simple question to check understanding]
A: [Answer]

Make it fun, engaging, and genuinely simple. Use emojis where appropriate."""


def audio_revision_prompt(transcript: str, title: str, length: str = "5min") -> str:
    word_count = "400-500 words" if length == "5min" else "1200-1500 words"

    return f"""Create an AUDIO REVISION SCRIPT ({word_count}) for this lecture.
This will be converted to speech, so write it in a natural, spoken-word style.

VIDEO: {title}
TRANSCRIPT: {transcript[:8000]}

RULES:
- Write as if you're SPEAKING, not writing
- Use natural transitions: "Now let's talk about...", "Moving on...", "Here's the important part..."
- NO bullet points, NO markdown, NO symbols — plain flowing text only
- Keep sentences short and clear for easy listening
- Include brief pauses indicated by "..." where needed

SCRIPT:

Hello! Today we're going to quickly revise "{title}".

[Continue with the revision content in natural spoken style...]

[End with]: That's everything for today's revision of {title}. Make sure you review these concepts again before your exam. Good luck!

Write ONLY the script text. Nothing else."""


def doubts_prompt(question: str, transcript: str, title: str) -> str:
    return f"""A student is asking a doubt about this lecture. Answer it using the lecture content.

LECTURE: {title}
STUDENT QUESTION: {question}

LECTURE TRANSCRIPT (for reference):
{transcript[:6000]}

Answer the student's question:

## 🎯 Your Answer

[Provide a clear, accurate answer based on the lecture content]

## 📍 Where This Was Discussed
[Reference the specific part of the lecture where this was covered]

## 💡 Additional Explanation
[Add any helpful context or elaboration]

## 🔗 Related Concepts from This Lecture
[List 2-3 related things from the lecture that connect to this question]

If the question is not covered in the lecture, say so clearly and answer from your general knowledge."""


def playlist_master_notes_prompt(all_transcripts: str, playlist_title: str, video_titles: list) -> str:
    videos_list = "\n".join([f"{i+1}. {t}" for i, t in enumerate(video_titles)])
    return f"""Create MASTER NOTES for this entire playlist.

PLAYLIST: {playlist_title}
VIDEOS IN PLAYLIST:
{videos_list}

COMBINED TRANSCRIPT EXCERPTS:
{all_transcripts[:10000]}

# Master Notes — {playlist_title}

## 📚 Playlist Overview
(What this playlist covers as a whole)

## 🗺️ Learning Path
(How the videos connect and build on each other)

## Key Topics Covered
### Topic 1: [From video(s)]
### Topic 2: [From video(s)]
(Continue for all major topics)

## Master Formula Sheet
(All formulas from the entire playlist)

## Comprehensive Revision Points
(Top 30 points from the entire playlist)

## Knowledge Gaps & Missing Topics
(Topics that seem to be missing or incomplete)

## Complete Glossary
- Term: Definition
(All terms from all videos)"""
