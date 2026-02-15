/**
 * BrushBunni Admin JS
 * - Drag & drop reorder for events, photos, notes
 * - Tab-style filtering for event status
 */

(function() {
    'use strict';

    // =========================================================================
    // DRAG & DROP — Generic for any list with .drag-handle elements
    // =========================================================================

    function initDragDrop() {
        const resultTable = document.querySelector('#result_list tbody');
        if (!resultTable) return;

        let dragRow = null;

        resultTable.querySelectorAll('.drag-handle').forEach(handle => {
            const row = handle.closest('tr');
            if (!row) return;

            row.setAttribute('draggable', 'true');

            row.addEventListener('dragstart', function(e) {
                dragRow = this;
                this.classList.add('dragging');
                e.dataTransfer.effectAllowed = 'move';
                e.dataTransfer.setData('text/plain', '');
            });

            row.addEventListener('dragend', function() {
                this.classList.remove('dragging');
                resultTable.querySelectorAll('.drag-over').forEach(el =>
                    el.classList.remove('drag-over'));
                dragRow = null;
            });

            row.addEventListener('dragover', function(e) {
                e.preventDefault();
                e.dataTransfer.dropEffect = 'move';
                if (this !== dragRow) {
                    resultTable.querySelectorAll('.drag-over').forEach(el =>
                        el.classList.remove('drag-over'));
                    this.classList.add('drag-over');
                }
            });

            row.addEventListener('dragleave', function() {
                this.classList.remove('drag-over');
            });

            row.addEventListener('drop', function(e) {
                e.preventDefault();
                this.classList.remove('drag-over');
                if (dragRow && dragRow !== this) {
                    const rows = Array.from(resultTable.querySelectorAll('tr'));
                    const dragIdx = rows.indexOf(dragRow);
                    const dropIdx = rows.indexOf(this);

                    if (dragIdx < dropIdx) {
                        this.parentNode.insertBefore(dragRow, this.nextSibling);
                    } else {
                        this.parentNode.insertBefore(dragRow, this);
                    }

                    saveOrder();
                }
            });
        });
    }

    function saveOrder() {
        const handles = document.querySelectorAll('#result_list .drag-handle');
        const ids = Array.from(handles).map(h => parseInt(h.dataset.id)).filter(id => !isNaN(id));

        if (ids.length === 0) return;

        // Determine which reorder endpoint to use based on current URL
        let endpoint = 'reorder/';
        const path = window.location.pathname;
        if (path.includes('/bbnote/')) {
            endpoint = 'reorder/';  // BBNote reorder
        }

        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value
            || getCookie('csrftoken');

        fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({ order: ids }),
        })
        .then(r => r.json())
        .then(data => {
            if (data.status === 'ok') {
                showToast('Order saved');
            }
        })
        .catch(err => console.error('Reorder error:', err));
    }


    // =========================================================================
    // TAB-STYLE STATUS FILTER
    // =========================================================================

    function initStatusTabs() {
        // Only on event changelist
        if (!window.location.pathname.includes('/event/')) return;

        const changelist = document.getElementById('changelist');
        if (!changelist) return;

        // Check if tabs already exist
        if (document.querySelector('.bb-tabs')) return;

        const params = new URLSearchParams(window.location.search);
        const currentStatus = params.get('status') || 'all';

        const tabs = document.createElement('div');
        tabs.className = 'bb-tabs';

        const tabData = [
            { label: 'All Events', value: 'all' },
            { label: 'Previous', value: 'past' },
            { label: 'Upcoming', value: 'upcoming' },
        ];

        tabData.forEach(t => {
            const a = document.createElement('a');
            a.className = 'bb-tab' + (currentStatus === t.value ? ' active' : '');
            a.textContent = t.label;
            if (t.value === 'all') {
                a.href = window.location.pathname;
            } else {
                a.href = window.location.pathname + '?status=' + t.value;
            }
            tabs.appendChild(a);
        });

        // Insert before the result table
        const toolbar = changelist.querySelector('.toolbar') ||
                        changelist.querySelector('#toolbar') ||
                        changelist.querySelector('form');
        if (toolbar) {
            toolbar.parentNode.insertBefore(tabs, toolbar);
        } else {
            changelist.prepend(tabs);
        }
    }


    // =========================================================================
    // PHOTO INLINE DRAG & DROP (on edit form)
    // =========================================================================

    function initPhotoInlineDrag() {
        const inlineGroup = document.querySelector('.tabular.inline-related');
        if (!inlineGroup) return;

        const tbody = inlineGroup.querySelector('tbody');
        if (!tbody) return;

        const rows = tbody.querySelectorAll('tr.form-row:not(.empty-form)');
        if (rows.length < 2) return;

        let dragRow = null;

        rows.forEach(row => {
            // Add a drag handle to each row
            const firstTd = row.querySelector('td');
            if (firstTd && !firstTd.querySelector('.photo-drag')) {
                const handle = document.createElement('span');
                handle.className = 'drag-handle photo-drag';
                handle.textContent = '⋮⋮';
                handle.style.marginRight = '8px';
                firstTd.prepend(handle);
            }

            row.setAttribute('draggable', 'true');

            row.addEventListener('dragstart', function(e) {
                dragRow = this;
                this.style.opacity = '0.4';
                e.dataTransfer.effectAllowed = 'move';
            });

            row.addEventListener('dragend', function() {
                this.style.opacity = '1';
                tbody.querySelectorAll('.drag-over').forEach(el =>
                    el.classList.remove('drag-over'));
            });

            row.addEventListener('dragover', function(e) {
                e.preventDefault();
                if (this !== dragRow) {
                    tbody.querySelectorAll('.drag-over').forEach(el =>
                        el.classList.remove('drag-over'));
                    this.classList.add('drag-over');
                }
            });

            row.addEventListener('drop', function(e) {
                e.preventDefault();
                this.classList.remove('drag-over');
                if (dragRow && dragRow !== this) {
                    const allRows = Array.from(tbody.querySelectorAll('tr.form-row:not(.empty-form)'));
                    const dragIdx = allRows.indexOf(dragRow);
                    const dropIdx = allRows.indexOf(this);
                    if (dragIdx < dropIdx) {
                        this.parentNode.insertBefore(dragRow, this.nextSibling);
                    } else {
                        this.parentNode.insertBefore(dragRow, this);
                    }
                }
            });
        });
    }


    // =========================================================================
    // UTILITIES
    // =========================================================================

    function getCookie(name) {
        const cookies = document.cookie.split(';');
        for (let c of cookies) {
            c = c.trim();
            if (c.startsWith(name + '=')) {
                return decodeURIComponent(c.substring(name.length + 1));
            }
        }
        return '';
    }

    function showToast(msg) {
        const toast = document.createElement('div');
        toast.textContent = msg;
        toast.style.cssText = `
            position: fixed; bottom: 24px; right: 24px; z-index: 9999;
            background: #333; color: white; padding: 12px 24px;
            border-radius: 8px; font-size: 14px; font-weight: 500;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            animation: fadeIn 0.3s, fadeOut 0.3s 1.7s;
        `;
        document.body.appendChild(toast);
        setTimeout(() => toast.remove(), 2000);

        // Inject animation if not present
        if (!document.querySelector('#bb-toast-style')) {
            const style = document.createElement('style');
            style.id = 'bb-toast-style';
            style.textContent = `
                @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
                @keyframes fadeOut { from { opacity: 1; } to { opacity: 0; } }
            `;
            document.head.appendChild(style);
        }
    }


    // =========================================================================
    // INIT
    // =========================================================================

    document.addEventListener('DOMContentLoaded', function() {
        initDragDrop();
        initStatusTabs();
        initPhotoInlineDrag();
    });

})();
