document.addEventListener('DOMContentLoaded', function() {
    const modal = document.getElementById('guidelines-modal');
    const closeBtn = document.querySelector('.close');
    
    // Close modal when clicking X
    closeBtn.onclick = function() {
        modal.style.display = "none";
    }
    
    // Close modal when clicking outside
    window.onclick = function(event) {
        if (event.target == modal) {
            modal.style.display = "none";
        }
    }
});

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
    contentDisplay.innerHTML = '<div class="loading">Processing document...</div>';
    
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
        displayResults(data);
        updateMetrics(data.metrics);
        
    } catch (error) {
        contentDisplay.innerHTML = `
            <div class="error">
                Error: ${error.message}
            </div>
        `;
    }
});

function displayResults(data) {
    const contentDisplay = document.getElementById('content-display');
    
    let html = '<div class="results-container">';
    
    // Display entities with PFS metrics
    html += '<div class="entities-section">';
    html += '<h2>Extracted Entities</h2>';
    
    data.entities.forEach(entity => {
        html += `
            <div class="entity ${entity.entity_type.toLowerCase()}">
                <div class="entity-header">
                    <h3>${entity.text}</h3>
                    <span class="entity-type ${entity.entity_type.toLowerCase()}">${entity.entity_type}</span>
                </div>
                
                <div class="pfs-metrics">
                    <div class="pfs-metric">
                        <h4>Membership</h4>
                        <span>${(entity.my * 100).toFixed(1)}%</span>
                    </div>
                    <div class="pfs-metric">
                        <h4>Non-membership</h4>
                        <span>${(entity.mn * 100).toFixed(1)}%</span>
                    </div>
                    <div class="pfs-metric">
                        <h4>Hesitancy</h4>
                        <span>${(entity.hesitancy * 100).toFixed(1)}%</span>
                    </div>
                </div>
                
                <button onclick="showGuidelines('${entity.text}', '${entity.entity_type}')" class="guidelines-btn">
                    View Guidelines
                </button>
            </div>
        `;
    });
    
    html += '</div>';
    contentDisplay.innerHTML = html;
}

async function showGuidelines(targetName, entityType) {
    const modal = document.getElementById('guidelines-modal');
    const content = document.getElementById('guidelines-content');
    
    // Show loading state
    content.innerHTML = '<div class="loading">Generating guidelines...</div>';
    modal.style.display = "block";
    
    try {
        const response = await fetch(`/api/guidelines?target=${encodeURIComponent(targetName)}&type=${encodeURIComponent(entityType)}`);
        const data = await response.json();
        
        content.innerHTML = `
            <h3>${targetName}</h3>
            <div class="guidelines-text">
                ${data.guidelines}
            </div>
        `;
    } catch (error) {
        content.innerHTML = `<div class="error">Error generating guidelines: ${error.message}</div>`;
    }
}

function updateMetrics(metrics) {
    document.getElementById('precision-value').textContent = `${(metrics.precision * 100).toFixed(1)}%`;
    document.getElementById('recall-value').textContent = `${(metrics.recall * 100).toFixed(1)}%`;
    document.getElementById('f1-value').textContent = `${(metrics.f1 * 100).toFixed(1)}%`;
}