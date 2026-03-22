import sqlite3
import json
from datetime import datetime
import streamlit as st
import pandas as pd
import os
from openai import OpenAI
from io import BytesIO
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    REPORTLAB_AVAILABLE = True
except Exception:
    REPORTLAB_AVAILABLE = False
DB_PATH = os.getenv("DB_PATH", "/tmp/career_bot.db")
OPENAI_API_KEY = st.secrets.get("OPENAI_API_KEY", None)
client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None


TRANSLATIONS = {
    "English": {
        "language_label": "Language / Langue",
        "journey_label": "Your journey",
        "start_discovery": "Start discovery",
        "my_journey": "My Journey",
        "account": "Account",
        "signed_in_as": "Signed in as:",
        "my_profile": "My profile",
        "name": "Name",
        "age": "Age",
        "country_focus": "Country focus",
        "edit_profile": "Edit my profile",
        "your_name": "Your name",
        "default_country_focus": "Default country focus",
        "update_profile": "Update profile",
        "logout": "Log out",
        "step1_progress": "Step 1 of 4 — Build your starting profile",
        "step1_badge": "Step 1",
        "discover_profile_title": "Discover your starting profile",
        "discover_profile_desc": "Start with instincts, not pressure. You can refine it in the next step.",
        "saved_profile_prefill": "Your saved profile is used to pre-fill this discovery. You can change values for this run without changing your default profile.",
        "student_name": "Student name",
        "completing_as": "You are completing this as",
        "observer_weight": "Observer weight",
        "observer_help": "Higher = greater influence when combining multiple responses. Self should usually be highest.",
        "tell_us_think_work": "Tell us how this person tends to think and work",
        "scale_caption": "1 = strongly disagree, 5 = strongly agree",
        "context_header": "A little more context",
        "fav_subjects": "Favourite subjects",
        "least_subjects": "Least favourite subjects",
        "ideal_day": "Describe an ideal working day",
        "super_powers": "Possible super powers or hidden strengths",
        "super_powers_help": "This is not for diagnosis. It is for strengths that may matter, especially things that are often misunderstood.",
        "start_discovery_btn": "Start discovery",
        "reset": "Reset",
        "profile_saved": "Profile saved. You can now start your journey.",
        "enter_name_continue": "We just need your name to get started.",
        "great_start": "Great start. You’ve already revealed some strong signals.",
        "refine_prompt": "Now let’s go a bit deeper before revealing your full Bright Future roadmap.",
        "level_up": "Level up your profile",
        "reveal_btn": "Reveal my Bright Future",
        "building_roadmap": "Building your roadmap...",
        "step3_progress": "Step 3 of 4 — Your Bright Future reveal",
        "step3_badge": "Step 3",
        "bright_future_title": "🌟 Your Bright Future",
        "bright_future_desc": "Your strongest fit zones and roadmap are shown below. Open the sections that interest you most.",
        "best_fit_direction": "This is your current best-fit direction based on how you think, what you enjoy, and what seems to energise you most.",
        "compare_previous": "Compare with previous results",
        "no_previous_result": "No previous saved result yet for this profile. Save another run later to compare changes over time.",
        "comparing_latest": "Comparing latest result from",
        "with_previous": "with previous result from",
        "explore_further": "🔍 Explore this result further",
        "pick_area": "Pick one area to explore in more depth.",
        "choose_topic": "Choose a topic",
        "explore_topic": "Explore this topic",
        "exploring_topic": "Exploring this topic...",
        "deep_dive": "Deep dive",
        "remember": "Remember:",
        "remember_body": "You don’t need to have everything figured out. The goal is to explore, test, and learn. The clearer your actions, the brighter your future becomes.",
        "journey_badge": "Journey",
        "journey_title": "My Journey",
        "journey_desc": "Revisit earlier runs, compare how your thinking changes, and reopen past roadmaps.",
        "no_journey_entries": "You have no saved journey entries yet. Start a discovery first.",
        "my_saved_entries": "My saved entries",
        "choose_past_entry": "Choose a past entry",
        "snapshot": "Snapshot",
        "favourite_subjects": "Favourite subjects",
        "ideal_working_day": "Ideal working day",
        "score_pattern": "Score pattern",
        "no_score_data": "No score data saved for this entry.",
        "could_not_read_score": "Could not read score data for this entry.",
        "ai_roadmap_entry": "AI roadmap from this entry",
        "no_saved_roadmap": "This entry does not yet have a saved AI roadmap.",
        "pdf_download": "Download PDF report",
        "pdf_download_entry": "Download this entry as PDF",
        "report_title": "Bright Future Report",
        "what_stands_out": "## ✨ What stands out about you",
        "what_could_make_you_different": "⚡ What could make you different",
        "possible_paths": "🧭 Your possible paths",
        "roadmap_appears": "Your roadmap will appear here after the AI interpretation is generated.",
        "what_to_do_next": "🎯 What to do next",
        "focus_school": "What to focus on at school",
        "practical_move": "One practical next move",
        "places_explore": "Places to explore",
        "look_at_env": "Look at environments such as",
        "full_fit_detail": "📘 See the full fit-zone detail",
        "suggested_further_studies": "Suggested further studies:",
        "starter_university_ideas": "Starter university ideas:",
        "journey_so_far": "### Your journey so far",
        "details": "#### Details",
        "unknown_role": "Unknown role",
        "support_msg": "Some of what you’ve written touches on sensitive topics. If you’re exploring careers that help people in difficult situations, that’s meaningful, and we can still help with that. If this is personal or affecting you directly, it’s important to talk to a trusted adult, parent, teacher, school counsellor, or local support service. If anyone is in immediate danger, contact local emergency services now.",
    },
    "Français": {
        "language_label": "Langue / Language",
        "journey_label": "Votre parcours",
        "start_discovery": "Commencer l’exploration",
        "my_journey": "Mon parcours",
        "account": "Compte",
        "signed_in_as": "Connecté en tant que :",
        "my_profile": "Mon profil",
        "name": "Nom",
        "age": "Âge",
        "country_focus": "Pays visé",
        "edit_profile": "Modifier mon profil",
        "your_name": "Votre nom",
        "default_country_focus": "Pays par défaut",
        "update_profile": "Mettre à jour le profil",
        "logout": "Se déconnecter",
        "step1_progress": "Étape 1 sur 4 — Construire votre profil de départ",
        "step1_badge": "Étape 1",
        "discover_profile_title": "Découvrez votre profil de départ",
        "discover_profile_desc": "Commencez par vos instincts, sans pression. Vous pourrez affiner au prochain étape.",
        "saved_profile_prefill": "Votre profil enregistré est utilisé pour préremplir cette exploration. Vous pouvez modifier les valeurs pour cette session sans changer votre profil par défaut.",
        "student_name": "Nom de l’élève",
        "completing_as": "Vous répondez en tant que",
        "observer_weight": "Poids de l’observateur",
        "observer_help": "Plus la valeur est élevée, plus cette réponse comptera dans le profil combiné. L’auto-évaluation doit généralement compter le plus.",
        "tell_us_think_work": "Décrivez comment cette personne pense et travaille",
        "scale_caption": "1 = pas du tout d’accord, 5 = tout à fait d’accord",
        "context_header": "Un peu plus de contexte",
        "fav_subjects": "Matières préférées",
        "least_subjects": "Matières les moins aimées",
        "ideal_day": "Décrivez une journée de travail idéale",
        "super_powers": "Super pouvoirs ou forces cachées possibles",
        "super_powers_help": "Ce n’est pas pour poser un diagnostic. Il s’agit de forces possibles, surtout celles souvent mal comprises.",
        "start_discovery_btn": "Commencer l’exploration",
        "reset": "Réinitialiser",
        "profile_saved": "Profil enregistré. Vous pouvez maintenant commencer votre parcours.",
        "enter_name_continue": "Nous avons juste besoin de votre nom pour commencer.",
        "great_start": "Très bon début. Vous avez déjà révélé des signaux forts.",
        "refine_prompt": "Allons un peu plus loin avant de révéler votre feuille de route Bright Future.",
        "level_up": "Affinez votre profil",
        "reveal_btn": "Révéler mon Bright Future",
        "building_roadmap": "Création de votre feuille de route...",
        "step3_progress": "Étape 3 sur 4 — Révélation de votre Bright Future",
        "step3_badge": "Étape 3",
        "bright_future_title": "🌟 Votre Bright Future",
        "bright_future_desc": "Vos zones de compatibilité les plus fortes et votre feuille de route sont ci-dessous. Ouvrez les sections qui vous intéressent le plus.",
        "best_fit_direction": "Voici votre direction la plus compatible actuellement, en fonction de votre façon de penser, de ce que vous aimez et de ce qui vous donne de l’énergie.",
        "compare_previous": "Comparer avec les résultats précédents",
        "no_previous_result": "Aucun résultat précédent enregistré pour ce profil. Faites une nouvelle exploration plus tard pour comparer l’évolution.",
        "comparing_latest": "Comparaison du dernier résultat du",
        "with_previous": "avec le résultat précédent du",
        "explore_further": "🔍 Explorer davantage ce résultat",
        "pick_area": "Choisissez un sujet à explorer plus en profondeur.",
        "choose_topic": "Choisir un sujet",
        "explore_topic": "Explorer ce sujet",
        "exploring_topic": "Exploration du sujet...",
        "deep_dive": "Approfondissement",
        "remember": "À retenir :",
        "remember_body": "Vous n’avez pas besoin d’avoir tout compris tout de suite. Le but est d’explorer, de tester et d’apprendre. Plus vos actions sont claires, plus votre avenir s’éclaircit.",
        "journey_badge": "Parcours",
        "journey_title": "Mon parcours",
        "journey_desc": "Revenez sur vos anciennes explorations, comparez l’évolution de votre réflexion et rouvrez les feuilles de route passées.",
        "no_journey_entries": "Vous n’avez pas encore d’entrées enregistrées. Commencez d’abord une exploration.",
        "my_saved_entries": "Mes entrées enregistrées",
        "choose_past_entry": "Choisir une entrée passée",
        "snapshot": "Aperçu",
        "favourite_subjects": "Matières préférées",
        "ideal_working_day": "Journée de travail idéale",
        "score_pattern": "Profil des scores",
        "no_score_data": "Aucune donnée de score enregistrée pour cette entrée.",
        "could_not_read_score": "Impossible de lire les données de score pour cette entrée.",
        "ai_roadmap_entry": "Feuille de route IA de cette entrée",
        "no_saved_roadmap": "Aucune feuille de route enregistrée pour cette entrée.",
        "pdf_download": "Télécharger le rapport PDF",
        "pdf_download_entry": "Télécharger cette entrée en PDF",
        "report_title": "Rapport Bright Future",
        "what_stands_out": "## ✨ Ce qui ressort chez vous",
        "what_could_make_you_different": "⚡ Ce qui pourrait vous rendre différent",
        "possible_paths": "🧭 Vos pistes possibles",
        "roadmap_appears": "Votre feuille de route apparaîtra ici après la génération de l’interprétation IA.",
        "what_to_do_next": "🎯 Que faire ensuite",
        "focus_school": "Ce sur quoi se concentrer à l’école",
        "practical_move": "Une prochaine action concrète",
        "places_explore": "Lieux à explorer",
        "look_at_env": "Explorez des environnements comme",
        "full_fit_detail": "📘 Voir le détail complet des zones de compatibilité",
        "suggested_further_studies": "Études suggérées :",
        "starter_university_ideas": "Idées d’établissements pour commencer :",
        "journey_so_far": "### Votre parcours jusqu’ici",
        "details": "#### Détails",
        "unknown_role": "Rôle inconnu",
        "support_msg": "Une partie de ce que vous avez écrit touche à des sujets sensibles. Si vous explorez des métiers qui aident des personnes en difficulté, c’est important et nous pouvons toujours vous aider dans cette réflexion. Si cela est personnel ou vous touche directement, il est important d’en parler à un adulte de confiance, à un parent, à un enseignant, à un conseiller scolaire ou à un service d’aide local. Si quelqu’un est en danger immédiat, contactez les services d’urgence locaux.",
    }
}

def tr(language, key):
    return TRANSLATIONS.get(language, TRANSLATIONS["English"]).get(key, key)

def build_pdf_report(title, sections):
    if not REPORTLAB_AVAILABLE:
        return None
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 50
    c.setTitle(title)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(40, y, title)
    y -= 30
    c.setFont("Helvetica", 10)
    for heading, lines in sections:
        if y < 80:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)
        c.setFont("Helvetica-Bold", 12)
        c.drawString(40, y, str(heading))
        y -= 18
        c.setFont("Helvetica", 10)
        for line in lines:
            for rawline in str(line).split("\n"):
                words = rawline.split()
                current = ""
                if not words:
                    y -= 14
                    continue
                for word in words:
                    trial = (current + " " + word).strip()
                    if c.stringWidth(trial, "Helvetica", 10) > width - 80:
                        c.drawString(50, y, current)
                        y -= 14
                        current = word
                        if y < 60:
                            c.showPage()
                            y = height - 50
                            c.setFont("Helvetica", 10)
                    else:
                        current = trial
                if current:
                    c.drawString(50, y, current)
                    y -= 14
                if y < 60:
                    c.showPage()
                    y = height - 50
                    c.setFont("Helvetica", 10)
        y -= 8
    c.save()
    buffer.seek(0)
    return buffer


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


HIGH_RISK_TERMS = [
    "suicide",
    "kill myself",
    "self harm",
    "self-harm",
    "cut myself",
    "hurt myself",
    "starve myself",
    "purge",
    "abuse",
    "overdose",
    "hurt someone",
    "how to make drugs",
    "drug dealing",
]


def contains_high_risk_terms(text):
    t = (text or "").lower()
    return any(term in t for term in HIGH_RISK_TERMS)


def moderate_text(text):
    if not text or client is None:
        return {"flagged": False, "categories": {}}

    try:
        result = client.moderations.create(
            model="omni-moderation-latest",
            input=text,
        )
        r = result.results[0]
        categories = r.categories.model_dump() if hasattr(r.categories, "model_dump") else {}
        return {"flagged": bool(r.flagged), "categories": categories}
    except Exception:
        return {"flagged": False, "categories": {}}


def should_redirect_to_support(*texts):
    combined_text = "\n".join([str(t) for t in texts if t])
    if not combined_text.strip():
        return False

    if contains_high_risk_terms(combined_text):
        return True

    moderation = moderate_text(combined_text)
    return bool(moderation.get("flagged", False))


def show_sensitive_support_message():
    st.warning(
        tr(language if "language" in globals() else "English", "support_msg")
    )


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
    output_language="English",
):
    top_clusters = top_matches(normalized_scores, n=3)

    return f"""
You are an outstanding career discovery adviser for teenagers.

Your role is to help a young person understand themselves, see realistic possibilities, and feel encouraged about the future.\n\nWrite the entire answer in {output_language}.\n
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

Safety rules:
- Never shame, discourage, or use absolute language about a young person's future.
- Never say someone is incapable, hopeless, or permanently unsuited to a path.
- Never recommend illegal, dangerous, exploitative, self-harming, or medically unsafe actions.
- If the user's text suggests self-harm, abuse, crisis, or immediate danger, do not continue normal career guidance. Instead encourage immediate support from a trusted adult or local emergency/crisis services.
- Keep all advice exploratory, supportive, and non-definitive.

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
    output_language="English",
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
        output_language=output_language,
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
    output_language="English",
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

Rules:\n- Write all 5 questions in {output_language}.\n- Ask exactly 5 questions
- Questions should be short, clear, and teenager-friendly
- Avoid corporate language
- Avoid deterministic phrasing
- Focus on surfacing personality, motivation, and preferences
- Return only a valid JSON list of 5 strings
- Do not ask questions that encourage risky, illegal, self-harming, or exploitative behaviour
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
    output_language="English",
):
    if client is None:
        return "Deep-dive AI is not available because no OPENAI_API_KEY is configured."

    prompt = f"""
You are helping a teenager explore their future in a practical and encouraging way.\n\nWrite the entire answer in {output_language}.\n
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
- if the text suggests self-harm, abuse, crisis, or immediate danger, do not continue normal guidance; encourage support from a trusted adult or local emergency/crisis services instead
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

    st.markdown(tr(language, "what_stands_out"))
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
        with st.expander(tr(language, "what_could_make_you_different"), expanded=False):
            st.write(super_powers_text)

    with st.expander(tr(language, "possible_paths"), expanded=True):
        if final_ai_text:
            st.write(final_ai_text)
        else:
            st.info(tr(language, "roadmap_appears"))

    next_steps = next_steps_suggestions(top, country_focus)
    with st.expander(tr(language, "what_to_do_next"), expanded=True):
        st.write(next_steps["headline"])
        st.markdown(f"**{tr(language, 'focus_school')}**")
        st.write(next_steps["subjects"])
        st.markdown(f"**{tr(language, 'practical_move')}**")
        st.write(next_steps["actions"])
        st.markdown(f"**{tr(language, 'places_explore')}**")
        st.write(f"{tr(language, 'look_at_env')} {next_steps['organisations']}.")

    with st.expander(tr(language, "full_fit_detail"), expanded=False):
        for cluster, score in top:
            studies, universities = generate_study_advice(cluster, country_focus)
            st.markdown(f"**{CLUSTER_ICONS.get(cluster, '✨')} {cluster} — {score}%**")
            st.write(CAREER_CLUSTERS[cluster]["description"])
            st.write(tr(language, "suggested_further_studies") + " " + ", ".join(studies[:5]))
            if universities:
                st.write(tr(language, "starter_university_ideas") + " " + ", ".join(universities[:4]))

        score_df = pd.DataFrame(
            {"Cluster": list(normalized_scores.keys()), "Fit %": list(normalized_scores.values())}
        ).sort_values("Fit %", ascending=False)
        st.bar_chart(score_df.set_index("Cluster"))



def next_steps_suggestions(top_clusters, country_focus):
    subject_map = {
        "Engineering & Technology": "Focus on maths, physics, coding, and problem-solving projects.",
        "Research & Analysis": "Focus on analytical subjects like maths, sciences, economics, and structured writing.",
        "Creative & Design": "Build your portfolio through art, design, writing, media, and visual storytelling.",
        "People, Health & Education": "Strengthen biology, psychology, communication, and people-facing experience.",
        "Business, Law & Leadership": "Build communication, writing, debate, and commercial awareness.",
        "Operations, Finance & Project Delivery": "Strengthen maths, organisation, reliability, and spreadsheet confidence.",
    }

    action_map = {
        "Engineering & Technology": "Try one hands-on project such as coding a simple app, robotics, CAD, or electronics.",
        "Research & Analysis": "Run a mini research project, analyse a dataset, or write a short evidence-based brief.",
        "Creative & Design": "Create something visible: a portfolio piece, short film, poster series, brand concept, or writing sample.",
        "People, Health & Education": "Try tutoring, volunteering, mentoring, or interviewing someone in education or healthcare.",
        "Business, Law & Leadership": "Join debate, pitch an idea, help organise an event, or follow a business/news topic each week.",
        "Operations, Finance & Project Delivery": "Plan something end-to-end, build a simple budget, or improve a process in a spreadsheet.",
    }

    org_map = {
        "Engineering & Technology": ["Airbus", "Dassault Systèmes", "Thales", "Capgemini Engineering"],
        "Research & Analysis": ["INSEE", "OECD", "think tanks", "research labs"],
        "Creative & Design": ["Ubisoft", "LVMH", "design studios", "media agencies"],
        "People, Health & Education": ["schools", "hospitals", "charities", "community organisations"],
        "Business, Law & Leadership": ["startups", "consulting firms", "law firms", "student enterprise groups"],
        "Operations, Finance & Project Delivery": ["operations teams", "banks", "supply-chain firms", "project offices"],
    }

    steps = []
    if not top_clusters:
        return {
            "headline": "Keep exploring and notice what gives you energy.",
            "subjects": "Pay attention to the subjects where effort feels most natural.",
            "actions": "Try one small project and reflect on what felt enjoyable or draining.",
            "organisations": "Look for one organisation or environment that matches your curiosity."
        }

    primary = top_clusters[0][0]
    secondary = top_clusters[1][0] if len(top_clusters) > 1 else None

    headline = f"Use {primary} as your main direction to test next."
    if secondary:
        headline = f"Use {primary} as your main direction, while keeping an eye on {secondary} as a strong secondary path."

    subjects = subject_map.get(primary, "Focus on the subjects that feel both energising and sustainable.")
    actions = action_map.get(primary, "Try one real-world project connected to this direction.")
    organisations = ", ".join(org_map.get(primary, ["companies", "organisations", "teams", "studios"]))

    return {
        "headline": headline,
        "subjects": subjects,
        "actions": actions,
        "organisations": organisations,
    }




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

with st.expander("How to use Bright Future" if language == "English" else "Comment utiliser Bright Future"):
    st.markdown(
        ("""
        **Bright Future is not here to box you in.**

        It helps you:
        - spot patterns in what energises you
        - explore realistic and stimulating future directions
        - think about studies, internships, and skills to build
        - understand how AI may change different career paths

        The goal is not to choose your whole life today.

        The goal is to get clearer, step by step.
        """ if language == "English" else """
        **Bright Future n’est pas là pour t’enfermer dans une case.**

        Il t’aide à :
        - repérer les tendances dans ce qui te donne de l’énergie
        - explorer des pistes réalistes et stimulantes
        - réfléchir aux études, stages et compétences à développer
        - comprendre comment l’IA peut transformer différents métiers

        Le but n’est pas de décider toute ta vie aujourd’hui.

        Le but est d’y voir plus clair, étape par étape.
        """)
    )

st.info(
    "Bright Future is for exploration, not diagnosis. It offers ideas and patterns to explore, "
    "not final verdicts about your future. If something here feels upsetting or serious, talk to a trusted adult."
)

if client is None:
    st.warning("AI interpretation is not active yet. Add OPENAI_API_KEY to Streamlit secrets to enable it.")

language = st.sidebar.selectbox(tr("English", "language_label"), ["English", "Français"])
page = st.sidebar.radio(tr(language, "journey_label"), [tr(language, "start_discovery"), tr(language, "my_journey")])
st.sidebar.markdown("---")
st.sidebar.markdown(f"### {tr(language, 'account')}")
st.sidebar.write(f"{tr(language, 'signed_in_as')} {current_user_email() or st.user.get('email', 'Unknown user')}")
if saved_profile is not None:
    with st.sidebar.expander(tr(language, "my_profile"), expanded=False):
        st.write(f"**{tr(language, 'name')}:** {saved_profile['display_name']}")
        st.write(f"**{tr(language, 'age')}:** {saved_profile['target_age']}")
        st.write(f"**{tr(language, 'country_focus')}:** {saved_profile['country_focus']}")

    with st.sidebar.expander(tr(language, "edit_profile"), expanded=False):
        edit_name = st.text_input(
            tr(language, "your_name"),
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
            tr(language, "default_country_focus"),
            edit_countries,
            index=edit_country_index,
            key="sidebar_edit_country",
        )

        if st.button(tr(language, "update_profile"), key="sidebar_update_profile"):
            if edit_name.strip():
                save_profile(current_user_email(), edit_name.strip(), int(edit_age), edit_country)
                st.sidebar.success("Profile updated.")
                st.rerun()
            else:
                st.sidebar.info("Just add your name to save the profile 🙂")

if st.sidebar.button(tr(language, "logout")):
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

if page == tr(language, "start_discovery"):
    st.progress(25, text=tr(language, "step1_progress"))
    card_start(tr(language, "step1_badge"), tr(language, "discover_profile_title"), tr(language, "discover_profile_desc"))
    st.caption(f"Signed in as {current_user_email()}")

    default_profile_name = str(saved_profile["display_name"]) if saved_profile is not None and pd.notnull(saved_profile["display_name"]) else ""
    default_age = int(saved_profile["target_age"]) if saved_profile is not None and pd.notnull(saved_profile["target_age"]) else 16
    default_country_focus = str(saved_profile["country_focus"]) if saved_profile is not None and pd.notnull(saved_profile["country_focus"]) else "France"
    profile_code = default_profile_code(current_user_email())

    st.caption(tr(language, "saved_profile_prefill"))

    col1, col2 = st.columns(2)
    with col1:
        profile_name = st.text_input(tr(language, "student_name"), value=default_profile_name, placeholder="e.g. Emma Smith")
    with col2:
        age = st.number_input("Age", min_value=12, max_value=25, value=default_age)

    col4, col5, col6 = st.columns(3)
    with col4:
        respondent_name = st.text_input(tr(language, "your_name"), placeholder="e.g. Mum / Mr Jones")
    with col5:
        respondent_role = st.selectbox(
            tr(language, "completing_as"),
            ["Self", "Parent", "Teacher", "Friend", "Coach/Mentor"],
        )
    with col6:
        country_options = ["France", "UK", "Switzerland"]
        default_country_index = country_options.index(default_country_focus) if default_country_focus in country_options else 0
        country_focus = st.selectbox("Country focus for studies", country_options, index=default_country_index)

    default_weight = role_default_weight(respondent_role)
    relation_weight = st.slider(
        tr(language, "observer_weight"),
        min_value=0.4,
        max_value=1.2,
        value=float(default_weight),
        step=0.05,
        help=tr(language, "observer_help"),
    )

    st.subheader(tr(language, "tell_us_think_work"))
    st.caption(tr(language, "scale_caption"))
    answers = {}
    qcols = st.columns(1)
    for idx, q in enumerate(QUESTIONS):
        with qcols[0]:
            answers[q["key"]] = st.slider(q["label"], 1, 5, 3, key=f"{respondent_role}_{q['key']}_{idx}")

    st.subheader(tr(language, "context_header"))
    favourite_subjects = st.text_input(tr(language, "fav_subjects"), placeholder="e.g. Maths, Biology, Art")
    least_subjects = st.text_input(tr(language, "least_subjects"), placeholder="e.g. Chemistry, History")
    dream_day = st.text_area(
        tr(language, "ideal_day"),
        placeholder="What would they be doing? Working with people, ideas, data, design, machines...",
    )
    super_powers = st.text_area(
        tr(language, "super_powers"),
        placeholder="Examples: unusual energy, empathy, resilience, dyslexia-style thinking, ADHD-style energy, sports discipline, creativity, pattern recognition, social instinct...",
        help=tr(language, "super_powers_help"),
    )

    col_a, col_b = st.columns([3, 1])
    with col_a:
        save_clicked = st.button(tr(language, "start_discovery_btn"), type="primary")
    with col_b:
        if st.button(tr(language, "reset")):
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
            st.success(tr(language, "great_start"))
            st.info(tr(language, "refine_prompt"))

            st.markdown(f"## {tr(language, 'level_up')}")

            if should_redirect_to_support(
                st.session_state["saved_favourite_subjects"],
                st.session_state["saved_least_subjects"],
                st.session_state["saved_dream_day"],
                st.session_state["saved_super_powers"],
            ):
                show_sensitive_support_message()
                card_end()
                st.stop()

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

            if st.button(tr(language, "reveal_btn"), key="generate_ai"):
                if should_redirect_to_support(
                    st.session_state["saved_favourite_subjects"],
                    st.session_state["saved_least_subjects"],
                    st.session_state["saved_dream_day"],
                    st.session_state["saved_super_powers"],
                    json.dumps(followup_answers),
                ):
                    show_sensitive_support_message()
                else:
                    with st.spinner(tr(language, "building_roadmap")):
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
            st.progress(100, text=tr(language, "step3_progress"))
            card_start(tr(language, "step3_badge"), tr(language, "bright_future_title"), tr(language, "bright_future_desc"))
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

            if st.session_state.get("final_ai_text"):
                pdf_sections = [
                    (tr(language, "report_title"), [f"{tr(language, 'name')}: {st.session_state.get('saved_profile_name', '')}",
                                                   f"{tr(language, 'age')}: {st.session_state.get('saved_age', '')}",
                                                   f"{tr(language, 'country_focus')}: {st.session_state.get('saved_country_focus', '')}"]),
                    (tr(language, "possible_paths"), [st.session_state.get("final_ai_text", "")]),
                ]
                pdf_buffer = build_pdf_report(
                    f"Bright Future - {st.session_state.get('saved_profile_name', 'report')}",
                    pdf_sections,
                )
                if pdf_buffer is not None:
                    st.download_button(
                        tr(language, "pdf_download"),
                        data=pdf_buffer,
                        file_name=f"{st.session_state.get('saved_profile_code', 'bright_future')}_report.pdf",
                        mime="application/pdf",
                        key="download_current_report",
                    )

            with st.expander(tr(language, "compare_previous"), expanded=False):
                history_df = get_profile_history(st.session_state["saved_profile_code"])
                history_df = history_df[history_df["user_email"] == current_user_email()] if "user_email" in history_df.columns else history_df
                comparison = compare_latest_to_previous(history_df)

                if comparison is None:
                    st.info(tr(language, "no_previous_result"))
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
                with st.expander(tr(language, "explore_further"), expanded=False):
                    st.write(tr(language, "pick_area"))

                    deep_dive_topic = st.selectbox(
                        tr(language, "choose_topic"),
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

                    if st.button(tr(language, "explore_topic"), key="explore_topic"):
                        if should_redirect_to_support(
                            st.session_state["saved_favourite_subjects"],
                            st.session_state["saved_least_subjects"],
                            st.session_state["saved_dream_day"],
                            st.session_state["saved_super_powers"],
                            deep_dive_topic,
                        ):
                            show_sensitive_support_message()
                        else:
                            with st.spinner(tr(language, "exploring_topic")):
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
                                    output_language=language,
                                )
                            st.session_state["deep_dive_text"] = deep_dive_text

                    if st.session_state.get("deep_dive_text"):
                        st.markdown(f"### {tr(language, 'deep_dive')}: {deep_dive_topic}")
                        st.write(st.session_state["deep_dive_text"])

                st.markdown("---")
                st.markdown(
                    f"**{tr(language, 'remember')}** {tr(language, 'remember_body')}"
                )
            card_end()

else:
    card_start(tr(language, "journey_badge"), tr(language, "journey_title"), tr(language, "journey_desc"))
    user_email = current_user_email()
    history_df = load_user_assessment_history(user_email)

    if history_df.empty:
        st.info(tr(language, "no_journey_entries"))
        card_end()
        st.stop()

    history_df = history_df.copy()
    history_df["entry_label"] = history_df.apply(
        lambda row: f"{row['created_at']} — {row['respondent_role'] or tr(language, 'unknown_role')}",
        axis=1,
    )

    with st.expander(tr(language, "my_saved_entries"), expanded=True):
        display_df = history_df[["created_at", "profile_name", "respondent_role", "country_focus"]].copy()
        st.dataframe(display_df, use_container_width=True)

    selected_label = st.selectbox(tr(language, "choose_past_entry"), history_df["entry_label"].tolist())
    selected_row = history_df[history_df["entry_label"] == selected_label].iloc[0]

    st.markdown(f"## {tr(language, 'snapshot')}")
    if pd.notnull(selected_row["profile_name"]):
        st.write(f"**Name:** {selected_row['profile_name']}")
    if pd.notnull(selected_row["country_focus"]):
        st.write(f"**Country focus:** {selected_row['country_focus']}")
    if pd.notnull(selected_row["favourite_subjects"]):
        st.write(f"**{tr(language, 'favourite_subjects')}:** {selected_row['favourite_subjects']}")
    if pd.notnull(selected_row["dream_day"]):
        st.write(f"**{tr(language, 'ideal_working_day')}:** {selected_row['dream_day']}")

    with st.expander(tr(language, "score_pattern"), expanded=False):
        try:
            scores = json.loads(selected_row["normalized_scores"]) if selected_row["normalized_scores"] else {}
            if scores:
                score_df = pd.DataFrame(
                    {"Cluster": list(scores.keys()), "Fit %": list(scores.values())}
                ).sort_values("Fit %", ascending=False)
                st.bar_chart(score_df.set_index("Cluster"))
            else:
                st.info(tr(language, "no_score_data"))
        except Exception:
            st.info(tr(language, "could_not_read_score"))

    with st.expander(tr(language, "ai_roadmap_entry"), expanded=True):
        if pd.notnull(selected_row["final_ai_text"]) and str(selected_row["final_ai_text"]).strip():
            st.write(selected_row["final_ai_text"])
        else:
            st.info(tr(language, "no_saved_roadmap"))

    entry_pdf = build_pdf_report(
        f"Bright Future - {selected_row['created_at']}",
        [
            (tr(language, "snapshot"), [
                f"{tr(language, 'name')}: {selected_row['profile_name']}" if pd.notnull(selected_row["profile_name"]) else "",
                f"{tr(language, 'country_focus')}: {selected_row['country_focus']}" if pd.notnull(selected_row["country_focus"]) else "",
                f"{tr(language, 'favourite_subjects')}: {selected_row['favourite_subjects']}" if pd.notnull(selected_row["favourite_subjects"]) else "",
                f"{tr(language, 'ideal_working_day')}: {selected_row['dream_day']}" if pd.notnull(selected_row["dream_day"]) else "",
            ]),
            (tr(language, "ai_roadmap_entry"), [selected_row["final_ai_text"] if pd.notnull(selected_row["final_ai_text"]) else ""]),
        ],
    )
    if entry_pdf is not None:
        st.download_button(
            tr(language, "pdf_download_entry"),
            data=entry_pdf,
            file_name=f"bright_future_{selected_row['id']}.pdf",
            mime="application/pdf",
            key=f"download_entry_{selected_row['id']}",
        )

    card_end()
