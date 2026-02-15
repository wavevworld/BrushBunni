/**
 * Photo Drag & Drop Reorder
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // Find photo inline table
    const table = document.querySelector('.inline-group .tabular tbody');
    if (!table) return;
    
    let draggedRow = null;
    
    // Add drag events to existing rows
    function initDragDrop() {
        const rows = table.querySelectorAll('tr.has_original');
        
        rows.forEach(row => {
            row.draggable = true;
            
            // Drag start
            row.addEventListener('dragstart', function(e) {
                draggedRow = this;
                this.classList.add('dragging');
                e.dataTransfer.effectAllowed = 'move';
            });
            
            // Drag end
            row.addEventListener('dragend', function() {
                this.classList.remove('dragging');
                table.querySelectorAll('tr').forEach(r => r.classList.remove('drag-over'));
                draggedRow = null;
                
                // Save new order
                saveOrder();
            });
            
            // Drag over
            row.addEventListener('dragover', function(e) {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
                
                if (this !== draggedRow) {
                    table.querySelectorAll('tr').forEach(r => r.classList.remove('drag-over'));
                    this.classList.add('drag-over');
                }
            });
            
            // Drop
            row.addEventListener('drop', function(e) {
                e.preventDefault();
                
                if (this !== draggedRow && draggedRow) {
                    // Determine position
                    const allRows = [...table.querySelectorAll('tr.has_original')];
                    const draggedIdx = allRows.indexOf(draggedRow);
                    const targetIdx = allRows.indexOf(this);
                    
                    if (draggedIdx < targetIdx) {
                        this.parentNode.insertBefore(draggedRow, this.nextSibling);
                    } else {
                        this.parentNode.insertBefore(draggedRow, this);
                    }
                }
                
                this.classList.remove('drag-over');
            });
        });
        
        // Also allow drag by handle
        const handles = table.querySelectorAll('.drag-handle');
        handles.forEach(handle => {
            handle.addEventListener('mousedown', function() {
                this.closest('tr').draggable = true;
            });
        });
    }
    
    // Save order via AJAX
    function saveOrder() {
        const rows = table.querySelectorAll('tr.has_original');
        const order = [];
        
        rows.forEach((row, idx) => {
            const handle = row.querySelector('.drag-handle');
            if (handle && handle.dataset.id) {
                order.push(parseInt(handle.dataset.id));
                
                // Also update hidden order field if exists
                const orderField = row.querySelector('input[name$="-order"]');
                if (orderField) {
                    orderField.value = idx * 10;
                }
            }
        });
        
        // Send to server
        if (order.length > 0) {
            fetch('/admin/blog/event/reorder-photos/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCSRFToken()
                },
                body: JSON.stringify({ order: order })
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'ok') {
                    showMessage('Order saved', 'success');
                }
            })
            .catch(err => {
                console.error('Failed to save order:', err);
            });
        }
    }
    
    // Get CSRF token
    function getCSRFToken() {
        const cookie = document.cookie
            .split('; ')
            .find(row => row.startsWith('csrftoken='));
        return cookie ? cookie.split('=')[1] : '';
    }
    
    // Show temporary message
    function showMessage(text, type) {
        const existing = document.querySelector('.drag-message');
        if (existing) existing.remove();
        
        const msg = document.createElement('div');
        msg.className = 'drag-message';
        msg.textContent = '✓ ' + text;
        msg.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #10b981;
            color: white;
            padding: 10px 16px;
            border-radius: 6px;
            font-size: 13px;
            font-weight: 500;
            z-index: 9999;
            animation: fadeIn 0.2s;
        `;
        document.body.appendChild(msg);
        
        setTimeout(() => msg.remove(), 2000);
    }
    
    // Initialize
    initDragDrop();
    
    // Re-init if rows added dynamically
    const observer = new MutationObserver(() => initDragDrop());
    observer.observe(table, { childList: true });
    
    console.log('Photo drag & drop ready');
});
