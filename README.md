# AI Skin Cancer Detection and CDSS

Streamlit-based clinical decision support prototype for skin lesion screening.

## Features

- Benign / malignant model prediction
- Confidence and probability breakdown
- Risk meter and ABCDE analysis
- Image validation and quality checks
- Grad-CAM explainability
- AI clinical summary and patient guidance
- PDF clinical report generation

## Run Locally

```powershell
python -m streamlit run app.py
```

## Streamlit Cloud Deployment

1. Push this repository to GitHub.
2. Open Streamlit Community Cloud.
3. Create a new app from this repository.
4. Set the main file path to:

```text
app.py
```

5. Add this secret in Streamlit Cloud app settings:

```toml
NVIDIA_API_KEY = "your_nvidia_api_key_here"
```

Do not commit `.streamlit/secrets.toml` to GitHub.

## Model Hosting

The trained model is downloaded at runtime from Hugging Face:

```text
reddysorgs/skin-cancer-cdss-model/final_resnet_texture_model.pth
```

## Disclaimer

This project is an educational clinical decision support prototype. It does not provide a final medical diagnosis.
