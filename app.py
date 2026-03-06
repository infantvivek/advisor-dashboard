

# --- 1. DATA SOURCE LINKS ---
# Ensure these links point to the specific tabs in your Google Sheet (Published as CSV)
#TEAM_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=0&single=true&output=csv"
#KPI_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=1918948844&single=true&output=csv"
#DSAT_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS8T5NPl5jhOiEIxvI5zo0MFE3CR3jaHPPW5I-9mK0k9WD8AMUZdMatNubJL3MYUo0HQT7sSrw84P2R/pub?gid=367459010&single=true&output=csv" 
elif freq == "Weekly":
    # 1. Calculate the start of the week (Sunday)
    # pd.to_timedelta(full_kpi['Date'].dt.dayofweek + 1 % 7, unit='d') ensures Sunday is start_date
    full_kpi['W_Start'] = full_kpi['Date'] - pd.to_timedelta((full_kpi['Date'].dt.dayofweek + 1) % 7, unit='d')
    
    # 2. Calculate the end of the week (Saturday)
    full_kpi['W_End'] = full_kpi['W_Start'] + pd.to_timedelta(6, unit='d')
    
    # 3. Create a combined label: "DD Mon YYYY - DD Mon YYYY"
    full_kpi['Week_Range'] = (
        full_kpi['W_Start'].dt.strftime('%d %b %Y') + 
        " - " + 
        full_kpi['W_End'].dt.strftime('%d %b %Y')
    )
    
    # 4. Get unique week ranges and sort them descending (newest week first)
    # We sort by the actual W_Start date column for accuracy
    week_options = full_kpi.sort_values('W_Start', ascending=False)['Week_Range'].unique()
    
    # 5. Display the dropdown
    sel = st.selectbox("Select Week:", week_options)
    
    # 6. Filter the data based on the selection
    f_kpi = full_kpi[full_kpi['Week_Range'] == sel]
    
    # Apply identical logic to DSAT data if it exists
    if not full_dsat.empty:
        full_dsat['W_Start'] = full_dsat['Date'] - pd.to_timedelta((full_dsat['Date'].dt.dayofweek + 1) % 7, unit='d')
        full_dsat['W_End'] = full_dsat['W_Start'] + pd.to_timedelta(6, unit='d')
        full_dsat['Week_Range'] = (
            full_dsat['W_Start'].dt.strftime('%d %b %Y') + 
            " - " + 
            full_dsat['W_End'].dt.strftime('%d %b %Y')
        )
        f_dsat = full_dsat[full_dsat['Week_Range'] == sel]
    else: 
        f_dsat = pd.DataFrame()
