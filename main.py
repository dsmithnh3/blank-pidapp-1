import streamlit as st
import pandas as pd
import os
from sqlalchemy import create_engine
from streamlit_drawable_canvas import st_canvas
import openai

# Configuration
st.set_page_config(page_title="P&ID Labeling Tool", layout="wide")
openai.api_key = "your_openai_api_key"
DATABASE_URL = "sqlite:///pid_labeling_tool.db"
engine = create_engine(DATABASE_URL)

# Initialize database
def init_db():
    with engine.connect() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )""")
        conn.execute("""
        CREATE TABLE IF NOT EXISTS components (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            label TEXT NOT NULL,
            metadata TEXT,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )""")

init_db()

# Functions
def get_projects():
    with engine.connect() as conn:
        return pd.read_sql("SELECT * FROM projects", conn)

def add_project(project_name):
    with engine.connect() as conn:
        conn.execute("INSERT INTO projects (name) VALUES (?)", (project_name,))

def get_project_components(project_id):
    with engine.connect() as conn:
        return pd.read_sql(
            "SELECT * FROM components WHERE project_id = ?", conn, params=(project_id,)
        )

def add_component(project_id, label, metadata):
    with engine.connect() as conn:
        conn.execute(
            "INSERT INTO components (project_id, label, metadata) VALUES (?, ?, ?)",
            (project_id, label, metadata),
        )

def generate_metadata_suggestion(label):
    prompt = f"Provide a detailed description and metadata for the component: {label}"
    response = openai.Completion.create(
        engine="text-davinci-003",
        prompt=prompt,
        max_tokens=100,
    )
    return response.choices[0].text.strip()

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
        auto_metadata = st.checkbox("Auto-generate metadata", value=True)
        if st.button("Add Label") and label:
            metadata = generate_metadata_suggestion(label) if auto_metadata else ""
            add_component(project_id, label, metadata)
            st.success(f"Added: {label}")

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
