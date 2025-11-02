AI Image Generator Backend

This repository runs a small Flask backend that enhances prompts and (optionally) calls a Hugging Face SDXL model to generate images. If the external API is unavailable or the token is not valid, the server returns a generated placeholder image for testing.

Security and GitHub

- Do NOT commit your Hugging Face token. The project reads `HF_API_TOKEN` from the environment (or from a `.env` file if you choose to use python-dotenv). A `.env.example` is included to show the required variable name. `.env` is ignored by `.gitignore`.

Quick start (Windows / PowerShell):

1. Create & activate a virtual environment (optional but recommended):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Provide your Hugging Face token (one of these methods):

- Temporary (PowerShell session):

```powershell
$env:HF_API_TOKEN = 'hf_your_token_here'
```

- Use a `.env` file locally (don't commit it). Copy the included `.env.example` to `.env` and fill the value. Optionally install `python-dotenv` and load it from your environment or integrate into your startup script.

3. Run the server:

```powershell
python app.py
```

4. Health check (open in browser):

http://127.0.0.1:5000/health

5. Example requests

- PowerShell (Invoke-RestMethod):

```powershell
$body = @{ prompt = "A dramatic sunset over snowy mountains, hyperdetailed, photorealistic" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/generate -ContentType 'application/json' -Body $body
```

- PowerShell demo endpoint (guaranteed offline placeholder — no HF token required):

```powershell
$body = @{ prompt = "Demo: colorful abstract" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://127.0.0.1:5000/generate_demo -ContentType 'application/json' -Body $body
```

- curl:

```powershell
curl -X POST http://127.0.0.1:5000/generate -H "Content-Type: application/json" -d '{ "prompt": "A dramatic sunset over snowy mountains, hyperdetailed, photorealistic" }'
```

Notes

- If `HF_API_TOKEN` is not set the server will return a demo/placeholder image (this is safer for public repos).
- The `.env.example` file shows how to name the variable; never commit your real `.env` or tokens.
- If you prefer logging to a file, configure a writable log path and add it to `.gitignore` (it already ignores `app.log`).

Publishing to GitHub

1. Ensure no secrets are committed (run `git status` and check for `.env`/files containing tokens).
2. Add a clear README (this file) and a `.gitignore` (included).
3. Create the repository on GitHub and push:

```powershell
git init
git add .
git commit -m "Initial commit: AI image generator backend"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

That's it — your repo will not contain any tokens, and users will be instructed to set their own `HF_API_TOKEN`.
