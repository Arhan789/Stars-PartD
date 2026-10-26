"""Reconstructed Stars Part D demonstration, not the original course starter app.
Data: illustrative synthetic catalogues, replace with original course data if available.
Stellar phase boundaries: simplified educational model, not research predictions.
"""
import numpy as np
import pandas as pd
import altair as alt
import streamlit as st
from pathlib import Path

st.set_page_config(page_title='Stars — Part D', layout='wide')
st.title('Stars — interactive stellar evolution')
st.caption('Reconstructed teaching demonstration. Synthetic catalogue and approximate stellar-evolution rules; not the original tutorial starter.')
BASE = Path(__file__).resolve().parent

@st.cache_data
def load_catalogue():
    return pd.read_csv(BASE / "hyg_stars.zip")

catalogue = load_catalogue()

st.sidebar.header('Star settings')
mass = st.sidebar.slider('Mass (solar masses)', 0.1, 300.0, 1.0, 0.1)
age = st.sidebar.slider('Age (billion years)', 0.0, 15.0, 4.6, 0.1)
metallicity = st.sidebar.slider('log10 metallicity', -4.0, -1.7, -2.0, 0.05)
solar_z = 0.02
z = 10 ** metallicity
z_ratio = z / solar_z

# Educational approximation: lower Z leads to higher effective mass at birth
# for the pair-instability window; real thresholds depend on stellar physics.
pair_lo = 140 * (1 + 0.08 * np.log10(max(z_ratio, 1e-6)))
pair_hi = 260 * (1 + 0.08 * np.log10(max(z_ratio, 1e-6)))
pair_lo = max(100, pair_lo)
pair_hi = max(pair_lo + 30, pair_hi)
life = 10 * mass ** -2.5
if age < 0.02 * life:
    phase = 'Protostar'
elif age < life:
    phase = 'Main sequence'
elif age < 1.15 * life:
    phase = 'Giant / supergiant'
else:
    if pair_lo <= mass <= pair_hi:
        phase = 'Pair-instability supernova — no remnant'
    elif mass >= 20:
        phase = 'Black hole'
    elif mass >= 8:
        phase = 'Neutron star'
    else:
        phase = 'White dwarf'

lum = max(1e-5, mass ** 3.5)
temp = 5772 * mass ** 0.48 * (1 + 0.035 * np.log10(solar_z / z))
if phase == 'Giant / supergiant':
    lum *= 100
    temp *= 0.7
elif phase == 'White dwarf':
    lum *= 0.002
    temp *= 2
elif phase in ['Black hole', 'Neutron star', 'Pair-instability supernova — no remnant']:
    lum = np.nan
    temp = np.nan

c1, c2 = st.columns(2)
with c1:
    st.subheader('Current star')
    st.metric('Evolutionary stage', phase)
    st.write(f'Mass: **{mass:.1f} M☉** · Age: **{age:.1f} billion years**')
    st.write(f'Metallicity: **{z:.5f}** (solar ≈ {solar_z:.2f})')
    st.write(f'Estimated main-sequence lifetime: **{life:.3g} billion years**')
    st.write(f'Approximate pair-instability window: **{pair_lo:.0f}–{pair_hi:.0f} M☉**')
    st.info('Approximate demonstration model. Phase boundaries are not calibrated to the course starter code.')

with c2:
    st.subheader('Hertzsprung–Russell diagram')
    df = catalogue[['temperature', 'luminosity', 'proper']].copy()
    df = df[(df.temperature > 0) & (df.luminosity > 0)].dropna()
    background = alt.Chart(df).mark_circle(size=17, opacity=0.30).encode(
        x=alt.X('temperature:Q', scale=alt.Scale(type='log', reverse=True), title='Surface temperature (K) — hot to left'),
        y=alt.Y('luminosity:Q', scale=alt.Scale(type='log'), title='Luminosity (solar units)'),
        tooltip=['proper:N', alt.Tooltip('temperature:Q', format='.0f'), alt.Tooltip('luminosity:Q', format='.3g')],
    )
    if np.isfinite(temp) and np.isfinite(lum):
        star = pd.DataFrame({'temperature': [temp], 'luminosity': [lum], 'label': ['Selected star']})
        foreground = alt.Chart(star).mark_point(color='#ff6b45', size=220, filled=True, shape='diamond').encode(
            x='temperature:Q', y='luminosity:Q', tooltip=['label:N', 'temperature:Q', 'luminosity:Q']
        )
        st.altair_chart((background + foreground).properties(height=430).interactive(), use_container_width=True)
    else:
        st.altair_chart(background.properties(height=430).interactive(), use_container_width=True)
        st.caption('No luminous star marker for the selected compact-remnant / no-remnant phase.')

st.divider()
st.subheader('Catalogue exploration')
st.caption('The supplied CSV files contain synthetic illustrative values, not measured Hipparcos observations.')
max_mag = st.slider('Maximum apparent magnitude', -2.0, 8.0, 6.5, 0.5)
visible = catalogue[catalogue['mag'] <= max_mag]
left, right = st.columns(2)
with left:
    st.write('Magnitude distribution')
    st.bar_chart(np.histogram(visible['mag'].dropna(), bins=20)[0])
with right:
    st.write('Star positions (right ascension and declination)')
    scatter = alt.Chart(visible.sample(min(1000, len(visible)), random_state=7)).mark_circle(size=13, opacity=0.45).encode(
        x=alt.X('ra:Q', title='Right ascension (hours)'),
        y=alt.Y('dec:Q', title='Declination (degrees)'),
        tooltip=['proper:N', 'mag:Q']
    ).properties(height=270)
    st.altair_chart(scatter, use_container_width=True)
if st.checkbox('Show raw catalogue data'):
    st.dataframe(visible, use_container_width=True)
