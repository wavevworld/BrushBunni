/**
 * BrushBunni Admin - Strapi Features JavaScript
 * =============================================
 * 
 * Strapi Content Manager features:
 * - Drag & drop reordering for repeatable components
 * - Media preview interactions
 * - Entry title auto-generation
 */

document.addEventListener('DOMContentLoaded', function() {
    
    // =========================================================================
    // DRAG & DROP REORDERING (Strapi: Repeatable Component)
    // =========================================================================
    
    /**
     * Initialize drag-drop for photo inline rows
     * Strapi behavior: Click and hold drag handle, drag to position, release
     */
    function initDragDrop() {
        const inlineRows = document.querySelectorAll('.tabular tbody tr');
        
        inlineRows.forEach(row => {
            const dragHandle = row.querySelector('.strapi-drag-handle');
            if (!dragHandle) return;
            
            // Make row draggable when handle is used
            dragHandle.addEventListener('mousedown', function(e) {
                row.setAttribute('draggable', 'true');
                row.classList.add('strapi-dragging');
            });
            
            row.addEventListener('dragstart', function(e) {
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/plain', row.rowIndex);
                row.classList.add('strapi-drag-source');
                
                // Slight delay for visual feedback
                setTimeout(() => {
                    row.style.opacity = '0.4';
                }, 0);
            });
            
            row.addEventListener('dragend', function(e) {
                row.setAttribute('draggable', 'false');
                row.classList.remove('strapi-dragging', 'strapi-drag-source');
                row.style.opacity = '1';
                
                // Remove all drag-over indicators
                document.querySelectorAll('.strapi-drag-over').forEach(el => {
                    el.classList.remove('strapi-drag-over');
                });
            });
            
            row.addEventListener('dragover', function(e) {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
                
                if (!row.classList.contains('strapi-drag-source')) {
                    row.classList.add('strapi-drag-over');
                }
            });
            
            row.addEventListener('dragleave', function(e) {
                row.classList.remove('strapi-drag-over');
            });
            
            row.addEventListener('drop', function(e) {
                e.preventDefault();
                row.classList.remove('strapi-drag-over');
                
                const sourceIndex = parseInt(e.dataTransfer.getData('text/plain'));
                const targetIndex = row.rowIndex;
                
                if (sourceIndex !== targetIndex) {
                    const tbody = row.parentNode;
                    const sourceRow = tbody.rows[sourceIndex - 1];
                    
                    if (sourceIndex < targetIndex) {
                        tbody.insertBefore(sourceRow, row.nextSibling);
                    } else {
                        tbody.insertBefore(sourceRow, row);
                    }
                    
                    // Update order fields
                    updateOrderFields(tbody);
                }
            });
        });
    }
    
    /**
     * Update hidden order fields after reordering
     */
    function updateOrderFields(tbody) {
        const rows = tbody.querySelectorAll('tr');
        rows.forEach((row, index) => {
            const orderInput = row.querySelector('input[name$="-order"]');
            if (orderInput) {
                orderInput.value = (index + 1) * 10;
            }
        });
    }
    
    // Initialize drag-drop
    initDragDrop();
    
    // Re-initialize when Django admin adds new inline rows
    const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
            if (mutation.addedNodes.length) {
                initDragDrop();
            }
        });
    });
    
    const inlineGroups = document.querySelectorAll('.inline-group');
    inlineGroups.forEach(group => {
        observer.observe(group, { childList: true, subtree: true });
    });
    
    // =========================================================================
    // ENTRY TITLE AUTO-UPPERCASE (Strapi: UID Field)
    // =========================================================================
    
    const entryTitleInput = document.querySelector('input[name="name"]');
    if (entryTitleInput) {
        entryTitleInput.addEventListener('input', function(e) {
            // Auto-uppercase for UID-style field
            const cursorPos = e.target.selectionStart;
            e.target.value = e.target.value.toUpperCase();
            e.target.setSelectionRange(cursorPos, cursorPos);
        });
        
        // Validate on blur - ensure it's a valid code
        entryTitleInput.addEventListener('blur', function(e) {
            let value = e.target.value.trim();
            // Replace spaces with hyphens
            value = value.replace(/\s+/g, '-');
            // Remove invalid characters
            value = value.replace(/[^A-Z0-9\-]/g, '');
            e.target.value = value;
        });
    }
    
    // =========================================================================
    // MEDIA PREVIEW INTERACTIONS
    // =========================================================================
    
    /**
     * Strapi: Click media preview to open full-size
     */
    const mediaPreviews = document.querySelectorAll('.strapi-media-preview');
    mediaPreviews.forEach(preview => {
        preview.addEventListener('click', function(e) {
            // Already handled by href, but we can add lightbox here
        });
    });
    
    // =========================================================================
    // FEATURED TOGGLE (Quick action)
    // =========================================================================
    
    /**
     * Toggle featured status via star click
     */
    document.querySelectorAll('.strapi-featured, .strapi-not-featured').forEach(star => {
        star.style.cursor = 'pointer';
        star.title = 'Click to toggle featured';
        
        star.addEventListener('click', function(e) {
            // Find the checkbox in this row
            const row = e.target.closest('tr');
            if (!row) return;
            
            const checkbox = row.querySelector('input[name$="-is_featured"]');
            if (checkbox) {
                checkbox.checked = !checkbox.checked;
                
                // Update visual
                if (checkbox.checked) {
                    e.target.textContent = '⭐';
                    e.target.className = 'strapi-featured';
                } else {
                    e.target.textContent = '☆';
                    e.target.className = 'strapi-not-featured';
                }
            }
        });
    });
    
    // =========================================================================
    // COLLAPSE SECTIONS (Strapi: Accordion)
    // =========================================================================
    
    document.querySelectorAll('fieldset.collapse h2').forEach(header => {
        header.addEventListener('click', function(e) {
            const fieldset = e.target.closest('fieldset');
            if (fieldset) {
                fieldset.classList.toggle('collapsed');
            }
        });
    });
    
    // =========================================================================
    // MEDIA DROPZONE ENHANCEMENT
    // =========================================================================
    
    const dropzone = document.querySelector('.strapi-media-input');
    if (dropzone) {
        const dropzoneContainer = dropzone.parentElement;
        
        // Add visual feedback for drag-over
        ['dragenter', 'dragover'].forEach(eventName => {
            dropzoneContainer.addEventListener(eventName, function(e) {
                e.preventDefault();
                dropzone.style.borderColor = '#4945ff';
                dropzone.style.background = '#f0f0ff';
            });
        });
        
        ['dragleave', 'drop'].forEach(eventName => {
            dropzoneContainer.addEventListener(eventName, function(e) {
                e.preventDefault();
                dropzone.style.borderColor = '';
                dropzone.style.background = '';
            });
        });
        
        // Show file count when files selected
        dropzone.addEventListener('change', function(e) {
            const count = e.target.files.length;
            if (count > 0) {
                // Find or create status text
                let status = dropzoneContainer.querySelector('.strapi-upload-status');
                if (!status) {
                    status = document.createElement('div');
                    status.className = 'strapi-upload-status';
                    status.style.marginTop = '8px';
                    status.style.fontSize = '13px';
                    status.style.color = '#4945ff';
                    dropzoneContainer.appendChild(status);
                }
                status.textContent = `✓ ${count} file(s) selected`;
            }
        });
    }
    
    // =========================================================================
    // STATUS DOT TOOLTIPS
    // =========================================================================
    
    document.querySelectorAll('.strapi-status-dot').forEach(dot => {
        dot.style.cursor = 'help';
    });
    
    // =========================================================================
    // ADD CSS FOR DRAG STATES
    // =========================================================================
    
    const dragStyles = document.createElement('style');
    dragStyles.textContent = `
        .strapi-dragging {
            background: #f0f0ff !important;
        }
        
        .strapi-drag-over {
            border-top: 2px solid #4945ff !important;
        }
        
        .strapi-drag-source {
            opacity: 0.4;
        }
        
        .strapi-drag-handle {
            cursor: grab;
        }
        
        .strapi-drag-handle:active {
            cursor: grabbing;
        }
    `;
    document.head.appendChild(dragStyles);
    
    console.log('BrushBunni Strapi Admin initialized');
});
