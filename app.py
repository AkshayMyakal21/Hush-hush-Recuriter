import pandas as pd
from database import connect_db
from notifier import notify_selected_candidates, DEFAULT_RECIPIENT
import streamlit as st
from config import ROLE_QUERIES

conn = connect_db()

role_options = ["All Roles"] + list(ROLE_QUERIES.keys())
st.title("HushHush Recruiter Dashboard")
selected_role = st.selectbox("Filter by role:", role_options)

if selected_role == "All Roles":
    df = pd.read_sql_query("""
        SELECT c.username, c.profile_url, c.followers, c.public_repos,
               c.total_stars, c.total_forks, c.commit_count, c.top_language,
               s.github_score, s.is_selected
        FROM candidates c
        JOIN scores s ON c.id = s.candidate_id
        WHERE s.id IN (SELECT MAX(id) FROM scores GROUP BY candidate_id)
        ORDER BY s.github_score DESC
    """, conn)
else:
    df = pd.read_sql_query("""
        SELECT DISTINCT c.username, c.profile_url, c.followers, c.public_repos,
               c.total_stars, c.total_forks, c.commit_count, c.top_language,
               s.github_score, s.is_selected
        FROM candidates c
        JOIN scores s ON c.id = s.candidate_id
        JOIN candidate_queries cq ON c.id = cq.candidate_id
        WHERE s.id IN (SELECT MAX(id) FROM scores GROUP BY candidate_id)
        AND cq.role = ?
        ORDER BY s.github_score DESC
    """, conn, params=(selected_role,))

conn.close()

# Snapshot of every selected candidate before any view filter is applied below.
selected_df = df[df["is_selected"] == 1].copy()

col1, col2, col3 = st.columns(3)
col1.metric("Total Candidate", len(df))
col2.metric("Selected", int(df["is_selected"].sum()))
col3.metric("Average Score", round(df["github_score"].mean(), 3))

search = st.text_input("Search by username")
show_selected = st.checkbox("Show only selected candidates")

if search:
    df = df[df["username"].str.contains(search, case=False)]
if show_selected:
    df = df[df["is_selected"] == 1]

df["is_selected"] = df["is_selected"].map({1: "✅", 0: "❌"})

st.subheader("Candidate List")
st.dataframe(
    df,
    column_config = {
        "profile_url": st.column_config.LinkColumn("Profile", help="Click to view profile"),
    },
    hide_index=True,
    use_container_width=True
)
st.subheader("Top 10 Score")
chart_data = df.head(10).sort_values(by="github_score", ascending=True)
st.bar_chart(chart_data, x="username", y="github_score", use_container_width=True)

st.subheader("📧 Notify Selected Candidates")
st.write(f"{len(selected_df)} candidate(s) are currently marked as selected.")

recipient = st.text_input("Send notification to", value=DEFAULT_RECIPIENT)

if st.button("Send email notification"):
    if selected_df.empty:
        st.warning("There are no selected candidates to notify about.")
    else:
        candidates = selected_df.to_dict(orient="records")
        try:
            sent_to = notify_selected_candidates(candidates, recipient)
            st.success(f"Notification with {len(candidates)} selected candidate(s) sent to {sent_to}.")
        except Exception as e:
            st.error(f"Could not send email: {e}")
