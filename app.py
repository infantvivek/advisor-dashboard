

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

# PRIVILEGED EMAILS
MANAGER_EMAIL = "vivek.j@gohighlevel.com" 
TEAM_LEAD_EMAIL = "ayush.bhadauria@gohighlevel.com"

# KPI TARGETS
TARGETS = {
    'IA_Hours': 6.0,
    'Shift_Score': 80.0,
    'Sent_Rate': 80.0,
    'Satisfied_Survey': 80.0
}

st.set_page_config(page_title="The Go Getters | Performance Portal", layout="wide")

# --- 2. DATA LOADING & CLEANING ---
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

# --- 3. AUTHENTICATION ---
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

# --- 4. DATA PREP ---
is_privileged = st.session_state['user_email'] in [MANAGER_EMAIL, TEAM_LEAD_EMAIL]
kpi_df = load_data(KPI_URL, is_kpi=True)
dsat_df = load_data(DSAT_URL)

c1, c2 = st.columns([2, 8])
with c1: 
    st.image("https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/48175265495/original/PTXBCP40UHx-8LCKsM1zqLX-pq8nndFHSw.png?1641235482", width='stretch')
with c2: 
    st.title("The Go Getters")
    st.subheader(f"Welcome {st.session_state['user_name']}!!")

if st.sidebar.button("Logout"):
    st.session_state['authenticated'] = False
    st.rerun()

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

# --- 5. FREQUENCY FILTERS ---
freq = st.radio("Frequency:", ["Daily", "Weekly", "Monthly"], horizontal=True)

if freq == "Daily":
    sel = st.selectbox("Select Date:", sorted(full_kpi['Date'].unique(), reverse=True), format_func=lambda x: x.strftime('%d %b %Y'))
    f_kpi = full_kpi[full_kpi['Date'] == sel]
    f_dsat = full_dsat[full_dsat['Date'].dt.normalize() == sel] if not full_dsat.empty else pd.DataFrame()
elif freq == "Weekly":
    full_kpi['W_Start'] = full_kpi['Date'] - pd.to_timedelta((full_kpi['Date'].dt.dayofweek + 1) % 7, unit='d')
    full_kpi['W_End'] = full_kpi['W_Start'] + pd.to_timedelta(6, unit='d')
    full_kpi['Week_Range'] = full_kpi['W_Start'].dt.strftime('%d %b %Y') + " - " + full_kpi['W_End'].dt.strftime('%d %b %Y')
    week_options = full_kpi.sort_values('W_Start', ascending=False)['Week_Range'].unique()
    sel = st.selectbox("Select Week:", week_options)
    f_kpi = full_kpi[full_kpi['Week_Range'] == sel]
    if not full_dsat.empty:
        full_dsat['Week_Range'] = (full_dsat['Date'] - pd.to_timedelta((full_dsat['Date'].dt.dayofweek + 1) % 7, unit='d')).dt.strftime('%d %b %Y') + " - " + (full_dsat['Date'] + pd.to_timedelta(6, unit='d')).dt.strftime('%d %b %Y')
        f_dsat = full_dsat[full_dsat['Week_Range'] == sel]
else:
    full_kpi['Month_Label'] = full_kpi['Date'].dt.strftime('%B %Y')
    month_options = full_kpi.sort_values('Date', ascending=False)['Month_Label'].unique()
    sel = st.selectbox("Select Month:", month_options)
    f_kpi = full_kpi[full_kpi['Month_Label'] == sel]
    if not full_dsat.empty:
        full_dsat['Month_Label'] = full_dsat['Date'].dt.strftime('%B %Y')
        f_dsat = full_dsat[full_dsat['Month_Label'] == sel]

# --- 6. PERFORMANCE NARRATIVE ---
st.divider()
st.subheader("Performance Narrative")

avg_score = f_kpi['Shift_Score'].mean()
avg_ia = f_kpi['IA_Hours'].mean()
avg_sent = f_kpi['Sent_Rate'].mean()
avg_sat = f_kpi['Satisfied_Survey'].mean()

if is_privileged:
    shout_out = f_kpi[(f_kpi['Sent_Rate'] >= 80) & (f_kpi['Satisfied_Survey'] > 95)]['Advisor Name'].unique()
    attention = f_kpi[(f_kpi['IA_Hours'] < 6) | (f_kpi['Shift_Score'] < 80) | (f_kpi['Satisfied_Survey'] < 80)]['Advisor Name'].unique()
    
    narrative = f"Team Performance for {sel}: Average Satisfaction is {avg_sat:.1f}% vs target of 80%. Sent Rate is {avg_sent:.1f}% vs target of 80%. "
    narrative += f"Average IA Hours stand at {avg_ia:.1f}h (Target: >6h). Shout-out to {', '.join(shout_out) if len(shout_out)>0 else 'none'} for hitting high standards. "
    narrative += f"Advisors needing target focus: {', '.join(attention) if len(attention)>0 else 'none'}."
    st.info(narrative)
else:
    status = "meeting" if (avg_ia >= 6 and avg_score >= 80 and avg_sent >= 80 and avg_sat >= 80) else "working towards"
    narrative = f"For {sel}, you are {status} your KPI targets. Your IA Hours ({avg_ia:.1f}h) and Shift Score ({avg_score:.1f}%) are your key drivers. "
    narrative += f"Current Satisfaction is {avg_sat:.1f}% (Target: 80%) and Sent Rate is {avg_sent:.1f}% (Target: 80%). Keep pushing!"
    st.info(narrative)

# --- 7. PERFORMANCE SUMMARY METRICS WITH COLOR ---
st.header("Performance summary")

def get_color(val, target, is_ia=False):
    # IA Hours uses >6, others use >=
    condition = val > target if is_ia else val >= target
    return "normal" if condition else "inverse"

m = st.columns(5)
# Shift Score
m[0].metric("Avg Shift Score", f"{avg_score:.1f}%", delta="Target: 80%", delta_color=get_color(avg_score, 80))
# IA Hours
m[1].metric("Avg IA Hours", f"{avg_ia:.1f}h", delta="Target: >6h", delta_color=get_color(avg_ia, 6, True))
# Sent Rate
m[2].metric("Avg Sent Rate %", f"{avg_sent:.1f}%", delta="Target: 80%", delta_color=get_color(avg_sent, 80))
# Satisfied Survey
m[3].metric("Avg Satisfied Survey", f"{avg_sat:.1f}%", delta="Target: 80%", delta_color=get_color(avg_sat, 80))
# Avg DSAT (Reference only)
m[4].metric("Avg DSAT %", f"{(100-avg_sat):.1f}%" if pd.notna(avg_sat) else "-", delta="Goal: <20%")

v = st.columns(4)
v[0].metric("Total OB Calls", int(f_kpi['OB_Calls'].sum()))
v[1].metric("Total QA Calls", int(f_kpi['QA_Calls'].sum()))
v[2].metric("Total MOB", int(f_kpi['MOB'].sum()))
v[3].metric("Total Call Abandons", int(f_kpi['Call_Abandons'].sum()))

# --- 8. PRIVILEGED LEADERBOARDS ---
if is_privileged:
    st.divider()
    st.header("🏆 Team Leaderboards")
    l_df = f_kpi.groupby('Advisor Name').agg({'Sent_Rate':'mean','Satisfied_Survey':'mean','Email':'first'}).reset_index()
    d_counts = f_dsat.groupby('Email').size().reset_index(name='Total DSAT') if not f_dsat.empty else pd.DataFrame(columns=['Email','Total DSAT'])
    l_df = l_df.merge(d_counts, on='Email', how='left').fillna(0)
    
    lc1, lc2, lc3 = st.columns(3)
    with lc1:
        st.subheader("🏆 Success Champions")
        eligible_df = l_df[l_df['Sent_Rate'] >= 80]
        st.dataframe(eligible_df.sort_values('Satisfied_Survey', ascending=False)[['Advisor Name', 'Sent_Rate', 'Satisfied_Survey']], hide_index=True)
    with lc2:
        st.subheader("Top Sent Rate")
        st.dataframe(l_df.sort_values('Sent_Rate', ascending=False)[['Advisor Name','Sent_Rate']], hide_index=True)
    with lc3:
        st.subheader("Total DSAT Received")
        st.dataframe(l_df.sort_values('Total DSAT', ascending=False)[['Advisor Name','Total DSAT']], hide_index=True)

# --- 9. PERFORMANCE TRENDS ---
st.divider()
st.header("Performance Trends")
chart_df = f_kpi.groupby('Date').mean(numeric_only=True).reset_index() if is_privileged else f_kpi.sort_values('Date')

t_col1, t_col2 = st.columns(2)
with t_col1:
    st.plotly_chart(px.line(chart_df, x='Date', y='Shift_Score', title="Shift Score Trend", markers=True), width='stretch')
    st.plotly_chart(px.line(chart_df, x='Date', y='Satisfied_Survey', title="Satisfied Survey (%) Trend", markers=True), width='stretch')
with t_col2:
    st.plotly_chart(px.line(chart_df, x='Date', y='IA_Hours', title="IA Hours Trend", markers=True), width='stretch')
    st.plotly_chart(px.line(chart_df, x='Date', y='Sent_Rate', title="Survey Sent (%) Trend", markers=True), width='stretch')

# DSAT & DETAILED REPORT
st.divider()
st.subheader(f"🚫 DSAT Analysis & Feedback ({len(f_dsat)})")
if not f_dsat.empty:
    st.dataframe(f_dsat.sort_values('Date', ascending=False), column_config={"Chat_Link": st.column_config.LinkColumn("View Chat")}, hide_index=True)
st.divider()
st.header("Detailed Report")
st.dataframe(f_kpi.sort_values('Date', ascending=False), hide_index=True)
