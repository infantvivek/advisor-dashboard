

# --- 1. DATA SOURCE LINKS ---
# Ensure these links point to the specific tabs in your Google Sheet (Published as CSV)
#TEAM_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=0&single=true&output=csv"
#KPI_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=1918948844&single=true&output=csv"
#DSAT_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=367459010&single=true&output=csv" 
import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. UPDATED DATA SOURCE LINKS ---
TEAM_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=0&single=true&output=csv"
KPI_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=1918948844&single=true&output=csv"
DSAT_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=367459010&single=true&output=csv"

st.set_page_config(page_title="The Go Getters | Performance Portal", layout="wide")

# --- 2. DATA LOADING & CLEANING ---
@st.cache_data(ttl=30)
def load_data(url, is_kpi=False):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip().str.replace('\ufeff', '')
        if 'Email' in df.columns:
            df['Email'] = df['Email'].str.strip().str.lower()
        if is_kpi:
            numeric_cols = ['IA_Hours', 'Shift_Score', 'Sent_Rate', 'Satisfied_Survey', 'OB_Calls', 'QA_Calls', 'Call_Abandons', 'MOB']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace('%', '').str.strip()
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except Exception as e:
        return None

# --- 3. LOGIN INTERFACE ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    col_logo, col_title = st.columns([1, 8])
    with col_logo:
        st.image("https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/48175265495/original/PTXBCP40UHx-8LCKsM1zqLX-pq8nndFHSw.png?1641235482", width=100)
    with col_title:
        st.title("The Go Getters Login")
    
    with st.form("Login"):
        email_input = st.text_input("Work Email").strip().lower()
        pass_input = st.text_input("Password", type="password")
        submit = st.form_submit_button("Access Portal")
        
        if submit:
            team_db = load_data(TEAM_URL)
            if team_db is not None:
                user_match = team_db[(team_db['Email'] == email_input) & (team_db['Password'].astype(str) == pass_input)]
                if not user_match.empty:
                    st.session_state['authenticated'] = True
                    st.session_state['user_email'] = email_input
                    st.session_state['user_name'] = user_match['Advisor Name'].iloc[0]
                    st.rerun()
                else:
                    st.error("Invalid Email or Password.")
    st.stop()

# --- 4. DASHBOARD CONTENT ---
user_email = st.session_state['user_email']
advisor_name = st.session_state['user_name']

col1, col2 = st.columns([1, 8])
with col1:
    st.image("https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/48175265495/original/PTXBCP40UHx-8LCKsM1zqLX-pq8nndFHSw.png?1641235482", width=100)
with col2:
    st.title("The Go Getters")
    st.subheader(f"Advisor Performance Dashboard | Welcome, {advisor_name}")

if st.sidebar.button("Logout"):
    st.session_state['authenticated'] = False
    st.rerun()

kpi_df = load_data(KPI_URL, is_kpi=True)
dsat_df = load_data(DSAT_URL)

if kpi_df is not None:
    user_kpi = kpi_df[kpi_df['Email'] == user_email].copy()
    user_kpi['Date'] = pd.to_datetime(user_kpi['Date'], format="%b'%d'%y", errors='coerce')
    user_kpi = user_kpi.dropna(subset=['Date']).sort_values('Date')

    freq = st.radio("Select View Frequency:", ["Daily", "Weekly", "Monthly"], horizontal=True)

    # --- FILTERING ---
    if freq == "Daily":
        sel = st.selectbox("Select Date:", sorted(user_kpi['Date'].unique(), reverse=True), format_func=lambda x: x.strftime('%d %b %Y'))
        filtered_kpi = user_kpi[user_kpi['Date'] == sel]
    elif freq == "Weekly":
        user_kpi['W_Start'] = user_kpi['Date'] - pd.to_timedelta(user_kpi['Date'].dt.dayofweek + 1 % 7, unit='d')
        user_kpi['Week_Range'] = user_kpi['W_Start'].dt.strftime('%d %b %Y') + " - " + (user_kpi['W_Start'] + pd.to_timedelta(6, unit='d')).dt.strftime('%d %b %Y')
        sel = st.selectbox("Select Week:", sorted(user_kpi['Week_Range'].unique(), reverse=True))
        filtered_kpi = user_kpi[user_kpi['Week_Range'] == sel]
    else: # Monthly
        user_kpi['Month_Label'] = user_kpi['Date'].dt.strftime('%B %Y')
        sel = st.selectbox("Select Month:", sorted(user_kpi['Month_Label'].unique(), reverse=True))
        filtered_kpi = user_kpi[user_kpi['Month_Label'] == sel]

    # --- PERFORMANCE SUMMARY BLOCK ---
    st.markdown("---")
    st.header("Performance summary")
    
    def f_v(v, s="%"): return f"{v:.1f}{s}" if pd.notna(v) and v != 0 else "-"
    avg_sat = filtered_kpi['Satisfied_Survey'].mean()

    m_row1 = st.columns(5)
    m_row1[0].metric("Avg Shift Score", f_v(filtered_kpi['Shift_Score'].mean()))
    m_row1[1].metric("Avg IA Hours", f_v(filtered_kpi['IA_Hours'].mean(), "h"))
    m_row1[2].metric("Avg Sent Rate %", f_v(filtered_kpi['Sent_Rate'].mean()))
    m_row1[3].metric("Avg Satisfied Survey", f_v(avg_sat))
    m_row1[4].metric("Avg DSAT %", f_v(100 - avg_sat if pd.notna(avg_sat) else None))

    m_row2 = st.columns(4)
    m_row2[0].metric("Total OB Calls", int(filtered_kpi['OB_Calls'].sum()))
    m_row2[1].metric("Total QA Calls", int(filtered_kpi['QA_Calls'].sum()))
    m_row2[2].metric("Total MOB", int(filtered_kpi['MOB'].sum()))
    m_row2[3].metric("Total Call Abandons", int(filtered_kpi['Call_Abandons'].sum()))

    # --- PERFORMANCE TRENDS ---
    st.divider()
    st.header("Performance Trends")
    chart_df = filtered_kpi.sort_values('Date')
    def make_c(df, y, t, c):
        if freq == "Daily": return px.bar(df, x='Date', y=y, title=t, color_discrete_sequence=[c])
        return px.line(df, x='Date', y=y, markers=True, title=t, color_discrete_sequence=[c])

    c1, c2 = st.columns(2)
    with c1:
        st.plotly_chart(make_c(chart_df, 'Shift_Score', "Shift Score Trend", "#3498db"), width='stretch')
        st.plotly_chart(make_c(chart_df, 'Satisfied_Survey', "Satisfied Survey (%) Trend", "#2ecc71"), width='stretch')
    with c2:
        st.plotly_chart(make_c(chart_df, 'IA_Hours', "IA Hours Trend", "#e67e22"), width='stretch')
        st.plotly_chart(make_c(chart_df, 'Sent_Rate', "Survey Sent (%) Trend", "#9b59b6"), width='stretch')

    # --- DSAT ANALYSIS ---
    st.divider()
    if dsat_df is not None:
        dsat_df['Date'] = pd.to_datetime(dsat_df['Date'], format="%d/%m/%Y", errors='coerce')
        user_dsat = dsat_df[dsat_df['Email'] == user_email].copy()
        if freq == "Daily": f_dsat = user_dsat[user_dsat['Date'].dt.normalize() == sel]
        elif freq == "Weekly": 
            user_dsat['Week_Range'] = (user_dsat['Date'] - pd.to_timedelta(user_dsat['Date'].dt.dayofweek + 1 % 7, unit='d')).dt.strftime('%d %b %Y')
            f_dsat = user_dsat[user_dsat['Week_Range'] == sel.split(' - ')[0]]
        else: f_dsat = user_dsat[user_dsat['Date'].dt.strftime('%B %Y') == sel]
        
        st.subheader(f"🚫 DSAT Analysis & Feedback ({len(f_dsat)})")
        st.dataframe(f_dsat[['Date', 'Chat_Link', 'Feedback']], column_config={"Chat_Link": st.column_config.LinkColumn("Chat")}, width='stretch', hide_index=True)
