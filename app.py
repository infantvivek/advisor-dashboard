import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Your Google Sheet CSV Link
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?output=csv"

st.set_page_config(page_title="KPI Performance Dashboard", layout="wide")

@st.cache_data(ttl=60)
def load_data():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip()
        
        # --- DATE FORMAT FIX ---
        # This converts Feb'28'26 into a real date Python can understand
        df['Date'] = pd.to_datetime(df['Date'], format="%b'%d'%y", errors='coerce')
        
        # Fill empty numbers with 0 to prevent crashes
        df = df.fillna(0)
        return df
    except Exception as e:
        st.error(f"Could not read data: {e}")
        return None

# --- UI LOGIC ---
st.title("📈 Advisor Performance Portal")

# Sidebar Login
user_email = st.sidebar.text_input("Login with Email").strip().lower()

if user_email:
    data = load_data()
    
    if data is not None:
        # Check if Email column exists (Step 1 from above)
        if 'Email' not in data.columns:
            st.error("Please add the 'Email' column to your Google Sheet using VLOOKUP.")
        else:
            # Filter for the logged in advisor
            user_df = data[data['Email'].str.lower() == user_email].copy()

            if user_df.empty:
                st.warning("Email not found. Check if you added the email column to the KPI sheet.")
            else:
                advisor_name = user_df['Advisor Name'].iloc[0]
                st.header(f"Performance for {advisor_name}")

                # --- TOP STATS ---
                latest = user_df.sort_values('Date').iloc[-1]
                
                c1, c2, c3, c4 = st.columns(4)
                # Using your exact header names
                c1.metric("Shift Score", f"{latest['Shift_Score']}%")
                c2.metric("IA Hours", f"{latest['IA_Hours']}")
                c3.metric("OB Calls", int(latest['OB_Calls']))
                c4.metric("Satisfied Survey", f"{latest['Satisfied_Survey']}%")

                # --- VISUAL TRENDS ---
                st.subheader("Performance Over Time")
                
                # Filter View (Daily/Weekly/Monthly)
                view = st.segmented_control("View Type", ["Daily", "Weekly", "Monthly"], default="Daily")
                
                plot_df = user_df.sort_values('Date')
                if view == "Weekly":
                    plot_df = plot_df.resample('W', on='Date').mean(numeric_only=True).reset_index()
                elif view == "Monthly":
                    plot_df = plot_df.resample('M', on='Date').mean(numeric_only=True).reset_index()

                fig = px.line(plot_df, x='Date', y=['Shift_Score', 'Satisfied_Survey'], 
                              markers=True, title="Quality vs Adherence")
                st.plotly_chart(fig, use_container_width=True)

                # --- CALL HANDLING SECTION ---
                st.subheader("Call Handling Stats")
                col_a, col_b = st.columns(2)
                
                with col_a:
                    fig2 = px.bar(plot_df, x='Date', y=['OB_Calls', 'QA_Calls'], barmode='group')
                    st.plotly_chart(fig2, use_container_width=True)
                
                with col_b:
                    fig3 = px.area(plot_df, x='Date', y=['Avg_OB_Time', 'Avg_QA_Time'])
                    st.plotly_chart(fig3, use_container_width=True)

                # --- RAW DATA ---
                with st.expander("View your raw logs"):
                    st.dataframe(user_df.sort_values('Date', ascending=False))
else:
    st.info("Enter your work email in the sidebar to view your performance metrics.")
