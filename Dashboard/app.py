import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import ast

# ---------------------------------------------------
# PAGE SETTINGS
# ---------------------------------------------------

st.set_page_config(
    page_title="Oncology Trial Analytics",
    layout="wide"
)

# ---------------------------------------------------
# TITLE
# ---------------------------------------------------

st.title("Oncology Clinical Trial Analytics")

st.markdown("""
Interactive dashboard for exploring operational trends in oncology clinical trials.

This dashboard transforms raw flat-file clinical trial data into cohort-level analytical insights.
""")

# ---------------------------------------------------
# LOAD DATA
# ---------------------------------------------------



@st.cache_data
def load_data():

    df = pd.read_excel(
        "data/SampleDateExtract.xlsx"
    )

    return df






df = load_data()

# ---------------------------------------------------
# COLUMN CLEANING
# ---------------------------------------------------

df.columns = (
    df.columns
    .str.strip()
    .str.lower()
    .str.replace("-", "_")
    .str.replace(" ", "_")
)

# ---------------------------------------------------
# STATUS STANDARDIZATION
# ---------------------------------------------------

status_mapping = {
    "ACTIVE_NOT_RECRUITING": "ACTIVE",
    "NOT_YET_RECRUITING": "PLANNED",
    "ENROLLING_BY_INVITATION": "RECRUITING"
}

df["status_standardized"] = (
    df["recruitment_status"]
    .replace(status_mapping)
)

# ---------------------------------------------------
# OUTCOME LOGIC
# ---------------------------------------------------

outcome_mapping = {

    "COMPLETED": "success_like",

    "TERMINATED": "failure_like",
    "WITHDRAWN": "failure_like",

    "RECRUITING": "ongoing",
    "ACTIVE": "ongoing",
    "PLANNED": "ongoing",

    "UNKNOWN": "ambiguous",
    "SUSPENDED": "ambiguous"
}

df["outcome_category"] = (
    df["status_standardized"]
    .map(outcome_mapping)
)

binary_mapping = {
    "success_like": 1,
    "failure_like": 0
}

df["success_proxy"] = (
    df["outcome_category"]
    .map(binary_mapping)
)

# ---------------------------------------------------
# HELPER FUNCTION
# ---------------------------------------------------

def clean_nested_value(x):

    while isinstance(x, list):

        if len(x) == 0:
            return None

        x = x[0]

    return str(x).strip()

# ---------------------------------------------------
# SIDEBAR
# ---------------------------------------------------

st.sidebar.header("Filters")

selected_phase = st.sidebar.multiselect(
    "Clinical Phase",
    options=sorted(
        df["phase"]
        .dropna()
        .unique()
    ),
    default=sorted(
        df["phase"]
        .dropna()
        .unique()
    )
)

filtered_df = df[
    df["phase"]
    .isin(selected_phase)
]

st.sidebar.markdown("---")

st.sidebar.info("""
Success in this dashboard refers to operational trial completion, not therapeutic efficacy.

The framework estimates operational progression trends using trial status metadata.
""")

# ---------------------------------------------------
# OVERVIEW METRICS
# ---------------------------------------------------

st.header("Dataset Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric(
        "Trials",
        filtered_df.shape[0]
    )

with col2:
    st.metric(
        "Indications",
        filtered_df["indications"]
        .nunique()
    )

with col3:
    st.metric(
        "Technology Types",
        filtered_df["main_technologies"]
        .nunique()
    )

with col4:
    st.metric(
        "Targets",
        filtered_df["target_names"]
        .nunique()
    )

# ---------------------------------------------------
# DOWNLOAD BUTTON
# ---------------------------------------------------

csv_data = filtered_df.to_csv(
    index=False
).encode("utf-8")

st.download_button(
    label="Download Filtered Dataset",
    data=csv_data,
    file_name="filtered_trials.csv",
    mime="text/csv"
)

# ---------------------------------------------------
# TABS
# ---------------------------------------------------

tab1, tab2, tab3, tab4 = st.tabs([
    "Phase Analysis",
    "Technology Analysis",
    "Indication Analysis",
    "Outcome Distribution"
])

# ===================================================
# TAB 1 : PHASE ANALYSIS
# ===================================================

with tab1:

    st.subheader(
        "Operational Success by Clinical Phase"
    )

    phase_success = (
        filtered_df
        .groupby("phase")["success_proxy"]
        .mean()
        .sort_values(ascending=False)
    )

    fig1, ax1 = plt.subplots(figsize=(8,4))

    phase_success.plot(
        kind="bar",
        ax=ax1,
        color="steelblue"
    )

    ax1.set_ylabel(
        "Success Rate"
    )

    ax1.set_xlabel(
        "Clinical Phase"
    )

    ax1.set_ylim(0,1)

    ax1.grid(
        axis="y",
        linestyle="--",
        alpha=0.4
    )

    st.pyplot(fig1)

    st.markdown("""
    Later-stage trials generally show higher operational completion rates compared to early exploratory studies.
    """)

# ===================================================
# TAB 2 : TECHNOLOGY ANALYSIS
# ===================================================

with tab2:

    st.subheader(
        "Operational Success by Technology Type"
    )

    technology_df = filtered_df.copy()

    technology_df["main_technologies"] = (
        technology_df["main_technologies"]
        .apply(ast.literal_eval)
    )

    technology_df = technology_df.explode(
        "main_technologies"
    )

    technology_df["main_technologies"] = (
        technology_df["main_technologies"]
        .apply(clean_nested_value)
    )

    technology_df = technology_df[
        technology_df["main_technologies"].notna()
    ]

    top_technologies = (
        technology_df["main_technologies"]
        .value_counts()
        .head(8)
        .index
    )

    technology_success = (
        technology_df[
            technology_df["main_technologies"]
            .isin(top_technologies)
        ]
        .groupby("main_technologies")["success_proxy"]
        .mean()
        .sort_values(ascending=False)
    )

    fig2, ax2 = plt.subplots(figsize=(9,5))

    technology_success.plot(
        kind="bar",
        ax=ax2,
        color="darkorange"
    )

    ax2.set_ylabel(
        "Success Rate"
    )

    ax2.set_xlabel(
        "Technology Type"
    )

    ax2.set_ylim(0,1)

    ax2.grid(
        axis="y",
        linestyle="--",
        alpha=0.4
    )

    plt.xticks(
        rotation=35,
        ha="right"
    )

    st.pyplot(fig2)

    st.markdown("""
    Different therapeutic technologies show varying operational completion patterns across oncology trials.
    """)

# ===================================================
# TAB 3 : INDICATION ANALYSIS
# ===================================================

with tab3:

    st.subheader(
        "Operational Success by Major Oncology Indications"
    )

    indication_df = filtered_df.copy()

    indication_df["indications"] = (
        indication_df["indications"]
        .apply(ast.literal_eval)
    )

    indication_df = indication_df.explode(
        "indications"
    )

    indication_df["indications"] = (
        indication_df["indications"]
        .apply(clean_nested_value)
    )

    indication_df = indication_df[
        indication_df["indications"].notna()
    ]

    top_indications = (
        indication_df["indications"]
        .value_counts()
        .head(10)
        .index
    )

    indication_success = (
        indication_df[
            indication_df["indications"]
            .isin(top_indications)
        ]
        .groupby("indications")["success_proxy"]
        .mean()
        .sort_values(ascending=False)
    )

    fig3, ax3 = plt.subplots(figsize=(11,5))

    indication_success.plot(
        kind="bar",
        ax=ax3,
        color="forestgreen"
    )

    ax3.set_ylabel(
        "Success Rate"
    )

    ax3.set_xlabel(
        "Cancer Indication"
    )

    ax3.set_ylim(0,1)

    ax3.grid(
        axis="y",
        linestyle="--",
        alpha=0.4
    )

    plt.xticks(
        rotation=40,
        ha="right"
    )

    st.pyplot(fig3)

    st.markdown("""
    Operational completion rates vary across oncology indications due to differences in disease complexity and trial recruitment.
    """)

# ===================================================
# TAB 4 : OUTCOME DISTRIBUTION
# ===================================================

with tab4:

    st.subheader(
        "Operational Outcome Categories"
    )

    outcome_counts = (
        filtered_df["outcome_category"]
        .value_counts()
    )

    fig4, ax4 = plt.subplots(figsize=(7,4))

    outcome_counts.plot(
        kind="bar",
        ax=ax4,
        color="mediumpurple"
    )

    ax4.set_ylabel(
        "Trial Count"
    )

    ax4.set_xlabel(
        "Outcome Category"
    )

    ax4.grid(
        axis="y",
        linestyle="--",
        alpha=0.4
    )

    st.pyplot(fig4)

    st.warning("""
    Trial completion does not necessarily imply therapeutic success or regulatory approval.
    """)

# ---------------------------------------------------
# FOOTER
# ---------------------------------------------------

st.markdown("---")

st.markdown("""
Built using:
- Python
- pandas
- matplotlib
- Streamlit

Focus areas:
- clinical trial analytics
- healthcare data engineering
- operational cohort analysis
""")

