// Control Center - All Section Templates and Logic

window.SECTIONS = {
    // Analytics Section
    analytics: `
        <div class="content-section" id="section-analytics">
            <div class="stats-grid">
                <div class="stat-card primary">
                    <div class="stat-label">Total Events</div>
                    <div class="stat-value" id="analytics-events">0</div>
                </div>
                <div class="stat-card success">
                    <div class="stat-label">Unique Users</div>
                    <div class="stat-value" id="analytics-users">0</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-label">Avg Session Time</div>
                    <div class="stat-value" id="analytics-session">0s</div>
                </div>
                <div class="stat-card info">
                    <div class="stat-label">Engagement Rate</div>
                    <div class="stat-value" id="analytics-engagement">0%</div>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px;">
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">📈 Traffic Trends</div>
                        <select class="form-select" style="width: 150px;" onchange="loadTrafficTrends(this.value)">
                            <option value="7">Last 7 days</option>
                            <option value="30">Last 30 days</option>
                            <option value="90">Last 90 days</option>
                        </select>
                    </div>
                    <div class="chart-container">
                        <canvas id="analyticsTrafficChart"></canvas>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <div class="card-title">⚡ Performance Metrics</div>
                    </div>
                    <div class="chart-container">
                        <canvas id="analyticsPerformanceChart"></canvas>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">🎯 User Engagement</div>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Event Type</th>
                                <th>Count</th>
                                <th>Unique Users</th>
                                <th>Avg Duration</th>
                                <th>Trend</th>
                            </tr>
                        </thead>
                        <tbody id="engagementTableBody"></tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">🤖 Provider Reliability & Fallbacks</div>
                    <select class="form-select" style="width: 160px;" onchange="loadFallbackStats(this.value)">
                        <option value="7">Last 7 days</option>
                        <option value="14">Last 14 days</option>
                        <option value="30">Last 30 days</option>
                    </select>
                </div>
                <div class="stats-grid" style="margin-bottom: 15px;">
                    <div class="stat-card primary">
                        <div class="stat-label">Total Attempts</div>
                        <div class="stat-value" id="fallback-total-attempts">0</div>
                    </div>
                    <div class="stat-card success">
                        <div class="stat-label">Successful</div>
                        <div class="stat-value" id="fallback-total-success">0</div>
                    </div>
                    <div class="stat-card warning">
                        <div class="stat-label">Fallback Saves</div>
                        <div class="stat-value" id="fallback-total-saves">0</div>
                    </div>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Provider</th>
                                <th>Attempts</th>
                                <th>Success Rate</th>
                                <th>Avg Latency</th>
                                <th>Fails</th>
                                <th>Fallback Saves</th>
                            </tr>
                        </thead>
                        <tbody id="fallbackProviderTableBody">
                            <tr><td colspan="6" style="text-align:center; color:#6b7280;">Loading...</td></tr>
                        </tbody>
                    </table>
                </div>
                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap:15px; margin-top:20px;">
                    <div>
                        <div class="card-title" style="margin-bottom:10px;">Fallback Depth Distribution</div>
                        <div id="fallbackDistribution" class="fallback-distribution"></div>
                    </div>
                    <div>
                        <div class="card-title" style="margin-bottom:10px;">Recent Failures</div>
                        <div id="fallbackFailures" class="failure-list"></div>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">⚙️ Analytics Actions</div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                    <button class="btn btn-primary" onclick="exportAnalyticsData()">
                        📥 Export Data
                    </button>
                    <button class="btn btn-outline" onclick="resetAnalytics()">
                        🔄 Reset Stats
                    </button>
                    <button class="btn btn-outline" onclick="generateReport()">
                        📊 Generate Report
                    </button>
                </div>
            </div>
        </div>
    `,

    // Translation Section
    translation: `
        <div class="content-section" id="section-translation">
            <div class="card">
                <div class="card-header">
                    <div class="card-title">🌍 Language Statistics (Last 30 Days)</div>
                    <button class="btn btn-outline btn-sm" onclick="loadTranslationStats()">Refresh</button>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Language</th>
                                <th>Requests</th>
                                <th>Cache Hits</th>
                                <th>Hit Rate</th>
                                <th>Total Cost</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="translationStatsBody"></tbody>
                    </table>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px;">
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">🗑️ Cache Management</div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Clear translations older than (days)</label>
                        <input type="number" class="form-input" id="translationCleanupDays" value="90" min="1">
                    </div>
                    <button class="btn btn-danger" onclick="cleanupTranslations()">
                        🗑️ Cleanup Old Translations
                    </button>
                    <div style="margin-top: 15px;">
                        <button class="btn btn-outline" onclick="clearAllTranslations()">
                            Clear All Cache
                        </button>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <div class="card-title">🔍 Translation Lookup</div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Source Text</label>
                        <textarea class="form-textarea" id="lookupText" placeholder="Enter text to check translation cache..."></textarea>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Target Language</label>
                        <select class="form-select" id="lookupLanguage">
                            <option value="en">English</option>
                            <option value="es">Spanish</option>
                            <option value="fr">French</option>
                            <option value="de">German</option>
                            <option value="it">Italian</option>
                            <option value="pt">Portuguese</option>
                            <option value="ja">Japanese</option>
                            <option value="zh">Chinese</option>
                            <option value="ar">Arabic</option>
                            <option value="ru">Russian</option>
                        </select>
                    </div>
                    <button class="btn btn-primary" onclick="lookupTranslation()">
                        🔍 Lookup Translation
                    </button>
                    <div id="lookupResult" style="margin-top: 15px;"></div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">📊 Translation Performance</div>
                </div>
                <div class="chart-container">
                    <canvas id="translationChart"></canvas>
                </div>
            </div>
        </div>
    `,

    // Sentiment Analysis Section
    sentiment: `
        <div class="content-section" id="section-sentiment">
            <div class="stats-grid">
                <div class="stat-card success">
                    <div class="stat-label">Positive Interactions</div>
                    <div class="stat-value" id="sentiment-positive">0</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-label">Negative Interactions</div>
                    <div class="stat-value" id="sentiment-negative">0</div>
                </div>
                <div class="stat-card danger">
                    <div class="stat-label">Escalations</div>
                    <div class="stat-value" id="sentiment-escalations">0</div>
                </div>
                <div class="stat-card info">
                    <div class="stat-label">Average Sentiment</div>
                    <div class="stat-value" id="sentiment-average">0.0</div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">😊 Sentiment Distribution</div>
                </div>
                <div class="chart-container">
                    <canvas id="sentimentDistChart"></canvas>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">🚨 Recent Escalations</div>
                    <button class="btn btn-outline btn-sm" onclick="loadEscalations()">Refresh</button>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Session ID</th>
                                <th>Sentiment</th>
                                <th>Score</th>
                                <th>Message Preview</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="escalationsTableBody"></tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">⚙️ Sentiment Settings</div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                    <div class="form-group">
                        <label class="form-label">Escalation Threshold</label>
                        <input type="range" min="0" max="1" step="0.1" value="0.7" id="escalationThreshold" onchange="updateThreshold(this)">
                        <div style="display: flex; justify-content: space-between; font-size: 12px; color: #6b7280;">
                            <span>Low (0)</span>
                            <span id="thresholdValue">0.7</span>
                            <span>High (1)</span>
                        </div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Auto-escalate on keywords</label>
                        <label class="toggle-switch">
                            <input type="checkbox" id="autoEscalate" checked>
                            <span class="toggle-slider"></span>
                        </label>
                    </div>
                </div>
            </div>
        </div>
    `,

    // Cache Section
    cache: `
        <div class="content-section" id="section-cache">
            <div class="stats-grid">
                <div class="stat-card primary">
                    <div class="stat-label">Total Cached Items</div>
                    <div class="stat-value" id="cache-total">0</div>
                </div>
                <div class="stat-card success">
                    <div class="stat-label">Cache Hits</div>
                    <div class="stat-value" id="cache-hits">0</div>
                </div>
                <div class="stat-card info">
                    <div class="stat-label">Hit Rate</div>
                    <div class="stat-value" id="cache-rate">0%</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-label">Cost Saved</div>
                    <div class="stat-value" id="cache-savings">$0</div>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px;">
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">📊 Cache Performance</div>
                    </div>
                    <div class="chart-container">
                        <canvas id="cachePerformanceChart"></canvas>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <div class="card-title">⚙️ Cache Management</div>
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 15px;">
                        <button class="btn btn-primary" onclick="loadCacheStats()">
                            🔄 Refresh Stats
                        </button>
                        <button class="btn btn-danger" onclick="clearAllCache()">
                            🗑️ Clear All Cache
                        </button>
                        <div class="alert alert-info">
                            <strong>ℹ️ Info:</strong> Clearing cache will temporarily reduce performance but ensure fresh responses.
                        </div>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">📋 Recent Cache Entries</div>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Question Hash</th>
                                <th>Provider</th>
                                <th>Hit Count</th>
                                <th>Last Used</th>
                                <th>Savings</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="cacheEntriesBody"></tbody>
                    </table>
                </div>
            </div>
        </div>
    `,

    // Rate Limiting Section
    ratelimit: `
        <div class="content-section" id="section-ratelimit">
            <div class="stats-grid">
                <div class="stat-card primary">
                    <div class="stat-label">Total API Keys</div>
                    <div class="stat-value" id="ratelimit-keys">0</div>
                </div>
                <div class="stat-card danger">
                    <div class="stat-label">Blocked Entities</div>
                    <div class="stat-value" id="ratelimit-blocked">0</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-label">Abuse Incidents (24h)</div>
                    <div class="stat-value" id="ratelimit-incidents">0</div>
                </div>
                <div class="stat-card info">
                    <div class="stat-label">Requests Today</div>
                    <div class="stat-value" id="ratelimit-requests">0</div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">🔑 API Key Usage</div>
                    <button class="btn btn-outline btn-sm" onclick="loadApiKeyUsage()">Refresh</button>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>API Key</th>
                                <th>Tier</th>
                                <th>Requests (24h)</th>
                                <th>Limit</th>
                                <th>Usage %</th>
                                <th>Last Request</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="apiKeyUsageBody"></tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">🛡️ Blocked Entities</div>
                    <button class="btn btn-outline btn-sm" onclick="loadBlockedEntities()">Refresh</button>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Type</th>
                                <th>Value</th>
                                <th>Reason</th>
                                <th>Blocked At</th>
                                <th>Expires At</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="blockedEntitiesBody"></tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">🚨 Recent Abuse Incidents</div>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Entity Type</th>
                                <th>Entity Value</th>
                                <th>Reason</th>
                                <th>Severity</th>
                                <th>Details</th>
                            </tr>
                        </thead>
                        <tbody id="abuseIncidentsBody"></tbody>
                    </table>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">➕ Block Entity</div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Entity Type</label>
                        <select class="form-select" id="blockEntityType">
                            <option value="api_key">API Key</option>
                            <option value="ip_address">IP Address</option>
                            <option value="user_id">User ID</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Entity Value</label>
                        <input type="text" class="form-input" id="blockEntityValue" placeholder="Enter value...">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Reason</label>
                        <input type="text" class="form-input" id="blockReason" placeholder="Abuse, spam, etc...">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Duration (hours, 0 = permanent)</label>
                        <input type="number" class="form-input" id="blockDuration" value="0" min="0">
                    </div>
                    <button class="btn btn-danger" onclick="blockEntity()">
                        🛡️ Block Entity
                    </button>
                </div>

                <div class="card">
                    <div class="card-header">
                        <div class="card-title">⚙️ Rate Limit Settings</div>
                    </div>
                    <div class="form-group">
                        <label class="form-label">Free Tier Limit (requests/day)</label>
                        <input type="number" class="form-input" value="100" id="freeTierLimit">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Basic Tier Limit (requests/day)</label>
                        <input type="number" class="form-input" value="1000" id="basicTierLimit">
                    </div>
                    <div class="form-group">
                        <label class="form-label">Premium Tier Limit (requests/day)</label>
                        <input type="number" class="form-input" value="10000" id="premiumTierLimit">
                    </div>
                    <button class="btn btn-primary" onclick="updateRateLimits()">
                        💾 Save Settings
                    </button>
                </div>
            </div>
        </div>
    `,

    // LLM API Tester Section
    llmTester: `
        <div class="content-section" id="section-llmTester">
            <div class="card">
                <div class="card-header">
                    <div>
                        <div class="card-title">🧪 LLM API Health Checks</div>
                        <div class="card-subtitle">Ping each configured provider, confirm keys, and capture latency samples.</div>
                    </div>
                    <div class="card-actions" style="gap:10px;">
                        <button class="btn btn-outline btn-sm" onclick="refreshLlmTester()">Refresh</button>
                        <button class="btn btn-primary btn-sm" onclick="runLlmTest()">Run All Tests</button>
                    </div>
                </div>
                <div id="llmTesterProviderGrid" class="llm-provider-grid">
                    <div class="llm-empty-state">No provider tests yet. Tap “Run All Tests” to capture live metrics.</div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">⚙️ Custom Prompt & Target</div>
                </div>
                <div class="form-group">
                    <label class="form-label">Test prompt</label>
                    <textarea class="form-textarea" id="llmTesterPrompt" rows="3" placeholder="Health check ping. Respond with the word 'pong'."></textarea>
                </div>
                <div class="form-group">
                    <label class="form-label">Run a single provider</label>
                    <div class="llm-provider-pills" id="llmTesterProviderPills">
                        <span class="llm-empty-state">Providers will appear after the first summary refresh.</span>
                    </div>
                </div>
                <div style="display:flex; flex-wrap:wrap; gap:10px;">
                    <button class="btn btn-primary" onclick="runLlmTest()">Run Across All Providers</button>
                    <button class="btn btn-outline" onclick="resetLlmTesterPrompt()">Reset Prompt</button>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">📜 Recent Test History</div>
                    <div class="card-actions" style="gap:10px;">
                        <select class="form-select" id="llmTesterHistoryFilter" onchange="changeLlmTesterHistoryFilter(this.value)">
                            <option value="all">All Providers</option>
                        </select>
                        <button class="btn btn-outline btn-sm" onclick="refreshLlmTesterHistory()">Refresh</button>
                    </div>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Provider</th>
                                <th>Status</th>
                                <th>Latency</th>
                                <th>Details</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody id="llmTesterHistoryBody">
                            <tr><td colspan="6" style="text-align:center; color:#6b7280;">No tests recorded yet.</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `,

    // Telephony Tester Section
    telephonyTester: `
        <div class="content-section" id="section-telephonyTester">
            <div class="card">
                <div class="card-header">
                    <div>
                        <div class="card-title">📞 Telephony Diagnostics</div>
                        <div class="card-subtitle">Validate Twilio credentials, webhook reachability, and outbound flow readiness.</div>
                    </div>
                    <div class="card-actions" style="gap:10px;">
                        <button class="btn btn-outline btn-sm" onclick="refreshTelephonyTester()">Refresh</button>
                        <button class="btn btn-primary btn-sm" onclick="runTelephonyTests()">Run All Tests</button>
                    </div>
                </div>
                <div class="telephony-overview">
                    <div>
                        <label class="form-label">Twilio Number</label>
                        <div class="telephony-value" id="telephonyTesterNumber">—</div>
                    </div>
                    <div>
                        <label class="form-label">Voice Webhook</label>
                        <div class="telephony-value" id="telephonyTesterWebhook">—</div>
                    </div>
                    <div>
                        <label class="form-label">Health Endpoint</label>
                        <div class="telephony-value" id="telephonyTesterHealth">—</div>
                    </div>
                    <div>
                        <label class="form-label">Mode</label>
                        <select class="form-select" id="telephonyTesterMode" onchange="changeTelephonyTesterMode(this.value)">
                            <option value="dry">Dry Run (safe)</option>
                            <option value="live">Live (calls Twilio APIs)</option>
                        </select>
                    </div>
                </div>
                <div class="telephony-env-alert" id="telephonyTesterEnvAlert"></div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">🧪 Telephony Test Matrix</div>
                    <div class="card-subtitle">Latest results across all diagnostics</div>
                </div>
                <div id="telephonyTesterGrid" class="telephony-grid">
                    <div class="telephony-empty-state">No tests have been recorded yet. Run diagnostics to populate this grid.</div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">📜 Telephony Test History</div>
                    <div class="card-actions" style="gap:10px;">
                        <select class="form-select" id="telephonyTesterHistoryFilter" onchange="changeTelephonyHistoryFilter(this.value)">
                            <option value="all">All Tests</option>
                        </select>
                        <button class="btn btn-outline btn-sm" onclick="refreshTelephonyTesterHistory()">Refresh</button>
                    </div>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Test</th>
                                <th>Status</th>
                                <th>Latency</th>
                                <th>Details</th>
                                <th></th>
                            </tr>
                        </thead>
                        <tbody id="telephonyTesterHistoryBody">
                            <tr><td colspan="6" style="text-align:center; color:#6b7280;">No tests recorded yet.</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    `,

    // Knowledge Base Section
    knowledge: `
        <div class="content-section" id="section-knowledge">
            <div class="stats-grid">
                <div class="stat-card warning">
                    <div class="stat-label">Unanswered Questions</div>
                    <div class="stat-value" id="kb-unanswered">0</div>
                </div>
                <div class="stat-card info">
                    <div class="stat-label">Pending FAQs</div>
                    <div class="stat-value" id="kb-pending">0</div>
                </div>
                <div class="stat-card success">
                    <div class="stat-label">Approved FAQs</div>
                    <div class="stat-value" id="kb-approved">0</div>
                </div>
                <div class="stat-card primary">
                    <div class="stat-label">Question Clusters</div>
                    <div class="stat-value" id="kb-clusters">0</div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">❓ Unanswered Questions</div>
                    <button class="btn btn-outline btn-sm" onclick="loadUnansweredQuestions()">Refresh</button>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Question</th>
                                <th>Count</th>
                                <th>Last Asked</th>
                                <th>Avg Confidence</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="unansweredQuestionsBody"></tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">💡 Pending FAQ Suggestions</div>
                    <button class="btn btn-outline btn-sm" onclick="loadPendingFAQs()">Refresh</button>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Question</th>
                                <th>Suggested Answer</th>
                                <th>Confidence</th>
                                <th>Based On</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="pendingFAQsBody"></tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">📚 Question Clusters</div>
                    <button class="btn btn-primary btn-sm" onclick="generateClusters()">Generate Clusters</button>
                </div>
                <div id="clustersContainer"></div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">⚙️ Knowledge Base Actions</div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                    <button class="btn btn-primary" onclick="generateFAQSuggestions()">
                        💡 Generate Suggestions
                    </button>
                    <button class="btn btn-outline" onclick="exportKnowledgeGaps()">
                        📥 Export Gaps
                    </button>
                    <button class="btn btn-outline" onclick="resetKnowledgeBase()">
                        🔄 Reset Stats
                    </button>
                </div>
            </div>
        </div>
    `,

    // FAQ Manager Section
    faqs: `
        <div class="content-section" id="section-faqs">
            <div class="card">
                <div class="card-header">
                    <div>
                        <div class="card-title">❓ FAQ Manager</div>
                        <p class="card-subtitle">Keep canonical answers aligned across every channel</p>
                    </div>
                    <div class="card-actions">
                        <button class="btn btn-outline btn-sm" onclick="loadFaqList(true)">
                            🔄 Refresh
                        </button>
                        <button class="btn btn-primary" onclick="openFaqModal()">
                            ➕ Add FAQ
                        </button>
                    </div>
                </div>

                <div class="faq-controls">
                    <div class="form-group inline">
                        <label class="form-label" for="faqSearchInput">Search</label>
                        <input type="text" class="form-input" id="faqSearchInput" placeholder="Search question, answer or tag..." oninput="handleFaqSearch(this.value)">
                    </div>
                    <div class="form-group inline">
                        <label class="form-label" for="faqStatusFilter">Status</label>
                        <select class="form-select" id="faqStatusFilter" onchange="setFaqFilter('status', this.value)">
                            <option value="">All Statuses</option>
                            <option value="active">Active</option>
                            <option value="draft">Draft</option>
                            <option value="archived">Archived</option>
                        </select>
                    </div>
                    <div class="form-group inline">
                        <label class="form-label" for="faqCategoryFilter">Category</label>
                        <select class="form-select" id="faqCategoryFilter" onchange="setFaqFilter('category', this.value)">
                            <option value="">All Categories</option>
                        </select>
                    </div>
                    <div class="form-group inline" style="max-width: 140px;">
                        <label class="form-label" for="faqPageSize">Per Page</label>
                        <select class="form-select" id="faqPageSize" onchange="setFaqPageSize(this.value)">
                            <option value="10">10</option>
                            <option value="20">20</option>
                            <option value="50">50</option>
                        </select>
                    </div>
                </div>

                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th style="width: 30%;">Question</th>
                                <th style="width: 18%;">Category</th>
                                <th style="width: 18%;">Tags</th>
                                <th style="width: 12%;">Status</th>
                                <th style="width: 14%;">Last Updated</th>
                                <th style="width: 8%;">Actions</th>
                            </tr>
                        </thead>
                        <tbody id="faqTableBody">
                            <tr>
                                <td colspan="6" class="loading">
                                    <div class="loading-spinner"></div>
                                    <p>Loading FAQs...</p>
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>

                <div class="faq-pagination">
                    <div>
                        <strong id="faqRangeText">0 - 0</strong>
                        <span>of</span>
                        <strong id="faqTotalText">0</strong>
                        <span>FAQs</span>
                    </div>
                    <div class="faq-pagination-controls">
                        <button class="btn btn-outline btn-sm" id="faqPrevBtn" onclick="changeFaqPage(-1)" disabled>← Previous</button>
                        <span class="faq-page-label" id="faqPageLabel">Page 1</span>
                        <button class="btn btn-outline btn-sm" id="faqNextBtn" onclick="changeFaqPage(1)" disabled>Next →</button>
                    </div>
                </div>
            </div>
        </div>
    `,

    // Conversations Section
    conversations: `
        <div class="content-section" id="section-conversations">
            <div class="stats-grid">
                <div class="stat-card primary">
                    <div class="stat-label">Active Sessions</div>
                    <div class="stat-value" id="conv-active">0</div>
                </div>
                <div class="stat-card success">
                    <div class="stat-label">Total Messages</div>
                    <div class="stat-value" id="conv-messages">0</div>
                </div>
                <div class="stat-card info">
                    <div class="stat-label">Avg Messages/Session</div>
                    <div class="stat-value" id="conv-avg">0</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-label">Longest Session</div>
                    <div class="stat-value" id="conv-longest">0</div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">💬 Recent Conversations</div>
                    <button class="btn btn-outline btn-sm" onclick="loadConversations()">Refresh</button>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Session ID</th>
                                <th>Started</th>
                                <th>Last Activity</th>
                                <th>Messages</th>
                                <th>Metadata</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="conversationsTableBody"></tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">⚙️ Conversation Management</div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px;">
                    <div>
                        <label class="form-label">Clear sessions older than (days)</label>
                        <input type="number" class="form-input" id="sessionCleanupDays" value="30" min="1">
                        <button class="btn btn-danger" style="width: 100%; margin-top: 10px;" onclick="cleanupSessions()">
                            🗑️ Cleanup Old Sessions
                        </button>
                    </div>
                    <div>
                        <label class="form-label">Export conversations</label>
                        <button class="btn btn-primary" style="width: 100%; margin-top: 10px;" onclick="exportConversations()">
                            📥 Export All
                        </button>
                    </div>
                </div>
            </div>
        </div>
    `,

    // Cost Analysis Section
    costs: `
        <div class="content-section" id="section-costs">
            <div class="stats-grid">
                <div class="stat-card primary">
                    <div class="stat-label">Total Cost (30 days)</div>
                    <div class="stat-value" id="cost-total">$0</div>
                </div>
                <div class="stat-card success">
                    <div class="stat-label">Cache Savings</div>
                    <div class="stat-value" id="cost-savings">$0</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-label">Avg Cost/Request</div>
                    <div class="stat-value" id="cost-avg">$0</div>
                </div>
                <div class="stat-card info">
                    <div class="stat-label">Projected (30d)</div>
                    <div class="stat-value" id="cost-projected">$0</div>
                </div>
            </div>

            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(400px, 1fr)); gap: 20px;">
                <div class="card">
                    <div class="card-header">
                        <div class="card-title">📊 Cost Breakdown by Provider</div>
                    </div>
                    <div class="chart-container">
                        <canvas id="costProviderChart"></canvas>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">
                        <div class="card-title">📈 Daily Cost Trend</div>
                    </div>
                    <div class="chart-container">
                        <canvas id="costTrendChart"></canvas>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">💰 Cost Details</div>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Provider</th>
                                <th>Requests</th>
                                <th>Input Tokens</th>
                                <th>Output Tokens</th>
                                <th>Total Cost</th>
                                <th>Avg Cost</th>
                            </tr>
                        </thead>
                        <tbody id="costDetailsBody"></tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">⚙️ Cost Management</div>
                </div>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                    <button class="btn btn-primary" onclick="exportCostReport()">
                        📥 Export Report
                    </button>
                    <button class="btn btn-outline" onclick="setCostAlert()">
                        🔔 Set Budget Alert
                    </button>
                    <button class="btn btn-outline" onclick="optimizeCosts()">
                        ⚡ Optimize Costs
                    </button>
                </div>
            </div>
        </div>
    `,

    // Settings Section
    settings: `
        <div class="content-section" id="section-settings">
            <div class="card">
                <div class="card-header">
                    <div class="card-title">🤖 LLM Provider Settings</div>
                </div>
                <div class="form-group">
                    <label class="form-label">Primary Provider</label>
                    <select class="form-select" id="primaryProvider">
                        <option value="" disabled selected>Loading providers...</option>
                    </select>
                </div>
                <div class="form-group">
                    <label class="form-label">Fallback Order</label>
                    <textarea class="form-input" id="fallbackOrderInput" rows="3" placeholder="Enter providers in preferred order, e.g. grok, gemini, local"></textarea>
                    <small class="form-helper-text">List providers separated by commas or new lines. Primary provider is automatically tried first.</small>
                </div>
                <div class="form-group">
                    <label class="form-label">
                        <input type="checkbox" id="autoFallback" checked> Enable automatic fallback
                    </label>
                </div>
                <button class="btn btn-primary" onclick="saveProviderSettings()">
                    💾 Save Provider Settings
                </button>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">📚 Retrieval Confidence Settings</div>
                </div>
                <p class="form-helper-text">Control the minimum similarity required before RAG results are given to the LLM.</p>
                <div class="form-group">
                    <label class="form-label">Confidence Threshold (0 - 2)</label>
                    <input type="number" class="form-input" id="ragConfidenceThreshold" min="0" max="2" step="0.05" value="0.35">
                    <small>Only context chunks with distance ≤ <span id="ragConfidenceDisplay">0.35</span> are used.</small>
                </div>
                <button class="btn btn-primary" onclick="saveRagSettings()">
                    💾 Save Retrieval Settings
                </button>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">⚡ Performance Settings</div>
                </div>
                <div class="form-group">
                    <label class="form-label">Cache TTL (seconds)</label>
                    <input type="number" class="form-input" id="cacheTTL" value="3600" min="60">
                </div>
                <div class="form-group">
                    <label class="form-label">Max Response Time (ms)</label>
                    <input type="number" class="form-input" id="maxResponseTime" value="5000" min="1000">
                </div>
                <div class="form-group">
                    <label class="form-label">
                        <input type="checkbox" id="enableCache" checked> Enable response caching
                    </label>
                </div>
                <div class="form-group">
                    <label class="form-label">
                        <input type="checkbox" id="enableCompression" checked> Enable response compression
                    </label>
                </div>
                <button class="btn btn-primary" onclick="savePerformanceSettings()">
                    💾 Save Performance Settings
                </button>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">🔔 Notification Settings</div>
                </div>
                <div class="form-group">
                    <label class="form-label">
                        <input type="checkbox" id="notifyEscalations" checked> Escalation alerts
                    </label>
                </div>
                <div class="form-group">
                    <label class="form-label">
                        <input type="checkbox" id="notifyAbuseDetection" checked> Abuse detection alerts
                    </label>
                </div>
                <div class="form-group">
                    <label class="form-label">
                        <input type="checkbox" id="notifyCostThreshold"> Cost threshold alerts
                    </label>
                </div>
                <div class="form-group">
                    <label class="form-label">Alert Email</label>
                    <input type="email" class="form-input" id="alertEmail" placeholder="admin@example.com">
                </div>
                <button class="btn btn-primary" onclick="saveNotificationSettings()">
                    💾 Save Notification Settings
                </button>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">🔐 Security Settings</div>
                </div>
                <div class="form-group">
                    <label class="form-label">
                        <input type="checkbox" id="requireApiKey" checked> Require API key authentication
                    </label>
                </div>
                <div class="form-group">
                    <label class="form-label">
                        <input type="checkbox" id="enableRateLimiting" checked> Enable rate limiting
                    </label>
                </div>
                <div class="form-group">
                    <label class="form-label">
                        <input type="checkbox" id="enableAbuseDetection" checked> Enable abuse detection
                    </label>
                </div>
                <div class="form-group">
                    <label class="form-label">Max requests per IP (per hour)</label>
                    <input type="number" class="form-input" id="maxRequestsPerIP" value="100" min="1">
                </div>
                <button class="btn btn-primary" onclick="saveSecuritySettings()">
                    💾 Save Security Settings
                </button>
            </div>
        </div>
    `,

    // System Logs Section
    logs: `
        <div class="content-section" id="section-logs">
            <div class="card">
                <div class="card-header">
                    <div class="card-title">📝 System Activity Logs</div>
                    <div class="card-actions">
                        <select class="form-select" style="width: 150px;" id="logLevel">
                            <option value="all">All Levels</option>
                            <option value="info">Info</option>
                            <option value="warning">Warning</option>
                            <option value="error">Error</option>
                        </select>
                        <button class="btn btn-outline btn-sm" onclick="loadSystemLogs()">Refresh</button>
                        <button class="btn btn-outline btn-sm" onclick="exportLogs()">Export</button>
                    </div>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Level</th>
                                <th>Component</th>
                                <th>Message</th>
                                <th>Details</th>
                            </tr>
                        </thead>
                        <tbody id="systemLogsBody">
                            <tr>
                                <td colspan="5" style="text-align: center; padding: 40px; color: #6b7280;">
                                    System logs will appear here
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">📊 Log Statistics</div>
                </div>
                <div class="stats-grid">
                    <div class="stat-card info">
                        <div class="stat-label">Total Logs</div>
                        <div class="stat-value" id="logs-total">0</div>
                    </div>
                    <div class="stat-card warning">
                        <div class="stat-label">Warnings</div>
                        <div class="stat-value" id="logs-warnings">0</div>
                    </div>
                    <div class="stat-card danger">
                        <div class="stat-label">Errors</div>
                        <div class="stat-value" id="logs-errors">0</div>
                    </div>
                    <div class="stat-card success">
                        <div class="stat-label">Success Rate</div>
                        <div class="stat-value" id="logs-success">0%</div>
                    </div>
                </div>
            </div>
        </div>
    `,

    // Voice & Calling Section
    voice: `
        <div class="content-section" id="section-voice">
            <div class="stats-grid">
                <div class="stat-card primary">
                    <div class="stat-label">Total Calls</div>
                    <div class="stat-value" id="voice-total-calls">0</div>
                </div>
                <div class="stat-card success">
                    <div class="stat-label">Active Calls</div>
                    <div class="stat-value" id="voice-active-calls">0</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-label">Avg Call Duration</div>
                    <div class="stat-value" id="voice-avg-duration">0s</div>
                </div>
                <div class="stat-card info">
                    <div class="stat-label">Success Rate</div>
                    <div class="stat-value" id="voice-success-rate">0%</div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">📞 Voice Orchestrator Status</div>
                    <button class="btn btn-outline btn-sm" onclick="checkVoiceOrchestratorHealth()">Check Health</button>
                </div>
                <div class="stats-grid">
                    <div class="stat-card" id="voice-health-card">
                        <div class="stat-label">Service Status</div>
                        <div class="stat-value" id="voice-status">Checking...</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Port</div>
                        <div class="stat-value">8004</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">IVR Version</div>
                        <div class="stat-value">v1.0</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">ASR/TTS</div>
                        <div class="stat-value">Enabled</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">📊 Call History (Last 24 Hours)</div>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Caller ID</th>
                                <th>Duration</th>
                                <th>Language</th>
                                <th>Intent</th>
                                <th>Status</th>
                            </tr>
                        </thead>
                        <tbody id="voiceCallHistoryBody">
                            <tr>
                                <td colspan="6" style="text-align: center; padding: 40px; color: #6b7280;">
                                    No recent calls
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">🔧 IVR Configuration</div>
                </div>
                <div class="form-group">
                    <label>Welcome Message</label>
                    <textarea class="form-input" rows="3" id="voice-welcome-message" placeholder="Hello, welcome to our customer service..."></textarea>
                </div>
                <div class="form-group">
                    <label>Default Language</label>
                    <select class="form-select" id="voice-default-language">
                        <option value="en">English</option>
                        <option value="es">Spanish</option>
                        <option value="fr">French</option>
                        <option value="de">German</option>
                    </select>
                </div>
                <div class="form-group">
                    <label>Max Call Duration (seconds)</label>
                    <input type="number" class="form-input" id="voice-max-duration" value="300" />
                </div>
                <button class="btn btn-primary" onclick="saveVoiceConfig()">💾 Save Configuration</button>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">📈 Call Analytics</div>
                </div>
                <div class="chart-container">
                    <canvas id="voiceCallsChart"></canvas>
                </div>
            </div>
        </div>
    `,

    // Email Support Section
    email: `
        <div class="content-section" id="section-email">
            <div class="stats-grid">
                <div class="stat-card primary">
                    <div class="stat-label">Emails Processed</div>
                    <div class="stat-value" id="email-total">0</div>
                </div>
                <div class="stat-card success">
                    <div class="stat-label">Pending Queue</div>
                    <div class="stat-value" id="email-pending">0</div>
                </div>
                <div class="stat-card warning">
                    <div class="stat-label">Avg Response Time</div>
                    <div class="stat-value" id="email-avg-time">0m</div>
                </div>
                <div class="stat-card info">
                    <div class="stat-label">Success Rate</div>
                    <div class="stat-value" id="email-success-rate">0%</div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">📧 Email Worker Status</div>
                    <button class="btn btn-outline btn-sm" onclick="checkEmailWorkerHealth()">Check Status</button>
                </div>
                <div class="stats-grid">
                    <div class="stat-card" id="email-health-card">
                        <div class="stat-label">Service Status</div>
                        <div class="stat-value" id="email-status">Checking...</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">IMAP Connection</div>
                        <div class="stat-value" id="email-imap-status">Unknown</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">SMTP Connection</div>
                        <div class="stat-value" id="email-smtp-status">Unknown</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-label">Queue Type</div>
                        <div class="stat-value">Background</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">📨 Recent Emails (Last 24 Hours)</div>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>From</th>
                                <th>Subject</th>
                                <th>Status</th>
                                <th>Response Time</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="emailHistoryBody">
                            <tr>
                                <td colspan="6" style="text-align: center; padding: 40px; color: #6b7280;">
                                    No recent emails
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">⚙️ Email Configuration</div>
                </div>
                <div class="form-group">
                    <label>IMAP Server</label>
                    <input type="text" class="form-input" id="email-imap-server" placeholder="imap.gmail.com" />
                </div>
                <div class="form-group">
                    <label>SMTP Server</label>
                    <input type="text" class="form-input" id="email-smtp-server" placeholder="smtp.gmail.com" />
                </div>
                <div class="form-group">
                    <label>Email Address</label>
                    <input type="email" class="form-input" id="email-address" placeholder="support@company.com" />
                </div>
                <div class="form-group">
                    <label>Auto-Reply Template</label>
                    <textarea class="form-input" rows="4" id="email-template" placeholder="Thank you for contacting us..."></textarea>
                </div>
                <div class="form-group">
                    <label>Check Interval (minutes)</label>
                    <input type="number" class="form-input" id="email-check-interval" value="5" />
                </div>
                <button class="btn btn-primary" onclick="saveEmailConfig()">💾 Save Configuration</button>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">📊 Email Analytics</div>
                </div>
                <div class="chart-container">
                    <canvas id="emailStatsChart"></canvas>
                </div>
            </div>
        </div>
    `,

    // Integrations Section
    integrations: `
        <div class="content-section" id="section-integrations">
            <div class="card">
                <div class="card-header">
                    <div class="card-title">🔗 Available Integrations</div>
                </div>
                <div id="integrationsGrid" style="display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px;">
                    <div class="integration-card placeholder-card">
                        <div class="integration-icon">⏳</div>
                        <h3>Loading integrations…</h3>
                        <p>Please wait while we fetch the latest status.</p>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">🔌 Custom Webhooks</div>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Name</th>
                                <th>URL</th>
                                <th>Events</th>
                                <th>Status</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="webhooksBody">
                            <tr>
                                <td colspan="5" style="text-align: center; padding: 40px; color: #6b7280;">
                                    Loading webhooks…
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <button class="btn btn-primary" onclick="showAddWebhookModal()">➕ Add Webhook</button>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">🔑 API Keys</div>
                </div>
                <div class="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>Service</th>
                                <th>Key Name</th>
                                <th>Status</th>
                                <th>Last Used</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody id="apiKeysBody">
                            <tr>
                                <td colspan="5" style="text-align: center; padding: 40px; color: #6b7280;">
                                    Loading API keys…
                                </td>
                            </tr>
                        </tbody>
                    </table>
                </div>
                <button class="btn btn-primary" onclick="showAddApiKeyModal()">➕ Add API Key</button>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-title">📊 Integration Analytics</div>
                </div>
                <div class="stats-grid">
                    <div class="stat-card primary">
                        <div class="stat-label">Total Integrations</div>
                        <div class="stat-value">8</div>
                    </div>
                    <div class="stat-card success">
                        <div class="stat-label">Active</div>
                        <div class="stat-value">2</div>
                    </div>
                    <div class="stat-card warning">
                        <div class="stat-label">Webhooks</div>
                        <div class="stat-value">0</div>
                    </div>
                    <div class="stat-card info">
                        <div class="stat-label">API Calls (24h)</div>
                        <div class="stat-value">1,234</div>
                    </div>
                </div>
            </div>

            <style>
                .integration-card {
                    background: white;
                    border-radius: 12px;
                    padding: 24px;
                    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
                    text-align: center;
                    transition: all 0.3s;
                }
                .integration-card:hover {
                    transform: translateY(-4px);
                    box-shadow: 0 4px 16px rgba(0,0,0,0.12);
                }
                .integration-icon {
                    font-size: 48px;
                    margin-bottom: 16px;
                }
                .integration-card h3 {
                    margin: 12px 0 8px;
                    font-size: 18px;
                    color: var(--dark);
                }
                .integration-card p {
                    color: #6b7280;
                    font-size: 14px;
                    margin-bottom: 16px;
                }
                .integration-status {
                    display: inline-block;
                    padding: 6px 12px;
                    border-radius: 20px;
                    font-size: 12px;
                    font-weight: 600;
                    margin-bottom: 16px;
                }
                .integration-status.connected {
                    background: #d1fae5;
                    color: #065f46;
                }
                .integration-status.disconnected {
                    background: #fee2e2;
                    color: #991b1b;
                }
                .badge {
                    padding: 4px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                    font-weight: 600;
                }
                .badge-success {
                    background: #d1fae5;
                    color: #065f46;
                }
            </style>
        </div>
    `
};

// Export for use in main HTML
if (typeof module !== 'undefined' && module.exports) {
    module.exports = window.SECTIONS;
}
