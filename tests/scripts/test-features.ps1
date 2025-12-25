# Test Script for New Features
# Tests multi-language, analytics, rate limiting, and knowledge gap features

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Testing New Platform Features" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"
$adminHeaders = @{ 'X-Admin-Token' = 'local-admin-token' }

# Test 1: Multi-language Support
Write-Host "1️⃣  Testing Multi-language Support..." -ForegroundColor Yellow
Write-Host ""

# Spanish question
Write-Host "   📝 Spanish: ¿Cuál es su política de devoluciones?" -ForegroundColor White
try {
    $spanishBody = @{
        message = "¿Cuál es su política de devoluciones?"
        session_id = "test-spanish-001"
    } | ConvertTo-Json

    $spanishResponse = Invoke-RestMethod -Uri "$baseUrl/chat" -Method Post -ContentType "application/json" -Body $spanishBody -TimeoutSec 30
    Write-Host "   ✅ Response:" -ForegroundColor Green
    Write-Host "      $($spanishResponse.answer_text.Substring(0, [Math]::Min(100, $spanishResponse.answer_text.Length)))..." -ForegroundColor Gray
    Write-Host "      Provider: $($spanishResponse.provider)" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# French question
Write-Host "   📝 French: Comment puis-je suivre ma commande?" -ForegroundColor White
try {
    $frenchBody = @{
        message = "Comment puis-je suivre ma commande?"
        session_id = "test-french-001"
    } | ConvertTo-Json

    $frenchResponse = Invoke-RestMethod -Uri "$baseUrl/chat" -Method Post -ContentType "application/json" -Body $frenchBody -TimeoutSec 30
    Write-Host "   ✅ Response:" -ForegroundColor Green
    Write-Host "      $($frenchResponse.answer_text.Substring(0, [Math]::Min(100, $frenchResponse.answer_text.Length)))..." -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Test 2: Translation Statistics
Write-Host "2️⃣  Checking Translation Statistics..." -ForegroundColor Yellow
Write-Host ""

try {
    $translationStats = Invoke-RestMethod -Uri "$baseUrl/admin/translation/stats" -Headers $adminHeaders -TimeoutSec 10
    Write-Host "   ✅ Translation Cache Stats:" -ForegroundColor Green
    Write-Host "      • Cached Translations: $($translationStats.total_cached_translations)" -ForegroundColor Gray
    Write-Host "      • Cache Hits: $($translationStats.total_cache_hits)" -ForegroundColor Gray
    Write-Host "      • Hit Rate: $($translationStats.cache_hit_rate)" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Test 3: Language Usage
Write-Host "3️⃣  Checking Language Usage..." -ForegroundColor Yellow
Write-Host ""

try {
    $languageUsage = Invoke-RestMethod -Uri "$baseUrl/admin/translation/languages?days=7" -Headers $adminHeaders -TimeoutSec 10
    Write-Host "   ✅ Language Usage (Last 7 days):" -ForegroundColor Green
    if ($languageUsage.languages.Count -gt 0) {
        foreach ($lang in $languageUsage.languages | Select-Object -First 5) {
            Write-Host "      • $($lang.language_name) ($($lang.language_code)): $($lang.total_usage) uses" -ForegroundColor Gray
        }
    } else {
        Write-Host "      No language data yet (run more tests)" -ForegroundColor Gray
    }
    Write-Host ""
} catch {
    Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Test 4: Analytics Dashboard
Write-Host "4️⃣  Checking Analytics Dashboard..." -ForegroundColor Yellow
Write-Host ""

try {
    $dashboard = Invoke-RestMethod -Uri "$baseUrl/admin/analytics/dashboard?days=7" -Headers $adminHeaders -TimeoutSec 10
    Write-Host "   ✅ Dashboard Overview (Last 7 days):" -ForegroundColor Green
    Write-Host "      • Total Interactions: $($dashboard.total_interactions)" -ForegroundColor Gray
    Write-Host "      • Active Sessions: $($dashboard.active_sessions)" -ForegroundColor Gray
    Write-Host "      • Avg Response Time: $($dashboard.avg_response_time_ms) ms" -ForegroundColor Gray
    Write-Host "      • Avg Confidence: $($dashboard.avg_confidence)" -ForegroundColor Gray
    Write-Host "      • Cache Hit Rate: $($dashboard.cache_hit_rate)" -ForegroundColor Gray
    Write-Host "      • Escalation Rate: $($dashboard.escalation_rate)%" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Test 5: Popular Questions
Write-Host "5️⃣  Checking Popular Questions..." -ForegroundColor Yellow
Write-Host ""

try {
    $popularQuestions = Invoke-RestMethod -Uri "$baseUrl/admin/analytics/popular-questions?limit=5" -Headers $adminHeaders -TimeoutSec 10
    Write-Host "   ✅ Top Questions:" -ForegroundColor Green
    if ($popularQuestions.questions.Count -gt 0) {
        $index = 1
        foreach ($q in $popularQuestions.questions) {
            $questionPreview = $q.question.Substring(0, [Math]::Min(60, $q.question.Length))
            Write-Host "      $index. $questionPreview... (asked $($q.count) times)" -ForegroundColor Gray
            $index++
        }
    } else {
        Write-Host "      No questions data yet" -ForegroundColor Gray
    }
    Write-Host ""
} catch {
    Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Test 6: Rate Limiting Stats
Write-Host "6️⃣  Checking Rate Limiting Stats..." -ForegroundColor Yellow
Write-Host ""

try {
    $rateLimitStats = Invoke-RestMethod -Uri "$baseUrl/admin/rate-limits/stats" -Headers $adminHeaders -TimeoutSec 10
    Write-Host "   ✅ Rate Limiting Overview:" -ForegroundColor Green
    Write-Host "      • Requests Today: $($rateLimitStats.requests_today)" -ForegroundColor Gray
    Write-Host "      • Unique API Keys: $($rateLimitStats.unique_api_keys)" -ForegroundColor Gray
    Write-Host "      • Abuse Incidents: $($rateLimitStats.abuse_incidents_today)" -ForegroundColor Gray
    Write-Host "      • Currently Blocked: $($rateLimitStats.currently_blocked)" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Test 7: Knowledge Gaps
Write-Host "7️⃣  Checking Knowledge Gaps..." -ForegroundColor Yellow
Write-Host ""

try {
    $knowledgeGaps = Invoke-RestMethod -Uri "$baseUrl/admin/knowledge-gaps?min_frequency=1&days=7" -Headers $adminHeaders -TimeoutSec 10
    Write-Host "   ✅ Knowledge Gaps:" -ForegroundColor Green
    if ($knowledgeGaps.total -gt 0) {
        Write-Host "      • Total Gaps Found: $($knowledgeGaps.total)" -ForegroundColor Gray
        foreach ($gap in $knowledgeGaps.knowledge_gaps | Select-Object -First 3) {
            Write-Host "      • $($gap.question.Substring(0, [Math]::Min(50, $gap.question.Length)))... (frequency: $($gap.frequency))" -ForegroundColor Gray
        }
    } else {
        Write-Host "      No knowledge gaps identified yet" -ForegroundColor Gray
    }
    Write-Host ""
} catch {
    Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Test 8: User Engagement
Write-Host "8️⃣  Checking User Engagement..." -ForegroundColor Yellow
Write-Host ""

try {
    $engagement = Invoke-RestMethod -Uri "$baseUrl/admin/analytics/engagement?days=7" -Headers $adminHeaders -TimeoutSec 10
    Write-Host "   ✅ User Engagement Metrics:" -ForegroundColor Green
    Write-Host "      • Total Sessions: $($engagement.total_sessions)" -ForegroundColor Gray
    Write-Host "      • Avg Messages/Session: $($engagement.avg_messages_per_session)" -ForegroundColor Gray
    Write-Host "      • Avg Session Duration: $($engagement.avg_session_duration_seconds)s" -ForegroundColor Gray
    Write-Host "      • Return Rate: $($engagement.return_rate_percent)%" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Test 9: Cost Analysis
Write-Host "9️⃣  Checking Cost Analysis..." -ForegroundColor Yellow
Write-Host ""

try {
    $costs = Invoke-RestMethod -Uri "$baseUrl/admin/analytics/costs?days=30" -Headers $adminHeaders -TimeoutSec 10
    Write-Host "   ✅ Cost Analysis (Last 30 days):" -ForegroundColor Green
    Write-Host "      • Estimated Cost: `$$($costs.estimated_cost_usd)" -ForegroundColor Gray
    Write-Host "      • Cache Savings: `$$($costs.cache_savings_usd)" -ForegroundColor Gray
    Write-Host "      • Total Requests: $($costs.total_requests)" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Test 10: Sentiment Analysis
Write-Host "🔟 Testing Sentiment Analysis..." -ForegroundColor Yellow
Write-Host ""

# Angry message
Write-Host "   📝 Angry: This is terrible! I want a refund now!" -ForegroundColor White
try {
    $angryBody = @{
        message = "This is terrible! I want a refund now!"
        session_id = "test-sentiment-001"
    } | ConvertTo-Json

    $angryResponse = Invoke-RestMethod -Uri "$baseUrl/chat" -Method Post -ContentType "application/json" -Body $angryBody -TimeoutSec 30
    Write-Host "   ✅ Sentiment Detected: $($angryResponse.sentiment.sentiment)" -ForegroundColor Green
    Write-Host "      • Score: $($angryResponse.sentiment.score)" -ForegroundColor Gray
    Write-Host "      • Needs Escalation: $($angryResponse.sentiment.needs_escalation)" -ForegroundColor Gray
    Write-Host ""
} catch {
    Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ✅ Testing Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "📊 View full analytics in the admin console:" -ForegroundColor Yellow
Write-Host "   Open: clients/admin-console/index-advanced.html" -ForegroundColor White
Write-Host ""
Write-Host "📚 Documentation:" -ForegroundColor Yellow
Write-Host "   • PROJECT_SUMMARY.md - Complete overview" -ForegroundColor White
Write-Host "   • QUICK_REFERENCE.md - API examples" -ForegroundColor White
Write-Host "   • TRANSLATION_SETUP.md - Language setup" -ForegroundColor White
Write-Host ""
