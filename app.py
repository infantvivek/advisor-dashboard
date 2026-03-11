

# --- 1. DATA SOURCE LINKS ---
# Ensure these links point to the specific tabs in your Google Sheet (Published as CSV)
#TEAM_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=0&single=true&output=csv"
#KPI_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=1918948844&single=true&output=csv"
#DSAT_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=367459010&single=true&output=csv" 
import streamlit as st
import pandas as pd
import plotly.express as px

# ---  PAGE CONFIGURATION ---
# Setting layout to "wide" allows the app to auto-adjust to the screen size
st.set_page_config(
    page_title="The Go Getters | Performance Portal", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

# --- 1. DATA SOURCE LINKS ---
TEAM_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=0&single=true&output=csv"
KPI_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=1918948844&single=true&output=csv"
DSAT_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=367459010&single=true&output=csv"

# PRIVILEGED EMAILS (Managers and Team Leads)
MANAGER_EMAIL = "vivek.j@gohighlevel.com" 
SR_MANAGER_EMAIL = "sumit.ludhwani@gohighlevel.com"
TEAM_LEAD_EMAIL = "ayush.bhadauria@gohighlevel.com"

# --- 2. HELPER FUNCTIONS ---
def parse_time_to_minutes(time_str):
    if pd.isna(time_str) or not isinstance(time_str, str): return 0
    try:
        hours, minutes = 0, 0
        parts = time_str.split()
        for part in parts:
            if 'h' in part: hours = int(part.replace('h', ''))
            elif 'm' in part: minutes = int(part.replace('m', ''))
        return (hours * 60) + minutes
    except: return 0

def format_minutes_to_hours(total_minutes):
    if pd.isna(total_minutes) or total_minutes <= 0: return "0h 0m"
    return f"{int(total_minutes // 60)}h {int(total_minutes % 60)}m"

# --- 3. DATA LOADING ---
@st.cache_data(ttl=30)
def load_data(url, is_kpi=False):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip().str.replace('\ufeff', '')
        if 'Email' in df.columns:
            df['Email'] = df['Email'].astype(str).str.strip().str.lower()
        if is_kpi:
            df['IA_Mins'] = df['IA_Hours'].apply(parse_time_to_minutes)
            df['Call_Mins'] = df['Advisor Call Time'].apply(parse_time_to_minutes)
            df['Shift_Score'] = (df['Call_Mins'] / df['IA_Mins'] * 100).fillna(0)
            numeric_cols = ['Sent Rate %', 'Satisfied Survey %', 'Call Abandons', 'MOB', 'OB Calls', 'Q/A Calls', 'Total Survey']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].astype(str).str.replace('%', '').str.strip(), errors='coerce').fillna(0)
        return df
    except: return None

# --- 4. AUTHENTICATION ---
if 'authenticated' not in st.session_state: st.session_state['authenticated'] = False
if not st.session_state['authenticated']:
    st.title("The Go Getters Login")
    with st.form("Login"):
        e_in, p_in = st.text_input("Email").lower(), st.text_input("Password", type="password")
        if st.form_submit_button("Login"):
            team_db = load_data(TEAM_URL)
            match = team_db[(team_db['Email'] == e_in) & (team_db['Password'].astype(str) == p_in)]
            if not match.empty:
                st.session_state.update({'authenticated': True, 'user_email': e_in, 'user_name': match['Advisor Name'].iloc[0]})
                st.rerun()
    st.stop()

# --- 5. DATA PREP & DRILL-DOWN ---
# Updated list to include Sr. Manager
is_privileged = st.session_state['user_email'] in [MANAGER_EMAIL, SR_MANAGER_EMAIL, TEAM_LEAD_EMAIL]
kpi_df, dsat_df = load_data(KPI_URL, is_kpi=True), load_data(DSAT_URL)

drill_down_advisor = None
view_mode = "Team Overview"

if is_privileged:
    st.sidebar.divider()
    view_mode = st.sidebar.radio("View Mode", ["Team Overview", "Specific Advisor View"])
    if view_mode == "Specific Advisor View":
        advisor_list = sorted(kpi_df['Advisor Name'].unique())
        drill_down_advisor = st.sidebar.selectbox("Select Advisor to Review", advisor_list)

c1, c2 = st.columns([2, 8])
with c1: st.image("https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/48175265495/original/PTXBCP40UHx-8LCKsM1zqLX-pq8nndFHSw.png?1641235482", width='stretch')
with c2: 
    st.title("The Go Getters")
    display_name = drill_down_advisor if drill_down_advisor else st.session_state['user_name']
    st.subheader(f"Welcome {st.session_state['user_name']}!! (Reviewing: {display_name})" if drill_down_advisor else f"Welcome {st.session_state['user_name']}!!")

if st.sidebar.button("Logout"):
    st.session_state['authenticated'] = False
    st.rerun()

# Set context for filtering
if not is_privileged:
    full_kpi = kpi_df[kpi_df['Email'] == st.session_state['user_email']].copy()
    active_email = st.session_state['user_email']
elif view_mode == "Specific Advisor View":
    full_kpi = kpi_df[kpi_df['Advisor Name'] == drill_down_advisor].copy()
    active_email = full_kpi['Email'].iloc[0] if not full_kpi.empty else ""
else:
    full_kpi = kpi_df.copy()

full_kpi['Date'] = pd.to_datetime(full_kpi['Date'], format="%b'%d'%y", errors='coerce')
full_kpi = full_kpi.dropna(subset=['Date']).sort_values('Date')

full_dsat = dsat_df.copy() if dsat_df is not None else pd.DataFrame()
if not full_dsat.empty:
    full_dsat['Date'] = pd.to_datetime(full_dsat['Date'], format="%d/%m/%Y", errors='coerce')
    full_dsat = full_dsat.dropna(subset=['Date'])
    if not is_privileged or view_mode == "Specific Advisor View":
        target_email = active_email if (is_privileged and view_mode == "Specific Advisor View") else st.session_state['user_email']
        full_dsat = full_dsat[full_dsat['Email'] == target_email]

freq = st.radio("Frequency:", ["Daily", "Weekly", "Monthly"], horizontal=True)

# Selection Filters
if freq == "Daily":
    sel = st.selectbox("Select Date:", sorted(full_kpi['Date'].unique(), reverse=True), format_func=lambda x: x.strftime('%d %b %Y'))
    f_kpi = full_kpi[full_kpi['Date'] == sel]
    f_dsat = full_dsat[full_dsat['Date'].dt.normalize() == sel] if not full_dsat.empty else pd.DataFrame()
elif freq == "Weekly":
    full_kpi['W_Start'] = full_kpi['Date'] - pd.to_timedelta((full_kpi['Date'].dt.dayofweek + 1) % 7, unit='d')
    full_kpi['Week_Range'] = full_kpi['W_Start'].dt.strftime('%d %b %Y') + " - " + (full_kpi['W_Start'] + pd.to_timedelta(6, unit='d')).dt.strftime('%d %b %Y')
    sel = st.selectbox("Select Week:", full_kpi.sort_values('W_Start', ascending=False)['Week_Range'].unique())
    f_kpi = full_kpi[full_kpi['Week_Range'] == sel]
    if not full_dsat.empty:
        full_dsat['W_Start'] = full_dsat['Date'] - pd.to_timedelta((full_dsat['Date'].dt.dayofweek + 1) % 7, unit='d')
        full_dsat['Week_Range'] = full_dsat['W_Start'].dt.strftime('%d %b %Y') + " - " + (full_dsat['W_Start'] + pd.to_timedelta(6, unit='d')).dt.strftime('%d %b %Y')
        f_dsat = full_dsat[full_dsat['Week_Range'] == sel]
else:
    full_kpi['Month_Label'] = full_kpi['Date'].dt.strftime('%B %Y')
    sel = st.selectbox("Select Month:", full_kpi.sort_values('Date', ascending=False)['Month_Label'].unique())
    f_kpi = full_kpi[full_kpi['Month_Label'] == sel]
    if not full_dsat.empty:
        full_dsat['Month_Label'] = full_dsat['Date'].dt.strftime('%B %Y')
        f_dsat = full_dsat[full_dsat['Month_Label'] == sel]

# Exclude 0 survey days from quality averages
avg_kpi = f_kpi[f_kpi['Total Survey'] > 0].copy()


# --- 6. ELABORATE PERFORMANCE NARRATIVE ---
st.divider()
st.subheader("📊 Performance Insight Summary")
avg_ia_mins = f_kpi['IA_Mins'].mean()
avg_score = f_kpi['Shift_Score'].mean()
avg_sent = avg_kpi['Sent Rate %'].mean() if not avg_kpi.empty else 0
avg_sat = avg_kpi['Satisfied Survey %'].mean() if not avg_kpi.empty else 0
total_surveys = f_kpi['Total Survey'].sum()
total_dsats = len(f_dsat)

# Extensive Narrative Logic
narrative = ""
if is_privileged and view_mode == "Team Overview":
    narrative += f"### Team Summary for {sel}\n"
    narrative += f"**Quality & Satisfaction Analysis:** The team currently maintains an average Satisfaction rate of **{avg_sat:.1f}%** across **{int(total_surveys)}** total surveys."
    
    if avg_sat >= 80:
        narrative += "This aligns with our high-performance benchmark, reflecting strong customer sentiment.\n"
    else:
        narrative += "This is currently below our 80% target, indicating a need for targeted quality reviews.\n"

    narrative += f"\n**Survey Engagement:** We recorded a Survey Sent Rate of **{avg_sent:.1f}%**. "
    if avg_sent < 80:
        narrative += "Attention is required here as low sent rates can skew data validity and hide potential customer pain points.\n"
    else:
        narrative += "Consistent survey distribution is ensuring we have a robust data set for analysis.\n"

    narrative += f"\n**Actionable Feedback (DSAT):** There are **{total_dsats}** DSAT records for this period. "
    if total_dsats > 0:
        narrative += "Immediate focus should be placed on the feedback provided in the DSAT Analysis section to mitigate recurring issues.\n"
    
    shout_out = avg_kpi[(avg_kpi['Sent Rate %'] >= 80) & (avg_kpi['Satisfied Survey %'] > 95)]['Advisor Name'].unique()
    if len(shout_out) > 0:
        narrative += f"\n**Success Champions:** Shout-out to **{', '.join(shout_out)}** for maintaining elite quality and engagement levels."
else:
    target_name = drill_down_advisor if drill_down_advisor else "Your"
    narrative += f"### Performance Deep-Dive: {target_name}\n"
    narrative += f"During **{sel}**, your Satisfaction score averaged **{avg_sat:.1f}%**. "
    
    if total_surveys == 0:
        narrative += "You have not received any surveys for this period. Focus on increasing customer engagement to trigger survey distribution.\n"
    else:
        narrative += f"This score is based on **{int(total_surveys)}** customer responses.\n"

    narrative += f"\n**Sent Rate Insights:** Your Survey Sent Rate is **{avg_sent:.1f}%**. "
    if avg_sent >= 80:
        narrative += "You are meeting the engagement target, ensuring your performance is accurately reflected in the data. \n"
    else:
        narrative += "Focus on sending surveys more consistently to hit the 80% benchmark. \n"

    if total_dsats > 0:
        narrative += f"\n**Feedback Alert:** You have **{total_dsats}** DSAT(s) to review. Please examine the 'DSAT Analysis' table below to identify specific areas for improvement.\n"
    else:
        narrative += "\n**Excellence Note:** You have zero DSATs for this period—excellent work on maintaining high quality standards!\n"

st.markdown(narrative)

# --- 7. PERFORMANCE SUMMARY ---
st.header("Performance summary")
def get_delta_color(val, target, is_ia=False):
    condition = val > target if is_ia else val >= target
    return "normal" if condition else "inverse"

m = st.columns(5)
m[0].metric("Avg Shift Score", f"{avg_score:.1f}%", delta="Goal: >80%", delta_color=get_delta_color(avg_score, 80))
m[1].metric("Avg IA Hours", format_minutes_to_hours(avg_ia_mins), delta="Goal: >6h", delta_color=get_delta_color(avg_ia_mins, 360, True))
m[2].metric("Avg Sent Rate %", f"{avg_sent:.1f}%", delta="Goal: >=80%", delta_color=get_delta_color(avg_sent, 80))
m[3].metric("Avg Satisfied Survey", f"{avg_sat:.1f}%", delta="Goal: >=80%", delta_color=get_delta_color(avg_sat, 80))
m[4].metric("Total Survey", int(f_kpi['Total Survey'].sum()))

v = st.columns(4)
v[0].metric("Total OB Calls", int(f_kpi['OB Calls'].sum()))
v[1].metric("Total Q/A Calls", int(f_kpi['Q/A Calls'].sum()))
v[2].metric("Total MOB", int(f_kpi['MOB'].sum()))
v[3].metric("Total Call Abandons", int(f_kpi['Call Abandons'].sum()))

# --- 8. PRIVILEGED LEADERBOARDS ---
if is_privileged and view_mode == "Team Overview":
    st.divider(); st.header("🏆 Leaderboards")
    ldb = avg_kpi.groupby('Advisor Name').agg({'Sent Rate %':'mean','Satisfied Survey %':'mean','Email':'first'}).reset_index()
    ldb_vol = f_kpi.groupby('Advisor Name').agg({'Q/A Calls':'sum','OB Calls':'sum','Email':'first'}).reset_index()
    if not f_dsat.empty:
        dsat_counts = f_dsat.groupby('Email').size().reset_index(name='Total DSAT')
        ldb_vol = ldb_vol.merge(dsat_counts, on='Email', how='left').fillna(0)
    if 'Total DSAT' not in ldb_vol.columns: ldb_vol['Total DSAT'] = 0
    
    col_l1, col_l2, col_l3 = st.columns(3)
    with col_l1:
        st.subheader("🏆 Success Champions")
        st.caption("Eligibility: Survey Sent Rate ≥ 80% and Satisfied Survey > 95% (Excludes 0-survey days)")
        sc = ldb[(ldb['Sent Rate %'] >= 80) & (ldb['Satisfied Survey %'] > 95)]
        st.dataframe(sc.sort_values('Satisfied Survey %', ascending=False)[['Advisor Name', 'Sent Rate %', 'Satisfied Survey %']], hide_index=True)
        st.subheader("Avg Satisfied Survey")
        st.dataframe(ldb.sort_values('Satisfied Survey %', ascending=False)[['Advisor Name', 'Satisfied Survey %']].round(2), hide_index=True)
    with col_l2:
        st.subheader("Total DSAT Received")
        st.dataframe(ldb_vol.sort_values('Total DSAT', ascending=False)[['Advisor Name', 'Total DSAT']], hide_index=True)
        st.subheader("Total QA Calls")
        st.dataframe(ldb_vol.sort_values('Q/A Calls', ascending=False)[['Advisor Name', 'Q/A Calls']], hide_index=True)
    with col_l3:
        st.subheader("Avg Survey Sent %")
        st.dataframe(ldb.sort_values('Sent Rate %', ascending=False)[['Advisor Name', 'Sent Rate %']].round(2), hide_index=True)
        st.subheader("Total OB Calls")
        st.dataframe(ldb_vol.sort_values('OB Calls', ascending=False)[['Advisor Name', 'OB Calls']], hide_index=True)

# --- 9. TRENDS ---
st.divider(); st.header("Performance Trends")
chart_df = f_kpi if (not is_privileged or view_mode == "Specific Advisor View") else f_kpi.groupby('Date').mean(numeric_only=True).reset_index()
t1, t2 = st.columns(2)
with t1:
    st.plotly_chart(px.line(chart_df, x='Date', y='Shift_Score', title="Shift Score Trend", markers=True), width='stretch')
    st.plotly_chart(px.line(avg_kpi.groupby('Date').mean(numeric_only=True).reset_index() if (is_privileged and view_mode == "Team Overview") else avg_kpi, 
                            x='Date', y='Satisfied Survey %', title="Satisfied Survey Trend (Excl. 0-survey days)", markers=True), width='stretch')
with t2:
    st.plotly_chart(px.line(chart_df, x='Date', y='IA_Mins', title="IA Minutes Trend", markers=True), width='stretch')
    st.plotly_chart(px.line(avg_kpi.groupby('Date').mean(numeric_only=True).reset_index() if (is_privileged and view_mode == "Team Overview") else avg_kpi, 
                            x='Date', y='Sent Rate %', title="Survey Sent Trend (Excl. 0-survey days)", markers=True), width='stretch')

# --- 10. DSAT & DETAILED REPORT ---
st.divider(); st.subheader(f"🚫 DSAT Analysis & Feedback ({len(f_dsat)})")
if not f_dsat.empty:
    display_cols = ['Date', 'Advisor Name', 'Chat_Link', 'Feedback'] if (is_privileged and view_mode == "Team Overview") else ['Date', 'Chat_Link', 'Feedback']
    st.dataframe(f_dsat[display_cols].sort_values('Date', ascending=False), column_config={"Chat_Link": st.column_config.LinkColumn("View Chat")}, hide_index=True, width='stretch')

st.divider(); st.header("Detailed Report")
st.dataframe(f_kpi.sort_values('Date', ascending=False), hide_index=True)
