/* ===================================================================
   BrushBunni Admin - JavaScript
   =================================================================== */

(function() {
    'use strict';
    
    // Wait for DOM to be ready
    document.addEventListener('DOMContentLoaded', function() {
        initEventDragAndDrop();
        initPhotoDragAndDrop();
        initPhotoDelete();
    });
    
    
    /* ================================================================
       EVENT DRAG AND DROP - Reorder events in list view
       ================================================================ */
    
    function initEventDragAndDrop() {
        const tbody = document.querySelector('#result_list tbody');
        if (!tbody) return;
        
        const rows = tbody.querySelectorAll('tr');
        if (rows.length === 0) return;
        
        rows.forEach(row => {
            const handle = row.querySelector('.drag-handle');
            if (!handle) return;
            
            // Make row draggable via handle
            handle.addEventListener('mousedown', function() {
                row.setAttribute('draggable', 'true');
            });
            
            handle.addEventListener('mouseup', function() {
                row.setAttribute('draggable', 'false');
            });
            
            // Drag events
            row.addEventListener('dragstart', handleEventDragStart);
            row.addEventListener('dragover', handleEventDragOver);
            row.addEventListener('drop', handleEventDrop);
            row.addEventListener('dragend', handleEventDragEnd);
        });
    }
    
    let draggedEventRow = null;
    
    function handleEventDragStart(e) {
        draggedEventRow = this;
        this.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
    }
    
    function handleEventDragOver(e) {
        if (e.preventDefault) {
            e.preventDefault();
        }
        
        e.dataTransfer.dropEffect = 'move';
        
        const afterElement = getDragAfterElement(this.parentElement, e.clientY);
        
        if (afterElement == null) {
            this.parentElement.appendChild(draggedEventRow);
        } else {
            this.parentElement.insertBefore(draggedEventRow, afterElement);
        }
        
        return false;
    }
    
    function handleEventDrop(e) {
        if (e.stopPropagation) {
            e.stopPropagation();
        }
        return false;
    }
    
    function handleEventDragEnd(e) {
        this.classList.remove('dragging');
        
        // Get new order
        const tbody = document.querySelector('#result_list tbody');
        const rows = tbody.querySelectorAll('tr');
        const eventIds = [];
        
        rows.forEach(row => {
            const handle = row.querySelector('.drag-handle');
            if (handle) {
                const id = handle.getAttribute('data-id');
                if (id) {
                    eventIds.push(id);
                }
            }
        });
        
        // Save order to server
        saveEventOrder(eventIds);
    }
    
    function getDragAfterElement(container, y) {
        const draggableElements = [...container.querySelectorAll('tr:not(.dragging)')];
        
        return draggableElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect();
            const offset = y - box.top - box.height / 2;
            
            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child };
            } else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element;
    }
    
    function saveEventOrder(eventIds) {
        fetch('/admin/blog/event/reorder/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ order: eventIds })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                console.log('✓ Event order saved');
            } else {
                console.error('Failed to save order:', data.message);
            }
        })
        .catch(error => {
            console.error('Error saving order:', error);
        });
    }
    
    
    /* ================================================================
       PHOTO DRAG AND DROP - Reorder photos in inline
       ================================================================ */
    
    function initPhotoDragAndDrop() {
        const photoTable = document.querySelector('.inline-group tbody');
        if (!photoTable) return;
        
        const rows = photoTable.querySelectorAll('tr');
        if (rows.length === 0) return;
        
        rows.forEach(row => {
            const handle = row.querySelector('.photo-drag-handle');
            if (!handle) return;
            
            // Make row draggable via handle
            handle.addEventListener('mousedown', function() {
                row.setAttribute('draggable', 'true');
            });
            
            handle.addEventListener('mouseup', function() {
                row.setAttribute('draggable', 'false');
            });
            
            // Drag events
            row.addEventListener('dragstart', handlePhotoDragStart);
            row.addEventListener('dragover', handlePhotoDragOver);
            row.addEventListener('drop', handlePhotoDrop);
            row.addEventListener('dragend', handlePhotoDragEnd);
        });
    }
    
    let draggedPhotoRow = null;
    
    function handlePhotoDragStart(e) {
        draggedPhotoRow = this;
        this.classList.add('dragging');
        e.dataTransfer.effectAllowed = 'move';
    }
    
    function handlePhotoDragOver(e) {
        if (e.preventDefault) {
            e.preventDefault();
        }
        
        e.dataTransfer.dropEffect = 'move';
        
        const afterElement = getDragAfterElement(this.parentElement, e.clientY);
        
        if (afterElement == null) {
            this.parentElement.appendChild(draggedPhotoRow);
        } else {
            this.parentElement.insertBefore(draggedPhotoRow, afterElement);
        }
        
        return false;
    }
    
    function handlePhotoDrop(e) {
        if (e.stopPropagation) {
            e.stopPropagation();
        }
        return false;
    }
    
    function handlePhotoDragEnd(e) {
        this.classList.remove('dragging');
        
        // Get new order
        const tbody = this.parentElement;
        const rows = tbody.querySelectorAll('tr');
        const photoIds = [];
        
        rows.forEach(row => {
            const handle = row.querySelector('.photo-drag-handle');
            if (handle) {
                const id = handle.getAttribute('data-photo-id');
                if (id) {
                    photoIds.push(id);
                }
            }
        });
        
        // Save order to server
        savePhotoOrder(photoIds);
    }
    
    function savePhotoOrder(photoIds) {
        fetch('/admin/blog/event/reorder-photos/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ order: photoIds })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                console.log('✓ Photo order saved');
            } else {
                console.error('Failed to save photo order:', data.message);
            }
        })
        .catch(error => {
            console.error('Error saving photo order:', error);
        });
    }
    
    
    /* ================================================================
       PHOTO DELETE - Red cross button functionality
       ================================================================ */
    
    function initPhotoDelete() {
        const deleteButtons = document.querySelectorAll('.photo-delete-btn');
        
        deleteButtons.forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();
                
                const photoId = this.getAttribute('data-photo-id');
                if (!photoId) return;
                
                // Confirm deletion
                if (!confirm('Delete this photo?')) {
                    return;
                }
                
                // Delete photo
                deletePhoto(photoId, this);
            });
        });
    }
    
    function deletePhoto(photoId, button) {
        fetch('/admin/blog/event/delete-photo/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({ photo_id: photoId })
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'ok') {
                // Remove the row from DOM
                const row = button.closest('tr');
                if (row) {
                    row.style.opacity = '0';
                    row.style.transform = 'scale(0.8)';
                    row.style.transition = 'all 0.3s ease';
                    
                    setTimeout(() => {
                        row.remove();
                        console.log('✓ Photo deleted');
                    }, 300);
                }
            } else {
                alert('Failed to delete photo: ' + (data.message || 'Unknown error'));
            }
        })
        .catch(error => {
            console.error('Error deleting photo:', error);
            alert('Error deleting photo. Please try again.');
        });
    }
    
    
    /* ================================================================
       UTILITY FUNCTIONS
       ================================================================ */
    
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    
})();
