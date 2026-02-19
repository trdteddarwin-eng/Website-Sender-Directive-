"""Configuration — loads .env and sets paths."""

import os
from dotenv import load_dotenv

# Load .env from workspace root (one level up from pipeline-app/)
WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(WORKSPACE_ROOT, ".env"))

# Google Sheets (lead data source)
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1rmxqViBWof7Jo2yX9AEBFTATzuzF_crqh5HxG2z-1b4/edit"
GOOGLE_SHEET_ID = "1rmxqViBWof7Jo2yX9AEBFTATzuzF_crqh5HxG2z-1b4"
GOOGLE_TOKEN_PATH = os.path.join(WORKSPACE_ROOT, "token.json")
GOOGLE_CREDS_PATH = os.path.join(WORKSPACE_ROOT, "credentials.json")

# Local data directory for operational tables (pipeline_runs, emails, etc.)
LOCAL_DATA_DIR = os.path.join(WORKSPACE_ROOT, ".tmp", "pipeline-data")

# API Keys
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
NETLIFY_AUTH_TOKEN = os.getenv("NETLIFY_AUTH_TOKEN", "")
NETLIFY_SITE_ID = os.getenv("NETLIFY_SITE_ID", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Gmail
GMAIL_TOKEN_PATH = os.path.join(WORKSPACE_ROOT, "gmail_token.json")
GMAIL_CREDS_PATH = os.path.join(WORKSPACE_ROOT, "gmail_credentials.json")

# Paths
TMP_DIR = os.path.join(WORKSPACE_ROOT, ".tmp")
EXECUTION_DIR = os.path.join(WORKSPACE_ROOT, "execution")

# Pipeline
PALETTES = [
    {"name": "Navy/Amber", "primary": "#0B1D3A", "accent": "#D4922A"},
    {"name": "Forest/Gold", "primary": "#1B4332", "accent": "#D4A22A"},
    {"name": "Charcoal/Red", "primary": "#2D2D2D", "accent": "#C0392B"},
    {"name": "Deep Blue/Orange", "primary": "#1A365D", "accent": "#E07C24"},
    {"name": "Dark Teal/Yellow", "primary": "#0D4F4F", "accent": "#E8B930"},
]

HERO_STYLES = ["full-bleed", "split-layout", "gradient-overlay", "diagonal-split"]
