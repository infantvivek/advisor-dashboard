

# --- 1. DATA SOURCE LINKS ---
# Ensure these links point to the specific tabs in your Google Sheet (Published as CSV)
#TEAM_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=0&single=true&output=csv"
#KPI_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=1918948844&single=true&output=csv"
#DSAT_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=367459010&single=true&output=csv" 
import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. DATA SOURCE LINKS ---
TEAM_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=0&single=true&output=csv"
KPI_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=1918948844&single=true&output=csv"
DSAT_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=367459010&single=true&output=csv"  

st.set_page_config(page_title="The Go Getters | Performance Portal", layout="wide")

# --- 2. BRANDING & LOGO ---
def add_branding():
    col1, col2 = st.columns([1, 8])
    with col1:
        st.image("https://s3.amazonaws.com/cdn.freshdesk.com/data/helpdesk/attachments/production/48175265495/original/PTXBCP40UHx-8LCKsM1zqLX-pq8nndFHSw.png?1641235482", width=100)
    with col2:
        st.title("The Go Getters")
        st.subheader("Advisor Performance & DSAT Analysis Dashboard")

@st.cache_data(ttl=30)
def load_data(url):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip().str.replace('\ufeff', '')
        # Clean email column immediately if it exists
        if 'Email' in df.columns:
            df['Email'] = df['Email'].str.strip().str.lower()
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return None

# --- UI START ---
add_branding()

user_email = st.sidebar.text_input("Login with Email").strip().lower()

if user_email:
    team_df = load_data(TEAM_URL)
    kpi_df = load_data(KPI_URL)
    dsat_df = load_data(DSAT_URL)
    
    # 1. Verify user exists in Team Detail
    if team_df is not None and user_email in team_df['Email'].values:
        user_row = team_df[team_df['Email'] == user_email]
        advisor_name = user_row['Advisor Name'].iloc[0]
        st.sidebar.success(f"User: {advisor_name}")
        
        # 2. Process KPI Data
        if kpi_df is not None:
            # Filter for logged-in user
            user_kpi = kpi_df[kpi_df['Email'] == user_email].copy()
            user_kpi['Date'] = pd.to_datetime(user_kpi['Date'], format="%b'%d'%y", errors='coerce')
            user_kpi = user_kpi.dropna(subset=['Date']).sort_values('Date')

            if user_kpi.empty:
                st.warning("No KPI records found for your email address.")
            else:
                freq = st.radio("Select View Frequency:", ["Daily", "Weekly", "Monthly"], horizontal=True)

                # --- FILTERING LOGIC ---
                if freq == "Daily":
                    available_dates = sorted(user_kpi['Date'].unique(), reverse=True)
                    selected_val = st.selectbox("Select Date:", available_dates, format_func=lambda x: x.strftime('%d %b %Y'))
                    filtered_kpi = user_kpi[user_kpi['Date'] == selected_val]
                    chart_df = filtered_kpi
                elif freq == "Weekly":
                    user_kpi['W_Start'] = user_kpi['Date'] - pd.to_timedelta(user_kpi['Date'].dt.dayofweek + 1 % 7, unit='d')
                    user_kpi['Week_Range'] = user_kpi['W_Start'].dt.strftime('%d %b %Y') + " - " + (user_kpi['W_Start'] + pd.to_timedelta(6, unit='d')).dt.strftime('%d %b %Y')
                    selected_val = st.selectbox("Select Week:", sorted(user_kpi['Week_Range'].unique(), reverse=True))
                    filtered_kpi = user_kpi[user_kpi['Week_Range'] == selected_val]
                    chart_df = filtered_kpi.sort_values('Date')
                else: # Monthly
                    user_kpi['Month_Label'] = user_kpi['Date'].dt.to_period('M').apply(lambda r: r.start_time)
                    selected_val = st.selectbox("Select Month:", sorted(user_kpi['Month_Label'].unique(), reverse=True), format_func=lambda x: x.strftime('%B %Y'))
                    filtered_kpi = user_kpi[user_kpi['Month_Label'] == selected_val]
                    chart_df = filtered_kpi.sort_values('Date')

                # --- SUMMARY METRICS ---
                st.markdown("---")
                def format_val(val, suffix="%"):
                    return f"{val:.1f}{suffix}" if pd.notna(val) and val != 0 else "-"

                avg_sat = filtered_kpi['Satisfied_Survey'].mean()
                
                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("Avg Shift Score", format_val(filtered_kpi['Shift_Score'].mean()))
                m2.metric("Avg IA Hours", format_val(filtered_kpi['IA_Hours'].mean(), "h"))
                m3.metric("Avg Satisfied Survey", format_val(avg_sat))
                m4.metric("Avg DSAT %", format_val(100 - avg_sat if pd.notna(avg_sat) else None))
                m5.metric("Avg Sent Rate", format_val(filtered_kpi['Sent_Rate'].mean()))

                # --- TREND GRAPHS ---
                def create_chart(df, y_col, title, color):
                    if freq == "Daily":
                        return px.bar(df, x='Date', y=y_col, title=title, color_discrete_sequence=[color])
                    return px.line(df, x='Date', y=y_col, markers=True, title=title, color_discrete_sequence=[color])

                st.divider()
                c1, c2 = st.columns(2)
                with c1:
                    st.plotly_chart(create_chart(chart_df, 'Shift_Score', "Shift Score", "#3498db"), width='stretch')
                    st.plotly_chart(create_chart(chart_df, 'Satisfied_Survey', "Satisfied Survey (%)", "#2ecc71"), width='stretch')
                with c2:
                    st.plotly_chart(create_chart(chart_df, 'IA_Hours', "IA Hours", "#e67e22"), width='stretch')
                    st.plotly_chart(create_chart(chart_df, 'Sent_Rate', "Survey Sent (%)", "#9b59b6"), width='stretch')

                # --- DSAT SECTION ---
                st.divider()
                if dsat_df is not None:
                    # Sync DSAT dates
                    dsat_df['Date'] = pd.to_datetime(dsat_df['Date'], format="%d/%m/%Y", errors='coerce')
                    user_dsat = dsat_df[dsat_df['Email'] == user_email].copy()
                    
                    if freq == "Daily":
                        filtered_dsat = user_dsat[user_dsat['Date'].dt.normalize() == selected_val]
                    elif freq == "Weekly":
                        user_dsat['W_Start'] = user_dsat['Date'] - pd.to_timedelta(user_dsat['Date'].dt.dayofweek + 1 % 7, unit='d')
                        user_dsat['Week_Range'] = user_dsat['W_Start'].dt.strftime('%d %b %Y') + " - " + (user_dsat['W_Start'] + pd.to_timedelta(6, unit='d')).dt.strftime('%d %b %Y')
                        filtered_dsat = user_dsat[user_dsat['Week_Range'] == selected_val]
                    else:
                        user_dsat['Month_Label'] = user_dsat['Date'].dt.to_period('M').apply(lambda r: r.start_time)
                        filtered_dsat = user_dsat[user_dsat['Month_Label'] == selected_val]

                    st.subheader(f"🚫 DSAT Analysis & Feedback ({len(filtered_dsat)})")
                    st.dataframe(filtered_dsat[['Date', 'Chat_Link', 'Feedback']], column_config={"Chat_Link": st.column_config.LinkColumn("Chat")}, width='stretch', hide_index=True)

                # --- RAW DATA TABLE ---
                st.divider()
                st.subheader("📋 Detailed Report (Filtered)")
                st.dataframe(filtered_kpi.sort_values('Date', ascending=False), width='stretch')
        else:
            st.error("Could not load KPI data. Check the KPI_URL.")
    else:
        st.sidebar.error("Email not found in Team Detail sheet.")
else:
    st.info("👈 Please enter your email in the sidebar to access the portal.")
