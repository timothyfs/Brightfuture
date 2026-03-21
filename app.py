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

# 👇 ADD DEBUG HERE
if OPENAI_API_KEY:
    st.write("✅ API key loaded from Streamlit secrets")
else:
    st.write("❌ No API key found in Streamlit secrets")

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

st.set_page_config(page_title="Pathfinder Career Discovery", page_icon="🧭", layout="wide")

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
        "weights": {"Creative & Design": 3, "Business, Law & Leadership": 1},
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
        "weights": {"Business, Law & Leadership": 3, "Creative & Design": 1},
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


def score_answers(answers):
    raw = {k: 0 for k in CAREER_CLUSTERS}
    for q in QUESTIONS:
        answer = int(answers.get(q["key"], 3))
        for cluster, weight in q["weights"].items():
            raw[cluster] += answer * weight

    max_score = max(raw.values()) if raw else 1
    normalized = {k: round((v / max_score) * 100, 1) if max_score else 0 for k, v in raw.items()}
    return raw, normalized


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
):
    top_clusters = top_matches(normalized_scores, n=3)

    return f"""
You are a thoughtful, future-aware career discovery adviser for teenagers.

Your job is NOT to give deterministic career advice.
Your job is to interpret patterns, explain tensions, and suggest promising directions to explore.

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

Top cluster scores:
{json.dumps(top_clusters, indent=2)}

All normalized scores:
{json.dumps(normalized_scores, indent=2)}

Please return your answer in the following sections:

1. Core profile summary
2. Strongest signals
3. Tensions or contradictions worth noting
4. Best-fit study directions
5. Adjacent or hybrid future-ready paths
6. Real-world experiments to try next
7. Caution against locking in too early

Important rules:
- Do not say "you should definitely become X"
- Do not be overly rigid
- Be practical, nuanced, and future-aware
- Treat creative + analytical or creative + leadership combinations as potentially powerful hybrids
- Keep the tone encouraging and grounded
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
    )

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt,
        )
        return response.output_text
    except Exception as e:
        return f"AI interpretation failed: {e}"


init_db()

st.title("🧭 Pathfinder Career Discovery")
st.write(
    "A repeatable discovery app for teenagers. It combines self-assessment with parent, teacher, or trusted-friend observations, then maps the result to career clusters, study directions, and a first-pass university shortlist."
)

with st.expander("Read this first"):
    st.markdown(
        """
        This should not be used to force an early decision.

        Use it to find **patterns** and test them in the real world.
        The university suggestions are **starter ideas**, not definitive advice.
        """
    )

if client is None:
    st.warning("AI interpretation is not active yet. Add OPENAI_API_KEY to Streamlit secrets to enable it.")

page = st.sidebar.radio("Choose a section", ["Take an assessment", "View combined profile"])

if page == "Take an assessment":
    st.header("New assessment")
    col1, col2, col3 = st.columns(3)
    with col1:
        profile_name = st.text_input("Teen profile name", placeholder="e.g. Emma Smith")
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

    st.subheader("Rate the statements")
    st.caption("1 = strongly disagree, 5 = strongly agree")
    answers = {}
    qcols = st.columns(2)
    for idx, q in enumerate(QUESTIONS):
        with qcols[idx % 2]:
            answers[q["key"]] = st.slider(q["label"], 1, 5, 3, key=f"{respondent_role}_{q['key']}_{idx}")

    st.subheader("Open reflection")
    favourite_subjects = st.text_input("Favourite subjects", placeholder="e.g. Maths, Biology, Art")
    least_subjects = st.text_input("Least favourite subjects", placeholder="e.g. Chemistry, History")
    dream_day = st.text_area(
        "Describe an ideal working day",
        placeholder="What would she be doing? Working with people, ideas, data, design, machines...",
    )

    if st.button("Save assessment and show results", type="primary"):
        if not profile_name or not profile_code:
            st.error("Add a profile name and profile code first.")
        else:
            raw_scores, normalized_scores = score_answers(answers)
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

            st.success("Assessment saved.")
            st.subheader("This assessment result")

            top = top_matches(normalized_scores)
            for cluster, score in top:
                studies, universities = generate_study_advice(cluster, country_focus)
                st.markdown(f"### {cluster} — {score}%")
                st.write(CAREER_CLUSTERS[cluster]["description"])
                st.write("Suggested further studies: " + ", ".join(studies[:5]))
                if universities:
                    st.write("Starter university ideas: " + ", ".join(universities[:4]))
                st.write("Try next:")
                for act in CAREER_CLUSTERS[cluster]["activities"]:
                    st.write(f"- {act}")

            score_df = pd.DataFrame(
                {"Cluster": list(normalized_scores.keys()), "Fit %": list(normalized_scores.values())}
            ).sort_values("Fit %", ascending=False)
            st.bar_chart(score_df.set_index("Cluster"))

            st.subheader("AI interpretation")
            with st.spinner("Generating AI interpretation..."):
                ai_text = get_ai_interpretation(
                    profile_name=profile_name,
                    age=age,
                    country_focus=country_focus,
                    favourite_subjects=favourite_subjects,
                    least_subjects=least_subjects,
                    dream_day=dream_day,
                    answers=answers,
                    normalized_scores=normalized_scores,
                    respondent_role=respondent_role,
                )
            st.write(ai_text)

else:
    st.header("Combined profile view")
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
