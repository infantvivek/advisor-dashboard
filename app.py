import streamlit as st
import pandas as pd
import plotly.express as px

# --- 1. DATA SOURCE LINKS ---
KPI_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?output=csv"
CSAT_URL = "PASTE_YOUR_CSAT_SHEET_CSV_LINK_HERE" 

st.set_page_config(page_title="Advisor Performance Portal", layout="wide")

@st.cache_data(ttl=30)
def load_kpi_data():
    try:
        df = pd.read_csv(KPI_URL)
        df.columns = df.columns.str.strip().str.replace('\ufeff', '')
        df['Date'] = pd.to_datetime(df['Date'], format="%b'%d'%y", errors='coerce')
        
        # Define all columns to be converted to numbers
        num_cols = ['IA_Hours', 'Shift_Score', 'Sent_Rate', 'Satisfied_Survey', 
                    'OB_Calls', 'QA_Calls', 'Call_Abandons', 'MOB', 
                    'Avg_OB_Time', 'Avg_QA_Time']
        
        for col in num_cols:
            if col in df.columns:
                if df[col].dtype == object:
                    df[col] = df[col].str.replace('%', '').str.strip()
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        return df.dropna(subset=['Date'])
    except: return None

# --- UI START ---
st.title("📈 Advisor Performance Portal")

user_email = st.sidebar.text_input("Login with Email").strip().lower()

if user_email:
    kpi_df = load_kpi_data()
    
    if kpi_df is not None:
        user_kpi = kpi_df[kpi_df['Email'].str.lower() == user_email].copy().sort_values('Date')

        if user_kpi.empty:
            st.warning("No KPI data found for this email.")
        else:
            advisor_name = user_kpi['Advisor Name'].iloc[0]
            st.header(f"Welcome, {advisor_name}")
            
            freq = st.radio("Frequency View:", ["Daily", "Weekly", "Monthly"], horizontal=True)

            # --- AGGREGATION LOGIC ---
            # We tell the app which columns to SUM and which to AVERAGE
            agg_rules = {
                'Shift_Score': 'mean', 'IA_Hours': 'mean', 'Sent_Rate': 'mean', 'Satisfied_Survey': 'mean',
                'OB_Calls': 'sum', 'QA_Calls': 'sum', 'Call_Abandons': 'sum', 'MOB': 'sum',
                'Avg_OB_Time': 'mean', 'Avg_QA_Time': 'mean'
            }

            if freq == "Daily":
                available_dates = sorted(user_kpi['Date'].unique(), reverse=True)
                selected_val = st.selectbox("Select Date:", available_dates, format_func=lambda x: x.strftime('%d %b %Y'))
                filtered_df = user_kpi[user_kpi['Date'] == selected_val]
                chart_df = user_kpi[user_kpi['Date'] <= selected_val].tail(30)

            elif freq == "Weekly":
                user_kpi['W_Start'] = user_kpi['Date'] - pd.to_timedelta(user_kpi['Date'].dt.dayofweek + 1 % 7, unit='d')
                user_kpi['W_End'] = user_kpi['W_Start'] + pd.to_timedelta(6, unit='d')
                user_kpi['Week_Range'] = (user_kpi['W_Start'].dt.strftime('%d %b %Y') + " - " + user_kpi['W_End'].dt.strftime('%d %b %Y'))
                
                week_options = user_kpi.sort_values('W_Start', ascending=False)['Week_Range'].unique()
                selected_val = st.selectbox("Select Week:", week_options)
                filtered_df = user_kpi[user_kpi['Week_Range'] == selected_val]
                
                chart_df = user_kpi.groupby('Week_Range').agg(agg_rules).reset_index()
                chart_df['Sort_Date'] = pd.to_datetime(chart_df['Week_Range'].str.split(' - ').str[0])
                chart_df = chart_df.sort_values('Sort_Date').rename(columns={'Sort_Date': 'Date'})

            else: # Monthly
                user_kpi['Month_Val'] = user_kpi['Date'].dt.to_period('M').apply(lambda r: r.start_time)
                month_options = sorted(user_kpi['Month_Val'].unique(), reverse=True)
                selected_val = st.selectbox("Select Month:", month_options, format_func=lambda x: x.strftime('%B %Y'))
                filtered_df = user_kpi[user_kpi['Month_Val'] == selected_val]
                
                chart_df = user_kpi.groupby('Month_Val').agg(agg_rules).reset_index().rename(columns={'Month_Val':'Date'})

            # --- SUMMARY METRICS ---
            st.markdown("---")
            st.subheader("Performance Summary")
            
            # Row 1: Quality Averages
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Avg Shift Score", f"{filtered_df['Shift_Score'].mean():.1f}%")
            m2.metric("Avg IA Hours", f"{filtered_df['IA_Hours'].mean():.2f}")
            m3.metric("Avg Satisfied Survey", f"{filtered_df['Satisfied_Survey'].mean():.1f}%")
            m4.metric("Avg Sent Rate", f"{filtered_df['Sent_Rate'].mean():.1f}%")

            # Row 2: Volume Totals
            v1, v2, v3, v4 = st.columns(4)
            total_calls = filtered_df['OB_Calls'].sum() + filtered_df['QA_Calls'].sum()
            v1.metric("Total Calls Handled", int(total_calls))
            v2.metric("Total OB Calls", int(filtered_df['OB_Calls'].sum()))
            v3.metric("Total Call Abandons", int(filtered_df['Call_Abandons'].sum()))
            v4.metric("Total MOB", int(filtered_df['MOB'].sum()))

            # --- PERFORMANCE TRENDS ---
            st.divider()
            st.subheader(f"Quality Trends ({freq})")
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                st.plotly_chart(px.line(chart_df, x='Date', y='Shift_Score', markers=True, title="Shift Score (%)"), width='stretch')
                st.plotly_chart(px.line(chart_df, x='Date', y='Sent_Rate', markers=True, title="Sent Rate (%)"), width='stretch')
            with t_col2:
                st.plotly_chart(px.line(chart_df, x='Date', y='Satisfied_Survey', markers=True, title="Satisfied Survey (%)"), width='stretch')
                st.plotly_chart(px.line(chart_df, x='Date', y='IA_Hours', markers=True, title="IA Hours"), width='stretch')

            st.subheader(f"Volume Trends ({freq} - Total Sum)")
            v_col1, v_col2 = st.columns(2)
            with v_col1:
                st.plotly_chart(px.bar(chart_df, x='Date', y=['OB_Calls', 'QA_Calls'], title="Call Volume (OB vs QA)", barmode='group'), width='stretch')
            with v_col2:
                st.plotly_chart(px.bar(chart_df, x='Date', y=['Call_Abandons', 'MOB'], title="Abandons & MOB Volume", barmode='group'), width='stretch')

            # --- RAW DATA (Strictly Filtered) ---
            st.divider()
            st.subheader(f"📋 Raw Data for this Selection")
            st.dataframe(filtered_df.sort_values('Date', ascending=False), width='stretch')

else:
    st.info("👈 Enter your email in the sidebar to begin.")
