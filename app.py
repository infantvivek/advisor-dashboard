import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. DATA SOURCE LINKS ---
KPI_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=0&single=true&output=csv"
CSAT_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=0&single=true&output=csv" 

st.set_page_config(page_title="The Go Getters | KPI Portal", layout="wide")

# --- 2. BRANDING & LOGO ---
def add_branding():
    col1, col2 = st.columns([1, 8])
    with col1:
        # HighLevel Logo
        st.image("https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/48175265495/original/PTXBCP40UHx-8LCKsM1zqLX-pq8nndFHSw.png?1641235482", width=100)
    with col2:
        st.title("The Go Getters")
        st.subheader("Advisor Performance Dashboard")

@st.cache_data(ttl=30)
def load_kpi_data():
    try:
        df = pd.read_csv(KPI_URL)
        df.columns = df.columns.str.strip().str.replace('\ufeff', '')
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

# --- UI START ---
add_branding()

user_email = st.sidebar.text_input("Login with Email").strip().lower()

if user_email:
    kpi_df = load_kpi_data()
    
    if kpi_df is not None:
        user_kpi = kpi_df[kpi_df['Email'].str.lower() == user_email].copy().sort_values('Date')

        if user_kpi.empty:
            st.warning("No KPI data found for this email.")
        else:
            advisor_name = user_kpi['Advisor Name'].iloc[0]
            st.sidebar.success(f"User: {advisor_name}")
            
            freq = st.radio("Select View Frequency:", ["Daily", "Weekly", "Monthly"], horizontal=True)

            # --- FILTERING LOGIC ---
            if freq == "Daily":
                available_dates = sorted(user_kpi['Date'].unique(), reverse=True)
                selected_val = st.selectbox("Select Date:", available_dates, format_func=lambda x: x.strftime('%d %b %Y'))
                # Filter strictly for that day
                filtered_df = user_kpi[user_kpi['Date'] == selected_val]
                # In Daily view, we show the chart for just that single selection as requested
                chart_df = filtered_df 

            elif freq == "Weekly":
                user_kpi['W_Start'] = user_kpi['Date'] - pd.to_timedelta(user_kpi['Date'].dt.dayofweek + 1 % 7, unit='d')
                user_kpi['W_End'] = user_kpi['W_Start'] + pd.to_timedelta(6, unit='d')
                user_kpi['Week_Range'] = (user_kpi['W_Start'].dt.strftime('%d %b %Y') + " - " + user_kpi['W_End'].dt.strftime('%d %b %Y'))
                
                week_options = user_kpi.sort_values('W_Start', ascending=False)['Week_Range'].unique()
                selected_val = st.selectbox("Select Week:", week_options)
                filtered_df = user_kpi[user_kpi['Week_Range'] == selected_val]
                chart_df = filtered_df.sort_values('Date')

            else: # Monthly
                user_kpi['Month_Label'] = user_kpi['Date'].dt.to_period('M').apply(lambda r: r.start_time)
                month_options = sorted(user_kpi['Month_Label'].unique(), reverse=True)
                selected_val = st.selectbox("Select Month:", month_options, format_func=lambda x: x.strftime('%B %Y'))
                filtered_df = user_kpi[user_kpi['Month_Label'] == selected_val]
                chart_df = filtered_df.sort_values('Date')

            # --- SUMMARY METRICS ---
            st.markdown("---")
            
            def format_val(val, suffix="%"):
                if pd.isna(val) or val == 0:
                    return "-"
                return f"{val:.1f}{suffix}"

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Avg Shift Score", format_val(filtered_df['Shift_Score'].mean()))
            m2.metric("Avg IA Hours", format_val(filtered_df['IA_Hours'].mean(), "h"))
            m3.metric("Avg Satisfied Survey", format_val(filtered_df['Satisfied_Survey'].mean()))
            m4.metric("Avg Sent Rate", format_val(filtered_df['Sent_Rate'].mean()))

            v1, v2, v3, v4 = st.columns(4)
            v1.metric("Total OB Calls", int(filtered_df['OB_Calls'].sum()))
            v2.metric("Total QA Calls", int(filtered_df['QA_Calls'].sum()))
            v3.metric("Total Call Abandons", int(filtered_df['Call_Abandons'].sum()))
            v4.metric("Total MOB", int(filtered_df['MOB'].sum()))

            # --- DYNAMIC GRAPHS ---
            st.divider()
            st.subheader(f"Visual Trends: {selected_val if freq != 'Daily' else selected_val.strftime('%d %b %Y')}")
            
            # Logic: If Daily is selected, use Bar charts for EVERYTHING.
            # If Weekly/Monthly, use Line charts for Quality and Bar for Volume.
            
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                if freq == "Daily":
                    fig_q1 = px.bar(chart_df, x='Date', y=['Shift_Score', 'Sent_Rate'], barmode='group', title="Quality Performance (Daily)")
                else:
                    fig_q1 = px.line(chart_df, x='Date', y=['Shift_Score', 'Sent_Rate'], markers=True, title="Quality Performance Trend")
                st.plotly_chart(fig_q1, width='stretch')

            with t_col2:
                if freq == "Daily":
                    fig_q2 = px.bar(chart_df, x='Date', y=['Satisfied_Survey', 'IA_Hours'], barmode='group', title="Survey & Adherence (Daily)")
                else:
                    fig_q2 = px.line(chart_df, x='Date', y=['Satisfied_Survey', 'IA_Hours'], markers=True, title="Survey & Adherence Trend")
                st.plotly_chart(fig_q2, width='stretch')

            v_col1, v_col2 = st.columns(2)
            # Volume graphs are bar charts in all views
            with v_col1:
                fig_v1 = px.bar(chart_df, x='Date', y=['OB_Calls', 'QA_Calls'], barmode='group', title="Call Volume Breakdown")
                st.plotly_chart(fig_v1, width='stretch')
            with v_col2:
                fig_v2 = px.bar(chart_df, x='Date', y=['Call_Abandons', 'MOB'], barmode='group', title="Abandons & MOB Breakdown")
                st.plotly_chart(fig_v2, width='stretch')

            # --- RAW DATA ---
            st.divider()
            st.subheader("📋 Detailed Records (Filtered)")
            st.dataframe(filtered_df.sort_values('Date', ascending=False), width='stretch')

else:
    st.info("👈 Please enter your email in the sidebar to access the dashboard.")
    
