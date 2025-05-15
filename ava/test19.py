import pandas as pd
import streamlit as st

def load_data(uploaded_file,rows):
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file, skiprows=rows)
        df["Field change time"] = pd.to_datetime(df["Field change time"], format="%d/%m/%Y %I:%M:%S.%f %p", errors='coerce')
        return df
    return None

def filter_data(df, start_date, end_date, selected_states):
    df_filtered = df[(df['Timestamp'].between(start_date, end_date)) & df['State'].isin(selected_states)]
    df_filtered['Adjusted Duration (seconds)'] = df_filtered['Duration (seconds)'].fillna(0)
    return df_filtered

def calculate_state_summary(df_filtered):
    state_duration_summary = df_filtered.groupby("State")["Adjusted Duration (seconds)"].sum().reset_index()
    total_duration = df_filtered["Adjusted Duration (seconds)"].sum()
    if total_duration > 0:
        state_duration_summary["Availability (%)"] = (state_duration_summary["Adjusted Duration (seconds)"] / total_duration) * 100
    else:
        state_duration_summary["Availability (%)"] = 0
    return state_duration_summary

def main():
    st.title("System State Analysis")
    uploaded_file = st.file_uploader("Upload an Excel file", type=["xlsx"])
    skiprows = 7

    if uploaded_file:
        df = load_data(uploaded_file,skiprows)
        if df is not None:
            start_date = st.date_input("Start Date", df['Field change time'].min().date())
            end_date = st.date_input("End Date", df['Field change time'].max().date())
            selected_states = st.multiselect("Select States", df['State'].unique(), default=df['State'].unique())
            
            df_filtered = filter_data(df, start_date, end_date, selected_states)
            state_summary = calculate_state_summary(df_filtered)
            
            st.subheader("State Duration Summary")
            st.dataframe(state_summary)
            
            st.subheader("Availability (%) Chart")
            st.bar_chart(state_summary.set_index("State")[["Availability (%)"]])
    
if __name__ == "__main__":
    main()
