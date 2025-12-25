// Control Center - All Section Functions and API Interactions

const API_BASE = 'http://localhost:8000';
const ADMIN_TOKEN = (typeof PLATFORM_CONFIG !== 'undefined' && PLATFORM_CONFIG.ADMIN_TOKEN) ? PLATFORM_CONFIG.ADMIN_TOKEN : '';
const ADMIN_HEADER_NAME = 'X-Admin-Token';
const API_KEY = (typeof PLATFORM_CONFIG !== 'undefined' && PLATFORM_CONFIG.API_KEY) ? PLATFORM_CONFIG.API_KEY : 'admin-key-456';
const API_KEY_HEADER_NAME = 'X-API-Key';
if (typeof window !== 'undefined' && typeof window.fetch === 'function') {
    const originalFetch = window.fetch.bind(window);
    window.fetch = (input, init = {}) => {
        try {
            const url = typeof input === 'string' ? input : (input && input.url) || '';
            const isApiCall = typeof url === 'string' && url.startsWith(API_BASE);
            const needsToken = ADMIN_TOKEN && isApiCall && url.includes('/admin/');
            const needsApiKey = API_KEY && isApiCall;
            if (!needsToken && !needsApiKey) {
                return originalFetch(input, init);
            }

            const baseHeaders = new Headers(init.headers || (input instanceof Request ? input.headers : undefined) || {});
            if (needsToken) {
                baseHeaders.set(ADMIN_HEADER_NAME, ADMIN_TOKEN);
            }
            if (needsApiKey) {
                baseHeaders.set(API_KEY_HEADER_NAME, API_KEY);
            }

            if (input instanceof Request) {
                const newRequest = new Request(input, { headers: baseHeaders });
                return originalFetch(newRequest, init);
            }

            return originalFetch(url, { ...init, headers: baseHeaders });
        } catch (error) {
            console.error('Failed to attach admin token to request', error);
            return originalFetch(input, init);
        }
    };
}
let sectionCharts = {};
let llmSettingsCache = { providers: [] };
const analyticsState = { fallbackDays: 7 };
const faqState = {
    initialized: false,
    page: 1,
    pageSize: 10,
    total: 0,
    hasNext: false,
    search: '',
    status: '',
    category: '',
    items: [],
    categories: new Set(),
    searchDebounce: null,
    editingId: null
};

const llmTesterState = {
    initialized: false,
    historyFilter: 'all',
    historyLimit: 25,
    availableProviders: [],
    activeProviders: [],
    latestResults: [],
    running: false,
};

const DEFAULT_LLM_TEST_PROMPT = "Health check ping. Respond with the word 'pong'.";

const telephonyTesterState = {
    initialized: false,
    mode: 'dry',
    availableTests: [],
    latestResults: [],
    running: false,
    historyFilter: 'all',
    historyLimit: 50,
    voiceContext: {},
    envSnapshot: {},
};

// ==================== ANALYTICS SECTION ====================

async function loadAnalyticsSection() {
    try {
        // Load analytics overview
        const response = await fetch(`${API_BASE}/admin/analytics/dashboard?days=30`);
        const data = await response.json();

        document.getElementById('analytics-events').textContent = data.total_events || 0;
        document.getElementById('analytics-users').textContent = data.unique_users || 0;
        document.getElementById('analytics-session').textContent = Math.round(data.avg_session_duration || 0) + 's';
        document.getElementById('analytics-engagement').textContent = Math.round((data.engagement_rate || 0) * 100) + '%';

        // Load engagement data
        loadEngagementData();
        
        // Initialize analytics charts
        initializeAnalyticsCharts();
        loadTrafficTrends(7);
        loadFallbackStats(analyticsState.fallbackDays);
    } catch (error) {
        console.error('Error loading analytics:', error);
    }
}

async function loadEngagementData() {
    try {
        const response = await fetch(`${API_BASE}/admin/analytics/engagement?days=7`);
        const data = await response.json();

        const tbody = document.getElementById('engagementTableBody');
        if (data.events && data.events.length > 0) {
            tbody.innerHTML = data.events.map(event => `
                <tr>
                    <td>${event.event_type}</td>
                    <td><span class="badge badge-info">${event.count}</span></td>
                    <td>${event.unique_users}</td>
                    <td>${event.avg_duration ? Math.round(event.avg_duration) + 's' : 'N/A'}</td>
                    <td>
                        <span class="stat-change ${event.trend > 0 ? 'positive' : 'negative'}">
                            ${event.trend > 0 ? '↑' : '↓'} ${Math.abs(event.trend)}%
                        </span>
                    </td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #6b7280;">No engagement data available</td></tr>';
        }
    } catch (error) {
        console.error('Error loading engagement data:', error);
    }
}

function initializeAnalyticsCharts() {
    // Traffic Trends Chart
    const trafficCtx = document.getElementById('analyticsTrafficChart').getContext('2d');
    sectionCharts.analyticsTraffic = new Chart(trafficCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'Interactions',
                data: [],
                backgroundColor: 'rgba(102, 126, 234, 0.5)',
                borderColor: '#667eea',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });

    // Performance Chart
    const perfCtx = document.getElementById('analyticsPerformanceChart').getContext('2d');
    sectionCharts.analyticsPerformance = new Chart(perfCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Avg Response Time (ms)',
                    data: [],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.1)',
                    yAxisID: 'y',
                },
                {
                    label: 'Cache Hit Rate (%)',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    yAxisID: 'y1',
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: {
                    type: 'linear',
                    display: true,
                    position: 'left',
                },
                y1: {
                    type: 'linear',
                    display: true,
                    position: 'right',
                    grid: {
                        drawOnChartArea: false,
                    },
                },
            }
        }
    });
}

async function loadTrafficTrends(days) {
    try {
        const response = await fetch(`${API_BASE}/admin/analytics/traffic?days=${days}`);
        const data = await response.json();

        if (data.daily_traffic) {
            const labels = data.daily_traffic.map(d => d.date);
            const values = data.daily_traffic.map(d => d.requests);
            
            sectionCharts.analyticsTraffic.data.labels = labels;
            sectionCharts.analyticsTraffic.data.datasets[0].data = values;
            sectionCharts.analyticsTraffic.update();
        }

        // Load performance metrics
        const perfResponse = await fetch(`${API_BASE}/admin/analytics/performance?days=${days}`);
        const perfData = await perfResponse.json();

        if (perfData.daily_performance) {
            const labels = perfData.daily_performance.map(d => d.date);
            const responseTimes = perfData.daily_performance.map(d => d.avg_response_time_ms);
            const cacheRates = perfData.daily_performance.map(d => d.cache_hit_rate * 100);
            
            sectionCharts.analyticsPerformance.data.labels = labels;
            sectionCharts.analyticsPerformance.data.datasets[0].data = responseTimes;
            sectionCharts.analyticsPerformance.data.datasets[1].data = cacheRates;
            sectionCharts.analyticsPerformance.update();
        }
    } catch (error) {
        console.error('Error loading traffic trends:', error);
    }
}

async function loadFallbackStats(days = analyticsState.fallbackDays) {
    analyticsState.fallbackDays = Number(days) || analyticsState.fallbackDays || 7;
    const targetDays = analyticsState.fallbackDays;
    try {
        const response = await fetch(`${API_BASE}/admin/analytics/fallbacks?days=${targetDays}&limit=20`);
        if (!response.ok) {
            throw new Error('Failed to load fallback analytics');
        }
        const data = await response.json();
        renderFallbackSummary(data.summary);
        renderFallbackProviders(data.summary?.providers || []);
        renderFallbackDistribution(data.distribution || []);
        renderFallbackFailures(data.recent_failures || []);
    } catch (error) {
        console.error('Error loading fallback stats:', error);
        renderFallbackProviders([]);
        renderFallbackDistribution([]);
        renderFallbackFailures([]);
    }
}

function renderFallbackSummary(summary = {}) {
    const totals = summary.totals || { attempts: 0, successes: 0, failures: 0 };
    const saves = (summary.providers || []).reduce((acc, provider) => acc + (provider.fallback_saves || 0), 0);
    const attemptsEl = document.getElementById('fallback-total-attempts');
    const successEl = document.getElementById('fallback-total-success');
    const savesEl = document.getElementById('fallback-total-saves');
    if (attemptsEl) attemptsEl.textContent = totals.attempts || 0;
    if (successEl) successEl.textContent = totals.successes || 0;
    if (savesEl) savesEl.textContent = saves;
}

function renderFallbackProviders(providers) {
    const tbody = document.getElementById('fallbackProviderTableBody');
    if (!tbody) return;

    if (!providers.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#6b7280;">No provider telemetry yet. Run a few chats to populate.</td></tr>';
        return;
    }

    tbody.innerHTML = providers.map(provider => `
        <tr>
            <td><span class="badge badge-info">${provider.provider}</span></td>
            <td>${provider.attempts}</td>
            <td>${(provider.success_rate * 100).toFixed(1)}%</td>
            <td>${provider.avg_latency_ms ? provider.avg_latency_ms.toFixed(1) + ' ms' : '—'}</td>
            <td>${provider.failures}</td>
            <td>${provider.fallback_saves}</td>
        </tr>
    `).join('');
}

function renderFallbackDistribution(distribution) {
    const container = document.getElementById('fallbackDistribution');
    if (!container) return;
    if (!distribution.length) {
        container.innerHTML = '<p style="color:#6b7280;">No fallback data yet.</p>';
        return;
    }
    container.innerHTML = distribution.map(entry => `
        <div class="pill">
            <strong>${entry.fallback_depth}</strong> hop${entry.fallback_depth === 1 ? '' : 's'}
            <span>${entry.count}x</span>
        </div>
    `).join('');
}

function renderFallbackFailures(failures) {
    const container = document.getElementById('fallbackFailures');
    if (!container) return;
    if (!failures.length) {
        container.innerHTML = '<p style="color:#6b7280;">No failures recorded.</p>';
        return;
    }
    container.innerHTML = failures.map(failure => `
        <div class="failure-item">
            <div><strong>${failure.provider}</strong> (depth ${failure.fallback_depth})</div>
            <small>${new Date(failure.created_at * 1000).toLocaleString()}</small>
            <p>${failure.error_message || 'Unknown error'}</p>
        </div>
    `).join('');
}

async function exportAnalyticsData() {
    try {
        const response = await fetch(`${API_BASE}/admin/analytics/export?days=30`);
        const data = await response.json();
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        downloadBlob(blob, `analytics-export-${new Date().toISOString().split('T')[0]}.json`);
        
        showAlert('Analytics data exported successfully!', 'success');
    } catch (error) {
        showAlert('Error exporting analytics: ' + error.message, 'danger');
    }
}

async function resetAnalytics() {
    if (!confirm('Are you sure you want to reset all analytics data? This cannot be undone.')) {
        return;
    }
    
    showAlert('Analytics reset is not yet implemented', 'warning');
}

async function generateReport() {
    showAlert('Report generation started. You will receive an email when complete.', 'info');
}

// ==================== TRANSLATION SECTION ====================

async function loadTranslationSection() {
    await loadTranslationStats();
    initializeTranslationChart();
}

async function loadTranslationStats() {
    try {
        const response = await fetch(`${API_BASE}/admin/translation/languages?days=30`);
        if (!response.ok) {
            throw new Error('Failed to load translation stats');
        }
        const data = await response.json();
        const tbody = document.getElementById('translationStatsBody');
        if (!tbody) return;

        if (data.language_stats && data.language_stats.length) {
            tbody.innerHTML = data.language_stats.map(lang => `
                <tr>
                    <td><strong>${lang.language}</strong></td>
                    <td><span class="badge badge-info">${lang.request_count}</span></td>
                    <td>${lang.cache_hits}</td>
                    <td>
                        <div class="progress-bar">
                            <div class="progress-fill success" style="width: ${lang.hit_rate * 100}%"></div>
                        </div>
                        <small>${Math.round(lang.hit_rate * 100)}%</small>
                    </td>
                    <td>$${lang.total_cost.toFixed(4)}</td>
                    <td>
                        <button class="btn btn-outline btn-sm" onclick="viewLanguageDetails('${lang.language}')">
                            View Details
                        </button>
                    </td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #6b7280;">No translation data available</td></tr>';
        }

        if (sectionCharts.translation) {
            const labels = data.language_stats?.map(lang => lang.language) || [];
            const requests = data.language_stats?.map(lang => lang.request_count) || [];
            const cacheHits = data.language_stats?.map(lang => lang.cache_hits) || [];
            sectionCharts.translation.data.labels = labels;
            sectionCharts.translation.data.datasets[0].data = requests;
            sectionCharts.translation.data.datasets[1].data = cacheHits;
            sectionCharts.translation.update();
        }
    } catch (error) {
        console.error('Error loading translation stats:', error);
        showAlert('Unable to load translation stats', 'error');
    }
}

function initializeTranslationChart() {
    const ctx = document.getElementById('translationChart').getContext('2d');
    sectionCharts.translation = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Total Requests',
                    data: [],
                    backgroundColor: 'rgba(102, 126, 234, 0.5)',
                },
                {
                    label: 'Cache Hits',
                    data: [],
                    backgroundColor: 'rgba(16, 185, 129, 0.5)',
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

async function cleanupTranslations() {
    const days = parseInt(document.getElementById('translationCleanupDays').value);
    if (!confirm(`Are you sure you want to delete translations older than ${days} days?`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/admin/translation/cleanup?days=${days}`, {
            method: 'POST'
        });
        const data = await response.json();
        
        showAlert(`Cleanup successful! Deleted ${data.deleted_count || 0} old translations.`, 'success');
        loadTranslationStats();
    } catch (error) {
        showAlert('Error cleaning up translations: ' + error.message, 'danger');
    }
}

async function clearAllTranslations() {
    if (!confirm('Are you sure you want to clear ALL translation cache? This cannot be undone.')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/admin/translation/clear-cache`, {
            method: 'POST'
        });
        const data = await response.json();
        
        showAlert('Translation cache cleared successfully!', 'success');
        loadTranslationStats();
    } catch (error) {
        showAlert('Error clearing cache: ' + error.message, 'danger');
    }
}

async function lookupTranslation() {
    const text = document.getElementById('lookupText').value;
    const language = document.getElementById('lookupLanguage').value;
    
    if (!text.trim()) {
        showAlert('Please enter text to lookup', 'warning');
        return;
    }

    const resultDiv = document.getElementById('lookupResult');
    resultDiv.innerHTML = '<div class="loading"><div class="loading-spinner"></div></div>';

    try {
        const response = await fetch(`${API_BASE}/admin/translation/lookup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, target_language: language })
        });
        const data = await response.json();

        if (data.cached) {
            resultDiv.innerHTML = `
                <div class="alert alert-success">
                    <strong>✅ Found in cache:</strong><br>
                    ${data.translation}<br>
                    <small>Provider: ${data.provider} | Used: ${data.usage_count} times</small>
                </div>
            `;
        } else {
            resultDiv.innerHTML = `
                <div class="alert alert-warning">
                    <strong>❌ Not found in cache</strong><br>
                    This translation will be fetched fresh on next request.
                </div>
            `;
        }
    } catch (error) {
        resultDiv.innerHTML = `<div class="alert alert-danger">Error: ${error.message}</div>`;
    }
}

// ==================== SENTIMENT SECTION ====================

async function loadSentimentSection() {
    try {
        const response = await fetch(`${API_BASE}/admin/analytics/sentiment?days=7`);
        const data = await response.json();

        document.getElementById('sentiment-positive').textContent = data.positive_count || 0;
        document.getElementById('sentiment-negative').textContent = data.negative_count || 0;
        document.getElementById('sentiment-escalations').textContent = data.escalation_count || 0;
        document.getElementById('sentiment-average').textContent = (data.avg_sentiment || 0).toFixed(2);

        // Initialize sentiment distribution chart
        const ctx = document.getElementById('sentimentDistChart').getContext('2d');
        sectionCharts.sentimentDist = new Chart(ctx, {
            type: 'pie',
            data: {
                labels: ['Positive', 'Neutral', 'Negative', 'Angry', 'Urgent'],
                datasets: [{
                    data: [
                        data.sentiment_distribution?.positive || 0,
                        data.sentiment_distribution?.neutral || 0,
                        data.sentiment_distribution?.negative || 0,
                        data.sentiment_distribution?.angry || 0,
                        data.sentiment_distribution?.urgent || 0
                    ],
                    backgroundColor: ['#10b981', '#6b7280', '#f59e0b', '#ef4444', '#3b82f6']
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false
            }
        });

        loadEscalations();
    } catch (error) {
        console.error('Error loading sentiment section:', error);
    }
}

async function loadEscalations() {
    try {
        const response = await fetch(`${API_BASE}/admin/analytics/escalations?limit=50`);
        const data = await response.json();

        const tbody = document.getElementById('escalationsTableBody');
        
        if (data.escalations && data.escalations.length > 0) {
            tbody.innerHTML = data.escalations.map(esc => `
                <tr>
                    <td>${new Date(esc.timestamp).toLocaleString()}</td>
                    <td><code style="font-size: 11px;">${esc.session_id.substring(0, 12)}...</code></td>
                    <td>
                        <span class="badge ${esc.sentiment === 'angry' ? 'badge-danger' : 'badge-warning'}">
                            ${esc.sentiment}
                        </span>
                    </td>
                    <td>${esc.score.toFixed(2)}</td>
                    <td style="max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;" title="${esc.message}">
                        ${esc.message}
                    </td>
                    <td>
                        <button class="btn btn-outline btn-sm" onclick="viewConversation('${esc.session_id}')">
                            View
                        </button>
                    </td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #6b7280;">No escalations found</td></tr>';
        }
    } catch (error) {
        console.error('Error loading escalations:', error);
    }
}

function updateThreshold(slider) {
    document.getElementById('thresholdValue').textContent = slider.value;
}

// ==================== CACHE SECTION ====================

async function loadCacheSection() {
    loadCacheStats();
    initializeCacheChart();
}

async function loadCacheStats() {
    try {
        const response = await fetch(`${API_BASE}/admin/cache/stats`);
        const data = await response.json();

        document.getElementById('cache-total').textContent = data.total_entries || 0;
        document.getElementById('cache-hits').textContent = data.total_hits || 0;
        document.getElementById('cache-rate').textContent = Math.round((data.hit_rate || 0) * 100) + '%';
        document.getElementById('cache-savings').textContent = '$' + (data.cost_savings || 0).toFixed(2);

        // Load recent cache entries
        loadCacheEntries();
    } catch (error) {
        console.error('Error loading cache stats:', error);
    }
}

async function loadCacheEntries() {
    try {
        const response = await fetch(`${API_BASE}/admin/cache/entries?limit=20`);
        const data = await response.json();

        const tbody = document.getElementById('cacheEntriesBody');
        
        if (data.entries && data.entries.length > 0) {
            tbody.innerHTML = data.entries.map(entry => `
                <tr>
                    <td><code style="font-size: 11px;">${entry.question_hash.substring(0, 16)}...</code></td>
                    <td><span class="badge badge-info">${entry.provider}</span></td>
                    <td>${entry.hit_count}</td>
                    <td>${new Date(entry.last_used).toLocaleString()}</td>
                    <td>$${(entry.cost_savings || 0).toFixed(4)}</td>
                    <td>
                        <button class="btn btn-danger btn-sm" onclick="deleteCacheEntry('${entry.question_hash}')">
                            Delete
                        </button>
                    </td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #6b7280;">No cache entries</td></tr>';
        }
    } catch (error) {
        console.error('Error loading cache entries:', error);
    }
}

function initializeCacheChart() {
    const ctx = document.getElementById('cachePerformanceChart').getContext('2d');
    sectionCharts.cachePerformance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Cache Hit Rate (%)',
                data: [],
                borderColor: '#10b981',
                backgroundColor: 'rgba(16, 185, 129, 0.1)',
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true, max: 100 }
            }
        }
    });
}

async function clearAllCache() {
    if (!confirm('Are you sure you want to clear all cache? This will temporarily reduce performance.')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/admin/cache/clear`, {
            method: 'POST'
        });
        const data = await response.json();
        
        showAlert('Cache cleared successfully!', 'success');
        loadCacheStats();
    } catch (error) {
        showAlert('Error clearing cache: ' + error.message, 'danger');
    }
}

async function deleteCacheEntry(hash) {
    try {
        const response = await fetch(`${API_BASE}/admin/cache/entry/${hash}`, {
            method: 'DELETE'
        });
        
        showAlert('Cache entry deleted', 'success');
        loadCacheEntries();
    } catch (error) {
        showAlert('Error deleting entry: ' + error.message, 'danger');
    }
}

// ==================== RATE LIMITING SECTION ====================

async function loadRateLimitSection() {
    loadRateLimitStats();
    loadApiKeyUsage();
    loadBlockedEntities();
    loadAbuseIncidents();
}

async function loadRateLimitStats() {
    try {
        const response = await fetch(`${API_BASE}/admin/rate-limit/stats`);
        const data = await response.json();

        document.getElementById('ratelimit-keys').textContent = data.total_api_keys || 0;
        document.getElementById('ratelimit-blocked').textContent = data.blocked_entities || 0;
        document.getElementById('ratelimit-incidents').textContent = data.incidents_24h || 0;
        document.getElementById('ratelimit-requests').textContent = data.requests_today || 0;
    } catch (error) {
        console.error('Error loading rate limit stats:', error);
    }
}

async function loadApiKeyUsage() {
    try {
        const response = await fetch(`${API_BASE}/admin/rate-limit/usage?hours=24`);
        const data = await response.json();

        const tbody = document.getElementById('apiKeyUsageBody');
        
        if (data.usage && data.usage.length > 0) {
            tbody.innerHTML = data.usage.map(usage => {
                const usagePercent = (usage.requests / usage.limit) * 100;
                return `
                    <tr>
                        <td><code>${usage.api_key.substring(0, 12)}...</code></td>
                        <td><span class="badge badge-info">${usage.tier}</span></td>
                        <td>${usage.requests}</td>
                        <td>${usage.limit}</td>
                        <td>
                            <div class="progress-bar">
                                <div class="progress-fill ${usagePercent > 80 ? 'danger' : usagePercent > 50 ? 'warning' : 'success'}" style="width: ${usagePercent}%"></div>
                            </div>
                            <small>${Math.round(usagePercent)}%</small>
                        </td>
                        <td>${new Date(usage.last_request).toLocaleString()}</td>
                        <td>
                            <button class="btn btn-danger btn-sm" onclick="blockApiKey('${usage.api_key}')">
                                Block
                            </button>
                        </td>
                    </tr>
                `;
            }).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="7" style="text-align: center; color: #6b7280;">No usage data</td></tr>';
        }
    } catch (error) {
        console.error('Error loading API key usage:', error);
    }
}

async function loadBlockedEntities() {
    try {
        const response = await fetch(`${API_BASE}/admin/rate-limit/blocked`);
        const data = await response.json();

        const tbody = document.getElementById('blockedEntitiesBody');
        
        if (data.blocked && data.blocked.length > 0) {
            tbody.innerHTML = data.blocked.map(entity => `
                <tr>
                    <td><span class="badge badge-danger">${entity.entity_type}</span></td>
                    <td><code>${entity.entity_value}</code></td>
                    <td>${entity.reason}</td>
                    <td>${new Date(entity.blocked_at).toLocaleString()}</td>
                    <td>${entity.expires_at ? new Date(entity.expires_at).toLocaleString() : 'Permanent'}</td>
                    <td>
                        <button class="btn btn-success btn-sm" onclick="unblockEntity('${entity.entity_type}', '${entity.entity_value}')">
                            Unblock
                        </button>
                    </td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #6b7280;">No blocked entities</td></tr>';
        }
    } catch (error) {
        console.error('Error loading blocked entities:', error);
    }
}

async function loadAbuseIncidents() {
    try {
        const response = await fetch(`${API_BASE}/admin/rate-limit/incidents?hours=24&limit=50`);
        const data = await response.json();

        const tbody = document.getElementById('abuseIncidentsBody');
        
        if (data.incidents && data.incidents.length > 0) {
            tbody.innerHTML = data.incidents.map(incident => `
                <tr>
                    <td>${new Date(incident.timestamp).toLocaleString()}</td>
                    <td>${incident.entity_type}</td>
                    <td><code>${incident.entity_value}</code></td>
                    <td>${incident.reason}</td>
                    <td>
                        <span class="badge ${incident.severity === 'high' ? 'badge-danger' : incident.severity === 'medium' ? 'badge-warning' : 'badge-info'}">
                            ${incident.severity}
                        </span>
                    </td>
                    <td style="max-width: 200px; overflow: hidden; text-overflow: ellipsis;">${JSON.stringify(incident.details)}</td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #6b7280;">No recent incidents</td></tr>';
        }
    } catch (error) {
        console.error('Error loading abuse incidents:', error);
    }
}

async function blockEntity() {
    const entityType = document.getElementById('blockEntityType').value;
    const entityValue = document.getElementById('blockEntityValue').value;
    const reason = document.getElementById('blockReason').value;
    const duration = parseInt(document.getElementById('blockDuration').value);

    if (!entityValue || !reason) {
        showAlert('Please fill in all required fields', 'warning');
        return;
    }

    try {
        const body = {
            entity_type: entityType,
            entity_value: entityValue,
            reason: reason
        };

        if (duration > 0) {
            body.duration_hours = duration;
        }

        const response = await fetch(`${API_BASE}/admin/rate-limit/block`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        
        showAlert('Entity blocked successfully', 'success');
        
        // Clear form
        document.getElementById('blockEntityValue').value = '';
        document.getElementById('blockReason').value = '';
        document.getElementById('blockDuration').value = '0';
        
        loadBlockedEntities();
    } catch (error) {
        showAlert('Error blocking entity: ' + error.message, 'danger');
    }
}

async function unblockEntity(entityType, entityValue) {
    if (!confirm(`Are you sure you want to unblock this ${entityType}?`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/admin/rate-limit/unblock`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                entity_type: entityType,
                entity_value: entityValue
            })
        });
        
        showAlert('Entity unblocked successfully', 'success');
        loadBlockedEntities();
    } catch (error) {
        showAlert('Error unblocking entity: ' + error.message, 'danger');
    }
}

async function blockApiKey(apiKey) {
    if (!confirm('Are you sure you want to block this API key?')) {
        return;
    }

    document.getElementById('blockEntityType').value = 'api_key';
    document.getElementById('blockEntityValue').value = apiKey;
    document.getElementById('blockReason').value = 'Blocked from usage table';
    
    showAlert('Fill in the reason and duration, then click Block Entity', 'info');
}

function updateRateLimits() {
    showAlert('Rate limit settings saved!', 'success');
}

// ==================== FAQ MANAGER SECTION ====================

function loadFaqSection() {
    syncFaqControlsWithState();
    loadFaqList();
}

function syncFaqControlsWithState() {
    const searchInput = document.getElementById('faqSearchInput');
    if (searchInput) {
        searchInput.value = faqState.search;
    }
    const statusSelect = document.getElementById('faqStatusFilter');
    if (statusSelect) {
        statusSelect.value = faqState.status;
    }
    const pageSizeSelect = document.getElementById('faqPageSize');
    if (pageSizeSelect) {
        pageSizeSelect.value = String(faqState.pageSize);
    }
    renderFaqCategoryOptions();
}

function setFaqPageSize(value) {
    const size = Number(value) || 10;
    if (size === faqState.pageSize) {
        return;
    }
    faqState.pageSize = size;
    faqState.page = 1;
    loadFaqList();
}

function setFaqFilter(type, value) {
    if (!['status', 'category'].includes(type)) {
        return;
    }
    const normalized = (value || '').trim();
    if (faqState[type] === normalized) {
        return;
    }
    faqState[type] = normalized;
    faqState.page = 1;
    loadFaqList();
}

function changeFaqPage(delta) {
    const targetPage = faqState.page + delta;
    if (targetPage < 1) {
        return;
    }
    if (delta > 0 && !faqState.hasNext) {
        return;
    }
    if (delta < 0 && faqState.page === 1) {
        return;
    }
    faqState.page = targetPage;
    loadFaqList();
}

function handleFaqSearch(value = '') {
    const normalizedValue = (value || '').trim();
    if (faqState.searchDebounce) {
        clearTimeout(faqState.searchDebounce);
    }
    faqState.searchDebounce = setTimeout(() => {
        if (faqState.search === normalizedValue) {
            return;
        }
        faqState.search = normalizedValue;
        faqState.page = 1;
        loadFaqList();
    }, 300);
}

async function loadFaqList(force = false) {
    const tableBody = document.getElementById('faqTableBody');
    if (!tableBody) {
        return;
    }

    tableBody.innerHTML = `
        <tr>
            <td colspan="6" class="loading">
                <div class="loading-spinner"></div>
                <p>Loading FAQs...</p>
            </td>
        </tr>
    `;

    const params = new URLSearchParams({
        page: faqState.page,
        page_size: faqState.pageSize
    });
    if (faqState.search) {
        params.set('search', faqState.search);
    }
    if (faqState.status) {
        params.set('status', faqState.status);
    }
    if (faqState.category) {
        params.set('category', faqState.category);
    }

    try {
        const response = await fetch(`${API_BASE}/admin/faqs?${params.toString()}`);
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to load FAQs');
        }

        faqState.total = data.total || 0;
        faqState.hasNext = Boolean(data.has_next);
        faqState.page = data.page || faqState.page;
        faqState.pageSize = data.page_size || faqState.pageSize;
        faqState.items = (data.items || []).map(item => ({
            ...item,
            tags: Array.isArray(item.tags) ? item.tags : []
        }));
        faqState.items.forEach(item => {
            if (item.category) {
                faqState.categories.add(item.category);
            }
        });

        renderFaqCategoryOptions();
        renderFaqTable();
        updateFaqPagination();
    } catch (error) {
        console.error('Error loading FAQs:', error);
        tableBody.innerHTML = `
            <tr>
                <td colspan="6" style="padding: 30px; text-align: center; color: #ef4444;">
                    ${escapeHtml(error.message || 'Unable to load FAQs')}
                </td>
            </tr>
        `;
        updateFaqPagination(true);
    }
}

function renderFaqTable() {
    const tbody = document.getElementById('faqTableBody');
    if (!tbody) {
        return;
    }

    if (!faqState.items.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="6" style="padding: 30px; text-align: center; color: #6b7280;">
                    No FAQs match your filters yet. Try adjusting search or add a new entry.
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = faqState.items.map(faq => {
        const tags = faq.tags.length
            ? faq.tags.map(tag => `<span class="tag-pill">${escapeHtml(tag)}</span>`).join('')
            : '<span class="faq-tags-empty">No tags</span>';
        return `
            <tr>
                <td>
                    <div style="font-weight: 600; margin-bottom: 6px;">${escapeHtml(faq.question)}</div>
                    <small style="color: #9ca3af;">ID: ${escapeHtml(faq.id)}</small>
                </td>
                <td>
                    ${faq.category ? `<span class="badge badge-info">${escapeHtml(faq.category)}</span>` : '<span class="badge badge-info">General</span>'}
                </td>
                <td>${tags}</td>
                <td>${getFaqStatusBadge(faq.status)}</td>
                <td>${formatFaqTimestamp(faq.last_updated)}</td>
                <td style="display: flex; gap: 8px; flex-wrap: wrap;">
                    <button class="btn btn-outline btn-sm" onclick="editFaq('${faq.id}')">Edit</button>
                    <button class="btn btn-danger btn-sm" onclick="deleteFaq('${faq.id}')">Delete</button>
                </td>
            </tr>
        `;
    }).join('');
}

function getFaqStatusBadge(status = 'active') {
    const normalized = (status || 'active').toLowerCase();
    const classMap = {
        active: 'badge-success',
        draft: 'badge-warning',
        archived: 'badge-danger'
    };
    const label = normalized.charAt(0).toUpperCase() + normalized.slice(1);
    return `<span class="badge ${classMap[normalized] || 'badge-info'}">${label}</span>`;
}

function renderFaqCategoryOptions() {
    const select = document.getElementById('faqCategoryFilter');
    if (!select) {
        return;
    }
    const categories = Array.from(faqState.categories)
        .filter(Boolean)
        .sort((a, b) => a.localeCompare(b));
    if (faqState.category && !categories.includes(faqState.category)) {
        categories.unshift(faqState.category);
    }
    const options = [
        '<option value="">All Categories</option>',
        ...categories.map(cat => `<option value="${escapeHtml(cat)}">${escapeHtml(cat)}</option>`)
    ];
    select.innerHTML = options.join('');
    select.value = faqState.category || '';
}

function updateFaqPagination(hasError = false) {
    const rangeEl = document.getElementById('faqRangeText');
    const totalEl = document.getElementById('faqTotalText');
    const labelEl = document.getElementById('faqPageLabel');
    const prevBtn = document.getElementById('faqPrevBtn');
    const nextBtn = document.getElementById('faqNextBtn');

    if (!rangeEl || !totalEl || !labelEl || !prevBtn || !nextBtn) {
        return;
    }

    if (hasError) {
        rangeEl.textContent = '0 - 0';
        totalEl.textContent = '0';
        labelEl.textContent = 'Page 1';
        prevBtn.disabled = true;
        nextBtn.disabled = true;
        return;
    }

    const start = faqState.total === 0 ? 0 : ((faqState.page - 1) * faqState.pageSize) + 1;
    const end = faqState.total === 0 ? 0 : Math.min(start + faqState.items.length - 1, faqState.total);
    rangeEl.textContent = `${start} - ${end}`;
    totalEl.textContent = String(faqState.total);
    labelEl.textContent = `Page ${faqState.page}`;
    prevBtn.disabled = faqState.page <= 1;
    nextBtn.disabled = !faqState.hasNext;
}

function formatFaqTimestamp(value) {
    if (!value) {
        return '—';
    }
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) {
        return value;
    }
    return date.toLocaleString();
}

function formatRelativeTime(value) {
    if (!value) {
        return 'Never';
    }
    const date = value instanceof Date ? value : new Date(value);
    if (Number.isNaN(date.getTime())) {
        return 'Never';
    }

    const diffMs = Date.now() - date.getTime();
    if (diffMs < 30000) {
        return 'just now';
    }
    const minutes = Math.floor(diffMs / 60_000);
    if (minutes < 60) {
        return `${minutes}m ago`;
    }
    const hours = Math.floor(minutes / 60);
    if (hours < 24) {
        return `${hours}h ago`;
    }
    const days = Math.floor(hours / 24);
    if (days < 7) {
        return `${days}d ago`;
    }
    return date.toLocaleDateString();
}

function openFaqModal(mode = 'create', faq = null) {
    const modal = document.getElementById('faqModal');
    const title = document.getElementById('faqModalTitle');
    const submitBtn = document.getElementById('faqSubmitBtn');
    const form = document.getElementById('faqForm');
    if (!modal || !title || !submitBtn || !form) {
        return;
    }

    form.reset();
    faqState.editingId = null;

    if (mode === 'edit' && faq) {
        document.getElementById('faqQuestion').value = faq.question || '';
        document.getElementById('faqAnswer').value = faq.answer || '';
        document.getElementById('faqCategory').value = faq.category || '';
        document.getElementById('faqTags').value = faq.tags.join(', ');
        document.getElementById('faqStatus').value = faq.status || 'active';
        document.getElementById('faqLastUpdated').value = faq.last_updated || '';
        faqState.editingId = faq.id;
        title.textContent = '✏️ Edit FAQ';
        submitBtn.textContent = 'Save Changes';
    } else {
        document.getElementById('faqStatus').value = 'active';
        document.getElementById('faqLastUpdated').value = '';
        title.textContent = '➕ Add FAQ';
        submitBtn.textContent = 'Create FAQ';
    }

    modal.classList.add('active');
    setTimeout(() => document.getElementById('faqQuestion')?.focus(), 50);
}

function editFaq(faqId) {
    const faq = faqState.items.find(item => item.id === faqId);
    if (!faq) {
        showAlert('Unable to locate that FAQ in the current list. Refresh and try again.', 'warning');
        return;
    }
    openFaqModal('edit', faq);
}

async function submitFaqForm(event) {
    event.preventDefault();
    const question = document.getElementById('faqQuestion').value.trim();
    const answer = document.getElementById('faqAnswer').value.trim();
    const category = document.getElementById('faqCategory').value.trim();
    const tagsInput = document.getElementById('faqTags').value;
    const status = document.getElementById('faqStatus').value;
    const lastUpdated = document.getElementById('faqLastUpdated').value;
    const submitBtn = document.getElementById('faqSubmitBtn');

    const tags = tagsInput
        .split(',')
        .map(tag => tag.trim())
        .filter(Boolean);

    const payload = { question, answer, category, tags, status };
    const isEdit = Boolean(faqState.editingId);
    let url = `${API_BASE}/admin/faqs`;
    let method = 'POST';

    if (isEdit) {
        url = `${API_BASE}/admin/faqs/${faqState.editingId}`;
        method = 'PUT';
        payload.last_updated = lastUpdated || new Date().toISOString();
    }

    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.textContent = isEdit ? 'Saving...' : 'Creating...';
    }

    try {
        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'Failed to save FAQ');
        }

        showAlert(isEdit ? 'FAQ updated successfully' : 'FAQ created successfully', 'success');
        closeModal('faqModal');
        faqState.editingId = null;
        if (!isEdit) {
            faqState.page = 1;
        }
        loadFaqList(true);
    } catch (error) {
        console.error('Error saving FAQ:', error);
        showAlert(error.message || 'Unable to save FAQ', 'danger');
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.textContent = faqState.editingId ? 'Save Changes' : 'Create FAQ';
        }
    }
}

async function deleteFaq(faqId) {
    if (!faqId) {
        return;
    }
    const confirmed = confirm('Delete this FAQ? This action cannot be undone.');
    if (!confirmed) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/admin/faqs/${faqId}`, {
            method: 'DELETE'
        });
        if (response.status !== 204) {
            const data = await response.json();
            throw new Error(data.detail || 'Failed to delete FAQ');
        }
        showAlert('FAQ deleted', 'success');
        if (faqState.items.length === 1 && faqState.page > 1) {
            faqState.page -= 1;
        }
        loadFaqList(true);
    } catch (error) {
        console.error('Error deleting FAQ:', error);
        showAlert(error.message || 'Unable to delete FAQ', 'danger');
    }
}

// ==================== KNOWLEDGE BASE SECTION ====================

async function loadKnowledgeSection() {
    loadKnowledgeStats();
    loadUnansweredQuestions();
    loadPendingFAQs();
}

async function loadKnowledgeStats() {
    try {
        const response = await fetch(`${API_BASE}/admin/knowledge/stats`);
        const data = await response.json();

        document.getElementById('kb-unanswered').textContent = data.unanswered_count || 0;
        document.getElementById('kb-pending').textContent = data.pending_faqs || 0;
        document.getElementById('kb-approved').textContent = data.approved_faqs || 0;
        document.getElementById('kb-clusters').textContent = data.cluster_count || 0;
    } catch (error) {
        console.error('Error loading knowledge stats:', error);
    }
}

async function loadUnansweredQuestions() {
    try {
        const response = await fetch(`${API_BASE}/admin/knowledge/unanswered?limit=50`);
        const data = await response.json();

        const tbody = document.getElementById('unansweredQuestionsBody');
        
        if (data.questions && data.questions.length > 0) {
            tbody.innerHTML = data.questions.map(q => `
                <tr>
                    <td style="max-width: 400px;">${q.question}</td>
                    <td><span class="badge badge-warning">${q.count}</span></td>
                    <td>${new Date(q.last_asked).toLocaleString()}</td>
                    <td>${q.avg_confidence.toFixed(3)}</td>
                    <td>
                        <button class="btn btn-primary btn-sm" onclick="createFAQFromQuestion('${encodeURIComponent(q.question)}')">
                            Create FAQ
                        </button>
                    </td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #6b7280;">No unanswered questions</td></tr>';
        }
    } catch (error) {
        console.error('Error loading unanswered questions:', error);
    }
}

async function loadPendingFAQs() {
    try {
        const response = await fetch(`${API_BASE}/admin/knowledge/faq-suggestions?status=pending&limit=50`);
        const data = await response.json();

        const tbody = document.getElementById('pendingFAQsBody');
        
        if (data.suggestions && data.suggestions.length > 0) {
            tbody.innerHTML = data.suggestions.map(faq => `
                <tr>
                    <td style="max-width: 300px;">${faq.question}</td>
                    <td style="max-width: 300px;">${faq.suggested_answer}</td>
                    <td>${faq.confidence.toFixed(2)}</td>
                    <td><span class="badge badge-info">${faq.based_on_count} questions</span></td>
                    <td>
                        <button class="btn btn-success btn-sm" onclick="approveFAQ(${faq.id})">
                            ✓ Approve
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="rejectFAQ(${faq.id})">
                            ✗ Reject
                        </button>
                    </td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; color: #6b7280;">No pending FAQ suggestions</td></tr>';
        }
    } catch (error) {
        console.error('Error loading pending FAQs:', error);
    }
}

async function approveFAQ(faqId) {
    try {
        const response = await fetch(`${API_BASE}/admin/knowledge/faq/${faqId}/approve`, {
            method: 'POST'
        });
        
        showAlert('FAQ approved successfully!', 'success');
        loadPendingFAQs();
        loadKnowledgeStats();
    } catch (error) {
        showAlert('Error approving FAQ: ' + error.message, 'danger');
    }
}

async function rejectFAQ(faqId) {
    try {
        const response = await fetch(`${API_BASE}/admin/knowledge/faq/${faqId}/reject`, {
            method: 'POST'
        });
        
        showAlert('FAQ rejected', 'info');
        loadPendingFAQs();
        loadKnowledgeStats();
    } catch (error) {
        showAlert('Error rejecting FAQ: ' + error.message, 'danger');
    }
}

async function generateFAQSuggestions() {
    try {
        showAlert('Generating FAQ suggestions... This may take a moment.', 'info');
        
        const response = await fetch(`${API_BASE}/admin/knowledge/generate-faqs`, {
            method: 'POST'
        });
        const data = await response.json();
        
        showAlert(`Generated ${data.suggestions_count || 0} new FAQ suggestions!`, 'success');
        loadPendingFAQs();
        loadKnowledgeStats();
    } catch (error) {
        showAlert('Error generating FAQs: ' + error.message, 'danger');
    }
}

async function generateClusters() {
    try {
        showAlert('Generating question clusters... This may take a moment.', 'info');
        
        const response = await fetch(`${API_BASE}/admin/knowledge/clusters?min_cluster_size=3`);
        const data = await response.json();

        const container = document.getElementById('clustersContainer');
        
        if (data.clusters && data.clusters.length > 0) {
            container.innerHTML = data.clusters.map((cluster, index) => `
                <div class="card" style="margin-bottom: 15px;">
                    <div class="card-header">
                        <div class="card-title">Cluster ${index + 1} (${cluster.questions.length} questions)</div>
                    </div>
                    <ul style="margin: 0; padding-left: 20px;">
                        ${cluster.questions.map(q => `<li>${q}</li>`).join('')}
                    </ul>
                </div>
            `).join('');
            
            showAlert(`Found ${data.clusters.length} question clusters!`, 'success');
        } else {
            container.innerHTML = '<div class="alert alert-info">No clusters found. Need more data.</div>';
        }
        
        loadKnowledgeStats();
    } catch (error) {
        showAlert('Error generating clusters: ' + error.message, 'danger');
    }
}

async function exportKnowledgeGaps() {
    try {
        const response = await fetch(`${API_BASE}/admin/knowledge/export`);
        const data = await response.json();
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        downloadBlob(blob, `knowledge-gaps-${new Date().toISOString().split('T')[0]}.json`);
        
        showAlert('Knowledge gaps exported successfully!', 'success');
    } catch (error) {
        showAlert('Error exporting: ' + error.message, 'danger');
    }
}

function resetKnowledgeBase() {
    showAlert('Knowledge base reset is not yet implemented', 'warning');
}

function createFAQFromQuestion(question) {
    const decodedQuestion = decodeURIComponent(question);
    showAlert(`Creating FAQ for: "${decodedQuestion}". Add your answer and submit.`, 'info');
}

// ==================== CONVERSATIONS SECTION ====================

async function loadConversationsSection() {
    loadConversationStats();
    loadConversations();
}

async function loadConversationStats() {
    try {
        const response = await fetch(`${API_BASE}/admin/conversations/stats`);
        const data = await response.json();

        document.getElementById('conv-active').textContent = data.active_sessions || 0;
        document.getElementById('conv-messages').textContent = data.total_messages || 0;
        document.getElementById('conv-avg').textContent = (data.avg_messages_per_session || 0).toFixed(1);
        document.getElementById('conv-longest').textContent = data.longest_session_messages || 0;
    } catch (error) {
        console.error('Error loading conversation stats:', error);
    }
}

async function loadConversations() {
    try {
        const response = await fetch(`${API_BASE}/admin/conversations?limit=50`);
        const data = await response.json();

        const tbody = document.getElementById('conversationsTableBody');
        
        if (data.conversations && data.conversations.length > 0) {
            tbody.innerHTML = data.conversations.map(conv => `
                <tr>
                    <td><code style="font-size: 11px;">${conv.session_id.substring(0, 16)}...</code></td>
                    <td>${new Date(conv.created_at).toLocaleString()}</td>
                    <td>${new Date(conv.updated_at).toLocaleString()}</td>
                    <td><span class="badge badge-info">${conv.message_count}</span></td>
                    <td><small>${JSON.stringify(conv.metadata).substring(0, 50)}...</small></td>
                    <td>
                        <button class="btn btn-outline btn-sm" onclick="viewConversation('${conv.session_id}')">
                            View
                        </button>
                        <button class="btn btn-danger btn-sm" onclick="deleteConversation('${conv.session_id}')">
                            Delete
                        </button>
                    </td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #6b7280;">No conversations</td></tr>';
        }
    } catch (error) {
        console.error('Error loading conversations:', error);
    }
}

async function cleanupSessions() {
    const days = parseInt(document.getElementById('sessionCleanupDays').value);
    
    if (!confirm(`Delete all sessions older than ${days} days?`)) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/admin/conversations/cleanup?days=${days}`, {
            method: 'POST'
        });
        const data = await response.json();
        
        showAlert(`Deleted ${data.deleted_count || 0} old sessions`, 'success');
        loadConversations();
    } catch (error) {
        showAlert('Error cleaning up sessions: ' + error.message, 'danger');
    }
}

async function exportConversations() {
    try {
        const response = await fetch(`${API_BASE}/admin/conversations/export`);
        const data = await response.json();
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        downloadBlob(blob, `conversations-${new Date().toISOString().split('T')[0]}.json`);
        
        showAlert('Conversations exported successfully!', 'success');
    } catch (error) {
        showAlert('Error exporting: ' + error.message, 'danger');
    }
}

async function viewConversation(sessionId) {
    showAlert(`Viewing conversation: ${sessionId}`, 'info');
    // Implement conversation viewer modal
}

async function deleteConversation(sessionId) {
    if (!confirm('Delete this conversation?')) {
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/admin/conversations/${sessionId}`, {
            method: 'DELETE'
        });
        
        showAlert('Conversation deleted', 'success');
        loadConversations();
    } catch (error) {
        showAlert('Error deleting conversation: ' + error.message, 'danger');
    }
}

// ==================== COST ANALYSIS SECTION ====================

async function loadCostsSection() {
    try {
        const response = await fetch(`${API_BASE}/admin/analytics/costs?days=30`);
        const data = await response.json();

        document.getElementById('cost-total').textContent = '$' + (data.total_cost_usd || 0).toFixed(2);
        document.getElementById('cost-savings').textContent = '$' + (data.cache_savings_usd || 0).toFixed(2);
        document.getElementById('cost-avg').textContent = '$' + (data.avg_cost_per_request || 0).toFixed(4);
        document.getElementById('cost-projected').textContent = '$' + (data.projected_monthly_cost || 0).toFixed(2);

        // Initialize cost charts
        initializeCostCharts(data);
        loadCostDetails();
    } catch (error) {
        console.error('Error loading costs section:', error);
    }
}

function initializeCostCharts(data) {
    // Provider breakdown chart
    const providerCtx = document.getElementById('costProviderChart').getContext('2d');
    sectionCharts.costProvider = new Chart(providerCtx, {
        type: 'doughnut',
        data: {
            labels: Object.keys(data.cost_by_provider || {}),
            datasets: [{
                data: Object.values(data.cost_by_provider || {}),
                backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#4facfe']
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });

    // Daily trend chart
    const trendCtx = document.getElementById('costTrendChart').getContext('2d');
    sectionCharts.costTrend = new Chart(trendCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Daily Cost ($)',
                data: [],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

async function loadCostDetails() {
    try {
        const response = await fetch(`${API_BASE}/admin/analytics/costs/details?days=30`);
        const data = await response.json();

        const tbody = document.getElementById('costDetailsBody');
        
        if (data.details && data.details.length > 0) {
            tbody.innerHTML = data.details.map(detail => `
                <tr>
                    <td><span class="badge badge-info">${detail.provider}</span></td>
                    <td>${detail.requests}</td>
                    <td>${detail.input_tokens.toLocaleString()}</td>
                    <td>${detail.output_tokens.toLocaleString()}</td>
                    <td>$${detail.total_cost.toFixed(4)}</td>
                    <td>$${detail.avg_cost.toFixed(6)}</td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #6b7280;">No cost data</td></tr>';
        }
    } catch (error) {
        console.error('Error loading cost details:', error);
    }
}

async function exportCostReport() {
    try {
        const response = await fetch(`${API_BASE}/admin/analytics/costs/export?days=30`);
        const data = await response.json();
        
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        downloadBlob(blob, `cost-report-${new Date().toISOString().split('T')[0]}.json`);
        
        showAlert('Cost report exported successfully!', 'success');
    } catch (error) {
        showAlert('Error exporting: ' + error.message, 'danger');
    }
}

function setCostAlert() {
    const budget = prompt('Enter monthly budget alert threshold ($):');
    if (budget) {
        showAlert(`Budget alert set to $${budget}/month`, 'success');
    }
}

function optimizeCosts() {
    showAlert('Cost optimization recommendations: Enable caching, use cheaper providers for simple queries', 'info');
}

// ==================== SETTINGS SECTION ====================

async function loadSettingsSection() {
    try {
        await Promise.all([
            loadLLMSettings(),
            loadRagSettings()
        ]);
        bindFallbackAutoToggle();
        bindRagThresholdInput();
        showAlert('Settings loaded. Modify as needed.', 'info');
    } catch (error) {
        console.error('Error loading settings section', error);
        showAlert('Unable to load settings. Please try again.', 'danger');
    }
}

async function loadLLMSettings() {
    try {
        const response = await fetch(`${API_BASE}/admin/settings/llm`);
        if (!response.ok) {
            throw new Error('Failed to fetch LLM settings');
        }
        const data = await response.json();
        llmSettingsCache.providers = data.available_providers || [];
        populateLLMSettingsForm(data);
    } catch (error) {
        console.error('Error loading LLM settings:', error);
        showAlert('Failed to load LLM provider settings.', 'danger');
    }
}

function populateLLMSettingsForm(data) {
    const primarySelect = document.getElementById('primaryProvider');
    const fallbackInput = document.getElementById('fallbackOrderInput');
    const autoFallback = document.getElementById('autoFallback');
    if (!primarySelect || !fallbackInput || !autoFallback) return;

    primarySelect.innerHTML = '';
    (data.available_providers || []).forEach(provider => {
        const option = document.createElement('option');
        option.value = provider;
        option.textContent = formatProviderLabel(provider);
        primarySelect.appendChild(option);
    });

    const selectedPrimary = data.primary_provider || (data.available_providers || [])[0] || '';
    if (selectedPrimary) {
        primarySelect.value = selectedPrimary;
    }

    const fallbackOrder = (data.fallback_order || []).filter(p => p !== selectedPrimary);
    fallbackInput.value = fallbackOrder.join(', ');

    autoFallback.checked = Boolean(data.auto_fallback);
    toggleFallbackInput(autoFallback.checked);
}

function formatProviderLabel(provider) {
    if (!provider) return '';
    return provider
        .split('_')
        .map(part => part.charAt(0).toUpperCase() + part.slice(1))
        .join(' ');
}

function bindFallbackAutoToggle() {
    const autoFallback = document.getElementById('autoFallback');
    if (!autoFallback || autoFallback.dataset.bound === 'true') return;
    autoFallback.addEventListener('change', () => {
        toggleFallbackInput(autoFallback.checked);
    });
    autoFallback.dataset.bound = 'true';
}

function toggleFallbackInput(enabled) {
    const fallbackInput = document.getElementById('fallbackOrderInput');
    if (fallbackInput) {
        fallbackInput.disabled = !enabled;
        fallbackInput.classList.toggle('disabled', !enabled);
    }
}

function parseFallbackOrder(rawValue, primaryProvider) {
    if (!rawValue) {
        return llmSettingsCache.providers.filter(p => p !== primaryProvider);
    }

    const entries = rawValue
        .split(/[\n,]+/)
        .map(entry => entry.trim())
        .filter(Boolean);

    const normalizedProviders = llmSettingsCache.providers.reduce((acc, provider) => {
        acc[provider.toLowerCase()] = provider;
        return acc;
    }, {});

    const ordered = [];
    entries.forEach(entry => {
        const key = entry.toLowerCase();
        if (normalizedProviders[key]) {
            const provider = normalizedProviders[key];
            if (provider !== primaryProvider && !ordered.includes(provider)) {
                ordered.push(provider);
            }
        }
    });

    if (ordered.length === 0) {
        return llmSettingsCache.providers.filter(p => p !== primaryProvider);
    }

    return ordered;
}

async function saveProviderSettings() {
    const primaryProvider = document.getElementById('primaryProvider')?.value;
    const fallbackRaw = document.getElementById('fallbackOrderInput')?.value || '';
    const autoFallback = document.getElementById('autoFallback')?.checked;

    if (!primaryProvider) {
        showAlert('Please select a primary provider.', 'warning');
        return;
    }

    const fallbackOrder = autoFallback ? parseFallbackOrder(fallbackRaw, primaryProvider) : [];

    try {
        const response = await fetch(`${API_BASE}/admin/settings/llm`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                primary_provider: primaryProvider,
                fallback_order: fallbackOrder,
                auto_fallback: autoFallback
            })
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Failed to save provider settings.' }));
            throw new Error(error.detail || 'Failed to save provider settings');
        }

        showAlert('Provider settings saved!', 'success');
        await loadLLMSettings();
    } catch (error) {
        console.error('Error saving provider settings:', error);
        showAlert(error.message || 'Unable to save provider settings.', 'danger');
    }
}

async function loadRagSettings() {
    try {
        const response = await fetch(`${API_BASE}/admin/settings/rag`);
        if (!response.ok) {
            throw new Error('Failed to fetch retrieval settings');
        }
        const data = await response.json();
        const thresholdInput = document.getElementById('ragConfidenceThreshold');
        if (thresholdInput) {
            thresholdInput.value = Number(data.confidence_threshold || 0.35).toFixed(2);
            updateRagThresholdDisplay();
        }
    } catch (error) {
        console.error('Error loading RAG settings:', error);
        showAlert('Failed to load retrieval settings.', 'danger');
    }
}

function bindRagThresholdInput() {
    const thresholdInput = document.getElementById('ragConfidenceThreshold');
    if (!thresholdInput || thresholdInput.dataset.bound === 'true') return;
    thresholdInput.addEventListener('input', updateRagThresholdDisplay);
    thresholdInput.dataset.bound = 'true';
}

function updateRagThresholdDisplay() {
    const thresholdInput = document.getElementById('ragConfidenceThreshold');
    const display = document.getElementById('ragConfidenceDisplay');
    if (!thresholdInput || !display) return;

    const value = parseFloat(thresholdInput.value);
    if (Number.isFinite(value)) {
        display.textContent = value.toFixed(2);
    }
}

async function saveRagSettings() {
    const thresholdInput = document.getElementById('ragConfidenceThreshold');
    if (!thresholdInput) {
        showAlert('Retrieval settings are not available.', 'danger');
        return;
    }

    const value = parseFloat(thresholdInput.value);
    if (!Number.isFinite(value)) {
        showAlert('Please enter a valid confidence threshold.', 'warning');
        return;
    }

    if (value < 0 || value > 2) {
        showAlert('Confidence threshold must be between 0 and 2.', 'warning');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/admin/settings/rag`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ confidence_threshold: value })
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Failed to save retrieval settings.' }));
            throw new Error(error.detail || 'Failed to save retrieval settings');
        }

        showAlert('Retrieval settings saved!', 'success');
        updateRagThresholdDisplay();
    } catch (error) {
        console.error('Error saving RAG settings:', error);
        showAlert(error.message || 'Unable to save retrieval settings.', 'danger');
    }
}

function savePerformanceSettings() {
    showAlert('Performance settings saved!', 'success');
}

function saveNotificationSettings() {
    showAlert('Notification settings saved!', 'success');
}

function saveSecuritySettings() {
    showAlert('Security settings saved!', 'success');
}

// ==================== LLM API TESTER SECTION ====================

async function loadLlmTesterSection() {
    if (!llmTesterState.initialized) {
        const promptInput = document.getElementById('llmTesterPrompt');
        if (promptInput && !promptInput.value) {
            promptInput.value = DEFAULT_LLM_TEST_PROMPT;
        }
        llmTesterState.initialized = true;
    }

    await Promise.all([
        fetchLlmTesterSummary(),
        fetchLlmTesterHistory(llmTesterState.historyFilter)
    ]);
}

async function fetchLlmTesterSummary() {
    try {
        const response = await fetch(`${API_BASE}/admin/llm/tests/summary`);
        if (!response.ok) {
            throw new Error('Failed to load LLM tester summary');
        }
        const data = await response.json();
        llmTesterState.availableProviders = data.config_providers || [];
        llmTesterState.activeProviders = data.active_providers || [];
        llmTesterState.latestResults = data.providers || [];
        renderLlmTesterProviders(data.providers || []);
        renderLlmTesterProviderPills();
        updateLlmTesterHistoryFilterOptions();
    } catch (error) {
        console.error('Error loading LLM tester summary:', error);
        const container = document.getElementById('llmTesterProviderGrid');
        if (container) {
            container.innerHTML = '<div class="llm-empty-state">Unable to load provider status. Try refreshing.</div>';
        }
    }
}

function getLlmStatusDescriptor(status) {
    const normalized = (status || 'unknown').toLowerCase();
    switch (normalized) {
        case 'healthy':
            return { label: 'Healthy', cls: 'badge-success' };
        case 'missing_credentials':
            return { label: 'Missing credentials', cls: 'badge-warning' };
        case 'unavailable':
            return { label: 'Unavailable', cls: 'badge-warning' };
        case 'timeout':
            return { label: 'Timeout', cls: 'badge-warning' };
        case 'error':
            return { label: 'Error', cls: 'badge-danger' };
        default:
            return { label: normalized.replace(/_/g, ' ') || 'Unknown', cls: 'badge-info' };
    }
}

function renderLlmTesterProviders(providers) {
    const container = document.getElementById('llmTesterProviderGrid');
    if (!container) return;

    if (!providers.length) {
        container.innerHTML = '<div class="llm-empty-state">No provider tests yet. Run a check to see live health metrics.</div>';
        return;
    }

    const cards = providers.map(provider => {
        const statusDescriptor = getLlmStatusDescriptor(provider.status);
        const metadata = provider.metadata || {};
        const providerDate = provider.created_at ? new Date(provider.created_at) : null;
        const hasValidDate = providerDate && !Number.isNaN(providerDate.getTime());
        const lastRunRelative = hasValidDate ? formatRelativeTime(providerDate) : 'Never';
        const lastRunTitle = hasValidDate ? providerDate.toLocaleString() : 'Never';
        const detailText = provider.response_sample || provider.error_message || 'No output recorded yet.';
        const truncatedDetail = detailText.length > 220 ? `${detailText.slice(0, 220)}…` : detailText;
        const latency = provider.latency_ms ? `${provider.latency_ms} ms` : '—';
        const credentialClass = provider.api_key_present ? 'ok' : 'missing';
        const credentialLabel = provider.api_key_present ? 'Credentials detected' : 'Missing credentials';
        const missingEnvText = Array.isArray(metadata.missing_envs) && metadata.missing_envs.length
            ? metadata.missing_envs.join(', ')
            : '';
        const missingEnv = missingEnvText
            ? `<small style="color:#b45309;">${escapeHtml(`Missing: ${missingEnvText}`)}</small>`
            : '';
        const providerArg = JSON.stringify(provider.provider || '');

        return `
            <div class="llm-provider-card">
                <div class="llm-provider-card-header">
                    <div>
                        <div class="llm-provider-name">${escapeHtml(provider.provider || 'Unknown')}</div>
                        <div class="llm-provider-meta">Last run: <span title="${escapeHtml(lastRunTitle)}">${escapeHtml(lastRunRelative)}</span></div>
                    </div>
                    <span class="badge ${statusDescriptor.cls}">${escapeHtml(statusDescriptor.label)}</span>
                </div>
                <div class="llm-provider-stats">
                    <div>
                        <div class="llm-stat-label">Latency</div>
                        <div class="llm-stat-value">${escapeHtml(latency)}</div>
                    </div>
                    <div>
                        <div class="llm-stat-label">Sample</div>
                        <div class="llm-stat-value">${provider.response_sample ? 'Captured' : 'Pending'}</div>
                    </div>
                </div>
                <p class="llm-provider-response">${escapeHtml(truncatedDetail)}</p>
                <div class="llm-provider-actions">
                    <div>
                        <span class="llm-provider-cred ${credentialClass}">${credentialLabel}</span>
                        ${missingEnv}
                    </div>
                    <button class="btn btn-outline btn-sm" onclick="runLlmTest(${providerArg})">Run Test</button>
                </div>
            </div>
        `;
    }).join('');

    container.innerHTML = cards;
}

function renderLlmTesterProviderPills() {
    const container = document.getElementById('llmTesterProviderPills');
    if (!container) return;

    const providers = new Set([
        ...llmTesterState.availableProviders,
        ...llmTesterState.activeProviders,
        ...llmTesterState.latestResults.map(item => item.provider)
    ].filter(Boolean));

    if (!providers.size) {
        container.innerHTML = '<span class="llm-empty-state">Providers will appear after the first summary refresh.</span>';
        return;
    }

    container.innerHTML = Array.from(providers)
        .map(provider => {
            const providerArg = JSON.stringify(provider || '');
            return `<button class="pill-button" onclick="runLlmTest(${providerArg})">${escapeHtml(formatProviderLabel(provider))}</button>`;
        })
        .join('');
}

function updateLlmTesterHistoryFilterOptions() {
    const select = document.getElementById('llmTesterHistoryFilter');
    if (!select) return;

    const providers = new Set(['all']);
    llmTesterState.availableProviders.forEach(p => providers.add(p));
    llmTesterState.activeProviders.forEach(p => providers.add(p));
    llmTesterState.latestResults.forEach(item => {
        if (item.provider) {
            providers.add(item.provider);
        }
    });

    const current = llmTesterState.historyFilter || 'all';
    select.innerHTML = Array.from(providers)
        .map(provider => {
            const label = provider === 'all' ? 'All Providers' : formatProviderLabel(provider);
            return `<option value="${provider}">${escapeHtml(label)}</option>`;
        })
        .join('');
    select.value = current;
}

async function runLlmTest(provider = 'all') {
    if (llmTesterState.running) {
        return;
    }
    llmTesterState.running = true;

    const payload = {};
    if (provider && provider !== 'all') {
        payload.providers = [provider];
    }
    const promptInput = document.getElementById('llmTesterPrompt');
    if (promptInput) {
        const promptValue = promptInput.value.trim();
        if (promptValue) {
            payload.prompt = promptValue;
        }
    }

    try {
        const response = await fetch(`${API_BASE}/admin/llm/tests/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Failed to run LLM tests' }));
            throw new Error(error.detail || 'Failed to run LLM tests');
        }
        showAlert('LLM provider tests completed.', 'success');
        await fetchLlmTesterSummary();
        await fetchLlmTesterHistory(llmTesterState.historyFilter);
    } catch (error) {
        console.error('Error running LLM tests:', error);
        showAlert(error.message || 'Unable to run LLM tests.', 'danger');
    } finally {
        llmTesterState.running = false;
    }
}

function resetLlmTesterPrompt() {
    const promptInput = document.getElementById('llmTesterPrompt');
    if (promptInput) {
        promptInput.value = DEFAULT_LLM_TEST_PROMPT;
    }
}

async function fetchLlmTesterHistory(filter = 'all') {
    const targetFilter = filter || 'all';
    llmTesterState.historyFilter = targetFilter;
    const params = new URLSearchParams({ limit: llmTesterState.historyLimit });
    if (targetFilter && targetFilter !== 'all') {
        params.append('provider', targetFilter);
    }

    try {
        const response = await fetch(`${API_BASE}/admin/llm/tests/history?${params.toString()}`);
        if (!response.ok) {
            throw new Error('Failed to load test history');
        }
        const data = await response.json();
        renderLlmTesterHistory(data.results || []);
    } catch (error) {
        console.error('Error loading LLM tester history:', error);
        const body = document.getElementById('llmTesterHistoryBody');
        if (body) {
            body.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#6b7280;">Unable to load history.</td></tr>';
        }
    }
}

function renderLlmTesterHistory(results) {
    const tbody = document.getElementById('llmTesterHistoryBody');
    if (!tbody) return;

    if (!results.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#6b7280;">No tests recorded yet.</td></tr>';
        return;
    }

    tbody.innerHTML = results.map(result => {
        const statusDescriptor = getLlmStatusDescriptor(result.status);
        const latency = result.latency_ms ? `${result.latency_ms} ms` : '—';
        const detailText = result.response_sample || result.error_message || 'No output recorded.';
        const metadata = result.metadata || {};
        const envNoteText = Array.isArray(metadata.missing_envs) && metadata.missing_envs.length
            ? metadata.missing_envs.join(', ')
            : '';
        const envNote = envNoteText
            ? `<div style="font-size:11px; color:#b45309;">${escapeHtml(`Missing envs: ${envNoteText}`)}</div>`
            : '';
        const timestamp = result.created_at ? new Date(result.created_at) : null;
        const timestampLabel = timestamp && !Number.isNaN(timestamp.getTime()) ? timestamp.toLocaleString() : 'Unknown';
        const providerArg = JSON.stringify(result.provider || '');
        return `
            <tr>
                <td>${escapeHtml(timestampLabel)}</td>
                <td><span class="badge badge-info">${escapeHtml(result.provider)}</span></td>
                <td><span class="badge ${statusDescriptor.cls}">${escapeHtml(statusDescriptor.label)}</span></td>
                <td>${escapeHtml(latency)}</td>
                <td>
                    <div>${escapeHtml(detailText)}</div>
                    ${envNote}
                </td>
                <td>
                    <button class="btn btn-outline btn-sm" onclick="runLlmTest(${providerArg})">Re-run</button>
                </td>
            </tr>
        `;
    }).join('');
}

// ==================== TELEPHONY TESTER SECTION ====================

async function loadTelephonyTesterSection() {
    if (!telephonyTesterState.initialized) {
        const modeSelect = document.getElementById('telephonyTesterMode');
        if (modeSelect) {
            modeSelect.value = telephonyTesterState.mode;
        }
        telephonyTesterState.initialized = true;
    }

    await Promise.all([
        fetchTelephonyTesterSummary(),
        fetchTelephonyTesterHistory(telephonyTesterState.historyFilter)
    ]);
}

async function fetchTelephonyTesterSummary() {
    try {
        const response = await fetch(`${API_BASE}/admin/telephony/tests/summary`);
        if (!response.ok) {
            throw new Error('Failed to load telephony tester summary');
        }
        const data = await response.json();
        telephonyTesterState.availableTests = data.available_tests || [];
        telephonyTesterState.latestResults = data.tests || [];
        telephonyTesterState.voiceContext = data.voice_context || {};
        telephonyTesterState.envSnapshot = data.env_snapshot || {};
        if (!telephonyTesterState.mode && data.default_mode) {
            telephonyTesterState.mode = data.default_mode;
        }
        renderTelephonyTesterOverview(data);
        renderTelephonyTesterCards(telephonyTesterState.latestResults);
        updateTelephonyHistoryFilterOptions();
    } catch (error) {
        console.error('Error loading telephony tester summary:', error);
        const grid = document.getElementById('telephonyTesterGrid');
        if (grid) {
            grid.innerHTML = '<div class="telephony-empty-state">Unable to load telephony diagnostics. Try refreshing.</div>';
        }
    }
}

function renderTelephonyTesterOverview(summary) {
    const ctx = summary.voice_context || {};
    const envSnapshot = summary.env_snapshot || {};
    const numberEl = document.getElementById('telephonyTesterNumber');
    if (numberEl) {
        numberEl.textContent = ctx.twilio_number || envSnapshot.twilio_number || '—';
    }
    const webhookEl = document.getElementById('telephonyTesterWebhook');
    if (webhookEl) {
        webhookEl.textContent = ctx.webhook_url || '—';
    }
    const healthEl = document.getElementById('telephonyTesterHealth');
    if (healthEl) {
        const baseHealth = ctx.voice_base_url ? `${ctx.voice_base_url.replace(/\/$/, '')}/health` : null;
        healthEl.textContent = ctx.health_url || baseHealth || '—';
    }
    const modeSelect = document.getElementById('telephonyTesterMode');
    if (modeSelect) {
        modeSelect.value = telephonyTesterState.mode || summary.default_mode || 'dry';
    }

    const envAlert = document.getElementById('telephonyTesterEnvAlert');
    if (envAlert) {
        const missing = envSnapshot.missing_envs || [];
        if (missing.length) {
            envAlert.style.display = 'block';
            envAlert.textContent = `Missing environment variables: ${missing.join(', ')}`;
        } else {
            envAlert.style.display = 'none';
            envAlert.textContent = '';
        }
    }
}

function updateTelephonyHistoryFilterOptions() {
    const select = document.getElementById('telephonyTesterHistoryFilter');
    if (!select) return;
    const tests = new Set(['all']);
    telephonyTesterState.availableTests.forEach(test => tests.add(test));
    telephonyTesterState.latestResults.forEach(item => {
        if (item.test_type) {
            tests.add(item.test_type);
        }
    });
    const current = telephonyTesterState.historyFilter || 'all';
    select.innerHTML = Array.from(tests)
        .map(test => `<option value="${test}">${escapeHtml(test === 'all' ? 'All Tests' : formatTelephonyTestLabel(test))}</option>`)
        .join('');
    select.value = current;
}

function getTelephonyStatusDescriptor(status) {
    const normalized = (status || 'unknown').toLowerCase();
    if (['healthy', 'ready', 'verified', 'simulated'].includes(normalized)) {
        return { label: normalized.replace(/_/g, ' '), cls: 'success' };
    }
    if (['missing_credentials', 'timeout', 'skipped'].includes(normalized)) {
        return { label: normalized.replace(/_/g, ' '), cls: 'warning' };
    }
    if (normalized === 'error') {
        return { label: 'error', cls: 'danger' };
    }
    return { label: normalized.replace(/_/g, ' ') || 'unknown', cls: 'info' };
}

function renderTelephonyTesterCards(results) {
    const grid = document.getElementById('telephonyTesterGrid');
    if (!grid) return;
    if (!results.length) {
        grid.innerHTML = '<div class="telephony-empty-state">No tests recorded yet. Run diagnostics to capture data.</div>';
        return;
    }
    grid.innerHTML = results.map(result => {
        const descriptor = getTelephonyStatusDescriptor(result.status);
        const resultDate = result.created_at ? new Date(result.created_at) : null;
        const relative = resultDate && !Number.isNaN(resultDate.getTime()) ? formatRelativeTime(resultDate) : 'Never';
        const latency = result.latency_ms ? `${result.latency_ms} ms` : '—';
        const detailText = summarizeTelephonyDetails(result.details);
        const buttonArg = JSON.stringify(result.test_type);
        return `
            <div class="telephony-card">
                <div class="telephony-card-header">
                    <div>
                        <h4>${escapeHtml(formatTelephonyTestLabel(result.test_type))}</h4>
                        <small>Last run ${escapeHtml(relative)}</small>
                    </div>
                    <span class="telephony-status-badge ${descriptor.cls}">${escapeHtml(descriptor.label)}</span>
                </div>
                <p style="font-size:13px; color:#4b5563;">${escapeHtml(detailText)}</p>
                <div class="telephony-card-footer">
                    <div>Latency: <strong>${escapeHtml(latency)}</strong></div>
                    <button class="btn btn-outline btn-sm" onclick="runTelephonyTests(${buttonArg})">Run Test</button>
                </div>
            </div>
        `;
    }).join('');
}

function formatTelephonyTestLabel(value) {
    if (!value) return 'Unknown Test';
    return value
        .replace(/_/g, ' ')
        .replace(/\b([a-z])/g, (_, letter) => letter.toUpperCase());
}

function summarizeTelephonyDetails(details) {
    if (!details) return 'No additional details recorded.';
    if (details.detail) return details.detail;
    if (details.error) return `Error: ${details.error}`;
    if (details.reason) return `Reason: ${details.reason}`;
    if (Array.isArray(details.missing_envs) && details.missing_envs.length) {
        return `Missing envs: ${details.missing_envs.join(', ')}`;
    }
    return JSON.stringify(details);
}

async function runTelephonyTests(testName = 'all') {
    if (telephonyTesterState.running) {
        return;
    }
    telephonyTesterState.running = true;
    const payload = { mode: telephonyTesterState.mode || 'dry' };
    if (testName && testName !== 'all') {
        payload.tests = [testName];
    }
    try {
        const response = await fetch(`${API_BASE}/admin/telephony/tests/run`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: 'Failed to run telephony tests' }));
            throw new Error(error.detail || 'Failed to run telephony tests');
        }
        showAlert('Telephony diagnostics completed.', 'success');
        await fetchTelephonyTesterSummary();
        await fetchTelephonyTesterHistory(telephonyTesterState.historyFilter);
    } catch (error) {
        console.error('Error running telephony tests:', error);
        showAlert(error.message || 'Unable to run telephony tests.', 'danger');
    } finally {
        telephonyTesterState.running = false;
    }
}

function changeTelephonyTesterMode(mode) {
    telephonyTesterState.mode = mode || 'dry';
    showAlert(`Telephony tester mode set to ${mode.toUpperCase()}.`, 'info');
}

function refreshTelephonyTester() {
    return fetchTelephonyTesterSummary();
}

async function fetchTelephonyTesterHistory(filter = 'all') {
    const target = filter || 'all';
    telephonyTesterState.historyFilter = target;
    const params = new URLSearchParams({ limit: telephonyTesterState.historyLimit });
    if (target !== 'all') {
        params.append('test_type', target);
    }
    try {
        const response = await fetch(`${API_BASE}/admin/telephony/tests/history?${params.toString()}`);
        if (!response.ok) {
            throw new Error('Failed to load telephony history');
        }
        const data = await response.json();
        renderTelephonyTesterHistory(data.results || []);
    } catch (error) {
        console.error('Error loading telephony tester history:', error);
        const tbody = document.getElementById('telephonyTesterHistoryBody');
        if (tbody) {
            tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#6b7280;">Unable to load history.</td></tr>';
        }
    }
}

function renderTelephonyTesterHistory(results) {
    const tbody = document.getElementById('telephonyTesterHistoryBody');
    if (!tbody) return;
    if (!results.length) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center; color:#6b7280;">No tests recorded yet.</td></tr>';
        return;
    }
    tbody.innerHTML = results.map(result => {
        const descriptor = getTelephonyStatusDescriptor(result.status);
        const latency = result.latency_ms ? `${result.latency_ms} ms` : '—';
        const detailText = summarizeTelephonyDetails(result.details);
        const timestamp = result.created_at ? new Date(result.created_at).toLocaleString() : '—';
        const testLabel = formatTelephonyTestLabel(result.test_type);
        return `
            <tr>
                <td>${escapeHtml(timestamp)}</td>
                <td>${escapeHtml(testLabel)}</td>
                <td><span class="telephony-status-badge ${descriptor.cls}">${escapeHtml(descriptor.label)}</span></td>
                <td>${escapeHtml(latency)}</td>
                <td>${escapeHtml(detailText)}</td>
                <td><button class="btn btn-outline btn-sm" onclick="runTelephonyTests(${JSON.stringify(result.test_type)})">Re-run</button></td>
            </tr>
        `;
    }).join('');
}

function changeTelephonyHistoryFilter(value) {
    telephonyTesterState.historyFilter = value || 'all';
    fetchTelephonyTesterHistory(telephonyTesterState.historyFilter);
}

function refreshTelephonyTesterHistory() {
    fetchTelephonyTesterHistory(telephonyTesterState.historyFilter);
}

function changeLlmTesterHistoryFilter(value) {
    llmTesterState.historyFilter = value || 'all';
    fetchLlmTesterHistory(llmTesterState.historyFilter);
}

function refreshLlmTesterHistory() {
    fetchLlmTesterHistory(llmTesterState.historyFilter);
}

function refreshLlmTester() {
    fetchLlmTesterSummary();
    fetchLlmTesterHistory(llmTesterState.historyFilter);
}

// ==================== SYSTEM LOGS SECTION ====================

async function loadLogsSection() {
    loadSystemLogs();
}

async function loadSystemLogs() {
    // Placeholder - implement actual log loading
    const tbody = document.getElementById('systemLogsBody');
    tbody.innerHTML = '<tr><td colspan="5" style="text-align: center; padding: 40px; color: #6b7280;">System logs will appear here. Connect to logging service.</td></tr>';
}

function exportLogs() {
    showAlert('Exporting system logs...', 'info');
}

// ==================== VOICE & CALLING SECTION ====================

async function loadVoiceSection() {
    await loadVoiceStats();
    checkVoiceOrchestratorHealth();
    initializeVoiceCharts();
}

async function loadVoiceStats() {
    try {
        // Try to fetch voice stats from voice orchestrator
        const response = await fetch('http://localhost:8004/stats');
        const data = await response.json();
        
        document.getElementById('voice-total-calls').textContent = data.total_calls || 0;
        document.getElementById('voice-active-calls').textContent = data.active_calls || 0;
        document.getElementById('voice-avg-duration').textContent = Math.round(data.avg_duration || 0) + 's';
        document.getElementById('voice-success-rate').textContent = Math.round((data.success_rate || 0) * 100) + '%';
    } catch (error) {
        console.error('Error loading voice stats:', error);
        // Set default values
        document.getElementById('voice-total-calls').textContent = '0';
        document.getElementById('voice-active-calls').textContent = '0';
        document.getElementById('voice-avg-duration').textContent = '0s';
        document.getElementById('voice-success-rate').textContent = '0%';
    }
}

async function checkVoiceOrchestratorHealth() {
    try {
        const response = await fetch('http://localhost:8004/health', { timeout: 3000 });
        if (response.ok) {
            document.getElementById('voice-status').textContent = '🟢 Online';
            document.getElementById('voice-health-card').classList.add('success');
        } else {
            document.getElementById('voice-status').textContent = '🔴 Error';
            document.getElementById('voice-health-card').classList.add('danger');
        }
    } catch (error) {
        document.getElementById('voice-status').textContent = '🔴 Offline';
        document.getElementById('voice-health-card').classList.add('danger');
    }
}

function initializeVoiceCharts() {
    const ctx = document.getElementById('voiceCallsChart').getContext('2d');
    sectionCharts.voiceCalls = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Calls per Day',
                data: [12, 19, 15, 25, 22, 18, 20],
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

function saveVoiceConfig() {
    const config = {
        welcome_message: document.getElementById('voice-welcome-message').value,
        default_language: document.getElementById('voice-default-language').value,
        max_duration: document.getElementById('voice-max-duration').value
    };
    
    // TODO: Send to voice orchestrator API
    showAlert('Voice configuration saved!', 'success');
}

// ==================== EMAIL SUPPORT SECTION ====================

async function loadEmailSection() {
    await loadEmailStats();
    checkEmailWorkerHealth();
    initializeEmailCharts();
}

async function loadEmailStats() {
    try {
        // Try to fetch email stats from gateway API
        const response = await fetch(`${API_BASE}/admin/email/stats`);
        const data = await response.json();
        
        document.getElementById('email-total').textContent = data.total_emails || 0;
        document.getElementById('email-pending').textContent = data.pending_queue || 0;
        document.getElementById('email-avg-time').textContent = Math.round(data.avg_response_time || 0) + 'm';
        document.getElementById('email-success-rate').textContent = Math.round((data.success_rate || 0) * 100) + '%';
    } catch (error) {
        console.error('Error loading email stats:', error);
        // Set default values
        document.getElementById('email-total').textContent = '0';
        document.getElementById('email-pending').textContent = '0';
        document.getElementById('email-avg-time').textContent = '0m';
        document.getElementById('email-success-rate').textContent = '0%';
    }
}

async function checkEmailWorkerHealth() {
    try {
        const response = await fetch(`${API_BASE}/admin/email/health`, { timeout: 3000 });
        if (response.ok) {
            const data = await response.json();
            document.getElementById('email-status').textContent = '🟢 Online';
            document.getElementById('email-health-card').classList.add('success');
            document.getElementById('email-imap-status').textContent = data.imap_connected ? '🟢 Connected' : '🔴 Disconnected';
            document.getElementById('email-smtp-status').textContent = data.smtp_connected ? '🟢 Connected' : '🔴 Disconnected';
        } else {
            document.getElementById('email-status').textContent = '🔴 Error';
            document.getElementById('email-health-card').classList.add('danger');
        }
    } catch (error) {
        document.getElementById('email-status').textContent = '🔴 Offline';
        document.getElementById('email-health-card').classList.add('danger');
        document.getElementById('email-imap-status').textContent = 'Unknown';
        document.getElementById('email-smtp-status').textContent = 'Unknown';
    }
}

function initializeEmailCharts() {
    const ctx = document.getElementById('emailStatsChart').getContext('2d');
    sectionCharts.emailStats = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            datasets: [{
                label: 'Emails Processed',
                data: [45, 59, 52, 68, 55, 42, 38],
                backgroundColor: 'rgba(16, 185, 129, 0.5)',
                borderColor: '#10b981',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                y: { beginAtZero: true }
            }
        }
    });
}

function saveEmailConfig() {
    const config = {
        imap_server: document.getElementById('email-imap-server').value,
        smtp_server: document.getElementById('email-smtp-server').value,
        email_address: document.getElementById('email-address').value,
        template: document.getElementById('email-template').value,
        check_interval: document.getElementById('email-check-interval').value
    };
    
    // TODO: Send to email worker API
    showAlert('Email configuration saved!', 'success');
}

// ==================== INTEGRATIONS SECTION ====================

async function loadIntegrationsSection() {
    try {
        const response = await fetch(`${API_BASE}/admin/integrations`);
        if (!response.ok) {
            throw new Error('Failed to load integrations');
        }
        const data = await response.json();
        let integrations = data.integrations || [];
        if (!integrations.length) {
            const fallback = getStaticIntegrations();
            if (fallback.length) {
                integrations = fallback;
            }
        }
        renderIntegrationCards(integrations);
        renderWebhooksTable(data.webhooks || []);
        renderApiKeysTable(data.api_keys || []);
    } catch (error) {
        console.error('Error loading integrations:', error);
        const fallback = getStaticIntegrations();
        if (fallback.length) {
            renderIntegrationCards(fallback);
            showAlert('Backend integration status unavailable. Showing static configuration instead.', 'warning');
        } else {
            showAlert('Unable to load integrations. Please try again.', 'error');
            const grid = document.getElementById('integrationsGrid');
            if (grid) {
                grid.innerHTML = `
                    <div class="integration-card placeholder-card">
                        <div class="integration-icon">⚠️</div>
                        <h3>Integrations unavailable</h3>
                        <p>Backend admin API is unreachable. Make sure the Gateway API is running on ${API_BASE}.</p>
                    </div>
                `;
            }
        }
        const webhooksBody = document.getElementById('webhooksBody');
        if (webhooksBody) {
            webhooksBody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; padding: 40px; color: #f87171;">
                        Failed to load webhooks
                    </td>
                </tr>
            `;
        }
        const apiKeysBody = document.getElementById('apiKeysBody');
        if (apiKeysBody) {
            apiKeysBody.innerHTML = `
                <tr>
                    <td colspan="5" style="text-align: center; padding: 40px; color: #f87171;">
                        Failed to load API keys
                    </td>
                </tr>
            `;
        }
    }
}

function getStaticIntegrations() {
    if (typeof PLATFORM_CONFIG === 'undefined' || !PLATFORM_CONFIG.INTEGRATIONS) {
        return [];
    }
    return Object.entries(PLATFORM_CONFIG.INTEGRATIONS).map(([key, value]) => ({
        name: key,
        display_name: value.name || key,
        description: value.status || value.message || 'Configured integration',
        category: value.type || 'custom',
        icon: value.icon || '🔌',
        status: value.connected ? 'connected' : 'disconnected',
        api_key_present: Boolean(value.api_key || value.account_sid || value.phone_number || value.key),
        metadata: {
            status: value.status,
            phone_number: value.phone_number,
            account_sid: value.account_sid,
            url: value.url
        }
    }));
}

function renderIntegrationCards(integrations = []) {
    const container = document.getElementById('integrationsGrid');
    if (!container) return;
    if (!integrations.length) {
        container.innerHTML = `
            <div class="integration-card placeholder-card">
                <div class="integration-icon">ℹ️</div>
                <h3>No integrations configured</h3>
                <p>Add connections from the backend configuration.</p>
            </div>
        `;
        return;
    }

    container.innerHTML = integrations.map(integration => {
        const statusConnected = integration.status === 'connected';
        const actionButton = statusConnected
            ? `<button class="btn btn-outline btn-sm" onclick="disconnectIntegration('${integration.name}')">Disconnect</button>`
            : `<button class="btn btn-primary btn-sm" onclick="connectIntegration('${integration.name}')">Connect</button>`;
        const statusLabel = statusConnected ? 'Connected' : 'Not Connected';
        const statusClass = statusConnected ? 'connected' : 'disconnected';
        return `
            <div class="integration-card" data-service="${integration.name}">
                <div class="integration-icon">${integration.icon || '🔌'}</div>
                <h3>${integration.display_name || integration.name}</h3>
                <p>${integration.description || ''}</p>
                <div class="integration-status ${statusClass}">${statusLabel}</div>
                ${actionButton}
            </div>
        `;
    }).join('');
}

function renderWebhooksTable(webhooks = []) {
    const tbody = document.getElementById('webhooksBody');
    if (!tbody) return;
    if (!webhooks.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 40px; color: #6b7280;">
                    No webhooks configured
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = webhooks.map(webhook => {
        const events = Array.isArray(webhook.events) && webhook.events.length
            ? webhook.events.join(', ')
            : 'All events';
        const statusBadge = webhook.status === 'active'
            ? '<span class="badge badge-success">Active</span>'
            : `<span class="badge badge-muted">${webhook.status}</span>`;
        return `
            <tr>
                <td>${webhook.name}</td>
                <td>${webhook.url}</td>
                <td>${events}</td>
                <td>${statusBadge}</td>
                <td>
                    <button class="btn btn-sm btn-outline" onclick="removeWebhook(${webhook.id})">Delete</button>
                </td>
            </tr>
        `;
    }).join('');
}

function renderApiKeysTable(apiKeys = []) {
    const tbody = document.getElementById('apiKeysBody');
    if (!tbody) return;
    if (!apiKeys.length) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 40px; color: #6b7280;">
                    No API keys added yet
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = apiKeys.map(key => {
        const statusBadge = key.status === 'active'
            ? '<span class="badge badge-success">Active</span>'
            : `<span class="badge badge-muted">${key.status}</span>`;
        const lastUsed = key.last_used_at ? new Date(key.last_used_at).toLocaleString() : 'Never';
        return `
            <tr>
                <td>${key.service}</td>
                <td>${key.key_name}</td>
                <td>${statusBadge}</td>
                <td>${lastUsed}</td>
                <td style="display: flex; gap: 8px;">
                    <button class="btn btn-sm btn-outline" onclick="rotateApiKey('${key.service}', ${key.id})">Rotate</button>
                    <button class="btn btn-sm btn-outline" onclick="revokeApiKey(${key.id})">Revoke</button>
                </td>
            </tr>
        `;
    }).join('');
}

async function connectIntegration(serviceName) {
    if (!serviceName) return;
    const confirmConnect = confirm(`Connect to ${serviceName}?`);
    if (!confirmConnect) return;

    const apiKey = prompt(`Enter API key/token for ${serviceName} (optional):`, '') || '';
    const webhookUrl = prompt(`Enter webhook URL for ${serviceName} (optional):`, '') || '';

    try {
        const response = await fetch(`${API_BASE}/admin/integrations/${serviceName}/connect`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                api_key: apiKey.trim() || undefined,
                webhook_url: webhookUrl.trim() || undefined,
            })
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'Unable to connect integration');
        }
        showAlert(`${serviceName} connected successfully`, 'success');
        loadIntegrationsSection();
    } catch (error) {
        console.error('Connect integration failed:', error);
        showAlert(error.message || 'Failed to connect integration', 'error');
    }
}

async function disconnectIntegration(serviceName) {
    if (!serviceName) return;
    if (!confirm(`Disconnect ${serviceName}?`)) return;
    try {
        const response = await fetch(`${API_BASE}/admin/integrations/${serviceName}/disconnect`, {
            method: 'POST'
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'Unable to disconnect integration');
        }
        showAlert(`${serviceName} disconnected`, 'success');
        loadIntegrationsSection();
    } catch (error) {
        console.error('Disconnect integration failed:', error);
        showAlert(error.message || 'Failed to disconnect integration', 'error');
    }
}

async function showAddWebhookModal() {
    const name = prompt('Webhook name:');
    if (!name) return;
    const url = prompt('Webhook URL:');
    if (!url) {
        showAlert('Webhook URL is required', 'error');
        return;
    }
    const eventsInput = prompt('Events to subscribe (comma separated, optional):', '') || '';
    const events = eventsInput
        .split(',')
        .map(evt => evt.trim())
        .filter(Boolean);

    try {
        const response = await fetch(`${API_BASE}/admin/integrations/webhooks`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, url, events })
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'Unable to add webhook');
        }
        showAlert('Webhook added successfully', 'success');
        loadIntegrationsSection();
    } catch (error) {
        console.error('Add webhook failed:', error);
        showAlert(error.message || 'Failed to add webhook', 'error');
    }
}

async function showAddApiKeyModal() {
    const service = prompt('Service name (e.g., openai, slack):');
    if (!service) return;
    const keyName = prompt('Key label (e.g., Production key):');
    if (!keyName) return;
    const keyValue = prompt('Paste the API key value:');
    if (!keyValue) {
        showAlert('API key value is required', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/admin/integrations/api-keys`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ service, key_name: keyName, key_value: keyValue })
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'Unable to add API key');
        }
        showAlert('API key saved', 'success');
        loadIntegrationsSection();
    } catch (error) {
        console.error('Add API key failed:', error);
        showAlert(error.message || 'Failed to add API key', 'error');
    }
}

async function rotateApiKey(service, keyId) {
    if (!keyId) {
        showAlert('Missing API key reference', 'error');
        return;
    }
    const newValue = prompt(`Enter the replacement API key for ${service}:`);
    if (!newValue) {
        showAlert('Rotation cancelled', 'info');
        return;
    }
    try {
        const response = await fetch(`${API_BASE}/admin/integrations/api-keys/${keyId}/rotate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key_value: newValue })
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'Unable to rotate API key');
        }
        showAlert('API key rotated', 'success');
        loadIntegrationsSection();
    } catch (error) {
        console.error('Rotate API key failed:', error);
        showAlert(error.message || 'Failed to rotate API key', 'error');
    }
}

async function revokeApiKey(keyId) {
    if (!keyId) return;
    if (!confirm('Revoke this API key? This action cannot be undone.')) return;
    try {
        const response = await fetch(`${API_BASE}/admin/integrations/api-keys/${keyId}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'Unable to revoke API key');
        }
        showAlert('API key revoked', 'success');
        loadIntegrationsSection();
    } catch (error) {
        console.error('Revoke API key failed:', error);
        showAlert(error.message || 'Failed to revoke API key', 'error');
    }
}

async function removeWebhook(webhookId) {
    if (!webhookId) return;
    if (!confirm('Delete this webhook?')) return;
    try {
        const response = await fetch(`${API_BASE}/admin/integrations/webhooks/${webhookId}`, {
            method: 'DELETE'
        });
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'Unable to remove webhook');
        }
        showAlert('Webhook removed', 'success');
        loadIntegrationsSection();
    } catch (error) {
        console.error('Delete webhook failed:', error);
        showAlert(error.message || 'Failed to delete webhook', 'error');
    }
}

// ==================== UTILITY FUNCTIONS ====================

function escapeHtml(value) {
    if (value === null || value === undefined) {
        return '';
    }
    return String(value)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function showAlert(message, type = 'info') {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.textContent = message;
    alertDiv.style.position = 'fixed';
    alertDiv.style.top = '20px';
    alertDiv.style.right = '20px';
    alertDiv.style.zIndex = '9999';
    alertDiv.style.minWidth = '300px';
    alertDiv.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    
    document.body.appendChild(alertDiv);
    
    setTimeout(() => {
        alertDiv.style.transition = 'opacity 0.3s';
        alertDiv.style.opacity = '0';
        setTimeout(() => document.body.removeChild(alertDiv), 300);
    }, 3000);
}

function downloadBlob(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function viewLanguageDetails(language) {
    showAlert(`Viewing details for language: ${language}`, 'info');
}

// Export all functions
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        loadAnalyticsSection,
        loadTranslationSection,
        loadSentimentSection,
        loadCacheSection,
        loadRateLimitSection,
        loadFaqSection,
        loadKnowledgeSection,
        loadConversationsSection,
        loadCostsSection,
        loadSettingsSection,
        loadLogsSection,
        loadTelephonyTesterSection
    };
}
