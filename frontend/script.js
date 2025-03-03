document.getElementById('pdf-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('pdf-file');
    const file = fileInput.files[0];
    
    if (file && file.type === 'application/pdf') {
        try {
            await uploadPDF(file);
        } catch (error) {
            alert('Error processing PDF: ' + error.message);
        }
    } else {
        alert('Please upload a valid PDF file.');
    }
});

async function uploadPDF(file) {
    const formData = new FormData();
    formData.append('file', file);

    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error('Upload failed: ' + response.statusText);
        }

        const data = await response.json();
        displaySegments(data.segments);
    } catch (error) {
        console.error('Upload error:', error);
        throw error;
    }
}

function displaySegments(segments) {
    // Clear any existing content
    const contentDisplay = document.getElementById('content-display');
    contentDisplay.innerHTML = '';

    // Display each segment
    segments.forEach(segment => {
        const chunkElement = document.createElement('div');
        chunkElement.classList.add('content-chunk');
        chunkElement.textContent = segment;
        contentDisplay.appendChild(chunkElement);
    });
}
