from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import requests
import base64
import io
import time # Added for Replicate status checking
from PIL import Image, ImageDraw, ImageFont # Used for the detailed placeholder
import random
import urllib.parse
import logging
import os

app = Flask(__name__)
CORS(app)

# Configure basic console logging for easier debugging during development.
# Writing to a file at import time can fail in some environments, so keep
# console logging here. If you prefer a file, uncomment and ensure the
# working directory is writable before enabling.
logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s %(message)s')

# Optionally load local .env for development (safe: .env is in .gitignore)
try:
    # Use a dynamic import to avoid static-analysis errors if python-dotenv isn't installed.
    import importlib
    dotenv = importlib.import_module('dotenv')  # may raise ModuleNotFoundError
    load_dotenv = getattr(dotenv, 'load_dotenv', None)
    if callable(load_dotenv):
        load_dotenv()
        logging.info('Loaded .env file (if present)')
    else:
        logging.info('python-dotenv package found but load_dotenv is not callable')
except ModuleNotFoundError:
    # python-dotenv not installed — that's fine in production
    logging.info('python-dotenv not installed; skipping .env load')
except Exception:
    logging.exception('Unexpected error while attempting to load .env')

# ----------------------------------------------------------------------
# 🔧 API Configuration
# ----------------------------------------------------------------------
# Changed to a powerful general-purpose SDXL model on Hugging Face
HF_API_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-xl-base-1.0"
# NOTE: Replace 'hf_...' with your actual token if it is not a working one
# Load Hugging Face API token from environment for security (do NOT commit your token)
HF_API_TOKEN = os.environ.get('HF_API_TOKEN')
if not HF_API_TOKEN:
    logging.warning('HF_API_TOKEN environment variable not set. The server will return placeholder/demo images unless you set HF_API_TOKEN.')

# ----------------------------------------------------------------------
# ✨ Prompt Enhancement Settings (General Purpose)
# ----------------------------------------------------------------------

# Terms to inject for higher quality and photorealism
QUALITY_INJECT = ", ultra high resolution, 8K, cinematic lighting, dramatic volumetric light, professional photograph, masterpiece, hyperdetailed, sharp focus, octane render, unreal engine, smooth, clear image"

# Terms that suggest a model is already high-quality (to avoid duplication)
QUALITY_KEYWORDS = ['high resolution', '8k', 'professional', 'photorealistic', 'detailed', 'cinematic']

def enhance_prompt(prompt):
    """Enhanced prompt system for high-quality general image generation."""
    original_prompt = prompt.strip()
    
    # 1. Clean the prompt (remove duplicates/trailing garbage)
    if original_prompt.count(original_prompt.split('.')[0]) > 1:
        parts = original_prompt.split('.')
        original_prompt = parts[0].strip()
        
    # 2. Check if quality tags are already present
    has_quality = any(keyword in original_prompt.lower() for keyword in QUALITY_KEYWORDS)
    
    enhanced = original_prompt
    
    # 3. Always add the high-quality descriptors if not present
    if not has_quality:
        enhanced += QUALITY_INJECT
        
    # 4. Add a Negative Prompt (crucial for quality)
    negative_prompt = "low quality, blurry, warped, distorted, low resolution, bad anatomy, deformed, worst quality, noise, grainy, signature, watermark"
    
    # Note: Hugging Face API models often use a separate parameter for negative prompts,
    # but some SD models can use a long prompt containing all details. For API compatibility, 
    # we'll keep the positive prompt clean and manage the negative prompt separately 
    # when calling the API, but inform the user here.
    
    return enhanced, negative_prompt

# Re-defining generate_detailed_placeholder using the code from the friend's file
def generate_detailed_placeholder(enhanced_prompt):
    """Generate a detailed placeholder that represents the prompt."""
    try:
        # Create a more sophisticated placeholder
        img = Image.new('RGB', (1024, 1024), color=(250, 250, 250))
        draw = ImageDraw.Draw(img)
        
        # Draw some abstract shapes
        draw.rectangle([0, 700, 1024, 1024], fill=(220, 220, 220))
        draw.rectangle([0, 0, 1024, 700], fill=(245, 245, 245))
        draw.rectangle([200, 500, 600, 650], fill=(100, 149, 237)) # Blue block
        draw.ellipse([700, 200, 900, 400], fill=(255, 165, 0)) # Orange circle

        # Add text overlay
        try:
            # Attempt to use a default font that is slightly larger
            font_large = ImageFont.load_default(size=40)
            font_small = ImageFont.load_default(size=20)
        except:
            font_large = font_small = None
        
        # Title
        title = "🖼 AI Image Generation Ready (High Quality Mode)"
        if font_large:
            # Need to get text size for centering
            text_width, text_height = draw.textsize(title, font=font_large)
            draw.text(((1024 - text_width) // 2, 50), title, fill=(50, 50, 50), font=font_large)
        
        # Enhanced prompt preview
        prompt_preview = f"Optimized Prompt: {enhanced_prompt[:50]}..."
        if font_small:
            text_width, text_height = draw.textsize(prompt_preview, font=font_small)
            draw.text(((1024 - text_width) // 2, 120), prompt_preview, fill=(80, 80, 80), font=font_small)
        
        # Status message
        status = "🎨 Image Generator Ready - Using General SDXL Model."
        if font_small:
            text_width, text_height = draw.textsize(status, font=font_small)
            draw.text(((1024 - text_width) // 2, 950), status, fill=(150, 150, 150), font=font_small)
        
        # Convert to base64
        img_buffer = io.BytesIO()
        img.save(img_buffer, format='PNG')
        img_buffer.seek(0)
        image_base64 = base64.b64encode(img_buffer.read()).decode('utf-8')
        
        return {
            'success': True,
            'image': f"data:image/png;base64,{image_base64}",
            'enhanced_prompt': enhanced_prompt,
            'demo_mode': True,
            'message': f"🖼 IMAGE READY: '{enhanced_prompt[:80]}...' - AI optimized for stunning visuals!"
        }
        
    except Exception as e:
        # Fallback to simple SVG if PIL fails
        return {
            'success': True,
            'image': "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTAyNCIgaGVpZ2h0PSIxMDI0IiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxyZWN0IHdpZHRoPSIxMDI0IiBoZWlnaHQ9IjEwMjQiIGZpbGw9IiNmMGYwZjAiLz48dGV4dCB4PSI1MTIiIHk9IjUxMiIgZm9udC1mYW1pbHk9IkFyaWFsIiBmb250LXNpemU9IjI0IiBmaWxsPSIjNjY2IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkeT0iLjNlbSI+R2VuZXJhdGlvbiBSZWFkeSAoR2VuZXJhbCBQcm9tcHQpPC90ZXh0Pjwvc3ZnPg==",
            'enhanced_prompt': enhanced_prompt,
            'demo_mode': True,
            'message': f"🖼 AI-optimized prompt ready for image generation: '{enhanced_prompt[:80]}...'"
        }

def generate_with_huggingface(prompt):
    """Generate image using the powerful SDXL model."""
    enhanced_prompt, negative_prompt = enhance_prompt(prompt)
    
    logging.info(f"Generating with prompt: {enhanced_prompt[:100]}...")
    
    # --- Primary Hugging Face SDXL Model ---
    try:
        headers = {
            "Authorization": f"Bearer {HF_API_TOKEN}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": enhanced_prompt,
            "parameters": {
                "negative_prompt": negative_prompt,
                "width": 1024,
                "height": 1024,
                "num_inference_steps": 50, # Higher steps for SDXL quality (Source 3.1)
                "guidance_scale": 7.5 # Standard for SDXL (Source 2.3)
            }
        }
        
        # Try the main API
        response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=90) # Increased timeout

        if response.status_code == 200 and response.content and 'image' in response.headers.get('Content-Type', ''):
            # Convert to base64 for display
            image_base64 = base64.b64encode(response.content).decode('utf-8')
            logging.info(f"Successfully generated image with Hugging Face SDXL ({len(response.content)} bytes)")
            return {
                'success': True,
                'image': f"data:image/png;base64,{image_base64}",
                'enhanced_prompt': enhanced_prompt,
                'model_used': 'SDXL-base-1.0 (Hugging Face)',
                'demo_mode': False
            }
        elif response.status_code == 402:
            logging.warning("API credits exceeded (402 Payment Required)")
            return {
                'success': False,
                'error': "API credits exhausted. Showing placeholder. Please check your HF token and/or credits.",
                'enhanced_prompt': enhanced_prompt
            }
        else:
            error_msg = f"HF API Error: {response.status_code} - {response.text[:100]}"
            logging.error(f"Generation failed: {error_msg}")

    except Exception as e:
        error_msg = f"Exception during Hugging Face SDXL generation: {str(e)}"
        logging.exception(error_msg)
        
    # --- Fallback: Show Placeholder to Confirm Prompt Enhancement ---
    logging.info("Falling back to Detailed Placeholder...")
    return generate_detailed_placeholder(enhanced_prompt)


@app.route('/')
def index():
    # Serve the frontend UI. Prefer a `templates/index.html` file so `render_template`
    # works in normal Flask setups. If that's not present (for example the repo
    # keeps `index.html` at project root, as in this repo), fall back to serving
    # the root-level `index.html` via send_from_directory. This makes the server
    # robust when deployed to platforms that run the Flask app as the runtime.
    try:
        templates_path = os.path.join(app.root_path, 'templates', 'index.html')
        root_index_path = os.path.join(app.root_path, 'index.html')

        if os.path.exists(templates_path):
            logging.info('Serving templates/index.html')
            return render_template('index.html')

        if os.path.exists(root_index_path):
            logging.info('Serving root index.html via send_from_directory')
            # send_from_directory requires the directory, so give the app root
            return send_from_directory(app.root_path, 'index.html')

        logging.info('No index.html found in templates/ or project root. Returning plain text status.')
        return "AI Image Generator Backend is Running. Use the /generate endpoint with a POST request."

    except Exception as e:
        logging.exception('Unexpected error when attempting to serve index.html')
        return "AI Image Generator Backend is Running. Use the /generate endpoint with a POST request."


@app.route('/generate_demo', methods=['POST'])
def generate_demo():
    """Return the detailed placeholder immediately without calling external APIs.

    Useful for testing client integrations and saving images locally when the HF API
    is unavailable or you prefer an offline demo response.
    """
    try:
        data = request.get_json() or {}
        prompt = data.get('prompt', 'Demo prompt: abstract scene')
        enhanced_prompt, _ = enhance_prompt(prompt)
        result = generate_detailed_placeholder(enhanced_prompt)
        # Ensure it's marked demo mode
        result['demo_mode'] = True
        return jsonify(result)
    except Exception as e:
        logging.exception('Error in /generate_demo')
        return jsonify({'success': False, 'error': str(e)})

@app.route('/generate', methods=['POST'])
def generate_image():
    try:
        data = request.get_json()
        prompt = data.get('prompt', '')
        
        if not prompt:
            return jsonify({'success': False, 'error': 'No prompt provided'})
        
        print(f"🎨 Received prompt: {prompt}")
        
        # Generate with the Hugging Face SDXL model
        result = generate_with_huggingface(prompt)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"❌ Error in generate_image: {str(e)}")
        # If any error occurs before API call, enhance the prompt and show placeholder
        enhanced_prompt, _ = enhance_prompt(prompt) 
        placeholder_result = generate_detailed_placeholder(enhanced_prompt)
        placeholder_result['success'] = False
        placeholder_result['error'] = f"Fatal server error: {str(e)}"
        return jsonify(placeholder_result)

@app.route('/health')
def health():
    return jsonify({'status': 'healthy', 'model': 'SDXL-base-1.0'})

if __name__ == '__main__':
    # Start the Flask development server for local testing.
    # Note: debug=True is intended for local development only.
    # Binding to 127.0.0.1 keeps the server local to this machine.
    app.run(debug=True, host='127.0.0.1', port=5000)
