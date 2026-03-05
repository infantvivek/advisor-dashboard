import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. DATA SOURCE LINKS ---
KPI_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?output=csv"

st.set_page_config(page_title="The Go Getters | KPI Portal", layout="wide")

# --- BRANDING & LOGO ---
# Displays GoHighLevel logo and Team Name at the top
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.image("https://images.g2crowd.com/uploads/product/image/social_landscape/social_landscape_47743d99435f375c329437149f6f79d0/gohighlevel.png", width=80)
with col_title:
    st.title("The Go Getters Performance Dashboard")
    st.markdown("### Advisor KPI Statistics")

@st.cache_data(ttl=30)
def load_kpi_data():
    try:
        df = pd.read_csv(KPI_URL)
        df.columns = df.columns.str.strip().str.replace('\ufeff', '')
        df['Date'] = pd.to_datetime(df['Date'], format="%b'%d'%y", errors='coerce')
        
        # Define columns for Average vs Sum
        num_cols = ['IA_Hours', 'Shift_Score', 'Sent_Rate', 'Satisfied_Survey', 
                    'OB_Calls', 'QA_Calls', 'Call_Abandons', 'MOB']
        
        for col in num_cols:
            if col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].str.replace('%', '').str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce')
        return df.dropna(subset=['Date'])
    except: return None

# --- UI LOGIC ---
user_email = st.sidebar.text_input("Login with Email").strip().lower()

if user_email:
    kpi_df = load_kpi_data()
    
    if kpi_df is not None:
        user_kpi = kpi_df[kpi_df['Email'].str.lower() == user_email].copy().sort_values('Date')

        if user_kpi.empty:
            st.warning("No KPI data found for this email.")
        else:
            advisor_name = user_kpi['Advisor Name'].iloc[0]
            st.sidebar.success(f"Advisor: {advisor_name}")
            
            freq = st.radio("Frequency View:", ["Daily", "Weekly", "Monthly"], horizontal=True)

            # --- STRICT FILTERING LOGIC ---
            if freq == "Daily":
                available_dates = sorted(user_kpi['Date'].unique(), reverse=True)
                selected_val = st.selectbox("Select Date:", available_dates, format_func=lambda x: x.strftime('%d %b %Y'))
                # Filter strictly for one day
                filtered_df = user_kpi[user_kpi['Date'] == selected_val]
                chart_df = filtered_df 

            elif freq == "Weekly":
                user_kpi['W_Start'] = user_kpi['Date'] - pd.to_timedelta(user_kpi['Date'].dt.dayofweek + 1 % 7, unit='d')
                user_kpi['W_End'] = user_kpi['W_Start'] + pd.to_timedelta(6, unit='d')
                user_kpi['Week_Range'] = (user_kpi['W_Start'].dt.strftime('%d %b %Y') + " - " + user_kpi['W_End'].dt.strftime('%d %b %Y'))
                
                week_options = user_kpi.sort_values('W_Start', ascending=False)['Week_Range'].unique()
                selected_val = st.selectbox("Select Week:", week_options)
                # Filter strictly for that week
                filtered_df = user_kpi[user_kpi['Week_Range'] == selected_val]
                chart_df = filtered_df.sort_values('Date')

            else: # Monthly
                user_kpi['Month_Label'] = user_kpi['Date'].dt.to_period('M').apply(lambda r: r.start_time)
                month_options = sorted(user_kpi['Month_Label'].unique(), reverse=True)
                selected_val = st.selectbox("Select Month:", month_options, format_func=lambda x: x.strftime('%B %Y'))
                # Filter strictly for that month
                filtered_df = user_kpi[user_kpi['Month_Label'] == selected_val]
                chart_df = filtered_df.sort_values('Date')

            # --- SUMMARY METRICS ---
            st.markdown("---")
            
            # Helper function for Nil values
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

            # --- FILTERED GRAPHS ---
            st.divider()
            st.subheader(f"Data Visuals for selected {freq} range")
            
            g_col1, g_col2 = st.columns(2)
            with g_col1:
                # Quality Trends (Filtered)
                fig_q = px.line(chart_df, x='Date', y=['Shift_Score', 'Sent_Rate', 'Satisfied_Survey'], 
                                markers=True, title="Quality Metrics (%)")
                st.plotly_chart(fig_q, width='stretch')
                
            with g_col2:
                # Volume Trends (Filtered)
                fig_v = px.bar(chart_df, x='Date', y=['OB_Calls', 'QA_Calls', 'Call_Abandons', 'MOB'], 
                               barmode='group', title="Volume Metrics (Count)")
                st.plotly_chart(fig_v, width='stretch')

            # --- FILTERED RAW DATA ---
            st.divider()
            st.subheader("📋 Selected Raw Data")
            st.dataframe(filtered_df.sort_values('Date', ascending=False), width='stretch')

else:
    st.info("Please enter your email in the sidebar to view 'The Go Getters' dashboard.")
