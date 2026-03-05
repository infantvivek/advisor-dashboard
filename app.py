

# --- 1. DATA SOURCE LINKS ---
# Ensure these links point to the specific tabs in your Google Sheet (Published as CSV)
#TEAM_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=0&single=true&output=csv"
#KPI_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=1918948844&single=true&output=csv"
#DSAT_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=367459010&single=true&output=csv" 
import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. DATA SOURCE LINKS ---
TEAM_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=0&single=true&output=csv"
KPI_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=1918948844&single=true&output=csv"
DSAT_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=367459010&single=true&output=csv"  



st.set_page_config(page_title="The Go Getters | Performance Portal", layout="wide")

# --- DATA LOADING WITH ERROR CATCHING ---
def load_data(url, name):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip().str.replace('\ufeff', '')
        return df
    except Exception as e:
        st.error(f"❌ Failed to load {name}. Check if the link is published as CSV.")
        st.stop()

# --- BRANDING ---
col1, col2 = st.columns([1, 8])
with col1:
    st.image("https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/48175265495/original/PTXBCP40UHx-8LCKsM1zqLX-pq8nndFHSw.png?1641235482", width=100)
with col2:
    st.title("The Go Getters")
    st.subheader("Advisor Performance & DSAT Analysis Dashboard")

# --- LOGIN LOGIC ---
st.sidebar.title("Login")
user_email_input = st.sidebar.text_input("Enter Email").strip().lower()

if user_email_input:
    # 1. Load Team DB to verify user
    team_df = load_data(TEAM_URL, "Team Detail Sheet")
    
    # Check if email exists in Team Detail
    if user_email_input in team_df['Email'].str.lower().values:
        advisor_name = team_df[team_df['Email'].str.lower() == user_email_input]['Advisor Name'].iloc[0]
        st.sidebar.success(f"Welcome, {advisor_name}")
        
        # 2. Load KPI and DSAT
        kpi_df = load_data(KPI_URL, "KPI Data Sheet")
        dsat_df = load_data(DSAT_URL, "DSAT Data Sheet")

        # Process KPI Dates (Feb'28'26)
        kpi_df['Date'] = pd.to_datetime(kpi_df['Date'], format="%b'%d'%y", errors='coerce')
        
        # Process DSAT Dates (10/02/2026)
        dsat_df['Date'] = pd.to_datetime(dsat_df['Date'], format="%d/%m/%Y", errors='coerce')
        dsat_df['Date'] = dsat_df['Date'].dt.normalize()

        # Clean KPI Numbers
        num_cols = ['IA_Hours', 'Shift_Score', 'Sent_Rate', 'Satisfied_Survey', 'OB_Calls', 'QA_Calls', 'Call_Abandons', 'MOB']
        for col in num_cols:
            if col in kpi_df.columns:
                if kpi_df[col].dtype == object:
                    kpi_df[col] = kpi_df[col].str.replace('%', '').str.strip()
                kpi_df[col] = pd.to_numeric(kpi_df[col], errors='coerce')

        # Filter for this specific advisor
        user_kpi = kpi_df[kpi_df['Email'].str.lower() == user_email_input].copy().sort_values('Date')
        
        # --- UI CONTENT ---
        freq = st.radio("Select Frequency:", ["Daily", "Weekly", "Monthly"], horizontal=True)

        # Filter Logic
        if freq == "Daily":
            dates = sorted(user_kpi['Date'].unique(), reverse=True)
            sel = st.selectbox("Select Date:", dates, format_func=lambda x: x.strftime('%d %b %Y'))
            filtered_kpi = user_kpi[user_kpi['Date'] == sel]
            filtered_dsat = dsat_df[(dsat_df['Email'].str.lower() == user_email_input) & (dsat_df['Date'] == sel)]
            chart_df = filtered_kpi
        
        elif freq == "Weekly":
            user_kpi['Week_Range'] = (user_kpi['Date'] - pd.to_timedelta(user_kpi['Date'].dt.dayofweek + 1 % 7, unit='d')).dt.strftime('%d %b %Y')
            weeks = user_kpi['Week_Range'].unique()
            sel = st.selectbox("Select Week:", weeks)
            filtered_kpi = user_kpi[user_kpi['Week_Range'] == sel]
            chart_df = filtered_kpi.sort_values('Date')
            # DSAT Weekly Filter
            dsat_df['Week_Range'] = (dsat_df['Date'] - pd.to_timedelta(dsat_df['Date'].dt.dayofweek + 1 % 7, unit='d')).dt.strftime('%d %b %Y')
            filtered_dsat = dsat_df[(dsat_df['Email'].str.lower() == user_email_input) & (dsat_df['Week_Range'] == sel)]

        else: # Monthly
            user_kpi['Month'] = user_kpi['Date'].dt.strftime('%B %Y')
            months = user_kpi['Month'].unique()
            sel = st.selectbox("Select Month:", months)
            filtered_kpi = user_kpi[user_kpi['Month'] == sel]
            chart_df = filtered_kpi.sort_values('Date')
            # DSAT Monthly Filter
            dsat_df['Month'] = dsat_df['Date'].dt.strftime('%B %Y')
            filtered_dsat = dsat_df[(dsat_df['Email'].str.lower() == user_email_input) & (dsat_df['Month'] == sel)]

        # --- SUMMARY ---
        st.markdown("---")
        avg_sat = filtered_kpi['Satisfied_Survey'].mean()
        def f_v(v, s="%"): return f"{v:.1f}{s}" if pd.notna(v) and v != 0 else "-"
        
        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric("Avg Shift Score", f_v(filtered_kpi['Shift_Score'].mean()))
        m2.metric("Avg IA Hours", f_v(filtered_kpi['IA_Hours'].mean(), "h"))
        m3.metric("Avg Satisfied Survey", f_v(avg_sat))
        m4.metric("Avg DSAT %", f_v(100-avg_sat if pd.notna(avg_sat) else None))
        m5.metric("Avg Sent Rate", f_v(filtered_kpi['Sent_Rate'].mean()))

        # --- CHARTS ---
        def make_c(df, y, t, c):
            if freq == "Daily": return px.bar(df, x='Date', y=y, title=t, color_discrete_sequence=[c])
            return px.line(df, x='Date', y=y, markers=True, title=t, color_discrete_sequence=[c])

        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(make_c(chart_df, 'Shift_Score', "Shift Score", "#3498db"), width='stretch')
            st.plotly_chart(make_c(chart_df, 'Satisfied_Survey', "Satisfied Survey (%)", "#2ecc71"), width='stretch')
        with c2:
            st.plotly_chart(make_c(chart_df, 'IA_Hours', "IA Hours", "#e67e22"), width='stretch')
            st.plotly_chart(make_c(chart_df, 'Sent_Rate', "Survey Sent (%)", "#9b59b6"), width='stretch')

        # --- DSAT SECTION ---
        st.divider()
        st.subheader(f"🚫 DSAT Analysis & Feedback ({len(filtered_dsat)})")
        st.dataframe(filtered_dsat[['Date', 'Chat_Link', 'Feedback']], column_config={"Chat_Link": st.column_config.LinkColumn("Chat")}, width='stretch', hide_index=True)

    else:
        st.sidebar.error("Email not found in Go Getters database.")
else:
    st.info("👈 Enter your work email in the sidebar to load the dashboard.")
