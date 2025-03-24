document.getElementById('pdf-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('pdf-file');
    const file = fileInput.files[0];
    const contentDisplay = document.getElementById('content-display');
    
    if (!file || file.type !== 'application/pdf') {
        alert('Please upload a valid PDF file.');
        return;
    }
    
    // Show loading state
    contentDisplay.innerHTML = '<div class="loading">Processing PDF...</div>';
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }
        
        const data = await response.json();
        
        // Display results
        contentDisplay.innerHTML = `
            <div class="results-container">
                <div class="text-segments">
                    <h2>Extracted Text Segments (${data.segment_count})</h2>
                    <div class="segments">
                        ${data.text_segments.map((segment, index) => `
                            <div class="segment">
                                <h3>Segment ${index + 1}</h3>
                                <p>${segment}</p>
                            </div>
                        `).join('')}
                    </div>
                </div>
                
                <div class="entities-container">
                    <h2>Extracted Entities</h2>
                    <div class="entities">
                        ${data.entities.map(entity => `
                            <div class="entity ${entity.type.toLowerCase()}">
                                <h3>${entity.text}</h3>
                                <div class="entity-details">
                                    <p>Type: ${entity.type}</p>
                                    <p>Confidence: ${(entity.confidence * 100).toFixed(1)}%</p>
                                    <p>Membership (MY): ${(entity.MY * 100).toFixed(1)}%</p>
                                    <p>Non-Membership (MN): ${(entity.MN * 100).toFixed(1)}%</p>
                                    <p>Hesitancy: ${(entity.hesitancy * 100).toFixed(1)}%</p>
                                    <p>Linguistic Term: ${entity.linguistic_term}</p>
                                </div>
                                ${entity.type === 'GENE' || entity.type === 'PROTEIN' || entity.type === 'PATHWAY' ? `
                                    <button onclick="getGuidelines('${entity.text}')" class="guidelines-btn">
                                        Get Guidelines
                                    </button>
                                ` : ''}
                            </div>
                        `).join('')}
                    </div>
                </div>
            </div>
        `;
        
    } catch (error) {
        contentDisplay.innerHTML = `<div class="error">Error: ${error.message}</div>`;
        console.error('Upload error:', error);
    }
});

async function getGuidelines(targetName) {
    try {
        const response = await fetch(`/api/guidelines/${encodeURIComponent(targetName)}`);
        if (!response.ok) {
            throw new Error('Failed to fetch guidelines');
        }
        
        const data = await response.json();
        const guidelinesModal = document.createElement('div');
        guidelinesModal.className = 'modal';
        guidelinesModal.innerHTML = `
            <div class="modal-content">
                <h2>Handling Guidelines for ${targetName}</h2>
                <p>${data.guidelines}</p>
                <button onclick="this.closest('.modal').remove()">Close</button>
            </div>
        `;
        document.body.appendChild(guidelinesModal);
        
    } catch (error) {
        alert(`Error fetching guidelines: ${error.message}`);
    }
}