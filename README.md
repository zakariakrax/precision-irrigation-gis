# Precision Irrigation GIS

Free Streamlit app prototype for satellite/GIS-supported precision irrigation research.

## Deploy on Streamlit Community Cloud

1. Create a GitHub account if needed.
2. Create a new **public** GitHub repository, for example `precision-irrigation-gis`.
3. Upload `app.py`, `requirements.txt`, and `README.md` to the repository root.
4. Open https://share.streamlit.io/ and sign in with GitHub.
5. Choose **Create app** (or **Deploy an app**).
6. Select your repository, branch `main`, and main file path `app.py`.
7. Click **Deploy**.

## Run locally on Windows

```powershell
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

## Important limitations

This is a research prototype. It does not automatically download Sentinel imagery yet. Default agronomic parameters are illustrative, not field-ready irrigation advice. Validate all inputs and outputs with local data and independent observations.
