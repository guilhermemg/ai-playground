let selectedPapers = new Set(); // Keep track of displayed papers
let currentMode = 'search';

function switchMode(mode) {
    currentMode = mode;
    
    // Update buttons
    document.querySelectorAll('.mode-button').forEach(btn => {
        if (btn.dataset.mode === mode) {
            btn.classList.add('active');
        } else {
            btn.classList.remove('active');
        }
    });

    // Update content visibility
    document.getElementById('searchMode').style.display = mode === 'search' ? 'block' : 'none';
    document.getElementById('chatMode').style.display = mode === 'chat' ? 'block' : 'none';

    if (mode === 'chat') {
        // Clear chat messages
        document.getElementById('chatMessages').innerHTML = '';
        
        // Update paper selections
        document.querySelectorAll('.paper-item').forEach(paper => {
            const paperId = paper.dataset.paperId;
            paper.classList.remove('active');
            
            // Restore selected class if paper is in selectedPapers
            if (selectedPapers.has(paperId)) {
                paper.classList.add('selected');
            }
        });
        
        // Render selected papers in chat mode
        renderSelectedPapers();
    } else {
        // In search mode, keep the selected papers in the Set but remove visual selection
        document.querySelectorAll('.paper-item').forEach(paper => {
            paper.classList.remove('selected');
        });
    }

    // Update search section visibility
    const searchSection = document.querySelector('.search-section');
    if (searchSection) {
        searchSection.style.display = mode === 'search' ? 'block' : 'none';
    }
}

function attachPaperHandlers() {
    document.querySelectorAll('.paper-item').forEach(item => {
        const paperId = item.getAttribute('data-paper-id');
        if (!paperId) {
            console.warn('Paper item found without ID:', item);
            return;
        }

        // Remove any existing click listener first to prevent duplicates
        item.removeEventListener('click', handlePaperClick);
        // Add the click listener
        item.addEventListener('click', handlePaperClick);
    });
}

async function handlePaperClick(e) {
    const item = e.currentTarget;
    const paperId = item.dataset.paperId;
    const paperTitle = item.dataset.title;
    
    console.log('Paper clicked:', paperId, 'Current mode:', currentMode);
    
    if (currentMode === 'chat') {
        // In chat mode, handle paper selection
        if (selectedPapers.has(paperId)) {
            // Deselect paper
            selectedPapers.delete(paperId);
            item.classList.remove('selected');
            removePaperFromChatSelection(paperId);
        } else {
            // Select paper
            selectedPapers.add(paperId);
            item.classList.add('selected');
            addPaperToChatSelection(paperId, paperTitle);
        }
        console.log('Selected papers after click:', Array.from(selectedPapers));
    } else {
        // In search mode, handle paper summary
        // Remove active class from all papers
        document.querySelectorAll('.paper-item').forEach(p => p.classList.remove('active'));
        item.classList.add('active');
        
        const summaryDiv = document.getElementById('selectedPaperSummary');
        
        // Create a new div for this paper's summary
        const paperSummaryId = `paper-summary-${paperId}`;
        if (!document.getElementById(paperSummaryId)) {
            const newSummaryDiv = document.createElement('div');
            newSummaryDiv.id = paperSummaryId;
            newSummaryDiv.className = 'summary-card';
            newSummaryDiv.innerHTML = `
                <div class="spinner"></div>
                <div class="loading-message">Loading...</div>
            `;
            summaryDiv.appendChild(newSummaryDiv);
            summaryDiv.style.display = 'grid';
            
            try {
                const response = await fetch(`/paper_summary/${paperId}`);
                if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
                const data = await response.json();
                
                if (data.error) {
                    newSummaryDiv.innerHTML = `
                        <button class="close-button" onclick="removeSummary('${paperSummaryId}')">×</button>
                        <div class="error-message">${data.summary}</div>
                    `;
                } else {
                    newSummaryDiv.innerHTML = `
                        <button class="close-button" onclick="removeSummary('${paperSummaryId}')">×</button>
                        <h3>${data.title}</h3>
                        <p><strong>Authors:</strong> ${data.authors.join(', ')}</p>
                        <p><strong>Summary:</strong> ${data.summary}</p>
                        <p><strong>Published:</strong> ${data.published ? new Date(data.published).toLocaleDateString() : 'N/A'}</p>
                        ${data.categories ? `
                            <div class="paper-categories">
                                ${data.categories.map(cat => `<span class="category-tag">${cat}</span>`).join(' ')}
                            </div>
                        ` : ''}
                        <p>
                            ${data.url ? `<a href="${data.url}" target="_blank">View on arXiv</a>` : ''}
                            ${data.pdf_url ? ` | <a href="${data.pdf_url}" target="_blank">Download PDF</a>` : ''}
                        </p>
                    `;
                }
            } catch (error) {
                newSummaryDiv.innerHTML = `
                    <button class="close-button" onclick="removeSummary('${paperSummaryId}')">×</button>
                    <div class="error-message">
                        Error loading paper summary.<br>
                        <small>${error.message}</small>
                    </div>
                `;
            }
        }
    }
}

function removeSummary(summaryId) {
    const summaryElement = document.getElementById(summaryId);
    if (summaryElement) {
        summaryElement.remove();
        
        // Hide the container if no summaries left
        const summaryContainer = document.getElementById('selectedPaperSummary');
        if (!summaryContainer.children.length) {
            summaryContainer.style.display = 'none';
        }
    }
}

// Attach handlers on page load
attachPaperHandlers();

async function searchPapers() {
    const searchInput = document.getElementById('searchInput');
    const resultsDiv = document.getElementById('results');
    const searchButton = document.querySelector('.search-button');
    const searchSource = document.querySelector('input[name="searchSource"]:checked').value;
    
    try {
        searchButton.classList.add('loading');
        searchButton.textContent = 'Searching...';
        
        const response = await fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                topic: searchInput.value,
                search_type: searchSource
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.message);
        }
        
        // Check if we have any results
        if (data.papers.length === 0) {
            resultsDiv.innerHTML = `
                <div class="no-results">
                    <p>No papers found for "${searchInput.value}" in ${searchSource} search.</p>
                    <p class="suggestion">Try:</p>
                    <ul>
                        <li>Using different keywords</li>
                        <li>Checking your spelling</li>
                        ${searchSource !== 'both' ? `<li>Searching in "Both" sources</li>` : ''}
                    </ul>
                </div>
            `;
            return;
        }
        
        // Display results
        resultsDiv.innerHTML = `
            <div class="search-results-actions">
                <input type="checkbox" id="selectAll" onchange="toggleAllPapers(this)">
                <label for="selectAll">Select All</label>
                <select id="collectionSelect" class="collection-select">
                    ${collections.map(c => `
                        <option value="${c.id}">${c.name}</option>
                    `).join('')}
                </select>
                <button onclick="downloadAndAddToCollection()" class="add-to-collection-btn">
                    Download & Add to Collection
                </button>
            </div>
            ${data.papers.map(paper => `
                <div class="paper-summary ${paper.source}">
                    <div class="paper-source">${paper.source === 'arxiv' ? 'arXiv' : 'Local'}</div>
                    <input type="checkbox" 
                            class="paper-checkbox" 
                            data-paper-id="${paper.source === 'arxiv' ? paper.entry_id : paper.id}"
                            data-paper-title="${paper.title}"
                            data-paper-source="${paper.source}"
                            ${paper.source === 'arxiv' ? `data-paper-url="${paper.pdf_url}"` : ''}>
                            <h3>${paper.title}</h3>
                    <p><strong>Authors:</strong> ${Array.isArray(paper.authors) ? paper.authors.join(', ') : paper.authors}</p>
                    <p><strong>${paper.source === 'arxiv' ? 'Abstract' : 'Summary'}:</strong> ${paper.summary}</p>
                    <p><strong>Published:</strong> ${paper.published ? new Date(paper.published).toLocaleDateString() : 'N/A'}</p>
                    ${paper.categories ? `
                        <p><strong>Categories:</strong> ${Array.isArray(paper.categories) ? paper.categories.join(', ') : paper.categories}</p>
                    ` : ''}
                    <p>
                        ${paper.source === 'arxiv' ? `
                            <a href="${paper.entry_id}" target="_blank">View on arXiv</a>
                            | <a href="${paper.pdf_url}" target="_blank">View PDF</a>
                        ` : `
                            <a href="${paper.url}" target="_blank">View on arXiv</a>
                            ${paper.pdf_url ? `| <a href="${paper.pdf_url}" target="_blank">View PDF</a>` : ''}
                        `}
                    </p>
                </div>
            `).join('')}
        `;
        
    } catch (error) {
        console.error('Error:', error);
        resultsDiv.innerHTML = `<p class="error-message">Error searching papers: ${error.message}</p>`;
    } finally {
        searchButton.classList.remove('loading');
        searchButton.textContent = 'Search';
    }
}

async function downloadAndAddToCollection() {
    const selectedCollection = document.getElementById('collectionSelect').value;
    const selectedPapers = Array.from(document.querySelectorAll('.paper-checkbox:checked')).map(checkbox => ({
        id: checkbox.dataset.paperId,
        title: checkbox.dataset.paperTitle,
        url: checkbox.dataset.paperUrl
    }));

    if (selectedPapers.length === 0) {
        alert('Please select at least one paper');
        return;
    }

    const targetCollection = collections.find(c => c.id === selectedCollection);
    if (!targetCollection) return;

    // Show loading state
    const addButton = document.querySelector('.add-to-collection-btn');
    const originalText = addButton.textContent;
    addButton.disabled = true;
    addButton.textContent = 'Downloading...';

    try {
        // Download and process each selected paper
        for (const paper of selectedPapers) {
            addButton.textContent = `Processing ${paper.title}...`;
            
            // Only process if not already in collection
            if (!targetCollection.papers.find(p => p.id === paper.id)) {
                const response = await fetch(`/process_paper/${paper.id}`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(paper)
                });

                if (response.ok) {
                    const processedPaper = await response.json();
                    targetCollection.papers.push(processedPaper);
                }
            }
        }

        // Save and update UI
        saveCollections();
        renderCollections();
        
        // Clear checkboxes
        document.getElementById('selectAll').checked = false;
        document.querySelectorAll('.paper-checkbox').forEach(box => box.checked = false);
        
        alert(`Added ${selectedPapers.length} papers to "${targetCollection.name}"`);

    } catch (error) {
        console.error('Error:', error);
        alert('Error processing papers. Please try again.');
    } finally {
        // Reset button state
        addButton.disabled = false;
        addButton.textContent = originalText;
    }
}

// Handle enter key in search input
document.getElementById('searchInput').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        searchPapers();
    }
});

// Initialize collections from localStorage
let collections = JSON.parse(localStorage.getItem('collections')) || [];

function addCollection() {
    const name = prompt('Enter collection name:');
    if (!name) return;

    const newCollection = {
        id: 'collection_' + Date.now(),
        name: name,
        papers: []
    };

    collections.push(newCollection);
    saveCollections();
    renderCollections();
}

function renderCollections() {
    const userCollectionsDiv = document.getElementById('userCollections');
    if (!userCollectionsDiv) {
        console.error('User collections container not found');
        return;
    }

    userCollectionsDiv.innerHTML = collections.map(collection => `
        <div class="collection" data-collection-id="${collection.id}">
            <div class="collection-header" onclick="toggleCollection(this)">
                <div class="collection-title">
                    <span class="expand-icon">▶</span>
                    <h3>${collection.name}</h3>
                </div>
                <div class="collection-actions">
                    <span class="paper-count">${collection.papers.length}</span>
                    <button class="collection-action-btn" onclick="renameCollection('${collection.id}', event)">✏️</button>
                    <button class="collection-action-btn delete-collection-btn" onclick="deleteCollection('${collection.id}', event)">🗑️</button>
                </div>
            </div>
            <div class="collection-papers" 
                 ondrop="drop(event)" 
                 ondragover="allowDrop(event)"
                 data-collection-id="${collection.id}">
                ${collection.papers.map(paper => `
                    <div class="paper-item" 
                         data-paper-id="${paper.id}"
                         data-title="${paper.title}"
                         draggable="true"
                         ondragstart="drag(event)">
                        <div class="paper-title">${paper.title}</div>
                    </div>
                `).join('')}
            </div>
        </div>
    `).join('');
    
    // Re-attach paper handlers after rendering collections
    attachPaperHandlers();
}

function saveCollections() {
    localStorage.setItem('collections', JSON.stringify(collections));
}

function initializeCollections() {
    // Load collections from localStorage
    collections = JSON.parse(localStorage.getItem('collections')) || [];
    renderCollections();
}

// Make sure collections are initialized when the page loads
document.addEventListener('DOMContentLoaded', () => {
    addStyles();
    initializeCollections();
    attachPaperHandlers();
    switchMode('search'); // Set initial mode
});

// Update the toggleCollection function
function toggleCollection(header) {
    const collection = header.closest('.collection');
    if (collection) {
        collection.classList.toggle('expanded');
        const expandIcon = header.querySelector('.expand-icon');
        if (expandIcon) {
            expandIcon.style.transform = collection.classList.contains('expanded') ? 'rotate(90deg)' : 'rotate(0deg)';
        }
    }
}

// Update the delete and rename functions
function deleteCollection(collectionId, event) {
    event.stopPropagation();
    if (confirm('Are you sure you want to delete this collection?')) {
        collections = collections.filter(c => c.id !== collectionId);
        saveCollections();
        renderCollections();
    }
}

function renameCollection(collectionId, event) {
    event.stopPropagation();
    const collection = collections.find(c => c.id === collectionId);
    if (collection) {
        const newName = prompt('Enter new name:', collection.name);
        if (newName && newName.trim()) {
            collection.name = newName.trim();
            saveCollections();
            renderCollections();
        }
    }
}

// Drag and Drop handlers
function allowDrop(ev) {
    ev.preventDefault();
    ev.currentTarget.classList.add('drag-over');
}

function drag(ev) {
    const paperItem = ev.target.closest('.paper-item');
    const paperId = paperItem.dataset.paperId;
    const paperTitle = paperItem.dataset.title;
    
    const paperData = {
        id: paperId,
        title: paperTitle
    };
    
    ev.dataTransfer.setData('text/plain', JSON.stringify(paperData));
}

function drop(ev) {
    ev.preventDefault();
    ev.currentTarget.classList.remove('drag-over');
    
    const paperData = JSON.parse(ev.dataTransfer.getData('text/plain'));
    const targetCollectionId = ev.currentTarget.dataset.collectionId;
    
    if (targetCollectionId === 'all') return; // Can't drop into "All Papers"
    
    const targetCollection = collections.find(c => c.id === targetCollectionId);
    if (targetCollection && !targetCollection.papers.find(p => p.id === paperData.id)) {
        targetCollection.papers.push(paperData);
        saveCollections();
        renderCollections();
    }
}

// Add these new functions
function toggleAllPapers(checkbox) {
    const paperCheckboxes = document.querySelectorAll('.paper-checkbox');
    paperCheckboxes.forEach(box => box.checked = checkbox.checked);
}

// Add Font Awesome for icons
const link = document.createElement('link');
link.rel = 'stylesheet';
link.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css';
document.head.appendChild(link);

// Chat functionality
function sendMessage() {
    const input = document.querySelector('.chat-input');
    const message = input.value.trim();
    if (!message) return;

    // Add user message
    addMessage(message, 'user');

    // Clear input
    input.value = '';

    // TODO: Send message to backend and get response
    // For now, just add a dummy response
    setTimeout(() => {
        addMessage('This is a placeholder response. Backend integration needed.', 'assistant');
    }, 1000);
}

function addMessage(text, type) {
    const messagesContainer = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    messageDiv.textContent = text;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function addPaperToChatSelection(paperId, paperTitle) {
    const selectedPapersDiv = document.getElementById('selectedPapersForChat');
    if (!selectedPapersDiv) {
        console.error('Selected papers container not found');
        return;
    }

    // Remove existing paper if it's already there
    const existingPaper = selectedPapersDiv.querySelector(`[data-paper-id="${paperId}"]`);
    if (existingPaper) {
        existingPaper.remove();
    }

    const paperDiv = document.createElement('div');
    paperDiv.className = 'selected-paper';
    paperDiv.dataset.paperId = paperId;
    paperDiv.innerHTML = `
        <span class="paper-title">${paperTitle}</span>
        <button class="remove-paper" onclick="removePaperFromSelection('${paperId}')">
            <i class="fas fa-times"></i>
        </button>
    `;
    selectedPapersDiv.appendChild(paperDiv);
    updateSelectedPapersCount();
}

function removePaperFromSelection(paperId) {
    console.log('Removing paper:', paperId);
    
    // Remove from Set
    selectedPapers.delete(paperId);
    
    // Remove from selected papers display in chat
    const paperElement = document.querySelector(`.selected-paper[data-paper-id="${paperId}"]`);
    if (paperElement) {
        paperElement.remove();
    }
    
    // Remove selected class from ALL matching papers in the collections panel
    document.querySelectorAll(`.paper-item[data-paper-id="${paperId}"]`).forEach(paper => {
        paper.classList.remove('selected');
    });
    
    updateSelectedPapersCount();
    console.log('Selected papers after removal:', Array.from(selectedPapers));
}

function removePaperFromChatSelection(paperId) {
    const paperElement = document.querySelector(`.selected-paper[data-paper-id="${paperId}"]`);
    if (paperElement) {
        paperElement.remove();
    }
}

function renderSelectedPapers() {
    const selectedPapersDiv = document.getElementById('selectedPapersForChat');
    if (!selectedPapersDiv) {
        console.error('Selected papers container not found');
        return;
    }
    
    // Clear existing papers
    selectedPapersDiv.innerHTML = '';
    
    // Iterate through selectedPapers Set and find corresponding paper elements
    selectedPapers.forEach(paperId => {
        const paperElement = document.querySelector(`.paper-item[data-paper-id="${paperId}"]`);
        if (paperElement) {
            const paperTitle = paperElement.dataset.title;
            addPaperToChatSelection(paperId, paperTitle);
        }
    });
}

function updateSelectedPapersCount() {
    const count = selectedPapers.size;
    const countElement = document.getElementById('selectedPapersCount');
    if (countElement) {
        countElement.textContent = count.toString();
    }
    console.log('Updated paper count:', count);
}

// Add CSS to show selected state
function addStyles() {
    const style = document.createElement('style');
    style.textContent = `
        .paper-item {
            cursor: pointer;
            transition: background-color 0.2s;
        }
        
        .paper-item:hover {
            background-color: #f5f5f5;
        }
        
        .paper-item.selected {
            background-color: #e3f2fd;
            border-left: 3px solid #1976d2;
        }
        
        .selected-paper {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 12px;
            margin-bottom: 8px;
            background-color: #e3f2fd;
            border-radius: 4px;
            border-left: 3px solid #1976d2;
        }
    `;
    document.head.appendChild(style);
} 

