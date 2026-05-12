// ScoutCloud - browser logic
let authToken = null;

function handleCognitoCallback() {
    const hash = window.location.hash;
    const params = new URLSearchParams(window.location.search);

    let token = null;
    if (hash.includes('access_token')) {
        token = new URLSearchParams(hash.slice(1)).get('access_token');
    } else if (params.get('code')) {
        // Authorization code flow - production would PKCE-exchange here.
        return;
    }
    if (token) {
        localStorage.setItem('sc_auth_token', token);
        window.history.replaceState({}, '', '/');
        authToken = token;
    }
}

async function fetchScores() {
    try {
        const res = await fetch('/scores');
        const data = await res.json();
        updateScoreCards(data.games || []);
        updateTicker(data.games || []);
        if (data.games && data.games[0] && data.games[0].updated_at) {
            updateTimestamp(data.games[0].updated_at);
        }
    } catch (e) {
        console.warn('fetchScores failed', e);
    }
}

function updateScoreCards(games) {
    games.forEach(g => {
        const card = document.querySelector(`[data-game-id="${g.game_id}"]`);
        if (!card) return;
        const scores = card.querySelectorAll('.team-score');
        if (scores.length >= 2) {
            scores[0].textContent = g.home_score;
            scores[1].textContent = g.away_score;
            scores[0].classList.toggle('winner', g.home_score > g.away_score);
            scores[1].classList.toggle('winner', g.away_score > g.home_score);
        }
        const status = card.querySelector('.status');
        const accent = card.querySelector('.accent');
        if (status) {
            status.textContent = g.status;
            status.className = 'status ' + statusClass(g.status);
        }
        if (accent) {
            accent.className = 'accent ' + (isLive(g.status) ? 'accent-live' : 'accent-scheduled');
        }
    });
}

function statusClass(status) {
    if (!status) return 'status-scheduled';
    if (status === 'Final') return 'status-final';
    if (/halftime/i.test(status)) return 'status-halftime';
    if (/Q\d|H[12]|live/i.test(status)) return 'status-live';
    return 'status-scheduled';
}

function isLive(status) {
    return status && /Q\d|H[12]|live/i.test(status);
}

function updateTicker(games) {
    if (!games || !games.length) return;
    const track = document.querySelector('.ticker-track');
    if (!track) return;
    const items = games.map(g =>
        `<span class="ticker-item"><span class="dot"></span>${g.away_team} @ ${g.home_team} - ${g.status} (${g.away_score}-${g.home_score})</span>`
    ).join('');
    track.innerHTML = items + items;
}

async function fetchPlayers() {
    try {
        const res = await fetch('/players');
        const data = await res.json();
        if (data.source !== 'placeholder' && data.players && data.players.length) {
            updatePlayerTable(data.players);
        }
    } catch (e) {
        console.warn('fetchPlayers failed', e);
    }
}

function updatePlayerTable(players) {
    const tbody = document.getElementById('player-tbody');
    if (!tbody) return;
    tbody.innerHTML = players.map(p => `
        <tr>
            <td class="player-cell">
                <div class="player-name">${escapeHtml(p.name)}</div>
                <div class="player-team">${escapeHtml(p.team || '')}</div>
            </td>
            <td class="stat-cell">${formatNum(p.ppg)}</td>
            <td class="stat-cell">${formatNum(p.apg)}</td>
            <td class="stat-cell">${formatNum(p.rpg)}</td>
            <td class="stat-cell">${formatNum(p.fg_pct)}%</td>
        </tr>
    `).join('');
}

function formatNum(n) {
    if (n === null || n === undefined) return '--';
    return Number(n).toFixed(1);
}

function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    }[c]));
}

function updateTimestamp(updated_at) {
    const mins = Math.floor((Date.now() - new Date(updated_at)) / 60000);
    const badge = document.querySelector('.badge-live');
    if (badge) badge.textContent = `● Updated ${mins} min ago · Lambda`;
}

async function fetchAnalytics(token) {
    try {
        const res = await fetch('/analytics', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (res.ok) {
            const data = await res.json();
            showAnalyticsUnlocked(data);
        } else {
            localStorage.removeItem('sc_auth_token');
        }
    } catch (e) {
        console.warn('fetchAnalytics failed', e);
    }
}

function showAnalyticsUnlocked(data) {
    document.querySelector('.analytics-locked')?.remove();
    const unlocked = document.getElementById('analytics-unlocked');
    if (unlocked) {
        unlocked.style.display = 'block';
        (data.shot_zones || []).forEach((zone, i) => {
            const cell = unlocked.querySelectorAll('.shot-cell')[i];
            if (cell) {
                const pct = cell.querySelector('.shot-pct');
                const label = cell.querySelector('.shot-label');
                if (pct) pct.textContent = zone.pct.toFixed(1) + '%';
                if (label) label.textContent = zone.zone;
            }
        });
        if (data.user_email) {
            const emailEl = unlocked.querySelector('.unlocked-email');
            if (emailEl) emailEl.textContent = data.user_email;
        }
    }
}

function checkStoredToken() {
    const token = localStorage.getItem('sc_auth_token');
    if (token) {
        authToken = token;
        fetchAnalytics(token);
    }
}

function startPolling() {
    setInterval(fetchScores, 30000);
}

function initScrollSpy() {
    const links = document.querySelectorAll('.nav-links a[data-section]');
    if (!links.length || !('IntersectionObserver' in window)) return;

    const linkBySection = {};
    links.forEach(a => { linkBySection[a.dataset.section] = a; });

    const setActive = (sectionId) => {
        links.forEach(a => a.classList.toggle('active', a.dataset.section === sectionId));
    };

    // Track which sections are currently visible; pick the topmost.
    const visible = new Map();
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(e => {
            if (e.isIntersecting) visible.set(e.target.id, e.boundingClientRect.top);
            else visible.delete(e.target.id);
        });
        if (visible.size > 0) {
            // The section closest to the top of the viewport wins.
            const top = [...visible.entries()].sort((a, b) => a[1] - b[1])[0][0];
            setActive(top);
        }
    }, {
        // Trigger when a section's center crosses the upper third of the viewport.
        rootMargin: '-30% 0px -55% 0px',
        threshold: 0
    });

    Object.keys(linkBySection).forEach(id => {
        const el = document.getElementById(id);
        if (el) observer.observe(el);
    });

    // Click-to-scroll smooth behavior + immediate active state.
    links.forEach(a => {
        a.addEventListener('click', (ev) => {
            const target = document.getElementById(a.dataset.section);
            if (!target) return;
            ev.preventDefault();
            setActive(a.dataset.section);
            target.scrollIntoView({ behavior: 'smooth', block: 'start' });
            history.replaceState({}, '', '#' + a.dataset.section);
        });
    });
}

document.addEventListener('DOMContentLoaded', () => {
    handleCognitoCallback();
    fetchScores();
    fetchPlayers();
    checkStoredToken();
    startPolling();
    initScrollSpy();

    const signinBtn = document.querySelector('.sign-in-btn');
    if (signinBtn) {
        signinBtn.addEventListener('click', () => {
            const cognitoUrl = signinBtn.dataset.cognitoUrl;
            if (cognitoUrl) window.location.href = cognitoUrl;
        });
    }

    const ctaBtn = document.querySelector('.lock-cta');
    if (ctaBtn) {
        ctaBtn.addEventListener('click', () => {
            const sb = document.querySelector('.sign-in-btn');
            sb?.click();
        });
    }
});
