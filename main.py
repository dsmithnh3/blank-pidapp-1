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

def add_component(project_id, label, metadata):
    logging.debug(f"Adding component: {label} to project_id: {project_id}")
    try:
        with engine.begin() as conn:  # Use engine.begin() for transaction management
            conn.execute(
                text("INSERT INTO components (project_id, label, metadata) VALUES (:project_id, :label, :metadata)"),
                {'project_id': project_id, 'label': label, 'metadata': metadata},
            )
        logging.debug(f"Component '{label}' added to project_id: {project_id}")
    except Exception as e:
        logging.error(f"Error adding component '{label}' to project_id '{project_id}': {e}")

def generate_metadata_suggestion(label):
    logging.debug(f"Generating metadata for label: {label}")
    prompt = f"Provide a detailed description and metadata for the component: {label}"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=100,
    )
    metadata = response.choices[0].text.strip()
    logging.debug(f"Metadata generated: {metadata}")
    return metadata

# Streamlit UI
st.title("P&ID Labeling Tool")
st.sidebar.header("Project Management")

# Project Management
projects = get_projects()
project_names = ["Select a project"] + list(projects["name"])
selected_project = st.sidebar.selectbox("Select or create a project", project_names)

if selected_project == "Select a project":
    new_project_name = st.sidebar.text_input("New project name")
    if st.sidebar.button("Create Project") and new_project_name:
        add_project(new_project_name)
        st.experimental_rerun()
else:
    project_id = projects[projects["name"] == selected_project].iloc[0]["id"]
    st.sidebar.success(f"Selected Project: {selected_project}")

    # Upload and display P&ID
    uploaded_file = st.file_uploader("Upload a P&ID (Image or PDF)", type=["png", "jpg", "jpeg", "pdf"])
    if uploaded_file:
        if uploaded_file.type == "application/pdf":
            st.warning("PDF rendering coming soon!")
        else:
            st.image(uploaded_file, caption="Uploaded P&ID", use_column_width=True)

    # Labeling Interface
    st.header("Label P&ID Components")
    with st.expander("Label Components"):
        label = st.text_input("Component Label")
        if st.button("Generate Metadata"):
            metadata = generate_metadata_suggestion(label)
            st.write(metadata)
        if st.button("Add Component"):
            add_component(project_id, label, metadata)
            st.success(f"Component '{label}' added successfully!")

    # Metadata Management
    st.header("Component Metadata")
    components = get_project_components(project_id)
    if not components.empty:
        for _, row in components.iterrows():
            with st.expander(row["label"]):
                st.text_area("Metadata", value=row["metadata"], key=f"metadata_{row['id']}")

    # Export Functionality
    st.sidebar.header("Export Options")
    if st.sidebar.button("Export to PDF"):
        st.info("Export functionality coming soon!")

    # Public Sharing Placeholder
    st.sidebar.header("Public Sharing")
    st.sidebar.info("Public sharing features coming soon!")
