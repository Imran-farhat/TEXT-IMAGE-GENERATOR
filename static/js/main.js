document.getElementById('promptForm').addEventListener('submit', async function(e) {
    e.preventDefault();

    const prompt = document.getElementById('promptInput').value.trim();
    const button = document.getElementById('generateButton');
    const status = document.getElementById('statusMessage');
    const imageContainer = document.getElementById('imageContainer');
    const promptInfo = document.getElementById('promptInfo');
    
    if (!prompt) {
        status.textContent = "Please enter a prompt!";
        return;
    }

    // Reset display
    status.innerHTML = 'Sending request to AI... This may take up to 90 seconds.';
    button.disabled = true;
    button.textContent = 'Generating... (Please Wait)';
    imageContainer.innerHTML = '';
    promptInfo.style.display = 'none';

    try {
        const response = await fetch('/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ prompt: prompt })
        });

        const data = await response.json();

        if (data.success) {
            status.textContent = data.message || "Image generated successfully!";
            
            const img = document.createElement('img');
            img.id = 'imageOutput';
            img.src = data.image;
            img.alt = data.enhanced_prompt.substring(0, 50) + '...';
            imageContainer.appendChild(img);
            
            // Display prompt info
            document.getElementById('enhancedPromptText').textContent = data.enhanced_prompt;
            document.getElementById('modelUsedText').textContent = data.model_used || 'Unknown/Fallback';
            promptInfo.style.display = 'block';

        } else {
            status.innerHTML = `<span class="error">Generation Failed:</span> ${data.error || 'Unknown error occurred.'}`;
            if (data.enhanced_prompt) {
                 document.getElementById('enhancedPromptText').textContent = data.enhanced_prompt;
                 document.getElementById('modelUsedText').textContent = 'Error/Fallback Mode';
                 promptInfo.style.display = 'block';
            }
            if (data.image) {
                const img = document.createElement('img');
                img.id = 'imageOutput';
                img.src = data.image;
                img.alt = 'Placeholder Image';
                imageContainer.appendChild(img);
            }
        }
    } catch (error) {
        status.innerHTML = `<span class="error">Network Error:</span> Could not connect to the Flask server. Is app.py running?`;
        console.error('Fetch error:', error);
    } finally {
        button.disabled = false;
        button.textContent = 'Generate Image';
    }
});
