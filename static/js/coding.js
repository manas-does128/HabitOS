/* ===== HabitOS Coding Profiles JS ===== */

// Skill radar chart (rendered on coding profiles page if canvas exists)
function renderSkillRadar(canvasId, labels, data) {
  const canvas = document.getElementById(canvasId);
  if (!canvas) return;
  new Chart(canvas, {
    type: 'radar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Skill Level',
        data: data,
        backgroundColor: 'rgba(124,58,237,0.2)',
        borderColor: 'var(--purple)',
        pointBackgroundColor: 'var(--purple)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'var(--purple)'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        r: {
          angleLines: { color: 'rgba(255,255,255,0.08)' },
          grid: { color: 'rgba(255,255,255,0.08)' },
          pointLabels: { color: '#aaa', font: { size: 12 } },
          ticks: { display: false },
          suggestedMin: 0,
          suggestedMax: 100
        }
      },
      plugins: {
        legend: { display: false }
      }
    }
  });
}

// Compute overall coding score from profile stats
function computeCodingScore(profiles) {
  let score = 0;
  profiles.forEach(p => {
    const s = p.stats || {};
    if (p.platform === 'LeetCode') score += (s.total_solved || 0) * 2;
    if (p.platform === 'Codeforces') score += (s.rating || 0) / 10;
    if (p.platform === 'GitHub') score += (s.public_repos || 0) * 5 + (s.total_stars || 0) * 3;
  });
  return Math.min(Math.round(score), 9999);
}
