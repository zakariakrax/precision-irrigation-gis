import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import date

st.set_page_config(page_title="Precision Irrigation GIS — Free", page_icon="🌱", layout="wide")
st.title("🌱 Precision Irrigation GIS")
st.caption("Free academic prototype | Satellite + GIS + crop-water estimates | Morocco-ready workflow")

with st.sidebar:
    st.header("Project settings")
    region = st.text_input("Study area", "Morocco (choose your study region)")
    period_days = st.number_input("Calculation period (days)", 1, 60, 7)
    eta = st.number_input("Reference ET₀ (mm/day)", 0.0, 15.0, 5.0, 0.1)
    rain = st.number_input("Effective rainfall during period (mm)", 0.0, 500.0, 2.0, 0.5)
    soil_contribution = st.number_input("Usable soil-water contribution (mm)", 0.0, 500.0, 0.0, 0.5)
    efficiency_pct = st.slider("Irrigation application efficiency (%)", 30, 100, 85)
    st.caption("Use local, documented inputs for research results. Defaults are examples only.")

KC = {
    "Wheat": {"Initial": 0.30, "Development": 0.75, "Mid-season": 1.15, "Late-season": 0.40},
    "Citrus": {"Initial": 0.65, "Development": 0.70, "Mid-season": 0.70, "Late-season": 0.65},
    "Olive": {"Initial": 0.50, "Development": 0.60, "Mid-season": 0.65, "Late-season": 0.60},
    "Tomato": {"Initial": 0.60, "Development": 1.05, "Mid-season": 1.15, "Late-season": 0.80},
    "Custom": {"Initial": 1.0, "Development": 1.0, "Mid-season": 1.0, "Late-season": 1.0}
}

tabs = st.tabs(["Dashboard", "Field calculator", "Upload field CSV", "NDVI time series", "GIS map", "Research workflow", "Free tools & setup"])

with tabs[0]:
    st.subheader("Platform overview")
    a,b,c,d = st.columns(4)
    a.metric("Cost", "Free")
    b.metric("Core mode", "Offline CSV")
    c.metric("GIS output", "Map + CSV")
    d.metric("Research focus", "Water balance")
    st.markdown("""
    This is a free, local Python application for research prototyping. It helps organize field data, estimate indicative irrigation demand, explore NDVI time series and map field-level results.

    **It does not automatically fetch satellite imagery in this version.** You can download imagery/products through free research services and import processed data. Google Earth Engine can be added as an optional free research workflow after account registration.
    """)
    st.info("Do not use default values as real irrigation instructions. Validate crop coefficients, weather inputs, soil-water terms and efficiency locally.")

with tabs[1]:
    st.subheader("Single-field irrigation estimate")
    left, right = st.columns(2)
    with left:
        field_id = st.text_input("Field ID", "FIELD-001")
        crop = st.selectbox("Crop", list(KC.keys()))
        stage = st.selectbox("Crop stage", ["Initial", "Development", "Mid-season", "Late-season"])
        custom = st.number_input("Custom Kc (used only for Custom crop)", 0.1, 2.0, 1.0, 0.05)
        kc = custom if crop == "Custom" else KC[crop][stage]
    etc = eta * kc * period_days
    net = max(0.0, etc - rain - soil_contribution)
    gross = net / (efficiency_pct / 100.0)
    with right:
        st.metric("Kc used", f"{kc:.2f}")
        st.metric("Estimated crop ET (period)", f"{etc:.1f} mm")
        st.metric("Net irrigation estimate", f"{net:.1f} mm")
        st.metric("Gross irrigation estimate", f"{gross:.1f} mm")
        st.metric("Gross volume per hectare", f"{gross*10:.0f} m³/ha")
    st.latex(r"ET_c = ET_0 \\times K_c \\times N")
    st.latex(r"I_{net} = \\max(0, ET_c - P_{eff} - S_{usable})")
    st.latex(r"I_{gross} = I_{net}/E_a")
    st.caption("Simplified screening calculation, not a complete FAO-56 soil-water balance. Ensure soil contribution is defined consistently for the chosen time step.")

with tabs[2]:
    st.subheader("Upload and analyse field data")
    st.write("Required column: `field_id`. Recommended columns are shown in the downloadable template.")
    template = pd.DataFrame([
        {"field_id":"EXAMPLE-01","crop":"Wheat","stage":"Mid-season","ndvi":0.72,"eto_mm_day":5.0,"days":7,"rain_mm":2.0,"soil_contribution_mm":0.0,"efficiency_pct":85,"area_ha":2.5,"latitude":31.63,"longitude":-7.99},
        {"field_id":"EXAMPLE-02","crop":"Citrus","stage":"Mid-season","ndvi":0.68,"eto_mm_day":4.8,"days":7,"rain_mm":0.0,"soil_contribution_mm":1.0,"efficiency_pct":85,"area_ha":1.2,"latitude":31.64,"longitude":-8.00},
        {"field_id":"EXAMPLE-03","crop":"Olive","stage":"Development","ndvi":0.55,"eto_mm_day":4.5,"days":7,"rain_mm":1.0,"soil_contribution_mm":0.5,"efficiency_pct":85,"area_ha":3.0,"latitude":31.62,"longitude":-7.98},
    ])
    st.download_button("Download free CSV template", template.to_csv(index=False).encode("utf-8"), "field_template.csv", "text/csv")
    uploaded = st.file_uploader("Upload your field CSV", type=["csv"])
    if uploaded:
        try:
            df = pd.read_csv(uploaded)
            if "field_id" not in df.columns:
                st.error("Missing required column: field_id")
            else:
                defaults = {"crop":"Custom","stage":"Mid-season","eto_mm_day":eta,"days":period_days,
                            "rain_mm":rain,"soil_contribution_mm":soil_contribution,"efficiency_pct":efficiency_pct}
                for col, val in defaults.items():
                    if col not in df.columns: df[col] = val
                if "kc" not in df.columns:
                    df["kc"] = [KC.get(str(c), KC["Custom"]).get(str(s),1.0) for c,s in zip(df["crop"],df["stage"])]
                df["etc_mm"] = pd.to_numeric(df["eto_mm_day"], errors="coerce") * pd.to_numeric(df["kc"], errors="coerce") * pd.to_numeric(df["days"], errors="coerce")
                df["net_irrigation_mm"] = (df["etc_mm"] - pd.to_numeric(df["rain_mm"],errors="coerce").fillna(0) - pd.to_numeric(df["soil_contribution_mm"],errors="coerce").fillna(0)).clip(lower=0)
                eff = pd.to_numeric(df["efficiency_pct"], errors="coerce").fillna(efficiency_pct).clip(1,100)/100
                df["gross_irrigation_mm"] = df["net_irrigation_mm"]/eff
                df["gross_m3_ha"] = df["gross_irrigation_mm"]*10
                if "area_ha" in df.columns:
                    df["gross_volume_m3"] = df["gross_m3_ha"]*pd.to_numeric(df["area_ha"],errors="coerce").fillna(0)
                st.dataframe(df, use_container_width=True)
                st.download_button("Download calculated results", df.to_csv(index=False).encode("utf-8"), "irrigation_results.csv", "text/csv")
                if "gross_irrigation_mm" in df:
                    st.plotly_chart(px.bar(df, x="field_id", y="gross_irrigation_mm", color="crop", title="Estimated gross irrigation by field"), use_container_width=True)
        except Exception as exc:
            st.error(f"Could not read CSV: {exc}")

with tabs[3]:
    st.subheader("NDVI time-series explorer")
    st.write("Upload a CSV with at least an `ndvi` column. Recommended: `date`, `field_id`, `ndvi`.")
    ndvi_file = st.file_uploader("Upload NDVI CSV", type=["csv"], key="ndvi")
    if ndvi_file:
        try:
            ndf = pd.read_csv(ndvi_file)
            if "ndvi" not in ndf.columns:
                st.error("CSV must contain an `ndvi` column.")
            else:
                x = "date" if "date" in ndf.columns else ("field_id" if "field_id" in ndf.columns else ndf.columns[0])
                color = "field_id" if "field_id" in ndf.columns and x != "field_id" else None
                st.plotly_chart(px.line(ndf, x=x, y="ndvi", color=color, markers=True, title="NDVI over time"), use_container_width=True)
                st.metric("Mean NDVI", f"{pd.to_numeric(ndf['ndvi'],errors='coerce').mean():.3f}")
        except Exception as exc:
            st.error(f"Could not read NDVI CSV: {exc}")
    st.warning("NDVI indicates vegetation greenness/cover; it is not a direct measurement of irrigation requirement or root-zone soil moisture.")

with tabs[4]:
    st.subheader("Map field-level estimates")
    st.write("Upload a CSV with `field_id`, `latitude`, `longitude`, and `gross_irrigation_mm` to create a map. Or calculate results in the CSV tab first.")
    mapfile = st.file_uploader("Upload map-ready CSV", type=["csv"], key="map")
    if mapfile:
        try:
            mdf = pd.read_csv(mapfile)
            needed = {"latitude","longitude"}
            if not needed.issubset(mdf.columns):
                st.error("Missing latitude and/or longitude columns.")
            else:
                color = "gross_irrigation_mm" if "gross_irrigation_mm" in mdf.columns else None
                hover = [c for c in ["field_id","crop","gross_irrigation_mm","gross_m3_ha"] if c in mdf.columns]
                fig = px.scatter_mapbox(mdf.dropna(subset=["latitude","longitude"]), lat="latitude", lon="longitude",
                                        color=color, hover_data=hover, hover_name="field_id" if "field_id" in mdf.columns else None,
                                        mapbox_style="open-street-map", zoom=5, title=f"Field map — {region}")
                st.plotly_chart(fig, use_container_width=True)
                st.caption("Map needs internet access for OpenStreetMap tiles. Example coordinates in the template are fictitious.")
        except Exception as exc:
            st.error(f"Could not build map: {exc}")

with tabs[5]:
    st.subheader("PhD workflow")
    st.markdown("""
    1. Define study region, crop types, season and research questions.
    2. Obtain Sentinel-2 imagery and mask clouds; record acquisition dates and quality.
    3. Obtain meteorological data and calculate ET₀ using a documented method (e.g. FAO-56 Penman–Monteith where inputs allow).
    4. Map crops and fields; document training/reference data and classification accuracy.
    5. Estimate crop ET and irrigation needs using crop coefficients and a consistent soil-water balance.
    6. Combine results in GIS and create field-level maps.
    7. Validate against independent field observations or credible irrigation records.
    8. Quantify uncertainty and sensitivity to missing data and model parameters.
    9. Test transferability on a separate season, crop or location.
    """)
    st.subheader("Evaluation metrics")
    st.write("Continuous estimates: MAE, RMSE, bias, R². Crop classification: precision, recall, F1 and confusion matrix. Water-management outcomes require independent data; do not claim water savings without suitable evidence.")

with tabs[6]:
    st.subheader("Hna Cv Dyalk")
    st.markdown("""
    - libghitih n7adroh
    - Chi fanida w dakchi
    - daba ha lma39ol ressources
    - **Google Earth Engine:** research platform with free access subject to account eligibility and terms — https://earthengine.google.com/
    - **Copernicus Data Space:** Sentinel imagery access — https://dataspace.copernicus.eu/
    - **CHIRPS precipitation:** https://www.chc.ucsb.edu/data/chirps
    - **ERA5-Land:** https://cds.climate.copernicus.eu/
    Hanti wa9tma khasak chi haja. Chatgpt ra3i rasmi.
    """)
    st.code("python -m pip install -r requirements.txt\npython -m streamlit run app.py", language="powershell")

st.divider()
st.caption("kijak had demo interface a faty hhhh.")

