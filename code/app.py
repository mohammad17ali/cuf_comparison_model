from flask import Flask, render_template, request
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.io as pio
from functions import get_excel, calc_e_array, success_rate, capex_calc

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/results', methods=['POST'])
def results():
    # Get user input from the form
    sol_range_start = float(request.form['solar_capacity_start'])
    sol_range_end = float(request.form['solar_capacity_end'])
    solar_step = float(request.form['solar_step'])

    wind_range_start = float(request.form['wind_capacity_start'])
    wind_range_end = float(request.form['wind_capacity_end'])
    wind_step = float(request.form['wind_step'])

    bess_initial_cap = float(request.form['bess_initial_cap'])
    bess_total_cap = float(request.form['bess_total_cap'])
    bess_step = float(request.form['bess_step'])

    excel_path = 'solar_and_wind_data.xlsm'
    sheet0_df = get_excel(excel_path)

    e_grid = sheet0_df['E_grid (33kV)']
    wind = sheet0_df['Wind']

    sol_range = np.arange(sol_range_start, sol_range_end, solar_step)
    wind_range = np.arange(wind_range_start, wind_range_end, wind_step)
    bess_range = np.arange(bess_initial_cap, bess_total_cap, bess_step)

    solar_cap_l = []
    wind_cap_l = []
    bess_l = []
    rtc_success_rate = []
    capex_val = []

    for i in sol_range:
        for j in wind_range:
            for k in bess_range:
                solar_cap_l.append(i)
                wind_cap_l.append(j)
                bess_l.append(k)

                e_array = calc_e_array(e_grid, wind, i, j)
                success = success_rate(e_array, k, k)
                capex = capex_calc(i, j, k)
                rtc_success_rate.append(success)
                capex_val.append(capex)

    # Create the DataFrame
    new_df = pd.DataFrame({
        'Solar Capacity (MW)': solar_cap_l,
        'Wind Capacity (MW)': wind_cap_l,
        'BESS Capacity (MWh)': bess_l,
        'Success Rate': rtc_success_rate,
        'Capex': capex_val
    })

    # Filter the DataFrame for Success Rate >= 85%
    success_df = new_df[new_df['Success Rate'] >= 85]
    success_df.sort_values(by='Capex', ascending=True, inplace=True)

    min_capex_df = success_df.loc[success_df.groupby('Solar Capacity (MW)')
                                  ['Capex'].idxmin()]
    # Reset the index
    min_capex_df = min_capex_df.reset_index(drop=True)
    success_df = success_df.reset_index(drop=True)

    # Generate Scatter Plot (Capex vs Success Rate)
    scatter_fig = px.scatter(
        success_df,
        x='Capex',
        y='Success Rate',
        title='Capex vs Success Rate Scatter Plot',
        labels={
            'Capex': 'Capex (Cr)',
            'Success Rate': 'Success Rate (%)'
        },
        hover_data={
            'Solar Capacity (MW)': True,
            'Wind Capacity (MW)': True,
            'BESS Capacity (MWh)': True,
            'Capex': ':,.2f',
            'Success Rate': ':,.2f'
        }
    )
    scatter_html = pio.to_html(scatter_fig, full_html=False)

    # Generate Parallel Coordinates Plot with better colors
    fig = px.parallel_categories(
        min_capex_df,
        dimensions=[
            'Solar Capacity (MW)', 'Wind Capacity (MW)', 'BESS Capacity (MWh)',
            'Success Rate', 'Capex'
        ],
        color='Capex',
        color_continuous_scale=px.colors.sequential.Inferno)

    fig2 = px.parallel_coordinates(
        min_capex_df,
        dimensions=[
            'Solar Capacity (MW)', 'Wind Capacity (MW)', 'BESS Capacity (MWh)',
            'Success Rate', 'Capex'
        ],
        color="Success Rate",
        color_continuous_scale=px.colors.diverging.Tealrose,
        title= 'Parallel Coordinates Plot for Solar, Wind, Battery, Success Rate, and Capex'
    )

    # Save the plot as an HTML file
    plot1_html = pio.to_html(fig, full_html=False)
    plot2_html = pio.to_html(fig2, full_html=False)

    # Render the results on the results page
    return render_template('results.html',
                           plot1_html=plot1_html,
                           plot2_html=plot2_html,
                           scatter_html=scatter_html,
                           table1=min_capex_df.to_html(classes='data',
                                                       header="true"),
                           table2=success_df.to_html(classes='data',
                                                     header="true"))


if __name__ == '__main__':
    app.run(debug=True)
