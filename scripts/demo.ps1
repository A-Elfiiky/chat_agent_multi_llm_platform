# Demo Script - Showcases All New Features
# Run this after starting the platform to see features in action

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🚀 Platform Features Demo" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8000"
$adminHeaders = @{ 'X-Admin-Token' = 'local-admin-token' }

# Demo 1: Multi-language Customer Support
Write-Host "Demo 1: Multi-language Customer Support" -ForegroundColor Magenta
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host ""

$languages = @(
    @{ lang="Spanish"; question="¿Dónde está mi pedido?"; code="es" },
    @{ lang="French"; question="Comment puis-je annuler ma commande?"; code="fr" },
    @{ lang="German"; question="Wie kann ich den Kundendienst kontaktieren?"; code="de" },
    @{ lang="Italian"; question="Qual è la vostra politica di reso?"; code="it" }
)

foreach ($test in $languages) {
    Write-Host "🌍 Customer from $($test.lang) asks:" -ForegroundColor Yellow
    Write-Host "   '$($test.question)'" -ForegroundColor White
    
    try {
        $body = @{
            message = $test.question
            session_id = "demo-$($test.code)-001"
        } | ConvertTo-Json

        $response = Invoke-RestMethod -Uri "$baseUrl/chat" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 30
        
        Write-Host "   💬 Bot responds in $($test.lang):" -ForegroundColor Green
        $preview = $response.answer_text.Substring(0, [Math]::Min(120, $response.answer_text.Length))
        Write-Host "   '$preview...'" -ForegroundColor Gray
        Write-Host "   ⏱️  Response time: $($response.processing_time)s" -ForegroundColor Cyan
        Write-Host ""
    } catch {
        Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
    }
    
    Start-Sleep -Seconds 1
}

Write-Host ""

# Demo 2: Sentiment Analysis in Action
Write-Host "Demo 2: Sentiment Analysis & Escalation" -ForegroundColor Magenta
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host ""

$sentiments = @(
    @{ type="Happy"; message="Thank you so much! This is exactly what I needed!"; emoji="😊" },
    @{ type="Frustrated"; message="I've been waiting for 2 weeks. This is getting ridiculous."; emoji="😤" },
    @{ type="Angry"; message="This is unacceptable! I demand to speak to a manager NOW!"; emoji="😡" },
    @{ type="Urgent"; message="URGENT: My order was supposed to arrive today for an event!"; emoji="⚠️" }
)

foreach ($test in $sentiments) {
    Write-Host "$($test.emoji) $($test.type) Customer:" -ForegroundColor Yellow
    Write-Host "   '$($test.message)'" -ForegroundColor White
    
    try {
        $body = @{
            message = $test.message
            session_id = "demo-sentiment-$($test.type.ToLower())"
        } | ConvertTo-Json

        $response = Invoke-RestMethod -Uri "$baseUrl/chat" -Method Post -ContentType "application/json" -Body $body -TimeoutSec 30
        
        Write-Host "   📊 Sentiment: $($response.sentiment.sentiment) (score: $($response.sentiment.score))" -ForegroundColor Cyan
        
        if ($response.sentiment.needs_escalation) {
            Write-Host "   🚨 ESCALATED TO HUMAN AGENT" -ForegroundColor Red
            Write-Host "   Flags: $($response.sentiment.flags -join ', ')" -ForegroundColor Red
        } else {
            Write-Host "   ✅ Handled by AI" -ForegroundColor Green
        }
        
        $preview = $response.answer_text.Substring(0, [Math]::Min(100, $response.answer_text.Length))
        Write-Host "   Response tone: $preview..." -ForegroundColor Gray
        Write-Host ""
    } catch {
        Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host ""
    }
    
    Start-Sleep -Seconds 1
}

Write-Host ""

# Demo 3: Performance & Analytics
Write-Host "Demo 3: Real-time Analytics Dashboard" -ForegroundColor Magenta
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host ""

try {
    $dashboard = Invoke-RestMethod -Uri "$baseUrl/admin/analytics/dashboard?days=7" -Headers $adminHeaders -TimeoutSec 10
    
    Write-Host "📊 Last 7 Days Performance:" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   Interactions:     $($dashboard.total_interactions)" -ForegroundColor White
    Write-Host "   Active Sessions:  $($dashboard.active_sessions)" -ForegroundColor White
    Write-Host "   Avg Response:     $($dashboard.avg_response_time_ms) ms" -ForegroundColor White
    Write-Host "   Cache Hit Rate:   $([math]::Round($dashboard.cache_hit_rate * 100, 1))%" -ForegroundColor White
    Write-Host "   Escalation Rate:  $($dashboard.escalation_rate)%" -ForegroundColor White
    Write-Host ""
    
    Write-Host "😊 Sentiment Distribution:" -ForegroundColor Yellow
    foreach ($key in $dashboard.sentiment_distribution.Keys) {
        Write-Host "   • $key : $($dashboard.sentiment_distribution[$key])" -ForegroundColor Gray
    }
    Write-Host ""
    
} catch {
    Write-Host "   ❌ Error fetching analytics: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Demo 4: Cost Analysis
Write-Host "Demo 4: Cost Optimization" -ForegroundColor Magenta
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host ""

try {
    $costs = Invoke-RestMethod -Uri "$baseUrl/admin/analytics/costs?days=30" -Headers $adminHeaders -TimeoutSec 10
    
    Write-Host "💰 Cost Analysis (Last 30 days):" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "   Total Requests:   $($costs.total_requests)" -ForegroundColor White
    Write-Host "   Estimated Cost:   `$$($costs.estimated_cost_usd)" -ForegroundColor White
    Write-Host "   Cache Savings:    `$$($costs.cache_savings_usd) 💵" -ForegroundColor Green
    Write-Host ""
    
    if ($costs.provider_breakdown.Count -gt 0) {
        Write-Host "   Provider Usage:" -ForegroundColor Yellow
        foreach ($key in $costs.provider_breakdown.Keys) {
            $cost = if ($costs.cost_per_provider.ContainsKey($key)) { $costs.cost_per_provider[$key] } else { 0 }
            Write-Host "   • $key : $($costs.provider_breakdown[$key]) requests (`$$cost)" -ForegroundColor Gray
        }
    }
    Write-Host ""
    
} catch {
    Write-Host "   ❌ Error fetching cost data: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Demo 5: Knowledge Base Learning
Write-Host "Demo 5: Knowledge Base Auto-Learning" -ForegroundColor Magenta
Write-Host "----------------------------------------" -ForegroundColor Gray
Write-Host ""

try {
    $knowledgeGaps = Invoke-RestMethod -Uri "$baseUrl/admin/knowledge-gaps?min_frequency=1" -Headers $adminHeaders -TimeoutSec 10
    
    if ($knowledgeGaps.total -gt 0) {
        Write-Host "🎓 System has identified $($knowledgeGaps.total) knowledge gap(s):" -ForegroundColor Yellow
        Write-Host ""
        
        foreach ($gap in $knowledgeGaps.knowledge_gaps | Select-Object -First 5) {
            Write-Host "   ❓ '$($gap.question)'" -ForegroundColor White
            Write-Host "      • Asked $($gap.frequency) times" -ForegroundColor Gray
            Write-Host "      • Avg confidence: $($gap.avg_confidence)" -ForegroundColor Gray
            Write-Host ""
        }
    } else {
        Write-Host "   ✅ No significant knowledge gaps detected!" -ForegroundColor Green
        Write-Host "   (System will identify gaps as it handles more questions)" -ForegroundColor Gray
        Write-Host ""
    }
    
    # Check FAQ suggestions
    $suggestions = Invoke-RestMethod -Uri "$baseUrl/admin/faq-suggestions?limit=5" -Headers $adminHeaders -TimeoutSec 10
    
    if ($suggestions.total -gt 0) {
        Write-Host "💡 Auto-generated FAQ suggestions: $($suggestions.total)" -ForegroundColor Yellow
        Write-Host "   (Review and approve in admin console)" -ForegroundColor Gray
        Write-Host ""
    }
    
} catch {
    Write-Host "   ❌ Error fetching knowledge gaps: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host ""
}

# Summary
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ✅ Demo Complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🎯 Key Features Demonstrated:" -ForegroundColor Yellow
Write-Host "   ✅ Multi-language support (20+ languages)" -ForegroundColor White
Write-Host "   ✅ Sentiment analysis & auto-escalation" -ForegroundColor White
Write-Host "   ✅ Real-time analytics dashboard" -ForegroundColor White
Write-Host "   ✅ Cost optimization with caching" -ForegroundColor White
Write-Host "   ✅ Knowledge base auto-learning" -ForegroundColor White
Write-Host ""
Write-Host "📊 Next Steps:" -ForegroundColor Yellow
Write-Host "   1. Open admin console: clients/admin-console/index-advanced.html" -ForegroundColor White
Write-Host "   2. Run ./test-features.ps1 for comprehensive tests" -ForegroundColor White
Write-Host "   3. Check PROJECT_SUMMARY.md for full documentation" -ForegroundColor White
Write-Host ""
