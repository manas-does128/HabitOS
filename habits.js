/* ===== HabitOS Habits JS ===== */

// Calendar heatmap modal
function showCalendar(habitId, habitName) {
  fetch(`/habits/calendar/${habitId}`)
    .then(r => r.json())
    .then(data => {
      renderHeatmap(data.completions, habitName);
      showModal('calendarModal');
    });
}

function renderHeatmap(completions, name) {
  const container = document.getElementById('heatmapContainer');
  if (!container) return;
  container.innerHTML = `<h4 style="margin-bottom:12px;color:var(--text-secondary)">${name} — Last 12 Weeks</h4>`;

  const today = new Date();
  const dateSet = new Set(completions);
  const weeks = 12;
  const grid = document.createElement('div');
  grid.style.cssText = 'display:grid;grid-template-columns:repeat(12,1fr);gap:4px;';

  for (let w = weeks - 1; w >= 0; w--) {
    const weekEl = document.createElement('div');
    weekEl.style.cssText = 'display:flex;flex-direction:column;gap:4px;';
    for (let d = 0; d < 7; d++) {
      const date = new Date(today);
      date.setDate(today.getDate() - (w * 7 + (6 - d)));
      const dateStr = date.toISOString().split('T')[0];
      const cell = document.createElement('div');
      cell.style.cssText = `width:14px;height:14px;border-radius:3px;background:${
        dateSet.has(dateStr) ? 'var(--purple)' : 'var(--bg-tertiary)'
      };title:${dateStr}`;
      cell.title = dateStr;
      weekEl.appendChild(cell);
    }
    grid.appendChild(weekEl);
  }
  container.appendChild(grid);
}

// Search/filter habits
function filterHabits(query) {
  const q = query.toLowerCase();
  document.querySelectorAll('.habit-card').forEach(card => {
    const name = card.querySelector('.habit-card-name')?.textContent.toLowerCase() || '';
    const cat = card.querySelector('.habit-category-tag')?.textContent.toLowerCase() || '';
    card.style.display = (name.includes(q) || cat.includes(q)) ? '' : 'none';
  });
}
