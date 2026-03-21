import sqlite3
import json
from datetime import datetime
import streamlit as st
import pandas as pd
import os
from openai import OpenAI

DB_PATH = os.getenv("DB_PATH", "/tmp/career_bot.db")
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", None)
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)


st.set_page_config(page_title="Bright Future", page_icon="✨", layout="wide")

CAREER_CLUSTERS = {
    "Engineering & Technology": {
        "description": "Technical, systems-oriented, analytical work with a strong problem-solving core.",
        "studies": [
            "Computer Science",
            "Software Engineering",
            "Electrical Engineering",
            "Mechanical Engineering",
            "Cybersecurity",
        ],
        "examples": [
            "Software engineer",
            "Systems engineer",
            "Product engineer",
            "Cybersecurity analyst",
        ],
        "activities": [
            "Build a small app",
            "Try robotics or CAD",
            "Take part in a coding or STEM challenge",
        ],
    },
    "Research & Analysis": {
        "description": "Evidence-based, investigative work that rewards curiosity, depth, and structured thinking.",
        "studies": [
            "Data Science",
            "Economics",
            "Mathematics",
            "Physics",
            "Politics/Policy",
            "Biology",
        ],
        "examples": ["Data analyst", "Researcher", "Economist", "Policy analyst"],
        "activities": [
            "Run a mini research project",
            "Analyse a dataset",
            "Write a structured evidence brief",
        ],
    },
    "Creative & Design": {
        "description": "Idea generation, storytelling, design, and original expression.",
        "studies": [
            "Graphic Design",
            "Product Design",
            "Architecture",
            "Marketing",
            "Media",
            "Writing",
        ],
        "examples": ["Designer", "Brand strategist", "Content creator", "Creative director"],
        "activities": [
            "Build a portfolio in Canva or Figma",
            "Create a short video project",
            "Write and publish something",
        ],
    },
    "People, Health & Education": {
        "description": "People-centered paths involving empathy, development, support, and communication.",
        "studies": [
            "Psychology",
            "Education",
            "Speech Therapy",
            "Nursing",
            "Medicine",
            "Social Sciences",
        ],
        "examples": ["Teacher", "Psychologist", "Coach", "Healthcare professional"],
        "activities": [
            "Volunteer",
            "Tutor someone younger",
            "Interview a psychologist or teacher",
        ],
    },
    "Business, Law & Leadership": {
        "description": "Commercial, strategic, persuasive, and leadership-heavy environments.",
        "studies": ["Business", "Law", "Management", "International Relations", "Entrepreneurship"],
        "examples": ["Lawyer", "Consultant", "Sales leader", "Founder", "General manager"],
        "activities": [
            "Pitch an idea",
            "Join debate or Model UN",
            "Run a small event or project",
        ],
    },
    "Operations, Finance & Project Delivery": {
        "description": "Structured execution, planning, detail orientation, reliability, and process improvement.",
        "studies": ["Finance", "Accounting", "Project Management", "Operations", "Supply Chain"],
        "examples": ["Project manager", "Operations lead", "Financial analyst", "Supply chain manager"],
        "activities": [
            "Plan a project end-to-end",
            "Build a simple budget model",
            "Optimise a process in a spreadsheet",
        ],
    },
}

QUESTIONS = [
    {
        "key": "logic",
        "label": "I enjoy solving difficult problems, puzzles, or technical challenges.",
        "weights": {
            "Engineering & Technology": 3,
            "Research & Analysis": 2,
            "Operations, Finance & Project Delivery": 1,
        },
        "type": "ability",
    },
    {
        "key": "numbers",
        "label": "I like working with numbers, evidence, or patterns in data.",
        "weights": {
            "Research & Analysis": 3,
            "Operations, Finance & Project Delivery": 2,
            "Engineering & Technology": 2,
        },
        "type": "ability",
    },
    {
        "key": "design",
        "label": "I enjoy designing, imagining, writing, or creating original things.",
        "weights": {"Creative & Design": 4},
        "type": "energy",
    },
    {
        "key": "visual_creativity",
        "label": "I care a lot about aesthetics, visual style, and how things look and feel.",
        "weights": {"Creative & Design": 4},
        "type": "energy",
    },
    {
        "key": "helping",
        "label": "I naturally notice how people feel and want to help them.",
        "weights": {"People, Health & Education": 3, "Business, Law & Leadership": 1},
        "type": "energy",
    },
    {
        "key": "persuasion",
        "label": "I like presenting, persuading, debating, or influencing people.",
        "weights": {"Business, Law & Leadership": 2, "Creative & Design": 1},
        "type": "energy",
    },
    {
        "key": "organising",
        "label": "I enjoy organising tasks, planning ahead, and keeping things on track.",
        "weights": {
            "Operations, Finance & Project Delivery": 3,
            "Business, Law & Leadership": 1,
        },
        "type": "ability",
    },
    {
        "key": "independent",
        "label": "I work well independently and can stay focused without much supervision.",
        "weights": {
            "Research & Analysis": 2,
            "Engineering & Technology": 2,
            "Creative & Design": 1,
        },
        "type": "style",
    },
    {
        "key": "team_energy",
        "label": "I get energy from teamwork, interaction, and being around people.",
        "weights": {
            "Business, Law & Leadership": 2,
            "People, Health & Education": 2,
        },
        "type": "style",
    },
    {
        "key": "building",
        "label": "I like building, fixing, making, or understanding how things work.",
        "weights": {
            "Engineering & Technology": 3,
            "Operations, Finance & Project Delivery": 1,
        },
        "type": "energy",
    },
    {
        "key": "curiosity",
        "label": "I enjoy going deep into a topic and understanding the why behind things.",
        "weights": {
            "Research & Analysis": 3,
            "Engineering & Technology": 1,
            "People, Health & Education": 1,
        },
        "type": "energy",
    },
    {
        "key": "stability",
        "label": "A stable and predictable career matters a lot to me.",
        "weights": {
            "Operations, Finance & Project Delivery": 2,
            "People, Health & Education": 2,
        },
        "type": "values",
    },
    {
        "key": "achievement",
        "label": "I am strongly motivated by achievement, leadership, or standing out.",
        "weights": {
            "Business, Law & Leadership": 2,
            "Creative & Design": 1,
        },
        "type": "values",
    },
    {
        "key": "precision",
        "label": "I am comfortable with details and usually catch mistakes others miss.",
        "weights": {
            "Operations, Finance & Project Delivery": 3,
            "Research & Analysis": 1,
        },
        "type": "ability",
    },
    {
        "key": "abstract",
        "label": "I like big ideas, theories, and conceptual thinking.",
        "weights": {
            "Research & Analysis": 2,
            "Creative & Design": 2,
            "Business, Law & Leadership": 1,
        },
        "type": "style",
    },
]

UNIVERSITY_DATA = {
    "UK": {
        "Engineering & Technology": [
            "Imperial College London",
            "University of Manchester",
            "University of Southampton",
            "University of Bristol",
        ],
        "Research & Analysis": [
            "University of Oxford",
            "UCL",
            "University of Warwick",
            "London School of Economics",
        ],
        "Creative & Design": [
            "University of the Arts London",
            "Loughborough University",
            "Kingston University London",
            "University of Leeds",
        ],
        "People, Health & Education": [
            "UCL",
            "University of Edinburgh",
            "University of Manchester",
            "University of Glasgow",
        ],
        "Business, Law & Leadership": [
            "LSE",
            "University of Warwick",
            "University of Bristol",
            "King's College London",
        ],
        "Operations, Finance & Project Delivery": [
            "University of Warwick",
            "Bayes Business School",
            "University of Bath",
            "University of Leeds",
        ],
    },
    "France": {
        "Engineering & Technology": ["École Polytechnique", "INSA Lyon", "UTC Compiègne", "EPITA"],
        "Research & Analysis": ["PSL", "Sorbonne Université", "Université Paris-Saclay", "Sciences Po"],
        "Creative & Design": ["Strate", "ENSCI-Les Ateliers", "École Boulle", "LISAA"],
        "People, Health & Education": [
            "Université Paris Cité",
            "Sorbonne Université",
            "Université de Strasbourg",
            "Université de Bordeaux",
        ],
        "Business, Law & Leadership": [
            "HEC Paris",
            "ESSEC",
            "Sciences Po",
            "Université Paris 1 Panthéon-Sorbonne",
        ],
        "Operations, Finance & Project Delivery": [
            "ESCP",
            "emlyon",
            "Université Paris Dauphine-PSL",
            "IAE Lyon",
        ],
    },
    "Switzerland": {
        "Engineering & Technology": ["ETH Zürich", "EPFL", "ZHAW", "FHNW"],
        "Research & Analysis": ["ETH Zürich", "EPFL", "University of Zurich", "University of Geneva"],
        "Creative & Design": ["HEAD Genève", "ECAL", "ZHdK", "SUPSI"],
        "People, Health & Education": [
            "University of Geneva",
            "University of Lausanne",
            "Bern University of Applied Sciences",
            "University of Fribourg",
        ],
        "Business, Law & Leadership": [
            "University of St.Gallen",
            "HEC Lausanne",
            "University of Geneva",
            "University of Zurich",
        ],
        "Operations, Finance & Project Delivery": [
            "University of St.Gallen",
            "HEC Lausanne",
            "ZHAW",
            "SUPSI",
        ],
    },
}


def init_db():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                profile_name TEXT NOT NULL,
                profile_code TEXT NOT NULL,
                respondent_name TEXT,
                respondent_role TEXT,
                relation_weight REAL,
                target_age INTEGER,
                country_focus TEXT,
                favourite_subjects TEXT,
                least_favourite_subjects TEXT,
                dream_day TEXT,
                raw_answers TEXT,
                raw_scores TEXT,
                normalized_scores TEXT,
                created_at TEXT NOT NULL
            )
            """
        )
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Database initialization failed: {e}")
        raise


def save_assessment(row):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO assessments (
                profile_name, profile_code, respondent_name, respondent_role, relation_weight,
                target_age, country_focus, favourite_subjects, least_favourite_subjects,
                dream_day, raw_answers, raw_scores, normalized_scores, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            row,
        )
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Failed to save assessment: {e}")
        raise


def load_assessments(profile_code):
    try:
        conn = get_connection()
        df = pd.read_sql_query(
            "SELECT * FROM assessments WHERE profile_code = ? ORDER BY created_at DESC",
            conn,
            params=(profile_code,),
        )
        conn.close()
        return df
    except Exception as e:
        st.error(f"Failed to load assessments: {e}")
        return pd.DataFrame()


def get_profile_history(profile_code):
    df = load_assessments(profile_code)
    if df.empty:
        return df
    df = df.copy()
    df["created_at_dt"] = pd.to_datetime(df["created_at"], errors="coerce")
    df = df.sort_values("created_at_dt")
    return df


def compare_latest_to_previous(df):
    if df.empty or len(df) < 2:
        return None

    df = df.copy().sort_values("created_at")
    latest = df.iloc[-1]
    previous = df.iloc[-2]

    latest_scores = json.loads(latest["normalized_scores"])
    previous_scores = json.loads(previous["normalized_scores"])

    comparison_rows = []
    for cluster in CAREER_CLUSTERS.keys():
        latest_val = float(latest_scores.get(cluster, 0))
        previous_val = float(previous_scores.get(cluster, 0))
        delta = round(latest_val - previous_val, 1)
        comparison_rows.append(
            {
                "Cluster": cluster,
                "Previous %": previous_val,
                "Latest %": latest_val,
                "Change": delta,
            }
        )

    comp_df = pd.DataFrame(comparison_rows).sort_values("Latest %", ascending=False)
    return {
        "latest_date": latest["created_at"],
        "previous_date": previous["created_at"],
        "comparison_df": comp_df,
    }


def build_history_chart_df(df):
    if df.empty:
        return pd.DataFrame()

    rows = []
    df = df.copy().sort_values("created_at")

    for _, row in df.iterrows():
        scores = json.loads(row["normalized_scores"])
        for cluster, score in scores.items():
            rows.append(
                {
                    "created_at": row["created_at"],
                    "Cluster": cluster,
                    "Fit %": score,
                }
            )

    return pd.DataFrame(rows)


def score_answers(answers):
    raw = {k: 0 for k in CAREER_CLUSTERS}
    for q in QUESTIONS:
        answer = int(answers.get(q["key"], 3))
        for cluster, weight in q["weights"].items():
            raw[cluster] += answer * weight
    max_score = max(raw.values()) if raw else 1
    normalized = {k: round((v / max_score) * 100, 1) if max_score else 0 for k, v in raw.items()}
    return raw, normalized


def apply_context_boost(raw_scores, favourite_subjects, least_subjects, dream_day):
    positive_text = f"{favourite_subjects} {dream_day}".lower()
    negative_text = f"{least_subjects}".lower()

    positive_keywords = {
        "Creative & Design": [
            "art", "design", "drawing", "fashion", "media", "photography",
            "film", "writing", "creative", "architecture", "music", "drama",
            "illustration", "animation", "theatre",
        ],
        "Engineering & Technology": [
            "math", "physics", "coding", "computer", "engineering",
            "robotics", "technology", "mechanical", "software",
        ],
        "Research & Analysis": [
            "economics", "science", "research", "analysis", "data",
            "history", "politics", "geography",
        ],
        "People, Health & Education": [
            "biology", "psychology", "teaching", "helping", "health",
            "medicine", "children", "care",
        ],
        "Business, Law & Leadership": [
            "business", "law", "debate", "leadership", "entrepreneurship",
            "management", "public speaking",
        ],
        "Operations, Finance & Project Delivery": [
            "finance", "accounting", "organisation", "planning",
            "project", "logistics", "spreadsheet",
        ],
    }

    negative_keywords = {
        "Creative & Design": ["art", "design", "drawing", "media"],
        "Engineering & Technology": ["math", "physics", "coding", "technology"],
        "Research & Analysis": ["economics", "science", "data", "history"],
        "People, Health & Education": ["biology", "psychology", "health"],
        "Business, Law & Leadership": ["business", "law", "debate"],
        "Operations, Finance & Project Delivery": ["finance", "accounting", "planning"],
    }

    for cluster, keywords in positive_keywords.items():
        matches = sum(1 for kw in keywords if kw in positive_text)
        raw_scores[cluster] += matches * 3

    for cluster, keywords in negative_keywords.items():
        matches = sum(1 for kw in keywords if kw in negative_text)
        raw_scores[cluster] -= matches * 1.5

    return raw_scores


def aggregate_scores(df):
    if df.empty:
        return None

    totals = {k: 0.0 for k in CAREER_CLUSTERS}
    total_weight = 0.0

    for _, row in df.iterrows():
        weight = float(row["relation_weight"] or 1.0)
        score_dict = json.loads(row["raw_scores"])
        for k, v in score_dict.items():
            totals[k] += v * weight
        total_weight += weight

    if total_weight == 0:
        total_weight = 1.0

    averaged = {k: round(v / total_weight, 2) for k, v in totals.items()}
    max_score = max(averaged.values()) if averaged else 1
    normalized = {k: round((v / max_score) * 100, 1) if max_score else 0 for k, v in averaged.items()}
    return averaged, normalized


def top_matches(scores, n=3):
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)[:n]


def role_default_weight(role):
    return {
        "Self": 1.0,
        "Parent": 0.85,
        "Friend": 0.6,
        "Teacher": 0.8,
        "Coach/Mentor": 0.75,
    }.get(role, 0.7)


def generate_study_advice(cluster, country):
    studies = CAREER_CLUSTERS[cluster]["studies"]
    universities = UNIVERSITY_DATA.get(country, {}).get(cluster, [])
    return studies, universities


def build_ai_prompt(
    profile_name,
    age,
    country_focus,
    favourite_subjects,
    least_subjects,
    dream_day,
    answers,
    normalized_scores,
    respondent_role=None,
    followup_answers=None,
):
    top_clusters = top_matches(normalized_scores, n=3)

    return f"""
You are an outstanding career discovery adviser for teenagers.

Your role is to help a young person understand themselves, see realistic possibilities, and feel encouraged about the future.

The aptitude results are the foundation of the analysis.
Use the score pattern as the primary structure, then use the follow-up answers to confirm, refine, or challenge the initial picture.

Be concise, sharp, motivating, and practical.
Do NOT ramble.
Do NOT give a huge report.
Do NOT try to cover everything.
Prioritise clarity over completeness.

Profile:
- Name: {profile_name}
- Age: {age}
- Country focus for studies: {country_focus}
- Respondent role: {respondent_role or "Unknown"}

Structured inputs:
- Favourite subjects: {favourite_subjects}
- Least favourite subjects: {least_subjects}
- Ideal working day: {dream_day}

Question responses:
{json.dumps(answers, indent=2)}

Follow-up interview answers:
{json.dumps(followup_answers or {}, indent=2)}

Top cluster scores:
{json.dumps(top_clusters, indent=2)}

All normalized scores:
{json.dumps(normalized_scores, indent=2)}

Return your answer using these exact headings only:

## 1. Big-picture encouragement
Write a short opening that feels encouraging, grounded, and intelligent.
Help the student feel possibility, not pressure.

## 2. What seems strongest in this profile
Give a short summary of:
- strongest strengths
- likely motivations
- what kind of environments may suit this person

Keep it to one short paragraph.

## 3. Three strong future directions
Give exactly 3 directions.
For each one include:
- Why it fits
- Example roles
- Why it could stay stimulating

Keep each direction concise.

## 4. What to focus on now
Give practical guidance on:
- school subjects to prioritise
- what to improve over the next 12 months
- useful habits or strengths to build

Be concrete.

## 5. AI: threat or advantage?
For each of the 3 directions, give:
- AI replacement risk score out of 10
- AI enablement value score out of 10
- one short sentence explaining the difference

Be balanced. AI is not just replacement.

## 6. Next 90 days
Give exactly 3 practical next actions.

Important rules:
- Do not say "you should definitely become X"
- Do not be overly rigid
- Do not sound elitist or snobbish
- Do not imply only traditional prestige careers matter
- If creative signals are strong, do not default to business or law unless clearly dominant
- Treat creative + analytical or creative + leadership combinations as potentially powerful hybrids
- Keep the whole response compact, useful, and energising
"""
def get_ai_interpretation(
    profile_name,
    age,
    country_focus,
    favourite_subjects,
    least_subjects,
    dream_day,
    answers,
    normalized_scores,
    respondent_role=None,
    followup_answers=None,
):
    if client is None:
        return "AI interpretation is not available because no OPENAI_API_KEY is configured in Streamlit secrets."

    prompt = build_ai_prompt(
        profile_name=profile_name,
        age=age,
        country_focus=country_focus,
        favourite_subjects=favourite_subjects,
        least_subjects=least_subjects,
        dream_day=dream_day,
        answers=answers,
        normalized_scores=normalized_scores,
        respondent_role=respondent_role,
        followup_answers=followup_answers,
    )

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )
        return response.output_text
    except Exception as e:
        return f"AI interpretation failed: {e}"


def get_ai_followup_questions(
    profile_name,
    age,
    country_focus,
    favourite_subjects,
    least_subjects,
    dream_day,
    answers,
    normalized_scores,
):
    fallback_questions = [
        "What kinds of activities make you lose track of time?",
        "Do you prefer creating something new, solving a problem, or helping someone?",
        "What school tasks feel most natural to you?",
        "What kind of people or environments energise you most?",
        "If nobody judged you, what would you be most excited to explore next?",
    ]

    if client is None:
        return fallback_questions

    prompt = f"""
You are helping a teenager explore future study and career direction.

Based on this profile, generate exactly 5 smart follow-up questions that will help clarify:
- true interests vs surface interests
- working style
- people vs systems orientation
- creative identity
- appetite for leadership, structure, and uncertainty

Profile:
- Name: {profile_name}
- Age: {age}
- Country focus: {country_focus}
- Favourite subjects: {favourite_subjects}
- Least favourite subjects: {least_subjects}
- Dream day: {dream_day}
- Answers: {json.dumps(answers)}
- Scores: {json.dumps(normalized_scores)}

Rules:
- Ask exactly 5 questions
- Questions should be short, clear, and teenager-friendly
- Avoid corporate language
- Avoid deterministic phrasing
- Focus on surfacing personality, motivation, and preferences
- Return only a valid JSON list of 5 strings
"""

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )
        text = response.output_text.strip()
        questions = json.loads(text)
        if isinstance(questions, list) and len(questions) == 5:
            return questions
        return fallback_questions
    except Exception:
        return fallback_questions


def get_ai_deep_dive(
    topic,
    profile_name,
    age,
    country_focus,
    favourite_subjects,
    least_subjects,
    dream_day,
    answers,
    normalized_scores,
    final_ai_text="",
):
    if client is None:
        return "Deep-dive AI is not available because no OPENAI_API_KEY is configured."

    prompt = f"""
You are helping a teenager explore their future in a practical and encouraging way.

Student profile:
- Name: {profile_name}
- Age: {age}
- Country focus: {country_focus}
- Favourite subjects: {favourite_subjects}
- Least favourite subjects: {least_subjects}
- Ideal working day: {dream_day}

Aptitude answers:
{json.dumps(answers, indent=2)}

Aptitude score pattern:
{json.dumps(normalized_scores, indent=2)}

Current roadmap summary:
{final_ai_text}

The aptitude results are the foundation of the analysis.
Use the score pattern as the primary structure, then use the roadmap context to go deeper.

The student wants to explore this topic in more depth:
{topic}

Your task:
- answer only this topic
- keep it clear, motivating, and practical
- avoid repeating the full roadmap
- be specific, not generic
- make the answer useful for a teenager and parent
- keep it concise but insightful

If the topic is about AI, explain both:
- replacement risk
- how AI can be used as an advantage in that field

If the topic is about studies or universities:
- focus on pathways and examples
- do not pretend admissions are guaranteed
"""

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )
        return response.output_text
    except Exception as e:
        return f"Deep-dive AI failed: {e}"


init_db()

if "show_results" not in st.session_state:
    st.session_state["show_results"] = False

if "followup_ready" not in st.session_state:
    st.session_state["followup_ready"] = False

if "roadmap_ready" not in st.session_state:
    st.session_state["roadmap_ready"] = False

if "final_ai_text" not in st.session_state:
    st.session_state["final_ai_text"] = None

if "deep_dive_text" not in st.session_state:
    st.session_state["deep_dive_text"] = None

st.title("✨ Bright Future")
st.subheader("Discover what could excite, challenge, and inspire your future")

st.write(
    "This is not about choosing a career today.\n\n"
    "It’s about discovering what energises you, what you're naturally good at, "
    "and what paths might lead to a future that feels meaningful and exciting."
)

with st.expander("How to use Bright Future"):
    st.markdown(
        """
        **Bright Future is not here to box you in.**

        It helps you:
        - spot patterns in what energises you
        - explore realistic and stimulating future directions
        - think about studies, internships, and skills to build
        - understand how AI may change different career paths

        The goal is not to choose your whole life today.

        The goal is to get clearer, step by step.
        """
    )

if client is None:
    st.warning("AI interpretation is not active yet. Add OPENAI_API_KEY to Streamlit secrets to enable it.")

page = st.sidebar.radio("Your journey", ["Start discovery", "View your progress"])

st.sidebar.markdown("---")
st.sidebar.markdown("### What this is for")
st.sidebar.markdown(
    """
    Bright Future helps students:
    - understand themselves better
    - explore possible futures
    - build confidence without pressure
    """
)

if page == "Start discovery":
    st.progress(25, text="Step 1 of 4 — Build your starting profile")
    st.header("Discover your starting profile")

    col1, col2, col3 = st.columns(3)
    with col1:
        profile_name = st.text_input("Student name", placeholder="e.g. Emma Smith")
    with col2:
        profile_code = st.text_input("Profile code", placeholder="e.g. emma-2026")
    with col3:
        age = st.number_input("Age", min_value=12, max_value=25, value=16)

    col4, col5, col6 = st.columns(3)
    with col4:
        respondent_name = st.text_input("Your name", placeholder="e.g. Mum / Mr Jones")
    with col5:
        respondent_role = st.selectbox(
            "You are completing this as",
            ["Self", "Parent", "Teacher", "Friend", "Coach/Mentor"],
        )
    with col6:
        country_focus = st.selectbox("Country focus for studies", ["France", "UK", "Switzerland"])

    default_weight = role_default_weight(respondent_role)
    relation_weight = st.slider(
        "Observer weight",
        min_value=0.4,
        max_value=1.2,
        value=float(default_weight),
        step=0.05,
        help="Higher = greater influence when combining multiple responses. Self should usually be highest.",
    )

    st.subheader("Tell us how this person tends to think and work")
    st.caption("1 = strongly disagree, 5 = strongly agree")
    answers = {}
    qcols = st.columns(2)
    for idx, q in enumerate(QUESTIONS):
        with qcols[idx % 2]:
            answers[q["key"]] = st.slider(q["label"], 1, 5, 3, key=f"{respondent_role}_{q['key']}_{idx}")

    st.subheader("A little more context")
    favourite_subjects = st.text_input("Favourite subjects", placeholder="e.g. Maths, Biology, Art")
    least_subjects = st.text_input("Least favourite subjects", placeholder="e.g. Chemistry, History")
    dream_day = st.text_area(
        "Describe an ideal working day",
        placeholder="What would they be doing? Working with people, ideas, data, design, machines...",
    )

    col_a, col_b = st.columns([3, 1])
    with col_a:
        save_clicked = st.button("Start discovery", type="primary")
    with col_b:
        if st.button("Reset"):
            st.session_state["show_results"] = False
            st.session_state["followup_ready"] = False
            st.session_state["roadmap_ready"] = False
            st.session_state["final_ai_text"] = None
            st.session_state["deep_dive_text"] = None
            for key in [
                "saved_profile_name",
                "saved_profile_code",
                "saved_age",
                "saved_country_focus",
                "saved_favourite_subjects",
                "saved_least_subjects",
                "saved_dream_day",
                "saved_answers",
                "saved_normalized_scores",
                "saved_respondent_role",
            ]:
                st.session_state.pop(key, None)
            st.rerun()

    if save_clicked:
        if not profile_name or not profile_code:
            st.error("Add a student name and profile code first.")
        else:
            raw_scores, _ = score_answers(answers)
            raw_scores = apply_context_boost(
                raw_scores,
                favourite_subjects=favourite_subjects,
                least_subjects=least_subjects,
                dream_day=dream_day,
            )

            max_score = max(raw_scores.values()) if raw_scores else 1
            normalized_scores = {
                k: round((v / max_score) * 100, 1) if max_score else 0
                for k, v in raw_scores.items()
            }

            now = datetime.utcnow().isoformat(timespec="seconds")
            save_assessment(
                (
                    profile_name,
                    profile_code.lower().strip(),
                    respondent_name,
                    respondent_role,
                    relation_weight,
                    age,
                    country_focus,
                    favourite_subjects,
                    least_subjects,
                    dream_day,
                    json.dumps(answers),
                    json.dumps(raw_scores),
                    json.dumps(normalized_scores),
                    now,
                )
            )

            st.session_state["show_results"] = True
            st.session_state["followup_ready"] = True
            st.session_state["roadmap_ready"] = False
            st.session_state["final_ai_text"] = None
            st.session_state["deep_dive_text"] = None

            st.session_state["saved_profile_name"] = profile_name
            st.session_state["saved_profile_code"] = profile_code.lower().strip()
            st.session_state["saved_age"] = age
            st.session_state["saved_country_focus"] = country_focus
            st.session_state["saved_favourite_subjects"] = favourite_subjects
            st.session_state["saved_least_subjects"] = least_subjects
            st.session_state["saved_dream_day"] = dream_day
            st.session_state["saved_answers"] = answers
            st.session_state["saved_normalized_scores"] = normalized_scores
            st.session_state["saved_respondent_role"] = respondent_role

    if st.session_state.get("show_results"):
        normalized_scores = st.session_state["saved_normalized_scores"]
        saved_answers = st.session_state["saved_answers"]

        if st.session_state.get("followup_ready") and not st.session_state.get("roadmap_ready"):
            st.progress(60, text="Step 2 of 4 — Refine your profile")
            st.success("Great start. You’ve already revealed some strong signals.")
            st.info("Now let’s go a bit deeper before revealing your full Bright Future roadmap.")

            st.markdown("## Level up your profile")
            followup_questions = get_ai_followup_questions(
                profile_name=st.session_state["saved_profile_name"],
                age=st.session_state["saved_age"],
                country_focus=st.session_state["saved_country_focus"],
                favourite_subjects=st.session_state["saved_favourite_subjects"],
                least_subjects=st.session_state["saved_least_subjects"],
                dream_day=st.session_state["saved_dream_day"],
                answers=saved_answers,
                normalized_scores=normalized_scores,
            )

            followup_answers = {}
            for i, question in enumerate(followup_questions, start=1):
                followup_answers[f"q{i}"] = st.text_area(
                    f"{i}. {question}",
                    key=f"followup_{st.session_state['saved_profile_code']}_{i}",
                )

            if st.button("Reveal my Bright Future", key="generate_ai"):
                with st.spinner("Building your roadmap..."):
                    ai_text = get_ai_interpretation(
                        profile_name=st.session_state["saved_profile_name"],
                        age=st.session_state["saved_age"],
                        country_focus=st.session_state["saved_country_focus"],
                        favourite_subjects=st.session_state["saved_favourite_subjects"],
                        least_subjects=st.session_state["saved_least_subjects"],
                        dream_day=st.session_state["saved_dream_day"],
                        answers=saved_answers,
                        normalized_scores=normalized_scores,
                        respondent_role=st.session_state["saved_respondent_role"],
                        followup_answers=followup_answers,
                    )
                st.session_state["final_ai_text"] = ai_text
                st.session_state["roadmap_ready"] = True
                st.session_state["followup_ready"] = False
                st.rerun()

        if st.session_state.get("roadmap_ready"):
            st.progress(100, text="Step 3 of 4 — Your Bright Future reveal")
            st.markdown("## 🌟 Your Bright Future")
            st.write(
                "This is your current best-fit direction based on how you think, what you enjoy, "
                "and what seems to energise you most."
            )

            top = top_matches(normalized_scores)
            metric_cols = st.columns(len(top))
            for i, (cluster, score) in enumerate(top):
                with metric_cols[i]:
                    st.metric(label=cluster, value=f"{score}%")

            st.markdown("### What your aptitude profile suggests")
            for cluster, score in top:
                studies, universities = generate_study_advice(cluster, st.session_state["saved_country_focus"])
                st.markdown(f"**{cluster} — {score}%**")
                st.write(CAREER_CLUSTERS[cluster]["description"])
                st.write("Suggested further studies: " + ", ".join(studies[:5]))
                if universities:
                    st.write("Starter university ideas: " + ", ".join(universities[:4]))

            score_df = pd.DataFrame(
                {"Cluster": list(normalized_scores.keys()), "Fit %": list(normalized_scores.values())}
            ).sort_values("Fit %", ascending=False)
            st.bar_chart(score_df.set_index("Cluster"))
            st.info("Before jumping to conclusions, explore what these paths actually feel like.")     
            # ---------------------------
            # 🔍 Deep Dive Exploration
            # ---------------------------

            if "deep_dive_ready" not in st.session_state:
                st.session_state["deep_dive_ready"] = False

            if st.button("🔍 Explore these paths deeper"):
                st.session_state["deep_dive_ready"] = True

            if st.session_state["deep_dive_ready"]:
                st.subheader("🔍 Explore before deciding")

                st.write("Click into any path to understand what it's REALLY like.")

                for cluster, score in top:
                    if st.button(f"Explore {cluster}", key=f"explore_{cluster}"):

                        deep_prompt = f"""
            Explain what it is REALLY like to work in {cluster}.

            Be honest, not idealistic.

            Include:
            - what people actually do day-to-day
            - what kind of people thrive here
            - what might feel boring or difficult
            - what makes it rewarding

            Make it engaging and realistic for a teenager.
            """

            try:
                response = client.responses.create(
                    model="gpt-4.1-mini",
                    input=deep_prompt,
                )
                st.write(response.output_text)
            except Exception as e:
                st.error(f"Deep dive failed: {e}")
            st.markdown("## Compare with previous results")
            history_df = get_profile_history(st.session_state["saved_profile_code"])
            comparison = compare_latest_to_previous(history_df)

            if comparison is None:
                st.info("No previous saved result yet for this profile. Save another run later to compare changes over time.")
            else:
                st.write(
                    f"Comparing latest result from **{comparison['latest_date']}** "
                    f"with previous result from **{comparison['previous_date']}**"
                )
                st.dataframe(comparison["comparison_df"], use_container_width=True)

                history_chart_df = build_history_chart_df(history_df)
                if not history_chart_df.empty:
                    pivot_df = history_chart_df.pivot(index="created_at", columns="Cluster", values="Fit %")
                    st.line_chart(pivot_df)

            if st.session_state.get("final_ai_text"):
                st.markdown("## Your integrated roadmap")
                st.write(st.session_state["final_ai_text"])

                st.markdown("## Explore this result further")
                st.write("Pick one area to explore in more depth.")

                deep_dive_topic = st.selectbox(
                    "Choose a topic",
                    [
                        "Why this profile fits",
                        "Best subjects to focus on",
                        "Higher education options",
                        "Internship and real-world exposure ideas",
                        "Skills to build outside school",
                        "How AI may affect these career directions",
                        "What to improve over the next year",
                        "How to choose between two possible paths",
                    ],
                    key="deep_dive_topic",
                )

                if st.button("Explore this topic", key="explore_topic"):
                    with st.spinner("Exploring this topic..."):
                        deep_dive_text = get_ai_deep_dive(
                            topic=deep_dive_topic,
                            profile_name=st.session_state["saved_profile_name"],
                            age=st.session_state["saved_age"],
                            country_focus=st.session_state["saved_country_focus"],
                            favourite_subjects=st.session_state["saved_favourite_subjects"],
                            least_subjects=st.session_state["saved_least_subjects"],
                            dream_day=st.session_state["saved_dream_day"],
                            answers=st.session_state["saved_answers"],
                            normalized_scores=st.session_state["saved_normalized_scores"],
                            final_ai_text=st.session_state["final_ai_text"],
                        )
                    st.session_state["deep_dive_text"] = deep_dive_text

                if st.session_state.get("deep_dive_text"):
                    st.markdown(f"### Deep dive: {deep_dive_topic}")
                    st.write(st.session_state["deep_dive_text"])

                st.markdown("---")
                st.markdown(
                    "**Remember:** You don’t need to have everything figured out. "
                    "The goal is to explore, test, and learn. The clearer your actions, "
                    "the brighter your future becomes."
                )

else:
    st.header("View your progress")
    profile_code_lookup = st.text_input("Enter profile code", placeholder="e.g. emma-2026")

    if profile_code_lookup:
        df = load_assessments(profile_code_lookup.lower().strip())
        if df.empty:
            st.warning("No assessments found for that profile code yet.")
        else:
            st.subheader("Responses on file")
            view_df = df[
                [
                    "created_at",
                    "respondent_name",
                    "respondent_role",
                    "relation_weight",
                    "country_focus",
                    "favourite_subjects",
                    "least_favourite_subjects",
                ]
            ].copy()
            st.dataframe(view_df, use_container_width=True)

            aggregated = aggregate_scores(df)
            if aggregated:
                raw_avg, norm_avg = aggregated
                st.subheader("Combined best-fit profile")
                top = top_matches(norm_avg)

                for i, (cluster, score) in enumerate(top, start=1):
                    studies, universities = generate_study_advice(cluster, df.iloc[0]["country_focus"])
                    st.markdown(f"### {i}. {cluster} — {score}% fit")
                    st.write(CAREER_CLUSTERS[cluster]["description"])
                    st.write("Likely further studies: " + ", ".join(studies[:5]))
                    if universities:
                        st.write("Starter university shortlist: " + ", ".join(universities[:4]))
                    st.write("Career examples: " + ", ".join(CAREER_CLUSTERS[cluster]["examples"]))
                    st.write("Real-world tests to run next:")
                    for act in CAREER_CLUSTERS[cluster]["activities"]:
                        st.write(f"- {act}")

                score_df = pd.DataFrame(
                    {"Cluster": list(norm_avg.keys()), "Fit %": list(norm_avg.values())}
                ).sort_values("Fit %", ascending=False)
                st.bar_chart(score_df.set_index("Cluster"))

                st.subheader("History and comparison")
                history_df = get_profile_history(profile_code_lookup.lower().strip())
                comparison = compare_latest_to_previous(history_df)

                if comparison is None:
                    st.info("No previous saved run yet for this profile.")
                else:
                    st.write(
                        f"Comparing latest result from **{comparison['latest_date']}** "
                        f"with previous result from **{comparison['previous_date']}**"
                    )
                    st.dataframe(comparison["comparison_df"], use_container_width=True)

                history_chart_df = build_history_chart_df(history_df)
                if not history_chart_df.empty:
                    pivot_df = history_chart_df.pivot(index="created_at", columns="Cluster", values="Fit %")
                    st.line_chart(pivot_df)

                st.subheader("AI interpretation of the combined profile")

                combined_answers = {
                    "note": "This is a combined multi-observer profile. Interpret the weighted score pattern and the open-text inputs from the saved records."
                }

                combined_favourites = " | ".join(
                    [str(x) for x in df["favourite_subjects"].dropna().tolist() if str(x).strip()]
                )
                combined_least = " | ".join(
                    [str(x) for x in df["least_favourite_subjects"].dropna().tolist() if str(x).strip()]
                )
                combined_dream_day = " | ".join(
                    [str(x) for x in df["dream_day"].dropna().tolist() if str(x).strip()]
                )

                if st.button("Generate combined AI interpretation", key="generate_combined_ai"):
                    with st.spinner("Generating combined AI interpretation..."):
                        ai_text = get_ai_interpretation(
                            profile_name=df.iloc[0]["profile_name"],
                            age=int(df.iloc[0]["target_age"]) if pd.notnull(df.iloc[0]["target_age"]) else 16,
                            country_focus=df.iloc[0]["country_focus"],
                            favourite_subjects=combined_favourites,
                            least_subjects=combined_least,
                            dream_day=combined_dream_day,
                            answers=combined_answers,
                            normalized_scores=norm_avg,
                            respondent_role="Combined profile",
                            followup_answers=None,
                        )
                    st.write(ai_text)

                st.subheader("What to do next")
                st.markdown(
                    """
                    1. Take the top 2 or 3 clusters seriously, not just the top 1.
                    2. Test each one with a real activity, shadowing experience, or short project.
                    3. Re-run the assessment after that exposure. Teenagers change fast; their clarity improves with evidence.
                    4. Build the university shortlist only after the career clusters and preferred subjects start to stabilise.
                    """
                )

                st.subheader("Raw data export")
                csv = df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "Download profile data (CSV)",
                    data=csv,
                    file_name=f"{profile_code_lookup}_career_profile.csv",
                    mime="text/csv",
                )
