from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import base64
import io
from typing import Optional
from huggingface_hub import InferenceClient, InferenceTimeoutError
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
CORS(app)

# ----------------------------------------------------------------------
# 🔧 REAL WORKING HuggingFace Model & Token
# ----------------------------------------------------------------------
HF_MODEL_ID = "black-forest-labs/FLUX.1-schnell"   # CORRECT model ID
HF_API_TOKEN = "hf_token"

hf_client: Optional[InferenceClient] = None

# ----------------------------------------------------------------------
# 🔥 Prompt Enhancer
# ----------------------------------------------------------------------
CATEGORY_KEYWORDS = {
    'interior design': ['living room', 'kitchen', 'bedroom', 'interior', 'furniture', 'apartment', 'office'],
    'character portrait': ['portrait', 'person', 'face', 'character', 'hero', 'villain', 'model', 'figure'],
    'landscape': ['landscape', 'mountain', 'forest', 'lake', 'valley', 'coast', 'skyline'],
    'fantasy scene': ['dragon', 'wizard', 'castle', 'magic', 'mythical', 'fantasy', 'sorcerer'],
    'sci-fi scene': ['cyberpunk', 'space', 'futuristic', 'robot', 'mech', 'alien', 'spaceship'],
    'product render': ['product', 'packaging', 'bottle', 'gadget', 'device', 'shoe', 'watch'],
    'vehicle render': ['car', 'vehicle', 'motorcycle', 'aircraft', 'spaceship', 'train'],
    'food photography': ['food', 'dish', 'meal', 'dessert', 'cuisine', 'plate'],
    'graphic design': ['poster', 'logo', 'typography', 'graphic design', 'layout', 'cover art'],
    'anime illustration': ['anime', 'manga', 'cel shading', 'chibi', '2d style']
}

CATEGORY_DESCRIPTORS = {
    'interior design': 'architectural lighting, styled furniture arrangement, cinematic wide angle, photorealistic materials',
    'character portrait': 'studio lighting, expressive pose, intricate facial details, cinematic depth of field',
    'landscape': 'epic composition, volumetric atmosphere, dramatic lighting, detailed environment',
    'fantasy scene': 'mythic atmosphere, rich world-building details, dramatic lighting, high fantasy realism',
    'sci-fi scene': 'futuristic materials, holographic accents, cinematic lighting, high-tech atmosphere',
    'product render': 'hero product shot, premium materials, immaculate studio lighting, sharp focus',
    'vehicle render': 'dynamic hero angle, motion detail, reflective surfaces, showroom lighting',
    'food photography': 'macro depth of field, appetizing styling, natural lighting, crisp detail',
    'graphic design': 'bold layout, balanced typography, print-ready composition, clean vector detail',
    'anime illustration': 'crisply inked lines, vibrant cel shading, expressive lighting, cinematic framing'
}

STYLE_KEYWORDS = {
    'photorealistic': ['photorealistic', 'photo', 'realistic', 'ultra realistic'],
    'cinematic': ['cinematic', 'epic', 'movie still', 'film still'],
    'watercolor': ['watercolor', 'ink wash', 'gouache'],
    'oil painting': ['oil painting', 'baroque', 'renaissance', 'impasto'],
    'digital art': ['digital art', 'concept art', 'matte painting', 'digital painting'],
    'low poly': ['low poly', 'isometric', '3d render'],
    'pixel art': ['pixel art', '8-bit', 'retro game'],
    'line art': ['line art', 'sketch', 'technical drawing']
}

STYLE_DESCRIPTORS = {
    'photorealistic': 'hyperreal detail, lifelike textures, precision optics, natural imperfections',
    'cinematic': 'anamorphic bokeh, storytelling lighting, dramatic color grading, film grain',
    'watercolor': 'fluid pigment diffusion, textured paper grain, layered washes, soft edges',
    'oil painting': 'rich brush strokes, classical lighting, layered pigments, gallery finish',
    'digital art': 'high-resolution digital painting, refined shading, concept art polish',
    'low poly': 'stylized facets, carefully simplified geometry, game-ready aesthetic',
    'pixel art': 'clean pixel clusters, color-limited palette, crisp dithering',
    'line art': 'precise line weight, technical accuracy, cross-hatching detail'
}

QUALITY_KEYWORDS = ['high resolution', '8k', 'ultra hd', 'photorealistic', 'professional', 'cinematic']

NEGATIVE_PROMPT = (
    "low quality, blurry, distorted, washed out, noisy, watermark, text overlay, malformed anatomy,"
    " bad proportions, low detail, overexposed, underexposed, amateur render"
)

def detect_category(prompt: str) -> Optional[str]:
    prompt_lower = prompt.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in prompt_lower for keyword in keywords):
            return category
    return None

def detect_style(prompt: str) -> Optional[str]:
    prompt_lower = prompt.lower()
    for style, keywords in STYLE_KEYWORDS.items():
        if any(keyword in prompt_lower for keyword in keywords):
            return style
    return None

def enhance_prompt(prompt: str) -> tuple[str, str]:
    original = prompt.strip()
    category = detect_category(original)
    style = detect_style(original)

    parts = [original]

    if category:
        parts.append(CATEGORY_DESCRIPTORS[category])
    if style:
        parts.append(STYLE_DESCRIPTORS[style])

    parts.append("ultra high resolution, global illumination, sharp detail, physically-based rendering")

    return ", ".join(parts), NEGATIVE_PROMPT

# ----------------------------------------------------------------------
# 🔥 FIXED Image Generation (num_steps <= 16)
# ----------------------------------------------------------------------
def generate_with_huggingface(prompt: str) -> dict:
    enhanced_prompt, negative_prompt = enhance_prompt(prompt)

    global hf_client
    try:
        if hf_client is None:
            hf_client = InferenceClient(
                model=HF_MODEL_ID,
                token=HF_API_TOKEN
            )

        image = hf_client.text_to_image(
            prompt=enhanced_prompt,
            negative_prompt=negative_prompt,
            guidance_scale=4.0,
            num_inference_steps=12,   # ✅ FIXED (Nebius limit = 16)
            width=1024,
            height=1024
        )

        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        image_bytes = base64.b64encode(buffer.getvalue()).decode("utf-8")

        return {
            "success": True,
            "image": "data:image/png;base64," + image_bytes,
            "enhanced_prompt": enhanced_prompt,
            "model_used": HF_MODEL_ID,
            "demo_mode": False
        }

    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "enhanced_prompt": enhanced_prompt,
            "model_used": "Error/Fallback Mode",
            "demo_mode": True
        }

# ----------------------------------------------------------------------
# 🌐 Flask Routes
# ----------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/generate", methods=["POST"])
def generate_image():
    data = request.get_json() or {}
    prompt = data.get("prompt", "").strip()

    if not prompt:
        return jsonify({"success": False, "error": "No prompt provided"}), 400

    return jsonify(generate_with_huggingface(prompt))

@app.route("/health")
def health():
    return jsonify({"status": "healthy", "model": HF_MODEL_ID})

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5001)
