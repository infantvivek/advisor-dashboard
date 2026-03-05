import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Your Google Sheet Link
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?output=csv"

st.set_page_config(page_title="Advisor Performance Dashboard", layout="wide")

# 2. Data Loading Function
@st.cache_data(ttl=300) # Refresh every 5 minutes
def load_data():
    try:
        # Load the CSV
        df = pd.read_csv(SHEET_URL)
        # Clean column names (removes any accidental spaces)
        df.columns = df.columns.str.strip()
        # Convert Date column to actual dates
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        return df
    except Exception as e:
        st.error(f"Error connecting to Google Sheets: {e}")
        return None

# --- UI LOGIC ---
st.title("📊 Subordinate KPI Portal")

# Sidebar Login
st.sidebar.header("Login")
user_email = st.sidebar.text_input("Enter your Email").strip().lower()

if user_email:
    all_data = load_data()
    
    if all_data is not None:
        # Check if Email column exists
        if 'Email' not in all_data.columns:
            st.error("Technical Error: The 'Email' column is missing from your Google Sheet.")
        else:
            # Filter data for the logged-in user
            user_data = all_data[all_data['Email'].str.lower() == user_email].copy()

            if user_data.empty:
                st.warning(f"Access Denied. No records found for: {user_email}")
            else:
                advisor_name = user_data['Advisor Name'].iloc[0]
                st.header(f"Welcome, {advisor_name}")

                # --- FILTERS ---
                view_type = st.radio("Select Performance View", ["Daily", "Weekly", "Monthly"], horizontal=True)
                
                # Logic to aggregate data based on view_type
                plot_df = user_data.sort_values('Date')
                if view_type == "Weekly":
                    plot_df = plot_df.resample('W', on='Date').mean(numeric_only=True).reset_index()
                elif view_type == "Monthly":
                    plot_df = plot_df.resample('M', on='Date').mean(numeric_only=True).reset_index()

                # --- KEY METRICS ROW ---
                st.markdown("### Most Recent Performance")
                m1, m2, m3, m4 = st.columns(4)
                
                # Get the last row of data
                latest = plot_df.iloc[-1]
                
                m1.metric("Shift Score", f"{latest['Shift_Score']}%")
                m2.metric("IA Hours", f"{latest['IA_Hours']:.2f}")
                m3.metric("Satisfied Survey", f"{latest['Satisfied_Survey']}%")
                m4.metric("OB Calls", int(latest['OB_Calls']))

                # --- CHARTS ---
                col_left, col_right = st.columns(2)

                with col_left:
                    st.subheader("Adherence & Quality Trends")
                    fig1 = px.line(plot_df, x='Date', y=['Shift_Score', 'Satisfied_Survey'], 
                                  markers=True, template="plotly_white")
                    st.plotly_chart(fig1, use_container_width=True)

                with col_right:
                    st.subheader("Call Volumes")
                    fig2 = px.bar(plot_df, x='Date', y=['OB_Calls', 'QA_Calls'], 
                                 barmode='group', template="plotly_white")
                    st.plotly_chart(fig2, use_container_width=True)

                # --- HANDLING TIME INSIGHTS ---
                st.markdown("---")
                st.subheader("Call Handling Insights")
                fig3 = px.area(plot_df, x='Date', y=['Avg_OB_Time', 'Avg_QA_Time'], 
                              title="Average Handling Time (OB vs QA)", 
                              line_shape='spline')
                st.plotly_chart(fig3, use_container_width=True)

                # --- RAW DATA TABLE ---
                with st.expander("Show Detailed Logs"):
                    st.write(user_data.sort_values('Date', ascending=False))

else:
    st.info("👈 Please enter your email address in the sidebar to access your personalized dashboard.")
