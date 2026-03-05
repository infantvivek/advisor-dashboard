import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Your Google Sheet Link (KPI Data Tab)
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?output=csv"

st.set_page_config(page_title="KPI Performance Portal", layout="wide")

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip().str.replace('\ufeff', '')
        
        # Parse the custom date format: Feb'28'26
        df['Date'] = pd.to_datetime(df['Date'], format="%b'%d'%y", errors='coerce')
        
        # Clean numeric data
        metrics = ['IA_Hours', 'Shift_Score', 'Sent_Rate', 'Satisfied_Survey', 'OB_Calls', 'QA_Calls']
        for col in metrics:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df.dropna(subset=['Date'])
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# --- UI START ---
st.title("📈 Advisor Performance Portal")

user_email = st.sidebar.text_input("Login with Email").strip().lower()

if user_email:
    df = load_data()
    
    if df is not None:
        # Filter for the logged-in advisor
        user_df = df[df['Email'].str.lower() == user_email].copy().sort_values('Date')

        if user_df.empty:
            st.warning(f"No data found for {user_email}. Check your Sheet for this email.")
        else:
            advisor_name = user_df['Advisor Name'].iloc[0]
            st.header(f"Performance for {advisor_name}")

            # --- FREQUENCY SELECTOR ---
            st.subheader("Select View Frequency")
            freq = st.radio("Frequency:", ["Daily", "Weekly", "Monthly"], horizontal=True)

            # --- LOGIC FOR DIFFERENT FREQUENCIES ---
            if freq == "Daily":
                # Requirements: Last 30 entries
                display_df = user_df.tail(30)
                selected_data = display_df # Metrics reflect last 30 entries
                st.info("Showing the last 30 available daily entries.")

            elif freq == "Weekly":
                # Requirement: Option to select week (Starting Sunday)
                user_df['Week'] = user_df['Date'].dt.to_period('W-SUN').apply(lambda r: r.start_time)
                available_weeks = sorted(user_df['Week'].unique(), reverse=True)
                
                selected_week = st.selectbox("Select Week (Week Starts Sunday):", available_weeks, 
                                            format_func=lambda x: f"Week of {x.strftime('%d %b %Y')}")
                
                selected_data = user_df[user_df['Week'] == selected_week]
                # Trend data aggregates by week
                display_df = user_df.groupby('Week').mean(numeric_only=True).reset_index().rename(columns={'Week': 'Date'})

            elif freq == "Monthly":
                # Requirement: Option to select month
                user_df['Month'] = user_df['Date'].dt.to_period('M').apply(lambda r: r.start_time)
                available_months = sorted(user_df['Month'].unique(), reverse=True)
                
                selected_month = st.selectbox("Select Month:", available_months, 
                                             format_func=lambda x: x.strftime('%B %Y'))
                
                selected_data = user_df[user_df['Month'] == selected_month]
                # Trend data aggregates by month
                display_df = user_df.groupby('Month').mean(numeric_only=True).reset_index().rename(columns={'Month': 'Date'})

            # --- SUMMARY METRICS ---
            st.markdown("---")
            st.subheader(f"Summary: {freq} Selection")
            m1, m2, m3, m4 = st.columns(4)
            
            # Calculate averages for the selected period
            avg_stats = selected_data.mean(numeric_only=True)
            
            m1.metric("Shift Score", f"{avg_stats.get('Shift_Score', 0):.1f}%")
            m2.metric("IA Hours", f"{avg_stats.get('IA_Hours', 0):.2f}")
            m3.metric("Satisfied Survey", f"{avg_stats.get('Satisfied_Survey', 0):.1f}%")
            m4.metric("Sent Rate", f"{avg_stats.get('Sent_Rate', 0):.1f}%")

            # --- PERFORMANCE TRENDS ---
            st.markdown("---")
            st.subheader(f"Individual {freq} Performance Trends")
            
            # Helper to create consistent charts
            def make_trend(data, y_col, title, color):
                fig = px.line(data, x='Date', y=y_col, markers=True, title=title)
                fig.update_traces(line_color=color)
                fig.update_layout(xaxis_title="Date", yaxis_title=y_col)
                return fig

            row1_col1, row1_col2 = st.columns(2)
            with row1_col1:
                st.plotly_chart(make_trend(display_df, 'Shift_Score', "Shift Score Trend", "#e74c3c"), use_container_width=True)
            with row1_col2:
                st.plotly_chart(make_trend(display_df, 'Satisfied_Survey', "Satisfied Survey % Trend", "#3498db"), use_container_width=True)

            row2_col1, row2_col2 = st.columns(2)
            with row2_col1:
                st.plotly_chart(make_trend(display_df, 'Sent_Rate', "Sent Rate % Trend", "#2ecc71"), use_container_width=True)
            with row2_col2:
                st.plotly_chart(make_trend(display_df, 'IA_Hours', "IA Hours Trend", "#f39c12"), use_container_width=True)

            # --- RAW LOGS ---
            with st.expander("View Detailed Logs for this Selection"):
                st.dataframe(selected_data.sort_values('Date', ascending=False))

else:
    st.info("👈 Enter your advisor email in the sidebar to begin.")
