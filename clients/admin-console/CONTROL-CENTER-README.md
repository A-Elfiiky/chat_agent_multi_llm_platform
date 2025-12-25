# 🎛️ Copilot Control Center - Centralized Admin Dashboard

## Overview

The **Copilot Control Center** is a comprehensive, unified admin dashboard that provides complete control over all platform features in one beautiful, intuitive interface. No more jumping between multiple endpoints - everything you need is now in one place!

## 🚀 Features

### 📊 Dashboard Overview
- **Real-time Statistics**: Monitor total interactions, cache hit rates, response times, escalation rates, and more
- **Visual Analytics**: Interactive charts showing traffic trends and sentiment distribution
- **Popular Questions**: Track the most frequently asked questions with performance metrics
- **Quick Actions**: One-click access to common administrative tasks

### 📈 Analytics
- **Comprehensive Metrics**: Total events, unique users, session times, engagement rates
- **Traffic Trends**: View daily/weekly/monthly traffic patterns
- **Performance Monitoring**: Track response times and cache effectiveness
- **User Engagement**: Analyze event types, user behavior, and trends
- **Export Capabilities**: Download analytics data for external analysis

### 🌍 Multi-language Support
- **Language Statistics**: View usage by language with cache hit rates
- **Translation Management**: Lookup, clear, and manage translation cache
- **Cost Tracking**: Monitor translation costs per language
- **Cache Cleanup**: Remove old translations to optimize storage
- **Performance Charts**: Visualize translation usage patterns

### 😊 Sentiment Analysis & Escalation
- **Sentiment Distribution**: Real-time breakdown of customer emotions
- **Escalation Tracking**: Monitor urgent/angry interactions requiring attention
- **Recent Escalations Table**: View escalated conversations with context
- **Threshold Configuration**: Adjust sensitivity for escalation triggers
- **Auto-escalation Settings**: Configure keyword-based escalation

### ⚡ Response Caching
- **Cache Statistics**: Total entries, hit rates, cost savings
- **Performance Metrics**: Track cache effectiveness over time
- **Entry Management**: View and delete individual cache entries
- **Bulk Operations**: Clear all cache with one click
- **Cost Savings Tracking**: See how much caching saves you

### 🛡️ Rate Limiting & Abuse Prevention
- **API Key Management**: Monitor usage per API key with tier limits
- **Blocked Entities**: View and manage blocked IPs, API keys, and users
- **Abuse Incidents**: Track recent abuse attempts with severity levels
- **Manual Blocking**: Block entities with custom durations and reasons
- **Unblock Capabilities**: Restore access to blocked entities
- **Usage Visualization**: See usage patterns and identify abusers
- **Rate Limit Configuration**: Set custom limits for different tiers

### 🧪 Diagnostics & Health Tests (NEW)
- **LLM API Tester**: Run curated prompts against every configured provider, capture latency + sample responses, and flag missing API keys before traffic is impacted.
- **LLM History View**: Drill into `llm_test_results` retention to compare prior runs, see failure causes, and export directly from the Control Center.
- **Telephony Tester**: Validate Twilio credentials, webhook reachability, Voice Orchestrator health, and optional outbound simulations without leaving the dashboard.
- **Voice Context Snapshot**: See which ngrok/Base URL, Twilio SID, and default IVR mode the backend is using so misconfigurations surface immediately.
- **Run Modes**: Trigger dry runs for config checks or live calls (`dry` vs `live`) with guardrails that prevent accidental customer calls.

### 🎓 Knowledge Base Auto-Learning
- **Unanswered Questions**: Identify knowledge gaps
- **FAQ Suggestions**: Review AI-generated FAQ recommendations
- **Approve/Reject Workflow**: Control what gets added to knowledge base
- **Question Clustering**: Find similar questions automatically
- **Generate FAQs**: Bulk create FAQ suggestions from patterns
- **Export Knowledge Gaps**: Download data for offline analysis

### 💬 Conversation Management
- **Active Sessions**: Monitor ongoing conversations
- **Message Statistics**: Track total messages and session metrics
- **Conversation Browser**: View full conversation histories
- **Cleanup Tools**: Remove old sessions automatically
- **Export Conversations**: Download conversation data
- **Session Details**: View metadata and message counts

### 💰 Cost Analysis
- **Total Cost Tracking**: Monitor LLM usage costs
- **Provider Breakdown**: See costs by AI provider (Claude, GPT, Gemini)
- **Cache Savings**: Quantify cost reduction from caching
- **Daily Trends**: Visualize cost patterns over time
- **Cost per Request**: Track average request costs
- **Projected Costs**: Forecast monthly expenses
- **Budget Alerts**: Set threshold notifications
- **Optimization Recommendations**: Get cost-saving suggestions

### ⚙️ Settings & Configuration
- **LLM Provider Settings**: Configure primary/fallback providers
- **Performance Settings**: Adjust cache TTL, response timeouts
- **Notification Settings**: Configure alerts for escalations, abuse, costs
- **Security Settings**: Manage API key requirements, rate limiting, abuse detection
- **Custom Limits**: Set request limits per IP

### 📝 System Logs
- **Activity Logs**: View all system activity
- **Error Tracking**: Monitor warnings and errors
- **Log Filtering**: Filter by level (info, warning, error)
- **Export Logs**: Download logs for analysis
- **Log Statistics**: Success rates and error counts

## 🎨 User Interface

### Design Features
- **Modern Design**: Clean, professional interface with gradient accents
- **Responsive Layout**: Works on desktop, tablet, and mobile
- **Sidebar Navigation**: Easy access to all sections
- **Real-time Updates**: Auto-refresh every 30 seconds
- **Interactive Charts**: Powered by Chart.js for beautiful visualizations
- **Color-coded Stats**: Quick visual indicators for key metrics
- **Modal Windows**: Focused interactions without page reload
- **Alert Notifications**: Non-intrusive toast notifications
- **Loading States**: Clear feedback during data loading
- **Progress Bars**: Visual representation of usage and limits

### Color Scheme
- **Primary**: Purple gradient (#667eea → #764ba2)
- **Success**: Green (#10b981)
- **Warning**: Orange (#f59e0b)
- **Danger**: Red (#ef4444)
- **Info**: Blue (#3b82f6)

## 📁 File Structure

```
clients/admin-console/
├── control-center.html              # Main dashboard HTML
├── control-center-sections.js       # Section templates
└── control-center-functions.js      # All API interactions and logic
```

## 🚀 Getting Started

### 1. Start the Backend
```powershell
cd services/gateway-api
python -m uvicorn main:app --reload --port 8000
```

### 2. Open the Control Center
```powershell
# Open in browser
start clients/admin-console/control-center.html

# Or use VS Code Live Server
# Right-click on control-center.html → "Open with Live Server"
```

### 3. Navigate the Dashboard
- Use the **sidebar** to switch between sections
- Click **Refresh** to update data manually
- Use **Quick Actions** for common tasks
- All sections auto-load data when opened
- Diagnostics modules appear under **LLM API Tests** and **Telephony Tests** so ops teams can run pre-flight checks directly from the sidebar.

### 💬 Test Chat Modal (NEW UX)
The Quick Actions panel includes a **Test Chat** button that now opens a fault-tolerant modal for validating the `/chat` endpoint without leaving the Control Center:
1. Pick an optional language override (leave blank to auto-detect).
2. Type your message and click **Send Message**.
3. The modal shows a spinner while the request is proxied through the Gateway API.
4. On success you’ll see the response text plus provider, latency, sentiment, confidence, and detected language in a single detail block.
5. Errors (missing API key, network failures, etc.) are caught and rendered inline so the UI never crashes with "Cannot set properties of null" again.

## 🔗 API Endpoints Used

The Control Center connects to these backend endpoints:

### Analytics
- `GET /admin/analytics/dashboard?days={days}`
- `GET /admin/analytics/popular-questions?limit={limit}`
- `GET /admin/analytics/traffic?days={days}`
- `GET /admin/analytics/engagement?days={days}`
- `GET /admin/analytics/sentiment?days={days}`
- `GET /admin/analytics/escalations?limit={limit}`
- `GET /admin/analytics/costs?days={days}`
- `GET /admin/analytics/export?days={days}`

### Translation
- `GET /admin/translation/languages?days={days}`
- `POST /admin/translation/cleanup?days={days}`
- `POST /admin/translation/clear-cache`
- `POST /admin/translation/lookup`

### Cache
- `GET /admin/cache/stats`
- `GET /admin/cache/entries?limit={limit}`
- `POST /admin/cache/clear`
- `DELETE /admin/cache/entry/{hash}`

### Rate Limiting
- `GET /admin/rate-limit/stats`
- `GET /admin/rate-limit/usage?hours={hours}`
- `GET /admin/rate-limit/blocked`
- `GET /admin/rate-limit/incidents?hours={hours}&limit={limit}`
- `POST /admin/rate-limit/block`
- `POST /admin/rate-limit/unblock`

### Knowledge Base
- `GET /admin/knowledge/stats`
- `GET /admin/knowledge/unanswered?limit={limit}`
- `GET /admin/knowledge/faq-suggestions?status={status}&limit={limit}`
- `GET /admin/knowledge/clusters?min_cluster_size={size}`
- `POST /admin/knowledge/faq/{id}/approve`
- `POST /admin/knowledge/faq/{id}/reject`
- `POST /admin/knowledge/generate-faqs`
- `GET /admin/knowledge/export`

### Diagnostics & Voice Health
- `GET /admin/llm/tests/summary`
- `GET /admin/llm/tests/history?provider={provider}&limit={limit}`
- `POST /admin/llm/tests/run`
- `GET /admin/telephony/tests/summary`
- `GET /admin/telephony/tests/history?test_type={test_type}&limit={limit}`
- `POST /admin/telephony/tests/run`

### Conversations
- `GET /admin/conversations/stats`
- `GET /admin/conversations?limit={limit}`
- `POST /admin/conversations/cleanup?days={days}`
- `DELETE /admin/conversations/{session_id}`
- `GET /admin/conversations/export`

### Chat (for testing)
- `POST /chat`

## 💡 Key Features & Capabilities

### 1. Unified Control
**Before**: Multiple endpoints, scattered documentation, hard to navigate
**After**: Everything in one beautiful dashboard - click to see it all!

### 2. Real-time Monitoring
- Auto-refreshes every 30 seconds
- Manual refresh button for instant updates
- Live statistics and metrics
- Active session monitoring

### 3. Powerful Analytics
- Historical trend analysis
- Sentiment distribution tracking
- Popular questions identification
- Performance metrics
- Cost analysis and forecasting

### 4. Proactive Management
- Identify knowledge gaps automatically
- Review and approve FAQ suggestions
- Block abusive users/IPs instantly
- Monitor escalations in real-time
- Optimize cache for better performance

### 5. Cost Optimization
- Track spending by provider
- Calculate cache savings
- Project future costs
- Set budget alerts
- Get optimization recommendations

### 6. Security & Protection
- Rate limit management
- Abuse detection and blocking
- API key monitoring
- IP blocking capabilities
- Incident tracking

## 🎯 Common Use Cases

### Daily Operations
1. **Start of Day**: Check dashboard for overnight activity
2. **Monitor Performance**: Review cache hit rates and response times
3. **Handle Escalations**: Check sentiment section for urgent issues
4. **Review Knowledge Gaps**: Approve new FAQ suggestions

### Weekly Reviews
1. **Analyze Trends**: Use analytics section for weekly patterns
2. **Cost Review**: Check cost analysis for spending trends
3. **Clean Up**: Remove old cache entries and conversations
4. **Security Check**: Review abuse incidents and blocked entities

### Monthly Tasks
1. **Generate Reports**: Export analytics data
2. **Budget Planning**: Review costs and set alerts
3. **Knowledge Base Update**: Bulk approve FAQs
4. **Performance Optimization**: Analyze and tune settings

### Incident Response
1. **Escalation Alert**: Navigate to sentiment section
2. **View Conversation**: Check full conversation history
3. **Identify Pattern**: Look for similar escalations
4. **Take Action**: Block if abuse, create FAQ if knowledge gap

## 🔧 Customization

### Modify Refresh Rate
```javascript
// In control-center.html, line ~1127
setInterval(loadDashboardData, 30000); // Change 30000 to desired milliseconds
```

### Change API Base URL
```javascript
// In control-center.html, line ~1118
const API_BASE = 'http://localhost:8000'; // Change to your API URL
```

### Add Custom Sections
1. Add section HTML to `control-center-sections.js`
2. Add loading function to `control-center-functions.js`
3. Add nav item in `control-center.html` sidebar

### Customize Theme Colors
Modify CSS variables in `control-center.html`:
```css
:root {
    --primary: #667eea;      /* Change primary color */
    --secondary: #764ba2;    /* Change secondary color */
    --success: #10b981;      /* Change success color */
    /* ... */
}
```

## 📱 Mobile Support

The Control Center is fully responsive:
- **Collapsible sidebar** on mobile devices
- **Touch-friendly buttons** and interactions
- **Optimized layouts** for small screens
- **Readable stats** on any device

## 🎨 Chart Types

- **Line Charts**: Traffic trends, performance metrics, cost trends
- **Bar Charts**: Analytics comparison, translation usage
- **Doughnut Charts**: Sentiment distribution, cost breakdown
- **Pie Charts**: Provider distribution
- **Progress Bars**: Usage percentages, cache hit rates

## 🚨 Alert Types

- **Success** (Green): Operation completed successfully
- **Info** (Blue): Informational messages
- **Warning** (Orange): Caution required
- **Danger** (Red): Error or critical issue

## 🔐 Security Notes

- Admin dashboard should be **password protected** in production
- Use **HTTPS** for all API calls in production
- Implement **authentication tokens** for admin endpoints
- **Rate limit** the admin endpoints to prevent abuse
- **Log all admin actions** for audit trails

## 📊 Performance Tips

1. **Limit Data Range**: Use shorter time ranges (7 days vs 90 days) for faster loading
2. **Pagination**: Set reasonable limits on table queries
3. **Auto-refresh**: Disable if you have slow connection
4. **Export Large Data**: Download for offline analysis instead of viewing all in browser

## 🐛 Troubleshooting

### Charts Not Loading
- Check browser console for JavaScript errors
- Ensure Chart.js CDN is accessible
- Verify API responses return valid data

### API Errors
- Confirm backend server is running
- Check API_BASE URL is correct
- Verify CORS settings on backend
- Check browser network tab for failed requests

### Slow Performance
- Reduce auto-refresh frequency
- Use shorter date ranges
- Clear browser cache
- Check backend database performance

### Sidebar Not Working
- Clear browser cache
- Check for JavaScript errors
- Verify responsive breakpoints

## 🎉 What's New in Control Center

✅ **Unified Interface** - All 8 features in one dashboard
✅ **Real-time Updates** - Auto-refresh every 30 seconds
✅ **Beautiful Charts** - Visual representation of all metrics
✅ **Quick Actions** - One-click common tasks
✅ **Export Capabilities** - Download data from any section
✅ **Mobile Responsive** - Works on any device
✅ **Interactive Tables** - Sort, filter, and manage data
✅ **Modal Windows** - Focused interactions
✅ **Alert System** - Non-intrusive notifications
✅ **Cost Tracking** - Complete financial visibility
✅ **Built-in Diagnostics** - LLM + telephony testers surface provider health, Twilio readiness, and historical logs without leaving the Control Center

## 📖 Next Steps

1. **Explore each section** to see all available features
2. **Test the chat** using the Test Chat modal
3. **Review analytics** to understand your platform usage
4. **Approve FAQs** to improve your knowledge base
5. **Monitor costs** to optimize spending
6. **Set up alerts** for important events
7. **Export data** for offline analysis
8. **Customize settings** to match your needs

## 🤝 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the API endpoint documentation
3. Check backend logs for errors
4. Verify database connectivity

## 📝 License

Part of the Copilot AI Customer Service Platform.

---

**Made with ❤️ for Easy Platform Management**

**Version**: 1.0.0
**Last Updated**: 2024
**Status**: ✅ Production Ready
