import streamlit as st
import pandas as pd
import plotly.express as px


# Load and process data
@st.cache_data
def load_data():
    df = pd.read_csv('excess-mortality-p-scores-projected-baseline.csv')
    vaccine = pd.read_csv(
        'https://raw.githubusercontent.com/owid/covid-19-data/refs/heads/master/public/data/vaccinations/vaccinations.csv')

    max_vaccination_stats = vaccine.groupby('location').agg({
        'people_vaccinated_per_hundred': 'max',
    }).reset_index()

    df['Date'] = pd.to_datetime(df['Day'])
    cutoff_date = pd.to_datetime('2021-09-30')

    result = df.groupby('Entity').apply(lambda x: pd.Series({
        'avg_before': x[x['Date'] <= cutoff_date]['p_proj_all_ages'].mean(),
        'avg_after': x[x['Date'] > cutoff_date]['p_proj_all_ages'].mean()
    })).reset_index()

    merged = pd.merge(result, max_vaccination_stats, left_on='Entity', right_on='location', how='inner')
    merged.drop('location', axis=1, inplace=True)
    merged['people_vaccinated_per_hundred'] = merged['people_vaccinated_per_hundred'].astype(float)
    merged.dropna(inplace=True)
    merged.sort_values(by='people_vaccinated_per_hundred', ascending=True, inplace=True)

    return merged


# Streamlit app
st.title('Average Before and After by Entity/People Vaccinated per Hundred')

# Load data
data = load_data()

# Create interactive plot
fig = px.scatter(data, x='people_vaccinated_per_hundred', y=['avg_before', 'avg_after'],
                 hover_data=['Entity'],
                 labels={'people_vaccinated_per_hundred': 'People Vaccinated per Hundred',
                         'value': 'Average',
                         'variable': 'Period'},
                 title='Average Before and After by Entity/People Vaccinated per Hundred')

fig.update_layout(legend_title_text='Period')

# Display the plot
st.plotly_chart(fig, use_container_width=True)

# Add a selectbox for choosing an entity
selected_entity = st.selectbox('Select an Entity', data['Entity'].unique())

# Display information for the selected entity
if selected_entity:
    entity_data = data[data['Entity'] == selected_entity].iloc[0]
    st.write(f"Selected Entity: {selected_entity}")
    st.write(f"Average Before: {entity_data['avg_before']:.2f}")
    st.write(f"Average After: {entity_data['avg_after']:.2f}")
    st.write(f"People Vaccinated per Hundred: {entity_data['people_vaccinated_per_hundred']:.2f}")

# Display the raw data
if st.checkbox('Show raw data'):
    st.write(data)
