

# --- 1. DATA SOURCE LINKS ---
# Ensure these links point to the specific tabs in your Google Sheet (Published as CSV)
#KPI_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=1918948844&single=true&output=csv"
#DSAT_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=367459010&single=true&output=csv" 
import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. DATA SOURCE LINKS ---
# Update these with your specific "Publish to Web" CSV links from Google Sheets
KPI_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=1918948844&single=true&output=csv"
DSAT_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=367459010&single=true&output=csv" 
import streamlit as st

st.set_page_config(page_title="The Go Getters | Performance Portal", layout="wide")

# --- 2. BRANDING & LOGO ---
def add_branding():
    col1, col2 = st.columns([1, 8])
    with col1:
        # HighLevel Logo
        st.image("https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/48175265495/original/PTXBCP40UHx-8LCKsM1zqLX-pq8nndFHSw.png?1641235482", width=100)
    with col2:
        st.title("The Go Getters")
        st.subheader("Advisor Performance & DSAT Analysis Dashboard")

@st.cache_data(ttl=30)
def load_kpi_data():
    try:
        df = pd.read_csv(KPI_URL)
        df.columns = df.columns.str.strip().str.replace('\ufeff', '')
        # Specific date format Feb'28'26
        df['Date'] = pd.to_datetime(df['Date'], format="%b'%d'%y", errors='coerce')
        
        num_cols = ['IA_Hours', 'Shift_Score', 'Sent_Rate', 'Satisfied_Survey', 
                    'OB_Calls', 'QA_Calls', 'Call_Abandons', 'MOB']
        
        for col in num_cols:
            if col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].str.replace('%', '').str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df.dropna(subset=['Date'])
    except: return None

@st.cache_data(ttl=30)
def load_dsat_data():
    try:
        df = pd.read_csv(DSAT_URL)
        df.columns = df.columns.str.strip().str.replace('\ufeff', '')
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df
    except: return None

# --- UI START ---
add_branding()

user_email = st.sidebar.text_input("Login with Email").strip().lower()

if user_email:
    kpi_df = load_kpi_data()
    dsat_df = load_dsat_data()
    
    if kpi_df is not None:
        user_kpi = kpi_df[kpi_df['Email'].str.lower() == user_email].copy().sort_values('Date')

        if user_kpi.empty:
            st.warning("No KPI data found for this email.")
        else:
            advisor_name = user_kpi['Advisor Name'].iloc[0]
            st.sidebar.success(f"User: {advisor_name}")
            
            freq = st.radio("Select View Frequency:", ["Daily", "Weekly", "Monthly"], horizontal=True)

            # Helper for metrics
            def format_val(val, suffix="%"):
                if pd.isna(val) or val == 0: return "-"
                return f"{val:.1f}{suffix}"

            # --- SELECTION & FILTERING LOGIC ---
            if freq == "Daily":
                available_dates = sorted(user_kpi['Date'].unique(), reverse=True)
                selected_val = st.selectbox("Select Date:", available_dates, format_func=lambda x: x.strftime('%d %b %Y'))
                filtered_kpi = user_kpi[user_kpi['Date'] == selected_val]
                chart_df = filtered_kpi
                
                if dsat_df is not None:
                    filtered_dsat = dsat_df[(dsat_df['Email'].str.lower() == user_email) & (dsat_df['Date'] == selected_val)]
                else: filtered_dsat = pd.DataFrame()

            elif freq == "Weekly":
                user_kpi['W_Start'] = user_kpi['Date'] - pd.to_timedelta(user_kpi['Date'].dt.dayofweek + 1 % 7, unit='d')
                user_kpi['W_End'] = user_kpi['W_Start'] + pd.to_timedelta(6, unit='d')
                user_kpi['Week_Range'] = (user_kpi['W_Start'].dt.strftime('%d %b %Y') + " - " + user_kpi['W_End'].dt.strftime('%d %b %Y'))
                selected_val = st.selectbox("Select Week:", user_kpi.sort_values('W_Start', ascending=False)['Week_Range'].unique())
                filtered_kpi = user_kpi[user_kpi['Week_Range'] == selected_val]
                chart_df = filtered_kpi.sort_values('Date')
                
                if dsat_df is not None:
                    dsat_df['W_Start'] = dsat_df['Date'] - pd.to_timedelta(dsat_df['Date'].dt.dayofweek + 1 % 7, unit='d')
                    dsat_df['W_End'] = dsat_df['W_Start'] + pd.to_timedelta(6, unit='d')
                    dsat_df['Week_Range'] = (dsat_df['W_Start'].dt.strftime('%d %b %Y') + " - " + dsat_df['W_End'].dt.strftime('%d %b %Y'))
                    filtered_dsat = dsat_df[(dsat_df['Email'].str.lower() == user_email) & (dsat_df['Week_Range'] == selected_val)]
                else: filtered_dsat = pd.DataFrame()

            else: # Monthly
                user_kpi['Month_Label'] = user_kpi['Date'].dt.to_period('M').apply(lambda r: r.start_time)
                selected_val = st.selectbox("Select Month:", sorted(user_kpi['Month_Label'].unique(), reverse=True), format_func=lambda x: x.strftime('%B %Y'))
                filtered_kpi = user_kpi[user_kpi['Month_Label'] == selected_val]
                chart_df = filtered_kpi.sort_values('Date')
                
                if dsat_df is not None:
                    dsat_df['Month_Label'] = dsat_df['Date'].dt.to_period('M').apply(lambda r: r.start_time)
                    filtered_dsat = dsat_df[(dsat_df['Email'].str.lower() == user_email) & (dsat_df['Month_Label'] == selected_val)]
                else: filtered_dsat = pd.DataFrame()

            # --- PERFORMANCE SUMMARY ---
            st.markdown("---")
            st.subheader("Performance Summary")
            
            avg_satisfied = filtered_kpi['Satisfied_Survey'].mean()
            avg_dsat_calc = 100 - avg_satisfied if not pd.isna(avg_satisfied) else None

            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Avg Shift Score", format_val(filtered_kpi['Shift_Score'].mean()))
            m2.metric("Avg IA Hours", format_val(filtered_kpi['IA_Hours'].mean(), "h"))
            m3.metric("Avg Satisfied Survey", format_val(avg_satisfied))
            m4.metric("Avg DSAT %", format_val(avg_dsat_calc))
            m5.metric("Avg Sent Rate", format_val(filtered_kpi['Sent_Rate'].mean()))

            v1, v2, v3, v4 = st.columns(4)
            v1.metric("Total OB Calls", int(filtered_kpi['OB_Calls'].sum()))
            v2.metric("Total QA Calls", int(filtered_kpi['QA_Calls'].sum()))
            v3.metric("Total Call Abandons", int(filtered_kpi['Call_Abandons'].sum()))
            v4.metric("Total MOB", int(filtered_kpi['MOB'].sum()))

            # --- DYNAMIC INDIVIDUAL TREND GRAPHS ---
            st.divider()
            st.subheader(f"Trends: {selected_val if freq != 'Daily' else selected_val.strftime('%d %b %Y')}")

            # Function to create charts based on frequency
            def create_chart(df, y_col, title, color):
                if freq == "Daily":
                    fig = px.bar(df, x='Date', y=y_col, title=title, color_discrete_sequence=[color])
                else:
                    fig = px.line(df, x='Date', y=y_col, markers=True, title=title, color_discrete_sequence=[color])
                return fig

            # Layout in a 2x2 Grid for Quality/Adherence
            row1_col1, row1_col2 = st.columns(2)
            with row1_col1:
                st.plotly_chart(create_chart(chart_df, 'Shift_Score', "Shift Score Trend", "#3498db"), width='stretch')
            with row1_col2:
                st.plotly_chart(create_chart(chart_df, 'IA_Hours', "IA Hours Trend", "#e67e22"), width='stretch')

            row2_col1, row2_col2 = st.columns(2)
            with row2_col1:
                st.plotly_chart(create_chart(chart_df, 'Satisfied_Survey', "Satisfied Survey (%) Trend", "#2ecc71"), width='stretch')
            with row2_col2:
                st.plotly_chart(create_chart(chart_df, 'Sent_Rate', "Survey Sent (%) Trend", "#9b59b6"), width='stretch')

            # Volume Graphs (Always Bar charts)
            st.markdown("### Volume Breakdown")
            v_col1, v_col2 = st.columns(2)
            with v_col1:
                st.plotly_chart(px.bar(chart_df, x='Date', y=['OB_Calls', 'QA_Calls'], barmode='group', title="OB vs QA Calls"), width='stretch')
            with v_col2:
                st.plotly_chart(px.bar(chart_df, x='Date', y=['Call_Abandons', 'MOB'], barmode='group', title="Abandons & MOB"), width='stretch')

            # --- DSAT ANALYSIS SECTION ---
            st.divider()
            dsat_count = len(filtered_dsat)
            st.subheader(f"🚫 DSAT Analysis & Feedback ({dsat_count})")
            
            if not filtered_dsat.empty:
                st.dataframe(
                    filtered_dsat[['Date', 'Chat_Link', 'Feedback']].sort_values('Date', ascending=False),
                    column_config={"Chat_Link": st.column_config.LinkColumn("View Chat")},
                    width='stretch', hide_index=True
                )
            else:
                st.info(f"No DSAT records found for this period.")

            # --- RAW DATA ---
            st.divider()
            st.subheader("📋 Detailed Records")
            st.dataframe(filtered_kpi.sort_values('Date', ascending=False), width='stretch')

else:
    st.info("👈 Please enter your email in the sidebar to access the portal.")
