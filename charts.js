/**
 * HabitOS — Monochrome Premium Charts Engine
 * Wraps Chart.js with frosted-glass styling, smooth curves,
 * white-glow gradients, animated entries, and peak-card rendering.
 */

// ── Global Chart.js defaults ─────────────────────────────────────────────────
Chart.defaults.font.family = "'Syne', 'Space Mono', sans-serif";
Chart.defaults.font.size = 11;
Chart.defaults.color = '#4a4a4a';
Chart.defaults.animation = { duration: 900, easing: 'easeOutQuart' };

// ── Monochrome palette ────────────────────────────────────────────────────────
const P = {
    white: '#ffffff',
    g100: '#e0e0e0',
    g200: '#b0b0b0',
    g300: '#888888',
    g400: '#555555',
    g500: '#333333',
    g600: '#1e1e1e',
    grid: 'rgba(255,255,255,0.05)',
    border: 'rgba(255,255,255,0.08)',

    // Monochrome shades used for multi-series / donut segments
    MONO: ['#e0e0e0', '#a0a0a0', '#606060', '#303030', '#181818'],
    // Subtle status tints (desaturated)
    green: '#6fcf97',
    amber: '#c8a96e',
    red: '#c47474',

    // Gradient factory (vertical, given canvas context)
    grad(ctx, h, top, bot) {
        const g = ctx.createLinearGradient(0, 0, 0, h);
        g.addColorStop(0, top);
        g.addColorStop(1, bot);
        return g;
    },
};

// ── Shared tooltip style ──────────────────────────────────────────────────────
const neonTooltip = {
    enabled: true,
    backgroundColor: 'rgba(8,8,8,0.95)',
    borderColor: 'rgba(255,255,255,0.12)',
    borderWidth: 1,
    titleColor: '#d0d0d0',
    bodyColor: '#888',
    padding: 10,
    cornerRadius: 8,
    titleFont: { weight: '700', size: 12 },
    bodyFont: { size: 11 },
    displayColors: false,
};

// ── Shared axis style ─────────────────────────────────────────────────────────
function neonAxis(opts = {}) {
    return {
        grid: { color: P.grid, lineWidth: 1, drawBorder: false, ...(opts.grid || {}) },
        ticks: { color: '#3a3a3a', font: { size: 10 }, padding: 5, ...(opts.ticks || {}) },
        border: { display: false },
        ...(opts.extra || {}),
    };
}

// ── Count-up animation ────────────────────────────────────────────────────────
function animateCount(el, target, suffix = '', duration = 900) {
    if (!el || isNaN(target)) return;
    const start = performance.now();
    function step(now) {
        const p = Math.min((now - start) / duration, 1);
        const ease = 1 - Math.pow(1 - p, 3);
        el.textContent = Math.round(target * ease) + suffix;
        if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
}

// ── Peak cards ────────────────────────────────────────────────────────────────
function renderPeakCards(containerId, labels, data, n = 3, unit = '') {
    const el = document.getElementById(containerId);
    if (!el || !data || !data.length) return;
    const medals = ['🥇', '🥈', '🥉'];
    const indexed = data.map((v, i) => [i, v]).sort((a, b) => b[1] - a[1]).slice(0, n);
    el.innerHTML = indexed.map(([i, v], rank) => `
    <div class="peak-card">
      <span class="peak-medal">${medals[rank] || '▪'}</span>
      <div class="peak-body">
        <span class="peak-label">${labels[i] || '–'}</span>
        <span class="peak-val">${v} ${unit}</span>
      </div>
    </div>`).join('');
}

// ─────────────────────────────────────────────────────────────────────────────
//  CHART FACTORIES — all monochrome
// ─────────────────────────────────────────────────────────────────────────────

/**
 * Area / Line chart — smooth bezier, gradient fill, soft white glow.
 */
function makeAreaChart(canvasId, labels, datasets, opts = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    const ctx = canvas.getContext('2d');

    const styledDatasets = datasets.map((ds, i) => {
        const colors = [P.white, P.g100, P.g200];
        const color = ds.color || colors[i % colors.length];
        // Use a plugin to build gradient after chart has sized itself
        const gradPlugin = {
            id: 'gradFill_' + canvasId + '_' + i,
            beforeDraw(chart) {
                const h = chart.height || 200;
                const gr = ctx.createLinearGradient(0, 0, 0, h);
                gr.addColorStop(0, color + '30');
                gr.addColorStop(1, color + '00');
                chart.data.datasets[i].backgroundColor = gr;
            }
        };
        return {
            label: ds.label || '',
            data: ds.data || [],
            borderColor: color,
            backgroundColor: color + '18',  // initial fallback
            borderWidth: 2,
            pointRadius: 3,
            pointHoverRadius: 6,
            pointBackgroundColor: color,
            pointBorderColor: '#080808',
            pointBorderWidth: 2,
            pointHoverBackgroundColor: '#fff',
            pointHoverBorderColor: color,
            pointHoverBorderWidth: 2,
            fill: true,
            tension: 0.45,
            _gradPlugin: gradPlugin,
            ...(ds.override || {}),
        };
    });

    const gradPlugins = styledDatasets.map(ds => ds._gradPlugin).filter(Boolean);

    return new Chart(canvas, {
        type: 'line',
        data: { labels, datasets: styledDatasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: opts.legend ?? {
                    display: datasets.length > 1,
                    labels: { color: '#555', boxWidth: 10, padding: 14 }
                },
                tooltip: { ...neonTooltip, ...(opts.tooltip || {}) },
            },
            scales: {
                x: neonAxis(opts.xAxis || {}),
                y: { ...neonAxis(opts.yAxis || {}), beginAtZero: true },
            },
            animation: { duration: 1000, easing: 'easeOutQuart' },
            ...(opts.extra || {}),
        },
        plugins: gradPlugins,
    });
}

/**
 * Bar chart — rounded tops, monochrome gradient fill.
 */
function makeBarChart(canvasId, labels, datasets, opts = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    const ctx = canvas.getContext('2d');

    const styledDatasets = datasets.map((ds, i) => {
        const colors = [P.g100, P.g200, P.g300];
        const color = ds.color || colors[i % colors.length];
        // If multiColor, use mono shades per bar; otherwise solid color
        const bg = ds.multiColor
            ? ds.data.map((_, j) => P.MONO[j % P.MONO.length] + 'cc')
            : color + 'aa';
        const bc = ds.multiColor
            ? ds.data.map((_, j) => P.MONO[j % P.MONO.length])
            : color;
        return {
            label: ds.label || '',
            data: ds.data || [],
            backgroundColor: bg,
            borderColor: bc,
            borderWidth: 1,
            borderRadius: opts.horizontal ? 4 : 5,
            borderSkipped: false,
            hoverBackgroundColor: color,
            ...(ds.override || {}),
        };
    });

    return new Chart(canvas, {
        type: 'bar',
        data: { labels, datasets: styledDatasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: opts.horizontal ? 'y' : 'x',
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: opts.legend ?? { display: false },
                tooltip: { ...neonTooltip, ...(opts.tooltip || {}) },
            },
            scales: {
                x: neonAxis(opts.xAxis || {}),
                y: { ...neonAxis(opts.yAxis || {}), beginAtZero: true },
            },
            animation: { duration: 900, easing: 'easeOutQuart' },
            ...(opts.extra || {}),
        },
    });
}

/**
 * Doughnut / Pie — monochrome shades, animated rotation.
 */
function makeDoughnut(canvasId, labels, data, opts = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;

    // Default: white → mid-gray → dark-gray for E/M/H
    const colors = opts.colors || ['#d0d0d0', '#888888', '#3a3a3a'];

    return new Chart(canvas, {
        type: opts.pie ? 'pie' : 'doughnut',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: colors.map(c => c + 'cc'),
                borderColor: colors.map(c => c + 'ff'),
                borderWidth: 2,
                hoverBackgroundColor: colors,
                hoverBorderWidth: 3,
                hoverOffset: 5,
            }],
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: opts.cutout ?? '68%',
            plugins: {
                legend: opts.legend ?? {
                    position: 'bottom',
                    labels: { color: '#555', boxWidth: 10, padding: 12, font: { size: 10 } },
                },
                tooltip: {
                    ...neonTooltip,
                    callbacks: {
                        label: i => ` ${i.label}: ${i.raw}  (${Math.round(i.raw / (i.dataset.data.reduce((a, b) => a + b, 0) || 1) * 100)
                            }%)`,
                    },
                    ...(opts.tooltipCallbacks || {}),
                },
            },
            animation: {
                animateRotate: true,
                animateScale: true,
                duration: 1000,
                easing: 'easeOutBack',
            },
            ...(opts.extra || {}),
        },
    });
}

/**
 * Heatmap — GitHub-style SVG, monochrome white cells.
 */
function renderHeatmap(containerId, data = {}, color = '#e0e0e0') {
    const wrap = document.getElementById(containerId);
    if (!wrap) return;

    const today = new Date();
    const dates = [];
    for (let i = 364; i >= 0; i--) {
        const d = new Date(today);
        d.setDate(d.getDate() - i);
        dates.push(d.toISOString().split('T')[0]);
    }

    const maxVal = Math.max(...Object.values(data), 1);
    const first = new Date(dates[0]);
    const offset = first.getDay();
    const weeks = Math.ceil((dates.length + offset) / 7);
    const cw = 13, ch = 13, gap = 3;
    const svgW = weeks * (cw + gap);
    const svgH = 7 * (ch + gap) + 20;

    // Month label positions
    const monthLabels = {};
    dates.forEach((d, idx) => {
        const col = Math.floor((idx + offset) / 7);
        const month = new Date(d).toLocaleString('default', { month: 'short' });
        if (!monthLabels[month]) monthLabels[month] = col;
    });

    let cells = '', months = '', dayLbls = '';

    // Day labels
    ['', 'Mon', '', 'Wed', '', 'Fri', ''].forEach((lbl, d) => {
        if (!lbl) return;
        const y = d * (ch + gap) + 20 + ch * 0.78;
        dayLbls += `<text x="-5" y="${y}" font-size="9" fill="#2e2e2e"
      text-anchor="end" font-family="'Space Mono',monospace">${lbl}</text>`;
    });

    // Month labels
    Object.entries(monthLabels).forEach(([m, col]) => {
        months += `<text x="${col * (cw + gap)}" y="13" font-size="9"
      fill="#3a3a3a" font-family="'Space Mono',monospace">${m}</text>`;
    });

    // Cells
    for (let w = 0; w < weeks; w++) {
        for (let d = 0; d < 7; d++) {
            const idx = w * 7 + d - offset;
            const x = w * (cw + gap);
            const y = d * (ch + gap) + 20;
            if (idx < 0 || idx >= dates.length) {
                cells += `<rect x="${x}" y="${y}" width="${cw}" height="${ch}" rx="3" fill="#111111"/>`;
                continue;
            }
            const date = dates[idx];
            const count = data[date] || 0;
            const inten = count === 0 ? 0 : Math.max(0.12, count / maxVal);
            const alpha = Math.round(inten * 255).toString(16).padStart(2, '0');
            const fill = count === 0 ? '#111111' : color + alpha;
            cells += `<rect x="${x}" y="${y}" width="${cw}" height="${ch}" rx="3"
        fill="${fill}" style="cursor:default">
        <title>${date}: ${count} contribution${count !== 1 ? 's' : ''}</title>
      </rect>`;
        }
    }

    wrap.innerHTML = `
    <div style="overflow-x:auto;padding-bottom:4px">
      <svg viewBox="-32 0 ${svgW + 36} ${svgH}" xmlns="http://www.w3.org/2000/svg"
           style="min-width:${svgW}px;display:block">
        ${months}${dayLbls}${cells}
      </svg>
    </div>
    <div class="heatmap-legend">
      <span class="hml-label">Less</span>
      ${[0.08, 0.25, 0.5, 0.75, 1].map(a =>
        `<rect-block style="background:${a < 0.1 ? '#111111' : color + Math.round(a * 220).toString(16).padStart(2, '0')}"></rect-block>`
    ).join('')}
      <span class="hml-label">More</span>
    </div>`;

    const active = Object.values(data).filter(v => v > 0).length;
    const badge = document.getElementById('heatmapBadge');
    if (badge) badge.textContent = `${active} active days`;
}

// ── Export ────────────────────────────────────────────────────────────────────
window.HC = {
    P, makeAreaChart, makeBarChart, makeDoughnut,
    renderHeatmap, renderPeakCards, animateCount,
};