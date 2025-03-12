document.getElementById('pdf-form').addEventListener('submit', function(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('pdf-file');
    const file = fileInput.files[0];
    
    if (file && file.type === 'application/pdf') {
        readPDF(file);
    } else {
        alert('Please upload a valid PDF file.');
    }
});

async function readPDF(file) {
    const pdf = await pdfjsLib.getDocument(URL.createObjectURL(file)).promise;
    const totalPages = pdf.numPages;
    let fullText = '';

    // Extract text from each page
    for (let pageNum = 1; pageNum <= totalPages; pageNum++) {
        const page = await pdf.getPage(pageNum);
        const textContent = await page.getTextContent();
        
        textContent.items.forEach(item => {
            fullText += item.str + ' ';
        });
    }

    // Once we have all the text, chunk and display
    chunkAndDisplayText(fullText);
}

function chunkAndDisplayText(text) {
    const words = text.split(/\s+/); // Split text into words
    const chunkSize = 50; // 50 words per chunk
    let currentChunk = '';

    // Clear any existing content
    const contentDisplay = document.getElementById('content-display');
    contentDisplay.innerHTML = '';

    // Process and display chunks
    for (let i = 0; i < words.length; i++) {
        currentChunk += words[i] + ' ';
        
        if ((i + 1) % chunkSize === 0 || i === words.length - 1) {
            const chunkElement = document.createElement('div');
            chunkElement.classList.add('content-chunk');
            chunkElement.textContent = currentChunk;
            contentDisplay.appendChild(chunkElement);
            
            // Clear current chunk and add a slight delay for smooth animation
            currentChunk = '';
        }
    }
}
