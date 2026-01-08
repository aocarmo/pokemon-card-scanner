// Configuration
let API_URL = localStorage.getItem('apiUrl') || 'http://192.168.1.100:5000';
let inventory = JSON.parse(localStorage.getItem('inventory') || '[]');

// Elements
const video = document.getElementById('video');
const canvas = document.getElementById('canvas');
const startCameraBtn = document.getElementById('startCamera');
const captureBtn = document.getElementById('capture');
const uploadBtn = document.getElementById('uploadBtn');
const fileInput = document.getElementById('fileInput');
const resultSection = document.getElementById('resultSection');
const loading = document.getElementById('loading');

// Camera
let stream = null;

startCameraBtn.addEventListener('click', async () => {
    try {
        stream = await navigator.mediaDevices.getUserMedia({ 
            video: { facingMode: 'environment' } 
        });
        video.srcObject = stream;
        video.style.display = 'block';
        startCameraBtn.style.display = 'none';
        captureBtn.style.display = 'inline-block';
    } catch (err) {
        alert('Erro ao acessar câmera: ' + err.message);
    }
});

captureBtn.addEventListener('click', () => {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);
    
    canvas.toBlob(blob => {
        processImage(blob);
    }, 'image/jpeg', 0.8);
});

uploadBtn.addEventListener('click', () => {
    fileInput.click();
});

fileInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) {
        processImage(file);
    }
});

async function processImage(blob) {
    loading.style.display = 'flex';
    
    try {
        // Convert to base64
        const base64 = await blobToBase64(blob);
        
        // Call API
        const response = await fetch(`${API_URL}/predict`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ image: base64.split(',')[1] })
        });
        
        if (!response.ok) throw new Error('API error');
        
        const result = await response.json();
        
        // Show result
        displayResult(result, blob);
        
    } catch (err) {
        alert('Erro ao processar imagem: ' + err.message);
    } finally {
        loading.style.display = 'none';
    }
}

function displayResult(result, imageBlob) {
    document.getElementById('cardName').textContent = result.nome;
    document.getElementById('cardCollection').textContent = result.colecao;
    document.getElementById('cardNumber').textContent = result.numero;
    document.getElementById('confidence').textContent = (result.confianca * 100).toFixed(1) + '%';
    
    const img = document.getElementById('capturedImage');
    img.src = URL.createObjectURL(imageBlob);
    
    resultSection.style.display = 'block';
    resultSection.dataset.result = JSON.stringify(result);
}

document.getElementById('addToInventory').addEventListener('click', () => {
    const result = JSON.parse(resultSection.dataset.result);
    
    // Check if card exists
    const existing = inventory.find(c => 
        c.nome === result.nome && 
        c.colecao === result.colecao && 
        c.numero === result.numero
    );
    
    if (existing) {
        existing.quantidade++;
    } else {
        inventory.push({
            ...result,
            quantidade: 1,
            adicionado: new Date().toISOString()
        });
    }
    
    saveInventory();
    updateInventoryDisplay();
    alert('✓ Carta adicionada ao estoque!');
});

function saveInventory() {
    localStorage.setItem('inventory', JSON.stringify(inventory));
}

function updateInventoryDisplay() {
    const list = document.getElementById('inventoryList');
    const total = inventory.reduce((sum, c) => sum + c.quantidade, 0);
    
    document.getElementById('totalCards').textContent = `(${total} cartas)`;
    
    if (inventory.length === 0) {
        list.innerHTML = '<p class="empty">Nenhuma carta no estoque</p>';
        return;
    }
    
    list.innerHTML = inventory.map(card => `
        <div class="inventory-item">
            <div>
                <strong>${card.nome}</strong>
                <small>${card.colecao} #${card.numero}</small>
            </div>
            <div class="quantity">
                <button onclick="changeQuantity('${card.nome}', -1)">-</button>
                <span>${card.quantidade}</span>
                <button onclick="changeQuantity('${card.nome}', 1)">+</button>
            </div>
        </div>
    `).join('');
}

window.changeQuantity = (nome, delta) => {
    const card = inventory.find(c => c.nome === nome);
    if (card) {
        card.quantidade += delta;
        if (card.quantidade <= 0) {
            inventory = inventory.filter(c => c.nome !== nome);
        }
        saveInventory();
        updateInventoryDisplay();
    }
};

document.getElementById('exportCSV').addEventListener('click', () => {
    const csv = [
        'Nome,Coleção,Número,Quantidade,Adicionado',
        ...inventory.map(c => 
            `"${c.nome}","${c.colecao}","${c.numero}",${c.quantidade},"${c.adicionado}"`
        )
    ].join('\n');
    
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `pokemon-inventory-${Date.now()}.csv`;
    a.click();
});

document.getElementById('clearInventory').addEventListener('click', () => {
    if (confirm('Limpar todo o estoque?')) {
        inventory = [];
        saveInventory();
        updateInventoryDisplay();
    }
});

document.getElementById('saveSettings').addEventListener('click', () => {
    API_URL = document.getElementById('apiUrl').value;
    localStorage.setItem('apiUrl', API_URL);
    alert('✓ Configurações salvas!');
});

// Helpers
function blobToBase64(blob) {
    return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(blob);
    });
}

// Initialize
document.getElementById('apiUrl').value = API_URL;
updateInventoryDisplay();
