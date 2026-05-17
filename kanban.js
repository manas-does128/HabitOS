/* ===== HabitOS Task Progress JS ===== */
let draggedId = null;
const STATUSES = ['todo','started','in_progress','done'];

function allowDrop(e) {
    e.preventDefault();
    e.currentTarget.classList.add('drag-over');
}

function drag(e, id) {
    draggedId = id;
    e.dataTransfer.setData('text/plain', id);
    setTimeout(() => {
        const el = document.getElementById(`task-${id}`);
        if (el) el.classList.add('dragging');
    }, 0);
}

function drop(e, status) {
    e.preventDefault();
    document.querySelectorAll('.kanban-col').forEach(c => c.classList.remove('drag-over'));
    const id = e.dataTransfer.getData('text/plain') || draggedId;
    if (!id) return;
    const card = document.getElementById(`task-${id}`);
    if (!card) return;
    card.classList.remove('dragging');
    const targetCol = document.getElementById(`col-${status}`);
    if (targetCol) {
        targetCol.appendChild(card);
        // add drop animation
        card.classList.add('drop-anim');
        setTimeout(() => card.classList.remove('drop-anim'), 400);
    }
    updateCounts();
    fetch(`/tasks/update/${id}`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({status})
    });
}

document.querySelectorAll('.kanban-col').forEach(col => {
    col.addEventListener('dragleave', e => {
        if (!col.contains(e.relatedTarget)) col.classList.remove('drag-over');
    });
});

function updateCounts() {
    STATUSES.forEach(s => {
        const col = document.getElementById(`col-${s}`);
        const cnt = document.getElementById(`count-${s}`);
        if (col && cnt) cnt.textContent = col.children.length;
    });
}

function showAddTask() { document.getElementById('addTaskModal').classList.add('active'); }

function addTask() {
    const title = document.getElementById('taskTitle').value.trim();
    if (!title) { alert('Please enter a task title.'); return; }
    const formData = new FormData();
    formData.append('title', title);
    formData.append('description', document.getElementById('taskDesc').value.trim());
    formData.append('priority', document.getElementById('taskPriority').value);
    formData.append('due_date', document.getElementById('taskDue').value);
    fetch('/tasks/add', {method:'POST', body: formData})
    .then(r => r.json())
    .then(data => {
        if (data.status === 'ok') { closeModal('addTaskModal'); location.reload(); }
    });
}

function deleteTask(id) {
    if (!confirm('Delete this task?')) return;
    fetch(`/tasks/delete/${id}`, {method:'POST'})
    .then(r => r.json())
    .then(() => {
        const card = document.getElementById(`task-${id}`);
        if (card) { card.classList.add('removing'); setTimeout(() => { card.remove(); updateCounts(); }, 300); }
    });
}

function showModal(id) { document.getElementById(id).classList.add('active'); }
function closeModal(id) {
    document.getElementById(id).classList.remove('active');
    ['taskTitle','taskDesc','taskDue'].forEach(f => { const el=document.getElementById(f); if(el) el.value=''; });
}
document.querySelectorAll('.modal-overlay').forEach(m =>
    m.addEventListener('click', e => { if(e.target===m) m.classList.remove('active'); }));
