import streamlit as st
import pandas as pd
import os
from sqlalchemy import create_engine, text
from streamlit_drawable_canvas import st_canvas
import openai
import logging

# Configuration
st.set_page_config(page_title="P&ID Labeling Tool", layout="wide")
openai.api_key = "your_openai_api_key"
DATABASE_URL = "sqlite:///pid_labeling_tool.db"
engine = create_engine(DATABASE_URL)

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

# Initialize database
def init_db():
    logging.debug("Initializing database...")
    try:
        with engine.connect() as conn:
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL
            )"""))
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS components (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                label TEXT NOT NULL,
                metadata TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            )"""))
        logging.debug("Database initialized.")
    except Exception as e:
        logging.error(f"Error initializing database: {e}")

init_db()

# Functions
def get_projects():
    logging.debug("Fetching projects...")
    try:
        with engine.connect() as conn:
            projects = pd.read_sql(text("SELECT * FROM projects"), conn)
        logging.debug(f"Projects fetched: {projects}")
        return projects
    except Exception as e:
        logging.error(f"Error fetching projects: {e}")
        return pd.DataFrame()

def add_project(project_name):
    logging.debug(f"Adding project: {project_name}")
    try:
        with engine.begin() as conn:  # Use engine.begin() for transaction management
            conn.execute(text("INSERT INTO projects (name) VALUES (:name)"), {'name': project_name})
        logging.debug(f"Project '{project_name}' added and committed.")
    except Exception as e:
        logging.error(f"Error adding project '{project_name}': {e}")

def get_project_components(project_id):
    logging.debug(f"Fetching components for project_id: {project_id}")
    try:
        with engine.connect() as conn:
            components = pd.read_sql(
                text("SELECT * FROM components WHERE project_id = :project_id"), conn, params={'project_id': project_id}
            )
        logging.debug(f"Components fetched: {components}")
        return components
    except Exception as e:
        logging.error(f"Error fetching components for project_id '{project_id}': {e}")
        return pd.DataFrame()

# Sidebar for adding projects
st.sidebar.header("Add New Project")
project_name = st.sidebar.text_input("Project Name")
if st.sidebar.button("Add Project"):
    logging.debug(f"Add Project button clicked with project name: {project_name}")
    if project_name:
        add_project(project_name)
        st.sidebar.success(f"Project '{project_name}' added.")
    else:
        st.sidebar.error("Please enter a project name.")

# Display projects
projects = get_projects()
st.write(projects)
