import streamlit as st
import pandas as pd
import plotly.express as px

# 1. PASTE YOUR NEW KPI-SPECIFIC LINK HERE
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?output=csv"

st.set_page_config(page_title="Advisor Dashboard", layout="wide")

@st.cache_data(ttl=10) # Short cache for testing
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # DEBUG: Check if Date exists. If not, show what we found.
        if 'Date' not in df.columns:
            st.error(f"Missing 'Date' column! I found these columns instead: {list(df.columns)}")
            st.info("Check: Did you publish the 'KPI data' tab or the 'Team detail' tab?")
            return None
            
        # Convert Date format Feb'28'26
        df['Date'] = pd.to_datetime(df['Date'], format="%b'%d'%y", errors='coerce')
        
        # Convert numeric columns safely
        numeric_cols = ['IA_Hours', 'Shift_Score', 'OB_Calls', 'QA_Calls', 'Satisfied_Survey']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
                
        return df
    except Exception as e:
        st.error(f"Technical Error: {e}")
        return None

# --- UI ---
st.title("📈 Advisor Performance Dashboard")

user_email = st.sidebar.text_input("Login with Email").strip().lower()

if user_email:
    df = load_data()
    
    if df is not None:
        # Check for Email column (created via VLOOKUP in your sheet)
        if 'Email' not in df.columns:
            st.error("Email column not found. Please add the Email column to your KPI data sheet.")
        else:
            user_df = df[df['Email'].str.lower() == user_email].copy()

            if user_df.empty:
                st.warning(f"No records found for {user_email}. Double check the Email column in your sheet.")
            else:
                advisor_name = user_df['Advisor Name'].iloc[0]
                st.header(f"Performance for {advisor_name}")

                # --- METRICS ---
                latest = user_df.sort_values('Date').iloc[-1]
                m1, m2, m3, m4 = st.columns(4)
                
                m1.metric("Shift Score", f"{latest['Shift_Score']}%")
                m2.metric("IA Hours", f"{latest['IA_Hours']}")
                m3.metric("OB Calls", int(latest['OB_Calls']))
                m4.metric("Satisfied Survey", f"{latest['Satisfied_Survey']}%")

                # --- TREND CHART ---
                st.subheader("Performance Trends")
                fig = px.line(user_df.sort_values('Date'), x='Date', 
                              y=['Shift_Score', 'Satisfied_Survey'], markers=True)
                st.plotly_chart(fig, use_container_width=True)
                
                # --- DATA TABLE ---
                with st.expander("View Logs"):
                    st.dataframe(user_df.sort_values('Date', ascending=False))
else:
    st.info("Please enter your email in the sidebar to view your dashboard.")
