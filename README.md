# Pathfinder Career Discovery Bot

A Streamlit prototype for repeatable teenager career exploration.

## What it does
- lets the teenager complete self-assessments repeatedly
- lets parents, teachers, mentors, or friends add observations
- combines weighted responses into a shared profile
- maps results to career clusters
- suggests further studies and a first-pass university shortlist by country focus
- stores results locally in SQLite so progress can be reviewed over time

## Important limitation
University recommendations are only starter ideas.
For real applications, course availability, entry requirements, and deadlines should be checked against official admissions platforms and university course pages before using the shortlist.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Good hosting options
### Streamlit Community Cloud
Best for a quick personal or family deployment when you want the fastest route from GitHub to a shared app.

### Render
Better if you want more control and a path to a more durable hosted service later.

## Recommended next build phase
- add sign-in links per teen profile
- split the university engine into a separate dataset
- add course-entry filters by country, language, grade band, and budget
- add trend tracking across multiple runs
- add a proper report export
