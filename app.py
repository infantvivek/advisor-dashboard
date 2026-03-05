
    
      import streamlit as st
import pandas as pd
import plotly.express as px

# --- CONFIGURATION ---
# Replace this with your Google Sheet 'Publish to Web' CSV URL
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?output=csv")

st.set_page_config(page_title="Advisor Performance Portal", layout="wide")

# --- DATA LOADING ---
@st.cache_data(ttl=600)  # Refreshes every 10 mins
def load_data():
    df = pd.read_csv(SHEET_URL)
    df['Date'] = pd.to_datetime(df['Date'])
    return df

try:
    df_kpi = load_data()
except:
    st.error("Failed to load data. Check your Google Sheet Publish link.")
    st.stop()

# --- SIMPLE LOGIN SYSTEM ---
st.sidebar.title("Login")
user_email = st.sidebar.text_input("Enter your Email to view stats")

if user_email:
    # Filter data for the specific user
    user_data = df_kpi[df_kpi['Email'].str.lower() == user_email.lower()]
    
    if user_data.empty:
        st.warning("No data found for this email.")
    else:
        st.title(f"Welcome, {user_data['Advisor Name'].iloc[0]}")
        
        # --- FILTERS ---
        view_type = st.radio("Select View", ["Daily", "Weekly", "Monthly"])
        
        # Logic to aggregate data based on view_type
        if view_type == "Weekly":
            plot_df = user_data.resample('W', on='Date').mean().reset_index()
        elif view_type == "Monthly":
            plot_df = user_data.resample('M', on='Date').mean().reset_index()
        else:
            plot_df = user_data

        # --- DASHBOARD LAYOUT ---
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Avg Shift Score", f"{plot_df['Shift_Score'].mean():.2f}")
        col2.metric("Satisfied %", f"{plot_df['Satisfied_Survey'].mean():.1%}")
        col3.metric("Total OB Calls", int(plot_df['OB_Calls'].sum()))
        col4.metric("Avg IA Hours", f"{plot_df['IA_Hours'].mean():.1f}")

        # --- VISUALS ---
        st.subheader("Performance Trends")
        fig = px.line(plot_df, x='Date', y=['Shift_Score', 'Satisfied_Survey'], 
                      title="Quality & Adherence Trend")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Call Handling Volume")
        fig2 = px.bar(plot_df, x='Date', y=['OB_Calls', 'QA_Calls'], barmode='group')
        st.plotly_chart(fig2, use_container_width=True)

        # --- CSAT SECTION ---
        st.divider()
        st.subheader("Recent CSAT/DSAT Feedback")
        # (Assuming you link the CSAT sheet similarly or combine data)
        st.dataframe(user_data[['Date', 'Type', 'Chat_Link']])

else:
    st.info("Please enter your email in the sidebar to access your personalized dashboard.")
