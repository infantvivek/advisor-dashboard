

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

MANAGER_EMAIL = "vivek.j@gohighlevel.com" 
TEAM_LEAD_EMAIL = "ayush.bhadauria@gohighlevel.com"

st.set_page_config(page_title="The Go Getters | Performance Portal", layout="wide")

# --- 2. HELPER FUNCTIONS ---
def parse_time_to_minutes(time_str):
    """Converts '3h 24m' or similar formats to total minutes."""
    if pd.isna(time_str) or not isinstance(time_str, str):
        return 0
    try:
        hours, minutes = 0, 0
        parts = time_str.split()
        for part in parts:
            if 'h' in part:
                hours = int(part.replace('h', ''))
            elif 'm' in part:
                minutes = int(part.replace('m', ''))
        return (hours * 60) + minutes
    except:
        return 0

def format_minutes_to_hours(total_minutes):
    """Converts total minutes back to '3h 24m' format."""
    if pd.isna(total_minutes) or total_minutes <= 0:
        return "0h 0m"
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)
    return f"{hours}h {minutes}m"

# --- 3. DATA LOADING ---
@st.cache_data(ttl=30)
def load_data(url, is_kpi=False):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip().str.replace('\ufeff', '')
        if 'Email' in df.columns:
            df['Email'] = df['Email'].astype(str).str.strip().str.lower()
        if is_kpi:
            # Handle Duration Fields
            df['IA_Mins'] = df['IA_Hours'].apply(parse_time_to_minutes)
            df['Call_Mins'] = df['Advisor Call Time'].apply(parse_time_to_minutes)
            
            # Formula: Shift_Score = (Total Recorded Call Time) / (Total IA Hours)
            df['Shift_Score'] = (df['Call_Mins'] / df['IA_Mins'] * 100).fillna(0)
            
            # Clean Percentages and Integers
            numeric_cols = ['Sent Rate %', 'Satisfied Survey %', 'Call Abandons', 'MOB', 'OB Calls', 'Q/A Calls', 'Total Survey']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace('%', '').str.strip()
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df
    except: return None

# --- 4. AUTHENTICATION ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.title("The Go Getters Login")
    with st.form("Login"):
        email_input = st.text_input("Work Email").strip().lower()
        pass_input = st.text_input("Password", type="password")
        if st.form_submit_button("Access Portal"):
            team_db = load_data(TEAM_URL)
            if team_db is not None:
                user_match = team_db[(team_db['Email'] == email_input) & (team_db['Password'].astype(str).str.strip() == pass_input.strip())]
                if not user_match.empty:
                    st.session_state.update({'authenticated': True, 'user_email': email_input, 'user_name': user_match['Advisor Name'].iloc[0]})
                    st.rerun()
            st.error("Invalid credentials.")
    st.stop()

# --- 5. DATA PREP ---
is_privileged = st.session_state['user_email'] in [MANAGER_EMAIL, TEAM_LEAD_EMAIL]
kpi_df = load_data(KPI_URL, is_kpi=True)
dsat_df = load_data(DSAT_URL)

c1, c2 = st.columns([2, 8])
with c1: st.image("https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/48175265495/original/PTXBCP40UHx-8LCKsM1zqLX-pq8nndFHSw.png?1641235482", width='stretch')
with c2: 
    st.title("The Go Getters")
    st.subheader(f"Welcome {st.session_state['user_name']}!!")

if st.sidebar.button("Logout"):
    st.session_state['authenticated'] = False
    st.rerun()

# Filter context
if not is_privileged:
    full_kpi = kpi_df[kpi_df['Email'] == st.session_state['user_email']].copy()
    full_dsat = dsat_df[dsat_df['Email'] == st.session_state['user_email']].copy() if dsat_df is not None else pd.DataFrame()
else:
    full_kpi = kpi_df.copy()
    full_dsat = dsat_df.copy() if dsat_df is not None else pd.DataFrame()

full_kpi['Date'] = pd.to_datetime(full_kpi['Date'], format="%b'%d'%y", errors='coerce')
full_kpi = full_kpi.dropna(subset=['Date']).sort_values('Date')
if not full_dsat.empty:
    full_dsat['Date'] = pd.to_datetime(full_dsat['Date'], format="%d/%m/%Y", errors='coerce')
    full_dsat = full_dsat.dropna(subset=['Date'])

# --- 6. FREQUENCY FILTERS ---
freq = st.radio("Frequency:", ["Daily", "Weekly", "Monthly"], horizontal=True)

if freq == "Daily":
    sel = st.selectbox("Select Date:", sorted(full_kpi['Date'].unique(), reverse=True), format_func=lambda x: x.strftime('%d %b %Y'))
    f_kpi = full_kpi[full_kpi['Date'] == sel]
    f_dsat = full_dsat[full_dsat['Date'].dt.normalize() == sel] if not full_dsat.empty else pd.DataFrame()
elif freq == "Weekly":
    full_kpi['W_Start'] = full_kpi['Date'] - pd.to_timedelta((full_kpi['Date'].dt.dayofweek + 1) % 7, unit='d')
    full_kpi['W_End'] = full_kpi['W_Start'] + pd.to_timedelta(6, unit='d')
    full_kpi['Week_Range'] = full_kpi['W_Start'].dt.strftime('%d %b %Y') + " - " + full_kpi['W_End'].dt.strftime('%d %b %Y')
    sel = st.selectbox("Select Week:", full_kpi.sort_values('W_Start', ascending=False)['Week_Range'].unique())
    f_kpi = full_kpi[full_kpi['Week_Range'] == sel]
    f_dsat = full_dsat[full_dsat['Date'].isin(f_kpi['Date'])] if not full_dsat.empty else pd.DataFrame()
else:
    full_kpi['Month_Label'] = full_kpi['Date'].dt.strftime('%B %Y')
    sel = st.selectbox("Select Month:", full_kpi.sort_values('Date', ascending=False)['Month_Label'].unique())
    f_kpi = full_kpi[full_kpi['Month_Label'] == sel]
    f_dsat = full_dsat[full_dsat['Date'].isin(f_kpi['Date'])] if not full_dsat.empty else pd.DataFrame()

# --- 7. PERFORMANCE NARRATIVE ---
st.divider()
st.subheader("Performance Narrative")
avg_ia_mins = f_kpi['IA_Mins'].mean()
avg_sat = f_kpi['Satisfied Survey %'].mean()
avg_sent = f_kpi['Sent Rate %'].mean()

if is_privileged:
    st.info(f"Team summary for {sel}: Average Satisfaction is {avg_sat:.2f}% and Sent Rate is {avg_sent:.2f}%. Total IA logged: {format_minutes_to_hours(f_kpi['IA_Mins'].sum())}.")
else:
    st.info(f"Your summary for {sel}: You achieved a Satisfaction score of {avg_sat:.1f}% across {int(f_kpi['Total Survey'].sum())} surveys.")

# --- 8. PERFORMANCE SUMMARY ---
st.header("Performance summary")
m = st.columns(5)
m[0].metric("Avg Shift Score", f"{f_kpi['Shift_Score'].mean():.1f}%")
m[1].metric("Avg IA Hours", format_minutes_to_hours(avg_ia_mins))
m[2].metric("Avg Advisor Call Time", format_minutes_to_hours(f_kpi['Call_Mins'].mean()))
m[3].metric("Avg Satisfied Survey", f"{avg_sat:.1f}%")
m[4].metric("Total Survey", int(f_kpi['Total Survey'].sum()))

v = st.columns(5)
v[0].metric("Avg Sent Rate %", f"{avg_sent:.1f}%")
v[1].metric("Total OB Calls", int(f_kpi['OB Calls'].sum()))
v[2].metric("Total Q/A Calls", int(f_kpi['Q/A Calls'].sum()))
v[3].metric("Total MOB", int(f_kpi['MOB'].sum()))
v[4].metric("Total Call Abandons", int(f_kpi['Call Abandons'].sum()))

# --- 9. PRIVILEGED LEADERBOARDS ---
if is_privileged:
    st.divider()
    st.header("🏆 Success Champions")
    l_df = f_kpi.groupby('Advisor Name').agg({'Sent Rate %':'mean','Satisfied Survey %':'mean','Email':'first'}).reset_index()
    eligible_df = l_df[l_df['Sent Rate %'] >= 80].round(2)
    st.dataframe(eligible_df.sort_values('Satisfied Survey %', ascending=False)[['Advisor Name', 'Sent Rate %', 'Satisfied Survey %']], hide_index=True, width=600)

# --- 10. TRENDS & REPORTS ---
st.divider()
st.header("Performance Trends")
chart_df = f_kpi.groupby('Date').mean(numeric_only=True).reset_index() if is_privileged else f_kpi.sort_values('Date')

t1, t2 = st.columns(2)
with t1:
    st.plotly_chart(px.line(chart_df, x='Date', y='Shift_Score', title="Shift Score Trend", markers=True), width='stretch')
    st.plotly_chart(px.line(chart_df, x='Date', y='Satisfied Survey %', title="Satisfied Survey Trend", markers=True), width='stretch')
with t2:
    st.plotly_chart(px.line(chart_df, x='Date', y='IA_Mins', title="IA Minutes Trend", markers=True), width='stretch')
    st.plotly_chart(px.line(chart_df, x='Date', y='Sent Rate %', title="Survey Sent Trend", markers=True), width='stretch')

# DSAT SECTION
st.divider()
st.subheader(f"🚫 DSAT Analysis & Feedback ({len(f_dsat)})")
if not f_dsat.empty:
    st.dataframe(f_dsat.sort_values('Date', ascending=False), column_config={"Chat_Link": st.column_config.LinkColumn("View Chat")}, hide_index=True)

# DETAILED REPORT
st.divider()
st.header("Detailed Report")
st.dataframe(f_kpi.sort_values('Date', ascending=False), hide_index=True)
