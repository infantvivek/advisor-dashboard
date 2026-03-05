import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. DATA SOURCE LINKS ---
KPI_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?output=csv"
CSAT_URL = "PASTE_YOUR_CSAT_SHEET_CSV_LINK_HERE" # Ensure this is updated

st.set_page_config(page_title="Advisor Performance Portal", layout="wide")

@st.cache_data(ttl=60)
def load_kpi_data():
    try:
        df = pd.read_csv(KPI_URL)
        df.columns = df.columns.str.strip().str.replace('\ufeff', '')
        # Specific date format Feb'28'26
        df['Date'] = pd.to_datetime(df['Date'], format="%b'%d'%y", errors='coerce')
        
        # Ensure all metrics are treated as numbers
        metrics = ['IA_Hours', 'Shift_Score', 'Sent_Rate', 'Satisfied_Survey', 'OB_Calls', 'QA_Calls']
        for col in metrics:
            if col in df.columns:
                # Remove % signs if they exist in the text, then convert to number
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
st.title("📈 Advisor KPI & CSAT Portal")

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
            st.header(f"Welcome, {advisor_name}")

            # --- FREQUENCY LOGIC ---
            freq = st.radio("Frequency View:", ["Daily", "Weekly", "Monthly"], horizontal=True)

            if freq == "Daily":
                # Last 30 entries as requested
                selected_data = user_kpi.tail(30)
                display_df = selected_data # For charts
                st.info("Top metrics reflect the average of the last 30 daily entries.")
                
            elif freq == "Weekly":
                # Week starts on Sunday
                user_kpi['Week'] = user_kpi['Date'].dt.to_period('W-SUN').apply(lambda r: r.start_time)
                available_weeks = sorted(user_kpi['Week'].unique(), reverse=True)
                selected_week = st.selectbox("Select Week:", available_weeks, format_func=lambda x: f"Week of {x.strftime('%d %b %Y')}")
                
                selected_data = user_kpi[user_kpi['Week'] == selected_week]
                # Chart data shows weekly averages for the whole history
                display_df = user_kpi.groupby('Week').mean(numeric_only=True).reset_index().rename(columns={'Week':'Date'})
                
            else: # Monthly
                user_kpi['Month'] = user_kpi['Date'].dt.to_period('M').apply(lambda r: r.start_time)
                available_months = sorted(user_kpi['Month'].unique(), reverse=True)
                selected_month = st.selectbox("Select Month:", available_months, format_func=lambda x: x.strftime('%B %Y'))
                
                selected_data = user_kpi[user_kpi['Month'] == selected_month]
                # Chart data shows monthly averages for the whole history
                display_df = user_kpi.groupby('Month').mean(numeric_only=True).reset_index().rename(columns={'Month':'Date'})

            # --- SUMMARY METRICS SECTION ---
            # Explicitly calculating the mean of the SELECTED data only
            avg_shift = selected_data['Shift_Score'].mean()
            avg_ia = selected_data['IA_Hours'].mean()
            avg_satisfied = selected_data['Satisfied_Survey'].mean()
            avg_sent = selected_data['Sent_Rate'].mean()

            st.markdown("---")
            st.subheader(f"Current Selection Summary ({freq})")
            m1, m2, m3, m4 = st.columns(4)
            
            # Formatted to 1 decimal place to ensure accuracy
            m1.metric("Avg Shift Score", f"{avg_shift:.1f}%")
            m2.metric("Avg IA Hours", f"{avg_ia:.2f}")
            m3.metric("Avg Satisfied Survey", f"{avg_satisfied:.1f}%")
            m4.metric("Avg Sent Rate", f"{avg_sent:.1f}%")

            # --- TRENDS ---
            st.subheader(f"Performance Trends ({freq})")
            t1, t2 = st.columns(2)
            with t1:
                st.plotly_chart(px.line(display_df, x='Date', y='Shift_Score', markers=True, title="Shift Score Trend"), use_container_width=True)
                st.plotly_chart(px.line(display_df, x='Date', y='Sent_Rate', markers=True, title="Sent Rate Trend"), use_container_width=True)
            with t2:
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
                    st.write("No survey data found for you yet.")
else:
    st.info("Please login with your email in the sidebar.")
