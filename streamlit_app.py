import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scipy import stats

# Load and process data
@st.cache_data
def load_data(cutoff_date, vax_metric):
    df = pd.read_csv('excess-mortality-p-scores-projected-baseline.csv')
    vaccine = pd.read_csv('https://raw.githubusercontent.com/owid/covid-19-data/refs/heads/master/public/data/vaccinations/vaccinations.csv')
    
    # Rename 'Entity' to 'Country' in the df dataframe
    df = df.rename(columns={'Entity': 'Country'})
    
    max_vaccination_stats = vaccine.groupby('location').agg({
        'people_vaccinated_per_hundred': 'max',
        'people_fully_vaccinated_per_hundred': 'max',
    }).reset_index()
    
    df['Date'] = pd.to_datetime(df['Day'])
    cutoff_date = pd.to_datetime(cutoff_date)
    
    result = df.groupby('Country').apply(lambda x: pd.Series({
        'avg_before': x[x['Date'] <= cutoff_date]['p_proj_all_ages'].mean(),
        'avg_after': x[x['Date'] > cutoff_date]['p_proj_all_ages'].mean()
    })).reset_index()
    
    merged = pd.merge(result, max_vaccination_stats, left_on='Country', right_on='location', how='inner')
    merged.drop('location', axis=1, inplace=True)
    merged['people_vaccinated_per_hundred'] = merged['people_vaccinated_per_hundred'].astype(float)
    merged['people_fully_vaccinated_per_hundred'] = merged['people_fully_vaccinated_per_hundred'].astype(float)
    merged.dropna(subset=[vax_metric, 'avg_before', 'avg_after'], inplace=True)
    merged.sort_values(by=vax_metric, ascending=True, inplace=True)
    
    return merged

# Streamlit app
st.title('Mortalità in eccesso prima e dopo vaccinazione')

# Add options for cutoff date and vaccination metric
cutoff_date = st.date_input('Select cutoff date', value=pd.to_datetime('2021-09-30'))
vax_metric = st.selectbox('Select vaccination metric', 
                          ['people_vaccinated_per_hundred', 'people_fully_vaccinated_per_hundred'],
                          format_func=lambda x: 'People Vaccinated per Hundred' if x == 'people_vaccinated_per_hundred' else 'People Fully Vaccinated per Hundred')

# Load data
data = load_data(cutoff_date, vax_metric)

# Create interactive plot
fig = px.scatter(data, x=vax_metric, y=['avg_before', 'avg_after'],
                 hover_data=['Country', 'people_vaccinated_per_hundred', 'people_fully_vaccinated_per_hundred'],
                 labels={vax_metric: 'Vaccination Rate per Hundred',
                         'value': 'Average excess mortality',
                         'variable': 'Periodo'},
                 title=f'Average excess mortality before and after vaccination by Country/Vaccination Rate (Cutoff: {cutoff_date.strftime("%Y-%m-%d")})')
fig.update_layout(legend_title_text='Periodo')

# Add regression button
if st.button('Add Regression Line for After Vaccination'):
    # Perform regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(data[vax_metric], data['avg_after'])
    
    # Add regression line to the plot
    x_range = np.linspace(data[vax_metric].min(), data[vax_metric].max(), 100)
    y_range = slope * x_range + intercept
    fig.add_trace(go.Scatter(x=x_range, y=y_range, mode='lines', name='Regression Line (After)',
                             line=dict(color='red', dash='dash')))
    
    # Display regression statistics
    st.write(f"Regression Statistics:")
    st.write(f"Slope: {slope:.4f}")
    st.write(f"Intercept: {intercept:.4f}")
    st.write(f"R-squared: {r_value**2:.4f}")
    st.write(f"P-value: {p_value:.4f}")

# Display the plot
st.plotly_chart(fig, use_container_width=True)

# Add a selectbox for choosing a country
selected_country = st.selectbox('Select a Country', data['Country'].unique())

# Display information for the selected country
if selected_country:
    country_data = data[data['Country'] == selected_country].iloc[0]
    st.write(f"Selected Country: {selected_country}")
    st.write(f"Prima della vaccinazione: {country_data['avg_before']:.2f}")
    st.write(f"Dopo vaccinazione: {country_data['avg_after']:.2f}")
    st.write(f"People Vaccinated per Hundred: {country_data['people_vaccinated_per_hundred']:.2f}")
    st.write(f"People Fully Vaccinated per Hundred: {country_data['people_fully_vaccinated_per_hundred']:.2f}")

# Display the raw data
if st.checkbox('Show raw data'):
    st.write(data)
