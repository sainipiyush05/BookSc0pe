// Upload functionality
document.getElementById('uploadForm').addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData(this);
    const statusDiv = document.getElementById('uploadStatus');
    
    statusDiv.innerHTML = '<div class="alert alert-info">Uploading and indexing document...</div>';
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (response.ok) {
            statusDiv.innerHTML = `<div class="alert alert-success">
                Document uploaded successfully! 
                <br>Book ID: ${result.book_id}
                <br>Words indexed: ${result.words_indexed}
            </div>`;
            this.reset();
        } else {
            statusDiv.innerHTML = `<div class="alert alert-danger">Error: ${result.error}</div>`;
        }
    } catch (error) {
        statusDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    }
});

// Search functionality
document.getElementById('searchBtn').addEventListener('click', performSearch);
document.getElementById('searchQuery').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        performSearch();
    }
});

async function performSearch() {
    const query = document.getElementById('searchQuery').value.trim();
    const resultsDiv = document.getElementById('searchResults');
    
    if (!query) {
        resultsDiv.innerHTML = '<div class="alert alert-warning">Please enter a search query.</div>';
        return;
    }
    
    resultsDiv.innerHTML = '<div class="alert alert-info">Searching...</div>';
    
    try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}&limit=20`);
        const result = await response.json();
        
        if (response.ok) {
            displaySearchResults(result);
        } else {
            resultsDiv.innerHTML = `<div class="alert alert-danger">Error: ${result.error}</div>`;
        }
    } catch (error) {
        resultsDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    }
}

function displaySearchResults(result) {
    const resultsDiv = document.getElementById('searchResults');
    
    if (result.total_results === 0) {
        resultsDiv.innerHTML = '<div class="alert alert-info">No results found for your search query.</div>';
        return;
    }
    
    let html = `<h4>Search Results (${result.total_results} found)</h4>`;
    
    result.results.forEach(item => {
        html += `
            <div class="result-item">
                <h5>${item.title}</h5>
                <p><strong>Author:</strong> ${item.author}</p>
                <p><strong>Found on pages:</strong> <span class="page-numbers">${item.pages.join(', ')}</span></p>
                <p><strong>Total matches:</strong> ${item.total_matches}</p>
                <p><strong>Keywords found:</strong> ${item.keywords_found.join(', ')}</p>
                <p><strong>Relevance score:</strong> ${item.relevance_score}</p>
            </div>
        `;
    });
    
    resultsDiv.innerHTML = html;
}
