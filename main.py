import asyncio
import datetime
import json

import matplotlib.pyplot as plt
import pandas as pd
from pyodide import create_proxy
from pyodide.http import pyfetch, open_url

plt.style.use('seaborn-whitegrid')

API_KEY = '0ILEgZh78yTcENxO5Yx5PpOzgoBSnZmeUZvkjbB8'
API_URL = 'https://api.usa.gov/crime/fbi/sapi'

crime_mapping = {
    'violent-crime': 'violent_crime',
    'homicide': 'homicide',
    'rape': 'rape',
    'robbery': 'robbery',
    'aggravated-assault': 'aggravated_assault',
    'property-crime': 'property_crime',
    'arson': 'arson',
    'burglary': 'burglary',
    'larceny': 'larceny',
    'motor-vehicle-theft': 'motor_vehicle_theft',
}


def loader(func):
    async def wrapper(*args, **kwargs):
        spinner = Element('trend-spinner').element
        spinner.classList.remove('is-hidden')
        await func()
        spinner.classList.add('is-hidden')

    return wrapper


async def fetch_states():
    response = await pyfetch(
        url=f'{API_URL}/api/states?API_KEY={API_KEY}&size=100',
        method='GET')
    states_data = await response.json()
    states = states_data.get('results')
    return states


class App:
    def __init__(self, start_year=2011, end_year=2021, show_values=False, data=None, crime_type='violent-crime',
                 location='US', crimes=None):
        self.start_year = start_year
        self.end_year = end_year
        self.show_values = show_values
        self.data = data or []
        self.crime_type = crime_type
        self.location = location
        self.crimes = crimes or []

    async def get_data(self):
        if self.location == 'US':
            endpoint = 'api/estimates/national'
        else:
            endpoint = f'api/estimates/states/{self.location}'
        response = await pyfetch(
            url=f'{API_URL}/{endpoint}/{self.start_year}/{self.end_year}?API_KEY={API_KEY}',
            method='GET')
        self.data = await response.json()
        return self.data

    def build_plot(self):
        df = pd.json_normalize(self.data, record_path=['results'])
        if self.crime_type == 'rape':
            df['rate_revised'] = df['rape_revised'] / df['population'] * 100000
            df['rate_legacy'] = df['rape_legacy'] / df['population'] * 100000
            df = df[['year', 'rate_legacy', 'rate_revised']].sort_values(by=['year'])
            ax = df.set_index('year').plot(marker='o', color={'rate_revised': '#485fc7', 'rate_legacy': '#6b7280'},
                                           figsize=(12, 8))
            if self.show_values:
                for i, j in zip(df['year'], df['rate_legacy']):
                    ax.annotate(str(round(j, 2)), xy=(i, j), ha="center",
                                bbox=dict(boxstyle="round,pad=0.3", fc="w", ec="0.5", alpha=0.9))
                for i, j in zip(df['year'], df['rate_revised']):
                    ax.annotate(str(round(j, 2)), xy=(i, j), ha="center",
                                bbox=dict(boxstyle="round,pad=0.3", fc="w", ec="0.5", alpha=0.9))
            ax.legend(['rate legacy', 'rate revised'])
        else:
            df['rate'] = df[crime_mapping[self.crime_type]] / df['population'] * 100000
            df = df[['year', 'rate']].sort_values(by=['year'])
            ax = df.set_index('year').plot(marker='o', color='#485fc7', figsize=(12, 8))
            if self.show_values:
                for i, j in zip(df['year'], df['rate']):
                    ax.annotate(str(round(j, 2)), xy=(i, j), ha="center",
                                bbox=dict(boxstyle="round,pad=0.3", fc="w", ec="0.5", alpha=0.9))

        ax.set_xticks(df['year'])
        ax.set_xticklabels(df['year'], rotation=40)
        plt.title('Rate per 100,000 people, by year')
        pyscript.write("trend-mpl", plt)


try:
    spinner = Element('trend-spinner').element
    spinner.classList.remove('is-hidden')

    app = App()
    data = await app.get_data()
    app.build_plot()

    spinner.classList.add('is-hidden')

    states = await fetch_states()
    location_select = Element('trend-location').element
    for state in states:
        option = document.createElement('option')
        option.innerHTML = state.get('state_name')
        option.value = state.get('state_abbr')
        location_select.appendChild(option)

    url_content = open_url('https://github.com/shundrikova/crime-data/blob/main/crime-crimes.json')
    crime_types = json.load(url_content)
    app.crimes = crime_types.get('results', {}).get('items')
    crime_select = Element('trend-crime-type').element
    for crime in app.crimes:
        option = document.createElement('option')
        option.innerHTML = crime.get('text')
        option.value = crime.get('id')
        crime_select.appendChild(option)
        if crime.get('id') == app.crime_type:
            crime_select.value = crime.get('id')
            Element('trend-crime-type-title').element.innerHTML = crime.get('text')
            Element('trend-crime-type-plot-title').element.innerHTML = crime.get('text')

    years = range(1985, datetime.date.today().year)
    from_select = Element('trend-from').element
    to_select = Element('trend-to').element
    for year in years:
        to_option = document.createElement('option')
        to_option.innerHTML = year
        to_option.value = year
        to_select.appendChild(to_option)
        if year == app.end_year:
            to_select.value = year
            Element('trend-crime-to-title').element.innerHTML = year
        from_option = to_option.cloneNode(True)
        from_select.appendChild(from_option)
        if year == app.start_year:
            from_select.value = year
            Element('trend-crime-from-title').element.innerHTML = year
except:
    alert('Please reload page')


def _update_show_values(*args, **kwargs):
    app.show_values = Element('trend-show-values').element.checked
    app.build_plot()


update_show_values = create_proxy(_update_show_values)
document.getElementById('trend-show-values').addEventListener("click", update_show_values)


@loader
async def _update_trends_location(*args, **kwargs):
    app.location = Element('trend-location').element.value
    data = await app.get_data()
    app.build_plot()


update_trends_location = create_proxy(_update_trends_location)
document.getElementById('trend-location').addEventListener("change", update_trends_location)


@loader
async def _update_trends_from(*args, **kwargs):
    app.start_year = Element('trend-from').element.value
    Element('trend-crime-from-title').element.innerHTML = app.start_year
    data = await app.get_data()
    app.build_plot()


update_trends_from = create_proxy(_update_trends_from)
document.getElementById('trend-from').addEventListener("change", update_trends_from)


@loader
async def _update_trends_to(*args, **kwargs):
    app.end_year = Element('trend-to').element.value
    Element('trend-crime-to-title').element.innerHTML = app.end_year
    data = await app.get_data()
    app.build_plot()


update_trends_to = create_proxy(_update_trends_to)
document.getElementById('trend-to').addEventListener("change", update_trends_to)


@loader
async def _update_trends_type(*args, **kwargs):
    app.crime_type = Element('trend-crime-type').element.value
    text = next(item.get('text') for item in app.crimes if item['id'] == app.crime_type)
    Element('trend-crime-type-title').element.innerHTML = text
    Element('trend-crime-type-plot-title').element.innerHTML = text
    data = await app.get_data()
    app.build_plot()


update_trends_type = create_proxy(_update_trends_type)
document.getElementById('trend-crime-type').addEventListener("change", update_trends_type)
