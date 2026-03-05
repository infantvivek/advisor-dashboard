import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. SETTINGS ---
# Ensure this link is for the "KPI data" tab specifically
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=1918948844&single=true&output=csv"

st.set_page_config(page_title="Advisor Performance Dashboard", layout="wide")

@st.cache_data(ttl=60)
def load_data():
    try:
        # Load data and clean column names from invisible characters/spaces
        df = pd.read_csv(SHEET_URL)
        df.columns = df.columns.str.strip().str.replace('﻿', '') # Removes BOM characters
        
        # Convert the specific Feb'28'26 format
        df['Date'] = pd.to_datetime(df['Date'], format="%b'%d'%y", errors='coerce')
        
        # Ensure numeric columns are clean
        metrics = ['IA_Hours', 'Shift_Score', 'Sent_Rate', 'Satisfied_Survey', 'OB_Calls', 'QA_Calls']
        for col in metrics:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        
        return df
    except Exception as e:
        st.error(f"Error loading sheet: {e}")
        return None

# --- 2. USER INTERFACE ---
st.title("📊 Advisor Performance Portal")

user_email = st.sidebar.text_input("Login with Email").strip().lower()

if user_email:
    df = load_data()
    
    if df is not None:
        # Filter for the specific advisor
        user_df = df[df['Email'].str.lower() == user_email].copy()

        if user_df.empty:
            st.warning(f"No records found for {user_email}. Check your Sheet's Email column.")
        else:
            advisor_name = user_df['Advisor Name'].iloc[0]
            st.header(f"Performance Summary: {advisor_name}")

            # --- FREQUENCY SELECTOR ---
            st.subheader("Filter Stats")
            freq = st.radio("Select Frequency", ["Daily", "Weekly", "Monthly"], horizontal=True)

            # Process data based on frequency
            plot_df = user_df.sort_values('Date')
            if freq == "Weekly":
                plot_df = plot_df.resample('W', on='Date').mean(numeric_only=True).reset_index()
            elif freq == "Monthly":
                plot_df = plot_df.resample('M', on='Date').mean(numeric_only=True).reset_index()

            # --- TOP LEVEL METRICS (Latest Available) ---
            latest = plot_df.iloc[-1]
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Shift Score", f"{latest['Shift_Score']:.1f}%")
            m2.metric("IA Hours", f"{latest['IA_Hours']:.1f}")
            m3.metric("Satisfied Survey", f"{latest['Satisfied_Survey']:.1f}%")
            m4.metric("Sent Rate", f"{latest['Sent_Rate']:.1f}%")

            st.divider()

            # --- INDIVIDUAL PERFORMANCE TRENDS ---
            st.subheader(f"{freq} Performance Trends")
            
            # Row 1: Quality Metrics
            col1, col2 = st.columns(2)
            with col1:
                fig_csat = px.line(plot_df, x='Date', y='Satisfied_Survey', markers=True, 
                                   title="Satisfied Survey % Trend", color_discrete_sequence=['#2E86C1'])
                st.plotly_chart(fig_csat, use_container_width=True)
            with col2:
                fig_sent = px.line(plot_df, x='Date', y='Sent_Rate', markers=True, 
                                   title="Sent Rate % Trend", color_discrete_sequence=['#239B56'])
                st.plotly_chart(fig_sent, use_container_width=True)

            # Row 2: Adherence Metrics
            col3, col4 = st.columns(2)
            with col3:
                fig_ia = px.area(plot_df, x='Date', y='IA_Hours', 
                                 title="IA Hours Trend", color_discrete_sequence=['#F39C12'])
                st.plotly_chart(fig_ia, use_container_width=True)
            with col4:
                fig_shift = px.line(plot_df, x='Date', y='Shift_Score', markers=True, 
                                    title="Shift Score Trend", color_discrete_sequence=['#E74C3C'])
                st.plotly_chart(fig_shift, use_container_width=True)

            # --- LOGS ---
            with st.expander("View Detailed Raw Logs"):
                st.dataframe(user_df.sort_values('Date', ascending=False))

else:
    st.info("👈 Please enter your email in the sidebar to view your metrics.")
