import streamlit as st
import pandas as pd
import plotly.express as px
from io import BytesIO

# --- 1. DATA SOURCE LINKS ---
KPI_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?output=csv"
CSAT_URL = "PASTE_YOUR_CSAT_SHEET_CSV_LINK_HERE" 

st.set_page_config(page_title="Advisor Performance Portal", layout="wide")

@st.cache_data(ttl=60)
def load_kpi_data():
    try:
        df = pd.read_csv(KPI_URL)
        df.columns = df.columns.str.strip().str.replace('\ufeff', '')
        df['Date'] = pd.to_datetime(df['Date'], format="%b'%d'%y", errors='coerce')
        metrics = ['IA_Hours', 'Shift_Score', 'Sent_Rate', 'Satisfied_Survey', 'OB_Calls', 'QA_Calls']
        for col in metrics:
            if col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].str.replace('%', '')
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df.dropna(subset=['Date'])
    except: return None

@st.cache_data(ttl=60)
def load_csat_data():
    try:
        df = pd.read_csv(CSAT_URL)
        df.columns = df.columns.str.strip().str.replace('\ufeff', '')
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df
    except: return None

# --- UI START ---
st.title("📈 Advisor Performance Portal")

user_email = st.sidebar.text_input("Login with Email").strip().lower()

if user_email:
    kpi_df = load_kpi_data()
    csat_df = load_csat_data()
    
    if kpi_df is not None:
        user_kpi = kpi_df[kpi_df['Email'].str.lower() == user_email].copy().sort_values('Date')

        if user_kpi.empty:
            st.warning("No KPI data found for this email.")
        else:
            advisor_name = user_kpi['Advisor Name'].iloc[0]
            
            # --- HEADER SECTION WITH EXPORT ---
            head_col1, head_col2 = st.columns([3, 1])
            with head_col1:
                st.header(f"Welcome, {advisor_name}")
            
            freq = st.radio("Frequency View:", ["Daily", "Weekly", "Monthly"], horizontal=True)

            # Selection Logic
            if freq == "Daily":
                selected_data = user_kpi.tail(30)
                display_df = selected_data
                report_name = f"{advisor_name}_Last_30_Days.csv"
            elif freq == "Weekly":
                user_kpi['Week_Start'] = user_kpi['Date'] - pd.to_timedelta(user_kpi['Date'].dt.dayofweek + 1 % 7, unit='d')
                user_kpi['Week_End'] = user_kpi['Week_Start'] + pd.to_timedelta(6, unit='d')
                user_kpi['Week_Range'] = (user_kpi['Week_Start'].dt.strftime('%d %b %Y') + " - " + user_kpi['Week_End'].dt.strftime('%d %b %Y'))
                week_options = user_kpi.sort_values('Week_Start', ascending=False)['Week_Range'].unique()
                selected_range = st.selectbox("Select Week:", week_options)
                selected_data = user_kpi[user_kpi['Week_Range'] == selected_range]
                report_name = f"{advisor_name}_Weekly_Report_{selected_range}.csv"
                display_df = user_kpi.groupby('Week_Range').mean(numeric_only=True).reset_index()
                display_df['Sort_Date'] = pd.to_datetime(display_df['Week_Range'].str.split(' - ').str[0])
                display_df = display_df.sort_values('Sort_Date').rename(columns={'Sort_Date': 'Date'})
            else:
                user_kpi['Month_Val'] = user_kpi['Date'].dt.to_period('M').apply(lambda r: r.start_time)
                month_options = sorted(user_kpi['Month_Val'].unique(), reverse=True)
                selected_month = st.selectbox("Select Month:", month_options, format_func=lambda x: x.strftime('%B %Y'))
                selected_data = user_kpi[user_kpi['Month_Val'] == selected_month]
                report_name = f"{advisor_name}_Monthly_Report_{selected_month.strftime('%b_%Y')}.csv"
                display_df = user_kpi.groupby('Month_Val').mean(numeric_only=True).reset_index().rename(columns={'Month_Val':'Date'})

            # --- DOWNLOAD BUTTON ---
            with head_col2:
                csv = selected_data.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Report (CSV)",
                    data=csv,
                    file_name=report_name,
                    mime='text/csv',
                    help="Click to download the currently selected data as an Excel-ready CSV file."
                )

            # --- SUMMARY METRICS ---
            avg_shift = selected_data['Shift_Score'].mean()
            avg_ia = selected_data['IA_Hours'].mean()
            avg_satisfied = selected_data['Satisfied_Survey'].mean()
            avg_sent = selected_data['Sent_Rate'].mean()

            st.markdown("---")
            st.subheader(f"Current Selection Summary ({freq})")
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Avg Shift Score", f"{avg_shift:.1f}%")
            m2.metric("Avg IA Hours", f"{avg_ia:.2f}")
            m3.metric("Avg Satisfied Survey", f"{avg_satisfied:.1f}%")
            m4.metric("Avg Sent Rate", f"{avg_sent:.1f}%")

            # --- TRENDS ---
            st.subheader(f"Performance Trends ({freq})")
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                st.plotly_chart(px.line(display_df, x='Date', y='Shift_Score', markers=True, title="Shift Score Trend"), use_container_width=True)
                st.plotly_chart(px.line(display_df, x='Date', y='Sent_Rate', markers=True, title="Sent Rate Trend"), use_container_width=True)
            with t_col2:
                st.plotly_chart(px.line(display_df, x='Date', y='Satisfied_Survey', markers=True, title="Satisfied Survey Trend"), use_container_width=True)
                st.plotly_chart(px.line(display_df, x='Date', y='IA_Hours', markers=True, title="IA Hours Trend"), use_container_width=True)

            # --- CSAT DATA TABLE ---
            st.divider()
            st.subheader("💬 Recent CSAT/DSAT Feedback")
            if csat_df is not None:
                user_csat = csat_df[csat_df['Advisor Name'] == advisor_name].copy()
                if not user_csat.empty:
                    st.dataframe(user_csat.sort_values('Date', ascending=False), 
                                 column_config={"Chat_Link": st.column_config.LinkColumn("Link to Chat")},
                                 use_container_width=True)
                else:
                    st.write("No survey data found.")
else:
    st.info("Please login with your email in the sidebar.")
