

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

# SET YOUR EMAIL HERE FOR MANAGER ACCESS
MANAGER_EMAIL = "vivek.infant@gohighlevel.com" 

st.set_page_config(page_title="The Go Getters | Manager Portal", layout="wide")

# --- 2. DATA LOADING ---
@st.cache_data(ttl=30)
def load_data(url, is_kpi=False):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip().str.replace('\ufeff', '')
        if 'Email' in df.columns:
            df['Email'] = df['Email'].astype(str).str.strip().str.lower()
        if is_kpi:
            numeric_cols = ['IA_Hours', 'Shift_Score', 'Sent_Rate', 'Satisfied_Survey', 'OB_Calls', 'QA_Calls', 'Call_Abandons', 'MOB']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = df[col].astype(str).str.replace('%', '').str.strip()
                    df[col] = pd.to_numeric(df[col], errors='coerce')
        return df
    except: return None

# --- 3. LOGIN ---
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

if not st.session_state['authenticated']:
    st.title("The Go Getters Login")
    with st.form("Login"):
        email_input = st.text_input("Work Email").strip().lower()
        pass_input = st.text_input("Password", type="password")
        if st.form_submit_button("Access Portal"):
            team_db = load_data(TEAM_URL)
            user_match = team_db[(team_db['Email'] == email_input) & (team_db['Password'].astype(str) == pass_input)]
            if not user_match.empty:
                st.session_state.update({'authenticated': True, 'user_email': email_input, 'user_name': user_match['Advisor Name'].iloc[0]})
                st.rerun()
            else: st.error("Invalid credentials.")
    st.stop()

# --- 4. DASHBOARD LOGIC ---
is_manager = st.session_state['user_email'] == MANAGER_EMAIL
kpi_df = load_data(KPI_URL, is_kpi=True)
dsat_df = load_data(DSAT_URL)

# Branding
c1, c2 = st.columns([1, 8])
with c1: st.image("https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/48175265495/original/PTXBCP40UHx-8LCKsM1zqLX-pq8nndFHSw.png?1641235482", width=100)
with c2: st.title(f"The Go Getters - {'Manager' if is_manager else 'Advisor'} View")

# Filter Data: If Manager, take ALL. If Advisor, take THEIRS.
if not is_manager:
    full_data = kpi_df[kpi_df['Email'] == st.session_state['user_email']].copy()
else:
    full_data = kpi_df.copy()

full_data['Date'] = pd.to_datetime(full_data['Date'], format="%b'%d'%y", errors='coerce')
full_data = full_data.dropna(subset=['Date']).sort_values('Date')

freq = st.radio("Frequency:", ["Daily", "Weekly", "Monthly"], horizontal=True)

# Selection Logic
if freq == "Daily":
    sel = st.selectbox("Select Date:", sorted(full_data['Date'].unique(), reverse=True), format_func=lambda x: x.strftime('%d %b %Y'))
    filtered_kpi = full_data[full_data['Date'] == sel]
elif freq == "Weekly":
    full_data['Week'] = (full_data['Date'] - pd.to_timedelta(full_data['Date'].dt.dayofweek + 1 % 7, unit='d')).dt.strftime('%d %b %Y')
    sel = st.selectbox("Select Week:", sorted(full_data['Week'].unique(), reverse=True))
    filtered_kpi = full_data[full_data['Week'] == sel]
else:
    full_data['Month'] = full_data['Date'].dt.strftime('%B %Y')
    sel = st.selectbox("Select Month:", sorted(full_data['Month'].unique(), reverse=True))
    filtered_kpi = full_data[full_data['Month'] == sel]

# --- PERFORMANCE SUMMARY ---
st.header("Performance summary")
avg_sat = filtered_kpi['Satisfied_Survey'].mean()
m = st.columns(5)
m[0].metric("Avg Shift Score", f"{filtered_kpi['Shift_Score'].mean():.1f}%")
m[1].metric("Avg IA Hours", f"{filtered_kpi['IA_Hours'].mean():.2f}h")
m[2].metric("Avg Sent Rate %", f"{filtered_kpi['Sent_Rate'].mean():.1f}%")
m[3].metric("Avg Satisfied Survey", f"{avg_sat:.1f}%")
m[4].metric("Avg DSAT %", f"{(100-avg_sat):.1f}%" if pd.notna(avg_sat) else "-")

v = st.columns(4)
v[0].metric("Total OB Calls", int(filtered_kpi['OB_Calls'].sum()))
v[1].metric("Total QA Calls", int(filtered_kpi['QA_Calls'].sum()))
v[2].metric("Total MOB", int(filtered_kpi['MOB'].sum()))
v[3].metric("Total Call Abandons", int(filtered_kpi['Call_Abandons'].sum()))

# --- MANAGER LEADERBOARD ---
if is_manager:
    st.divider()
    st.header("🏆 Team Leaderboard")
    
    # Prep Leaderboard Data
    leader_df = filtered_kpi.groupby('Advisor Name').agg({
        'Sent_Rate': 'mean',
        'Satisfied_Survey': 'mean',
        'Email': 'first'
    }).reset_index()
    
    # Get DSAT counts per advisor from the DSAT sheet
    dsat_df['Date'] = pd.to_datetime(dsat_df['Date'], format="%d/%m/%Y", errors='coerce')
    dsat_counts = dsat_df.groupby('Email').size().reset_index(name='Total DSAT')
    leader_df = leader_df.merge(dsat_counts, on='Email', how='left').fillna(0)
    
    l1, l2, l3 = st.columns(3)
    with l1:
        st.subheader("Top Satisfied Survey")
        st.dataframe(leader_df.sort_values('Satisfied_Survey', ascending=False)[['Advisor Name', 'Satisfied_Survey']].head(5), hide_index=True)
    with l2:
        st.subheader("Top Sent Rate")
        st.dataframe(leader_df.sort_values('Sent_Rate', ascending=False)[['Advisor Name', 'Sent_Rate']].head(5), hide_index=True)
    with l3:
        st.subheader("Lowest DSAT (Leader)")
        st.dataframe(leader_df.sort_values('Total DSAT', ascending=True)[['Advisor Name', 'Total DSAT']].head(5), hide_index=True)

# --- TRENDS ---
st.divider()
st.header("Performance Trends")
chart_data = filtered_kpi.groupby('Date').mean(numeric_only=True).reset_index() if is_manager else filtered_kpi

t1, t2 = st.columns(2)
with t1:
    st.plotly_chart(px.line(chart_data, x='Date', y='Shift_Score', title="Team Shift Score Trend") if is_manager else px.bar(chart_data, x='Date', y='Shift_Score', title="Daily Shift Score"), use_container_width=True)
with t2:
    st.plotly_chart(px.line(chart_data, x='Date', y='Satisfied_Survey', title="Team Satisfaction Trend") if is_manager else px.bar(chart_data, x='Date', y='Satisfied_Survey', title="Daily Satisfaction"), use_container_width=True)

if st.sidebar.button("Logout"):
    st.session_state['authenticated'] = False
    st.rerun()
