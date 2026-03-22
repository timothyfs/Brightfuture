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

def login_screen():
    st.markdown("## 🔐 Bright Future is private")
    st.write("Please sign in with Google to access your profiles and history.")

    if st.button("Log in with Google"):
        st.login()

# --- AUTH GATE ---
if not st.user.is_logged_in:
    login_screen()
    st.stop()

APP_CSS = """
<style>
.hero-wrap {
    text-align: center;
    padding: 1.2rem 0 1.4rem 0;
    margin-bottom: 0.6rem;
}
.hero-title {
    font-size: 2.6rem;
    font-weight: 800;
    margin: 0;
    letter-spacing: -0.02em;
}
.hero-subtitle {
    font-size: 1.08rem;
    color: #6b7280;
    margin-top: 0.35rem;
}
.card {
    background: rgba(255,255,255,0.92);
    border: 1px solid rgba(0,0,0,0.06);
    border-radius: 18px;
    padding: 1rem 1rem 0.35rem 1rem;
    margin: 0.5rem 0 1rem 0;
    box-shadow: 0 6px 18px rgba(0,0,0,0.04);
}
.section-kicker {
    font-size: 0.85rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: #7c3aed;
    margin-bottom: 0.2rem;
}
.small-muted {
    color: #6b7280;
    font-size: 0.95rem;
}
</style>
"""
st.markdown(APP_CSS, unsafe_allow_html=True)

def render_hero():
    st.markdown(
        """
        <div class="hero-wrap">
            <div class="hero-title">✨ Bright Future</div>
            <div class="hero-subtitle">Discover what could excite, challenge, and inspire your future</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def card_start(kicker=None, title=None, subtitle=None):
    st.markdown('<div class="card">', unsafe_allow_html=True)
    if kicker:
        st.markdown(f'<div class="section-kicker">{kicker}</div>', unsafe_allow_html=True)
    if title:
        st.markdown(f"### {title}")
    if subtitle:
        st.markdown(f'<div class="small-muted">{subtitle}</div>', unsafe_allow_html=True)

def card_end():
    st.markdown('</div>', unsafe_allow_html=True)

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


def ensure_column_exists(conn, table_name, column_name, column_def):
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info({table_name})")
    existing = [row[1] for row in cur.fetchall()]
    if column_name not in existing:
        cur.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_def}")


def init_db():
    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS assessments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT,
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
                super_powers TEXT,
                raw_answers TEXT,
                raw_scores TEXT,
                normalized_scores TEXT,
                final_ai_text TEXT,
                created_at TEXT NOT NULL
            )
            """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT UNIQUE,
                display_name TEXT,
                target_age INTEGER,
                country_focus TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )

        ensure_column_exists(conn, "assessments", "super_powers", "TEXT")
        ensure_column_exists(conn, "assessments", "user_email", "TEXT")
        ensure_column_exists(conn, "assessments", "final_ai_text", "TEXT")

        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Database initialization failed: {e}")
        raise


def get_current_user_email():
    return st.user.get("email", "") if st.user.is_logged_in else ""


def load_profile(user_email):
    try:
        conn = get_connection()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT UNIQUE,
                display_name TEXT,
                target_age INTEGER,
                country_focus TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )
        df = pd.read_sql_query(
            "SELECT * FROM profiles WHERE user_email = ?",
            conn,
            params=(user_email,),
        )
        conn.close()
        return df
    except Exception as e:
        st.error(f"Failed to load profile: {e}")
        return pd.DataFrame()

def save_profile(user_email, name, age, country):
    try:
        conn = get_connection()
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS profiles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_email TEXT UNIQUE,
                display_name TEXT,
                target_age INTEGER,
                country_focus TEXT,
                created_at TEXT,
                updated_at TEXT
            )
            """
        )

        cur = conn.cursor()
        now = datetime.utcnow().isoformat()

        cur.execute(
            """
            INSERT INTO profiles (user_email, display_name, target_age, country_focus, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_email) DO UPDATE SET
                display_name=excluded.display_name,
                target_age=excluded.target_age,
                country_focus=excluded.country_focus,
                updated_at=excluded.updated_at
            """,
            (user_email, name, age, country, now, now),
        )

        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Failed to save profile: {e}")
        raise
def save_assessment(row):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO assessments (
                user_email, profile_name, profile_code, respondent_name, respondent_role, relation_weight,
                target_age, country_focus, favourite_subjects, least_favourite_subjects,
                dream_day, super_powers, raw_answers, raw_scores, normalized_scores, final_ai_text, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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


def load_user_profiles(user_email):
    try:
        conn = get_connection()
        df = pd.read_sql_query(
            """
            SELECT
                profile_code,
                MAX(profile_name) AS profile_name,
                MAX(target_age) AS target_age,
                MAX(country_focus) AS country_focus,
                MAX(created_at) AS last_updated,
                COUNT(*) AS assessment_count
            FROM assessments
            WHERE user_email = ?
            GROUP BY profile_code
            ORDER BY last_updated DESC
            """,
            conn,
            params=(user_email,),
        )
        conn.close()
        return df
    except Exception as e:
        st.error(f"Failed to load user profiles: {e}")
        return pd.DataFrame()


def load_assessments_for_user(profile_code, user_email):
    try:
        conn = get_connection()
        df = pd.read_sql_query(
            "SELECT * FROM assessments WHERE profile_code = ? AND user_email = ? ORDER BY created_at DESC",
            conn,
            params=(profile_code, user_email),
        )
        conn.close()
        return df
    except Exception as e:
        st.error(f"Failed to load assessments for user: {e}")
        return pd.DataFrame()


def current_user_email():
    return st.user.get("email", "") if getattr(st, "user", None) and st.user.is_logged_in else ""


def default_profile_code(user_email):
    if not user_email:
        return "default-profile"
    base = user_email.split("@")[0].strip().lower()
    safe = "".join(ch if ch.isalnum() else "-" for ch in base)
    while "--" in safe:
        safe = safe.replace("--", "-")
    safe = safe.strip("-")
    return f"{safe or 'default'}-profile"


def load_user_assessment_history(user_email):
    try:
        conn = get_connection()
        df = pd.read_sql_query(
            """
            SELECT
                id,
                created_at,
                profile_name,
                respondent_name,
                respondent_role,
                country_focus,
                favourite_subjects,
                dream_day,
                normalized_scores,
                final_ai_text
            FROM assessments
            WHERE user_email = ?
            ORDER BY created_at DESC
            """,
            conn,
            params=(user_email,),
        )
        conn.close()
        return df
    except Exception as e:
        st.error(f"Failed to load journey history: {e}")
        return pd.DataFrame()


def update_assessment_ai_text(user_email, created_at, final_ai_text):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE assessments
            SET final_ai_text = ?
            WHERE user_email = ? AND created_at = ?
            """,
            (final_ai_text, user_email, created_at),
        )
        conn.commit()
        conn.close()
    except Exception as e:
        st.error(f"Failed to update AI text: {e}")


def get_profile_history(profile_code):
    df = load_assessments(profile_code)
    if df.empty:
        return df
    df = df.copy()
    df["created_at_dt"] = pd.to_datetime(df["created_at"], errors="coerce")
    return df.sort_values("created_at_dt")


def compare_latest_to_previous(df):
    if df.empty or len(df) < 2:
        return None

    df = df.copy().sort_values("created_at")
    latest = df.iloc[-1]
    previous = df.iloc[-2]

    latest_scores = json.loads(latest["normalized_scores"])
    previous_scores = json.loads(previous["normalized_scores"])

    rows = []
    for cluster in CAREER_CLUSTERS.keys():
        latest_val = float(latest_scores.get(cluster, 0))
        previous_val = float(previous_scores.get(cluster, 0))
        rows.append(
            {
                "Cluster": cluster,
                "Previous %": previous_val,
                "Latest %": latest_val,
                "Change": round(latest_val - previous_val, 1),
            }
        )

    comp_df = pd.DataFrame(rows).sort_values("Latest %", ascending=False)
    return {
        "latest_date": latest["created_at"],
        "previous_date": previous["created_at"],
        "comparison_df": comp_df,
    }


def build_history_chart_df(df):
    if df.empty:
        return pd.DataFrame()

    rows = []
    for _, row in df.sort_values("created_at").iterrows():
        scores = json.loads(row["normalized_scores"])
        for cluster, score in scores.items():
            rows.append({"created_at": row["created_at"], "Cluster": cluster, "Fit %": score})
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
user_email = get_current_user_email()
profile_df = load_profile(user_email)
saved_profile = None
if not profile_df.empty:
    saved_profile = profile_df.iloc[0]
if profile_df.empty:
    st.header("👋 Let's explore what makes you unique")
    st.caption("There are no right or wrong answers here — just discovery.")
    st.write("Let's create your personal profile first.")

    name = st.text_input("Your name")
    age = st.number_input("Your age", 12, 25, 16)
    country = st.selectbox("Where do you want to study?", ["France", "UK", "Switzerland"])

    if st.button("Save my profile"):
        if name:
            save_profile(user_email, name, age, country)
            st.success("Nice — your profile is set up. Let's explore your future 🚀")
            st.rerun()
        else:
            st.info("We just need your name to get started 🙂")

    st.stop()

def apply_context_boost(raw_scores, favourite_subjects, least_subjects, dream_day, super_powers):
    positive_text = f"{favourite_subjects} {dream_day} {super_powers}".lower()
    negative_text = f"{least_subjects}".lower()

    positive_keywords = {
        "Creative & Design": [
            "art", "design", "drawing", "fashion", "media", "photography",
            "film", "writing", "creative", "architecture", "music", "drama",
            "illustration", "animation", "theatre", "dyslexia", "visual"
        ],
        "Engineering & Technology": [
            "math", "physics", "coding", "computer", "engineering",
            "robotics", "technology", "mechanical", "software", "building"
        ],
        "Research & Analysis": [
            "economics", "science", "research", "analysis", "data",
            "history", "politics", "geography", "curiosity"
        ],
        "People, Health & Education": [
            "biology", "psychology", "teaching", "helping", "health",
            "medicine", "children", "care", "empathy", "listening"
        ],
        "Business, Law & Leadership": [
            "business", "law", "debate", "leadership", "entrepreneurship",
            "management", "public speaking", "persuasion"
        ],
        "Operations, Finance & Project Delivery": [
            "finance", "accounting", "organisation", "planning",
            "project", "logistics", "spreadsheet", "discipline"
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
    super_powers,
    answers,
    normalized_scores,
    respondent_role=None,
    followup_answers=None,
):
    top_clusters = top_matches(normalized_scores, n=3)

    return f"""
You are an outstanding career discovery adviser for teenagers.

Your role is to help a young person understand themselves, see realistic possibilities, and feel encouraged about the future.

You must combine:
- grounded advice
- practical next steps
- future awareness
- emotional intelligence
- encouragement without false promises

You are NOT allowed to sound elitist, rigid, snobbish, or deterministic.
You must NOT imply that only traditional prestige careers matter.
You must NOT frame success as “doctor, lawyer, engineer or failure.”
You must recognise that meaningful, stimulating, respected careers can exist in many forms.

The aptitude results are the foundation of the analysis.
Use the score pattern as the primary structure, then use the follow-up answers to confirm, refine, or challenge the initial picture.
When the aptitude results and follow-up answers point in different directions, explain the tension clearly instead of forcing a simplistic answer.

Profile:
- Name: {profile_name}
- Age: {age}
- Country focus for studies: {country_focus}
- Respondent role: {respondent_role or "Unknown"}

Structured inputs:
- Favourite subjects: {favourite_subjects}
- Least favourite subjects: {least_subjects}
- Ideal working day: {dream_day}
- Possible super powers / hidden strengths / traits that may matter: {super_powers}

Question responses:
{json.dumps(answers, indent=2)}

Follow-up interview answers:
{json.dumps(followup_answers or {}, indent=2)}

Top cluster scores:
{json.dumps(top_clusters, indent=2)}

All normalized scores:
{json.dumps(normalized_scores, indent=2)}

Please return your answer using the exact section headings below.

## 1. Encouraging big-picture message
Start with a short, warm, intelligent message.
It should help the student feel optimistic, capable, and open-minded.

## 2. Core profile summary
Summarise the student's likely strengths, motivations, working style, and what seems to energise them.
Explain what kind of environments may suit them.
Be clear about both strengths and tensions.

## 3. Best-fit stimulating career directions
Give exactly 3 to 4 career directions.
For each include:
- Why it fits
- Example roles
- Why it may stay stimulating

## 4. Practical school roadmap
Explain:
- Which school subjects matter most now
- Which academic strengths to build now
- Which bac specialities or school profile may make sense where relevant
- What level of academic ambition to aim for
- Give practical guidance on marks and performance bands to target, but do not pretend exact admissions cutoffs are guaranteed

If the country focus is France:
- Refer naturally to lycée, spécialités and baccalauréat where relevant
- Be realistic and practical
- Do not invent fake official thresholds

## 5. Higher education routes to explore
Suggest realistic higher-education paths relevant to the country focus.
Use three buckets where relevant:
- stretch options
- strong realistic options
- applied / progression-based options

Include route types such as:
- university
- BUT / BTS
- prépa
- grande école
- design school
- specialist school
- apprenticeships
- work-linked routes

Also include example institutions to explore, making clear they are examples, not guarantees.

## 6. Internships and real-world exposure
Suggest practical, age-appropriate environments to explore:
- companies
- studios
- labs
- public bodies
- NGOs
- workshops
- shadowing or project settings

## 7. Skills to build outside school
Suggest useful extracurriculars such as:
- sports
- creative work
- competitions
- clubs
- coding projects
- portfolio work
- volunteering
- public speaking
- teamwork
- personal projects

Explain why these matter for this profile.

## 8. Super powers and hidden strengths
Interpret the “super powers” input with care.
Do not diagnose anything.
Do not medicalise unnecessarily.
Instead explain how unusual traits, energy, empathy, resilience, dyslexia-style thinking, ADHD-style energy, sports discipline, pattern recognition, creativity, or social instinct could become strengths in the right environment.
Also mention the kinds of work or roles where these qualities may become an advantage.

## 9. AI outlook for each direction
For each career direction, provide:
- AI replacement risk score from 1 to 10
- AI enablement value score from 1 to 10
- A short explanation of how AI is likely to change the field
- A short explanation of how learning AI tools could strengthen the student's future performance in that field

Important:
- Do NOT present AI as simple replacement
- Show where AI is a tool, amplifier, co-pilot, or productivity layer
- Be balanced and realistic

## 10. Next 90 days
Give exactly 3 concrete actions the student can take now.

Important rules:
- Do not say "you should definitely become X"
- Do not be overly rigid
- Be practical, nuanced, and future-aware
- Be specific and concrete
- Avoid generic career advice
- If creative signals are strong, do not default to business or law unless clearly dominant
- Treat creative + analytical or creative + leadership combinations as potentially powerful hybrids
- Keep the tone encouraging and grounded
- Make the student feel possibility, not pressure
"""


def get_ai_interpretation(
    profile_name,
    age,
    country_focus,
    favourite_subjects,
    least_subjects,
    dream_day,
    super_powers,
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
        super_powers=super_powers,
        answers=answers,
        normalized_scores=normalized_scores,
        respondent_role=respondent_role,
        followup_answers=followup_answers,
    )

    try:
        response = client.responses.create(model="gpt-4.1-mini", input=prompt)
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
    super_powers,
    answers,
    normalized_scores,
):
    fallback_questions = [
        "What kinds of activities make you lose track of time?",
        "Do you prefer creating something new, solving a problem, or helping someone?",
        "What school tasks feel most natural to you?",
        "What kind of people or environments energise you most?",
        "What is one thing about you that people often misunderstand, but could actually be a strength?",
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
- possible hidden strengths or “super powers”

Profile:
- Name: {profile_name}
- Age: {age}
- Country focus: {country_focus}
- Favourite subjects: {favourite_subjects}
- Least favourite subjects: {least_subjects}
- Dream day: {dream_day}
- Super powers / strengths / unusual traits: {super_powers}
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
        response = client.responses.create(model="gpt-4.1-mini", input=prompt)
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
    super_powers,
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
- Super powers / hidden strengths / unusual traits: {super_powers}

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
- include stretch / realistic / progression-based options where relevant
- focus on pathways and examples
- do not pretend admissions are guaranteed
"""

    try:
        response = client.responses.create(model="gpt-4.1-mini", input=prompt)
        return response.output_text
    except Exception as e:
        return f"Deep-dive AI failed: {e}"


CLUSTER_ICONS = {
    "Engineering & Technology": "⚙️",
    "Research & Analysis": "🔬",
    "Creative & Design": "🎨",
    "People, Health & Education": "💛",
    "Business, Law & Leadership": "🚀",
    "Operations, Finance & Project Delivery": "📊",
}


def short_cluster_signal(cluster, score):
    icon = CLUSTER_ICONS.get(cluster, "✨")
    desc = CAREER_CLUSTERS.get(cluster, {}).get("description", "")
    short_desc = desc.split(".")[0].strip()
    return icon, f"{score}%", short_desc


def reveal_summary_text(top_matches_list):
    if not top_matches_list:
        return "You're starting to build a picture of what suits you."

    top_names = [name for name, _ in top_matches_list[:3]]
    if len(top_names) == 1:
        return f"Your strongest signal right now points toward {top_names[0]}."
    if len(top_names) == 2:
        return f"Your strongest signals right now point toward {top_names[0]} and {top_names[1]}."
    return f"Your strongest signals right now point toward {top_names[0]}, with {top_names[1]} and {top_names[2]} also showing up strongly."


def render_reveal_section(normalized_scores, country_focus, final_ai_text, super_powers_text=None):
    top = top_matches(normalized_scores)

    st.markdown("## ✨ What stands out about you")
    st.info(reveal_summary_text(top))

    cols = st.columns(len(top) if top else 1)
    for i, (cluster, score) in enumerate(top):
        icon, score_text, short_desc = short_cluster_signal(cluster, score)
        with cols[i]:
            st.markdown(f"### {icon} {cluster}")
            st.metric("Signal", score_text)
            if short_desc:
                st.caption(short_desc)

    if super_powers_text and str(super_powers_text).strip():
        with st.expander("⚡ What could make you different", expanded=False):
            st.write(super_powers_text)

    with st.expander("🧭 Your possible paths", expanded=True):
        if final_ai_text:
            st.write(final_ai_text)
        else:
            st.info("Your roadmap will appear here after the AI interpretation is generated.")

    with st.expander("📘 See the full fit-zone detail", expanded=False):
        for cluster, score in top:
            studies, universities = generate_study_advice(cluster, country_focus)
            st.markdown(f"**{CLUSTER_ICONS.get(cluster, '✨')} {cluster} — {score}%**")
            st.write(CAREER_CLUSTERS[cluster]["description"])
            st.write("Suggested further studies: " + ", ".join(studies[:5]))
            if universities:
                st.write("Starter university ideas: " + ", ".join(universities[:4]))

        score_df = pd.DataFrame(
            {"Cluster": list(normalized_scores.keys()), "Fit %": list(normalized_scores.values())}
        ).sort_values("Fit %", ascending=False)
        st.bar_chart(score_df.set_index("Cluster"))


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
if "saved_created_at" not in st.session_state:
    st.session_state["saved_created_at"] = None

render_hero()
st.markdown(
    """
    <div class="small-muted" style="text-align:center; margin-bottom:1rem;">
        This is not about choosing a career today. It’s about discovering what energises you,
        what you’re naturally good at, and what paths might lead to a future that feels meaningful and exciting.
    </div>
    """,
    unsafe_allow_html=True,
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

page = st.sidebar.radio("Your journey", ["Start discovery", "My Journey"])
st.sidebar.markdown("---")
st.sidebar.markdown("### Account")
st.sidebar.write(f"Signed in as: {current_user_email() or st.user.get('email', 'Unknown user')}")
if saved_profile is not None:
    with st.sidebar.expander("My profile", expanded=False):
        st.write(f"**Name:** {saved_profile['display_name']}")
        st.write(f"**Age:** {saved_profile['target_age']}")
        st.write(f"**Country focus:** {saved_profile['country_focus']}")

    with st.sidebar.expander("Edit my profile", expanded=False):
        edit_name = st.text_input(
            "Your name",
            value=str(saved_profile["display_name"] or ""),
            key="sidebar_edit_name",
        )
        edit_age = st.number_input(
            "Your age",
            min_value=12,
            max_value=25,
            value=int(saved_profile["target_age"]) if pd.notnull(saved_profile["target_age"]) else 16,
            key="sidebar_edit_age",
        )
        edit_countries = ["France", "UK", "Switzerland"]
        current_country = str(saved_profile["country_focus"] or "France")
        edit_country_index = edit_countries.index(current_country) if current_country in edit_countries else 0
        edit_country = st.selectbox(
            "Default country focus",
            edit_countries,
            index=edit_country_index,
            key="sidebar_edit_country",
        )

        if st.button("Update profile", key="sidebar_update_profile"):
            if edit_name.strip():
                save_profile(current_user_email(), edit_name.strip(), int(edit_age), edit_country)
                st.sidebar.success("Profile updated.")
                st.rerun()
            else:
                st.sidebar.info("Just add your name to save the profile 🙂")

if st.sidebar.button("Log out"):
    st.logout()
st.sidebar.markdown("---")
st.sidebar.markdown("### ✨ What this is for")
st.sidebar.markdown(
    """
    **Bright Future helps you:**

    🔍 **Understand yourself**
    - What energises you  
    - How you think and work  

    🚀 **Explore possibilities**
    - Real career directions  
    - Different study paths  

    💪 **Build confidence**
    - Without pressure  
    - Without being boxed in  

    ---
    💡 *You don’t need all the answers. Just a better next step.*
    """
)
st.sidebar.markdown("---")
st.sidebar.markdown("### My data")
st.sidebar.caption("Your saved profiles and history are now tied to your signed-in account.")

if page == "Start discovery":
    st.progress(25, text="Step 1 of 4 — Build your starting profile")
    card_start("Step 1", "Discover your starting profile", "Start with instincts, not pressure. You can refine it in the next step.")
    st.caption(f"Signed in as {current_user_email()}")

    default_profile_name = str(saved_profile["display_name"]) if saved_profile is not None and pd.notnull(saved_profile["display_name"]) else ""
    default_age = int(saved_profile["target_age"]) if saved_profile is not None and pd.notnull(saved_profile["target_age"]) else 16
    default_country_focus = str(saved_profile["country_focus"]) if saved_profile is not None and pd.notnull(saved_profile["country_focus"]) else "France"
    profile_code = default_profile_code(current_user_email())

    st.caption("Your saved profile is used to pre-fill this discovery. You can change values for this run without changing your default profile.")

    col1, col2 = st.columns(2)
    with col1:
        profile_name = st.text_input("Student name", value=default_profile_name, placeholder="e.g. Emma Smith")
    with col2:
        age = st.number_input("Age", min_value=12, max_value=25, value=default_age)

    col4, col5, col6 = st.columns(3)
    with col4:
        respondent_name = st.text_input("Your name", placeholder="e.g. Mum / Mr Jones")
    with col5:
        respondent_role = st.selectbox(
            "You are completing this as",
            ["Self", "Parent", "Teacher", "Friend", "Coach/Mentor"],
        )
    with col6:
        country_options = ["France", "UK", "Switzerland"]
        default_country_index = country_options.index(default_country_focus) if default_country_focus in country_options else 0
        country_focus = st.selectbox("Country focus for studies", country_options, index=default_country_index)

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
    qcols = st.columns(1)
    for idx, q in enumerate(QUESTIONS):
        with qcols[0]:
            answers[q["key"]] = st.slider(q["label"], 1, 5, 3, key=f"{respondent_role}_{q['key']}_{idx}")

    st.subheader("A little more context")
    favourite_subjects = st.text_input("Favourite subjects", placeholder="e.g. Maths, Biology, Art")
    least_subjects = st.text_input("Least favourite subjects", placeholder="e.g. Chemistry, History")
    dream_day = st.text_area(
        "Describe an ideal working day",
        placeholder="What would they be doing? Working with people, ideas, data, design, machines...",
    )
    super_powers = st.text_area(
        "Possible super powers or hidden strengths",
        placeholder="Examples: unusual energy, empathy, resilience, dyslexia-style thinking, ADHD-style energy, sports discipline, creativity, pattern recognition, social instinct...",
        help="This is not for diagnosis. It is for strengths that may matter, especially things that are often misunderstood.",
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
                "saved_super_powers",
                "saved_answers",
                "saved_normalized_scores",
                "saved_respondent_role",
                "saved_created_at",
            ]:
                st.session_state.pop(key, None)
            st.rerun()

    card_end()

    if save_clicked:
        if not profile_name:
            st.info("Start by adding a name so we can personalise this for you")
        else:
            raw_scores, _ = score_answers(answers)
            raw_scores = apply_context_boost(
                raw_scores,
                favourite_subjects=favourite_subjects,
                least_subjects=least_subjects,
                dream_day=dream_day,
                super_powers=super_powers,
            )

            max_score = max(raw_scores.values()) if raw_scores else 1
            normalized_scores = {
                k: round((v / max_score) * 100, 1) if max_score else 0
                for k, v in raw_scores.items()
            }

            now = datetime.utcnow().isoformat(timespec="seconds")
            save_assessment(
                (
                    current_user_email(),
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
                    super_powers,
                    json.dumps(answers),
                    json.dumps(raw_scores),
                    json.dumps(normalized_scores),
                    None,
                    now,
                )
            )

            st.session_state["saved_created_at"] = now
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
            st.session_state["saved_super_powers"] = super_powers
            st.session_state["saved_answers"] = answers
            st.session_state["saved_normalized_scores"] = normalized_scores
            st.session_state["saved_respondent_role"] = respondent_role

    if st.session_state.get("show_results"):
        normalized_scores = st.session_state["saved_normalized_scores"]
        saved_answers = st.session_state["saved_answers"]

        if st.session_state.get("followup_ready") and not st.session_state.get("roadmap_ready"):
            st.progress(60, text="Step 2 of 4 — Refine your profile")
            card_start("Step 2", "Refine your profile", "A few smarter follow-up questions will help make the final reveal more accurate and more personal.")
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
                super_powers=st.session_state["saved_super_powers"],
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
                        super_powers=st.session_state["saved_super_powers"],
                        answers=saved_answers,
                        normalized_scores=normalized_scores,
                        respondent_role=st.session_state["saved_respondent_role"],
                        followup_answers=followup_answers,
                    )
                st.session_state["final_ai_text"] = ai_text
                update_assessment_ai_text(
                    current_user_email(),
                    st.session_state.get("saved_created_at", ""),
                    ai_text,
                )
                st.session_state["roadmap_ready"] = True
                st.session_state["followup_ready"] = False
                st.rerun()

            card_end()

        if st.session_state.get("roadmap_ready"):
            st.progress(100, text="Step 3 of 4 — Your Bright Future reveal")
            card_start("Step 3", "🌟 Your Bright Future", "Your strongest fit zones and roadmap are shown below. Open the sections that interest you most.")
            st.write(
                "This is your current best-fit direction based on how you think, what you enjoy, "
                "and what seems to energise you most."
            )

            render_reveal_section(
                normalized_scores=normalized_scores,
                country_focus=st.session_state["saved_country_focus"],
                final_ai_text=st.session_state.get("final_ai_text"),
                super_powers_text=st.session_state.get("saved_super_powers", ""),
            )

            with st.expander("Compare with previous results", expanded=False):
                history_df = get_profile_history(st.session_state["saved_profile_code"])
                history_df = history_df[history_df["user_email"] == current_user_email()] if "user_email" in history_df.columns else history_df
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
                with st.expander("🔍 Explore this result further", expanded=False):
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
                            "How super powers or hidden strengths could help",
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
                                super_powers=st.session_state["saved_super_powers"],
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
            card_end()

else:
    card_start("Journey", "My Journey", "Revisit earlier runs, compare how your thinking changes, and reopen past roadmaps.")

    user_email = current_user_email()
    history_df = load_user_assessment_history(user_email)

    if history_df.empty:
        st.info("You have no saved journey entries yet. Start a discovery first.")
        card_end()
        st.stop()

    history_df = history_df.copy()
    history_df = history_df.sort_values("created_at", ascending=False)

    st.markdown("### Your journey so far")

    for _, row in history_df.iterrows():
        role = row["respondent_role"] if pd.notnull(row["respondent_role"]) and str(row["respondent_role"]).strip() else "Unknown role"
        title = f"{row['created_at']} — {role}"

        preview = ""
        if pd.notnull(row["favourite_subjects"]) and str(row["favourite_subjects"]).strip():
            preview = str(row["favourite_subjects"])
        elif pd.notnull(row["dream_day"]) and str(row["dream_day"]).strip():
            preview = str(row["dream_day"])

        with st.expander(f"📅 {title}", expanded=False):
            if preview:
                st.markdown(f"**Snapshot:** {preview}")

            st.markdown("#### Details")

            if pd.notnull(row["profile_name"]):
                st.write(f"**Name:** {row['profile_name']}")
            if pd.notnull(row["country_focus"]):
                st.write(f"**Country focus:** {row['country_focus']}")
            if pd.notnull(row["favourite_subjects"]):
                st.write(f"**Favourite subjects:** {row['favourite_subjects']}")
            if pd.notnull(row["dream_day"]):
                st.write(f"**Ideal working day:** {row['dream_day']}")

            with st.expander("Score pattern", expanded=False):
                try:
                    scores = json.loads(row["normalized_scores"]) if row["normalized_scores"] else {}
                    if scores:
                        score_df = pd.DataFrame(
                            {"Cluster": list(scores.keys()), "Fit %": list(scores.values())}
                        ).sort_values("Fit %", ascending=False)
                        st.bar_chart(score_df.set_index("Cluster"))
                    else:
                        st.info("No score data for this entry.")
                except Exception:
                    st.info("Could not read score data.")

            with st.expander("AI roadmap", expanded=False):
                if pd.notnull(row["final_ai_text"]) and str(row["final_ai_text"]).strip():
                    st.write(row["final_ai_text"])
                else:
                    st.info("No saved roadmap for this entry.")

        card_end()
        st.stop()

    history_df = history_df.copy()
    history_df["entry_label"] = history_df.apply(
        lambda row: f"{row['created_at']} — {row['respondent_role'] or 'Unknown role'}",
        axis=1,
    )

    with st.expander("My saved entries", expanded=True):
        display_df = history_df[["created_at", "profile_name", "respondent_role", "country_focus"]].copy()
        st.dataframe(display_df, use_container_width=True)

    selected_label = st.selectbox("Choose a past entry", history_df["entry_label"].tolist())
    selected_row = history_df[history_df["entry_label"] == selected_label].iloc[0]

    st.markdown("## Snapshot")
    if pd.notnull(selected_row["profile_name"]):
        st.write(f"**Name:** {selected_row['profile_name']}")
    if pd.notnull(selected_row["country_focus"]):
        st.write(f"**Country focus:** {selected_row['country_focus']}")
    if pd.notnull(selected_row["favourite_subjects"]):
        st.write(f"**Favourite subjects:** {selected_row['favourite_subjects']}")
    if pd.notnull(selected_row["dream_day"]):
        st.write(f"**Ideal working day:** {selected_row['dream_day']}")

    with st.expander("Score pattern", expanded=False):
        try:
            scores = json.loads(selected_row["normalized_scores"]) if selected_row["normalized_scores"] else {}
            if scores:
                score_df = pd.DataFrame(
                    {"Cluster": list(scores.keys()), "Fit %": list(scores.values())}
                ).sort_values("Fit %", ascending=False)
                st.bar_chart(score_df.set_index("Cluster"))
            else:
                st.info("No score data saved for this entry.")
        except Exception:
            st.info("Could not read score data for this entry.")

    with st.expander("AI roadmap from this entry", expanded=True):
        if pd.notnull(selected_row["final_ai_text"]) and str(selected_row["final_ai_text"]).strip():
            st.write(selected_row["final_ai_text"])
        else:
            st.info("This entry does not yet have a saved AI roadmap.")

    card_end()
