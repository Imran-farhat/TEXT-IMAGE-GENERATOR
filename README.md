# Flux Image Studio

A Flask-powered image-generation studio that enhances prompts, calls the **black-forest-labs/FLUX.1-schnell** model on Hugging Face, and serves a polished web UI for running generations, viewing enhanced prompts, and downloading results.

## Features
- Prompt enhancer that infers subject category & art style, then appends cinematic descriptors + a high-quality safety net.
- Hugging Face inference client with tuned guidance scale, 1,024×1,024 output, and safe defaults (≤16 inference steps).
- Modern single-page UI (templates/index.html) with status pulses, prompt history, chips for sample prompts, and download-ready previews.
- Health check + JSON API suitable for integrating your own frontend or workflows.

## Prerequisites
- Python 3.10+
- Hugging Face access token with permissions for `black-forest-labs/FLUX.1-schnell`
- (Optional) `python -m venv .venv` for an isolated environment

## Setup (Windows PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Configure Secrets
Never commit secrets. Provide `HF_API_TOKEN` via one of the following:
```powershell
# Temporary for current shell
$env:HF_API_TOKEN = "hf_your_token"

# Or create .env (not tracked) using the provided .env.example template
```

## Run the Server
```powershell
python app.py
```
- Web UI: http://127.0.0.1:5001/
- Health: http://127.0.0.1:5001/health

## API Usage
`POST /generate`
```json
{ "prompt": "Majestic dragon between floating islands, cinematic" }
```
Response contains:
- `image`: base64 data URL (PNG)
- `enhanced_prompt`
- `model_used`
- `demo_mode` flag (True if generation fell back to an error state)

Errors return `success: false` and an `error` message (no placeholder image is generated).

## Troubleshooting
- **401/403** → Token missing or lacks model permission.
- **InferenceTimeoutError** → Model load slow; retry with simpler prompt or lower resolution.
- **Large prompts** → Keep text concise to stay under HF request limits.

## Contributing / Publishing
1. Confirm `git status` is clean and no `.env` or tokens are staged.
2. Follow standard GitHub flow (`git init`, `git add`, `git commit`, `git push`).
3. Open an issue/PR for enhancements like persistent history, model switching, or mobile tweaks.

Happy prompting!
