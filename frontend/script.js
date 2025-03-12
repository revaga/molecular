// document.getElementById('pdf-form').addEventListener('submit', async function(e) {
//     e.preventDefault();
    
//     const fileInput = document.getElementById('pdf-file');
//     const file = fileInput.files[0];
    
//     if (file && file.type === 'application/pdf') {
//         try {
//             await uploadPDF(file);
//         } catch (error) {
//             alert('Error processing PDF: ' + error.message);
//         }
//     } else {
//         alert('Please upload a valid PDF file.');
//     }
// });

// async function uploadPDF(file) {
//     const formData = new FormData();
//     formData.append('file', file);

//     try {
//         const response = await fetch('/api/upload', {
//             method: 'POST',
//             body: formData
//         });

//         if (!response.ok) {
//             throw new Error('Upload failed: ' + response.statusText);
//         }

//         const data = await response.json();
//         displaySegments(data.segments);
//     } catch (error) {
//         console.error('Upload error:', error);
//         throw error;
//     }
// }

// function displaySegments(segments) {
//     // Clear any existing content
//     const contentDisplay = document.getElementById('content-display');
//     contentDisplay.innerHTML = '';

//     // Display each segment
//     segments.forEach(segment => {
//         const chunkElement = document.createElement('div');
//         chunkElement.classList.add('content-chunk');
//         chunkElement.textContent = segment;
//         contentDisplay.appendChild(chunkElement);
//     });
// }


// Add collapsible functionality
document.addEventListener('click', function(e) {
    if (e.target.classList.contains('collapsible')) {
        e.target.classList.toggle('active');
        const content = e.target.nextElementSibling;
        if (content.style.maxHeight) {
            content.style.maxHeight = null;
        } else {
            content.style.maxHeight = content.scrollHeight + 'px';
        }
    }
});

// Update upload function
document.getElementById('uploadBtn').addEventListener('click', async () => {
    const fileInput = document.getElementById('fileInput').files[0];
    const resultsDiv = document.getElementById('results');
    
    // Show loader
    resultsDiv.innerHTML = '<div class="loader"></div>';
    
    let formData = new FormData();
    formData.append('file', fileInput);
    
    try {
        let response = await fetch('http://localhost/api/upload', {
            method: 'POST',
            body: formData
        });
        
        let result = await response.json();
        
        // Render results
        resultsDiv.innerHTML = result.entities.map(entity => `
            <div class="entity">
                <h3>${entity.name}</h3>
                <div class="confidence-bar">
                    <div class="confidence-level" style="width: ${entity.confidence * 100}%"></div>
                </div>
                <div>
                    MY: ${entity.my.toFixed(2)} 
                    MN: ${entity.mn.toFixed(2)}
                    <span class="uncertainty-indicator ${getUncertaintyClass(entity.hesitancy)}"></span>
                </div>
                ${entity.guidelines ? `
                <div class="guideline">
                    <button class="collapsible">Guidelines</button>
                    <div class="content">
                        <p>${entity.guidelines}</p>
                        ${entity.context ? `<p class="context">Context: ${entity.context}</p>` : ''}
                    </div>
                </div>` : ''}
            </div>
        `).join('');
    } catch (error) {
        resultsDiv.innerHTML = `<div class="error">Error: ${error.message}</div>`;
    }
});

// Helper function for uncertainty indicator
function getUncertaintyClass(hesitancy) {
    if (hesitancy < 0.3) return 'low-uncertainty';
    if (hesitancy < 0.7) return 'medium-uncertainty';
    return 'high-uncertainty';
}