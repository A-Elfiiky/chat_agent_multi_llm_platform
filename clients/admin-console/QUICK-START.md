# 🚀 Control Center - Quick Start Guide

## 🎯 Get Started in 3 Steps

### Step 1: Start the Backend

```powershell
# Navigate to the gateway API
cd services/gateway-api

# Start the server
python -m uvicorn main:app --reload --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### Step 2: Open the Control Center

**Option A - Direct Open:**
```powershell
# Open in default browser
start clients/admin-console/control-center.html
```

**Option B - VS Code Live Server:**
1. Open `clients/admin-console/control-center.html` in VS Code
2. Right-click in editor
3. Select "Open with Live Server"

**Option C - Python HTTP Server:**
```powershell
cd clients/admin-console
python -m http.server 3000
# Then open http://localhost:3000/control-center.html
```

### Step 3: Explore!

The dashboard will automatically load. Navigate using the sidebar:

1. 📊 **Dashboard** - Overview of everything
2. 📈 **Analytics** - Deep dive into metrics
3. 🌍 **Multi-language** - Translation management
4. 😊 **Sentiment** - Customer emotion tracking
5. ⚡ **Cache** - Performance optimization
6. 🛡️ **Rate Limiting** - Security and protection
7. 🎓 **Knowledge Base** - Auto-learning system
8. 💬 **Conversations** - Chat history
9. 💰 **Costs** - Financial tracking
10. ⚙️ **Settings** - Configuration
11. 📝 **Logs** - System activity

## ⚡ Quick Actions

### Test the Chat
1. Click **"💬 Test Chat"** button on dashboard
2. Select language (or auto-detect)
3. Type a question
4. Click **Send Message**
5. View response with sentiment, provider, and timing

### View Analytics
1. Go to **📈 Analytics** section
2. Select time range (7, 30, or 90 days)
3. View traffic trends and engagement metrics
4. Click **"📥 Export Data"** to download

### Manage Translations
1. Navigate to **🌍 Multi-language** section
2. View usage by language
3. Use lookup tool to check cache
4. Clean up old translations

### Monitor Cache Performance
1. Open **⚡ Cache** section
2. View hit rates and savings
3. Check recent cache entries
4. Clear cache if needed

### Handle Escalations
1. Go to **😊 Sentiment** section
2. Review recent escalations
3. Click **View** to see full conversation
4. Adjust escalation threshold if needed

### Block Abusive Users
1. Navigate to **🛡️ Rate Limiting**
2. Review abuse incidents
3. Fill in Block Entity form:
   - Entity Type: IP, API Key, or User ID
   - Value: The identifier to block
   - Reason: Why they're being blocked
   - Duration: Hours (0 = permanent)
4. Click **"🛡️ Block Entity"**

### Approve Knowledge Base FAQs
1. Go to **🎓 Knowledge Base** section
2. Review unanswered questions
3. Check pending FAQ suggestions
4. Click **✓ Approve** or **✗ Reject**
5. Or click **"💡 Generate Suggestions"** for bulk

### Review Costs
1. Open **💰 Costs** section
2. View total cost and savings
3. Check breakdown by provider
4. Set budget alert if needed
5. Export cost report

### Export Data
Available in multiple sections:
- **Analytics**: Full metrics export
- **Knowledge Base**: Unanswered questions
- **Conversations**: Chat histories
- **Costs**: Financial report

## 🎨 Dashboard Overview

### Key Metrics (Auto-updating every 30 seconds)

**Top Row Stats:**
- **Total Interactions** - All chat messages processed
- **Cache Hit Rate** - Percentage of cached responses
- **Avg Response Time** - Speed in milliseconds
- **Escalation Rate** - Percentage requiring human intervention
- **Active Languages** - Number of languages in use
- **Cost Savings** - Money saved from caching

**Charts:**
- **Traffic Overview** - Daily interaction volume
- **Sentiment Distribution** - Emotional breakdown (pie chart)

**Popular Questions Table:**
- Most frequently asked questions
- Count, confidence score, response time
- Helps identify knowledge base gaps

## 🔧 Common Tasks

### Daily Monitoring
```
1. Open Dashboard
2. Check escalation rate
3. Review popular questions
4. Monitor cache hit rate
5. Check for abuse incidents
```

### Weekly Analysis
```
1. Go to Analytics
2. Set date range to 7 days
3. Review traffic trends
4. Check engagement metrics
5. Export data for reports
```

### Knowledge Base Update
```
1. Open Knowledge Base section
2. Review unanswered questions
3. Click "Generate Suggestions"
4. Approve relevant FAQs
5. Generate clusters for insights
```

### Cost Optimization
```
1. Open Costs section
2. Review provider breakdown
3. Check cache savings
4. Identify expensive patterns
5. Optimize based on recommendations
```

### Security Check
```
1. Go to Rate Limiting
2. Review recent incidents
3. Check blocked entities
4. Monitor API key usage
5. Block suspicious activity
```

## 📱 Mobile Access

The Control Center works on mobile devices:

1. **Sidebar**: Tap ☰ to toggle menu
2. **Stats**: Scroll vertically to see all cards
3. **Tables**: Swipe horizontally to see all columns
4. **Charts**: Tap to see data points
5. **Forms**: Full touch support

## ⚙️ Settings & Configuration

### Change Refresh Rate
Default: 30 seconds

To modify, edit `control-center.html` line ~1127:
```javascript
setInterval(loadDashboardData, 30000); // milliseconds
```

### Change API URL
If your backend isn't on localhost:8000, edit line ~1118:
```javascript
const API_BASE = 'http://your-server:8000';
```

### Customize Theme
Edit CSS variables in `control-center.html`:
```css
:root {
    --primary: #667eea;
    --secondary: #764ba2;
    /* etc. */
}
```

## 🐛 Troubleshooting

### "Failed to fetch" errors
**Problem**: Can't connect to backend
**Solution**: 
1. Verify backend is running (check step 1)
2. Check API_BASE URL
3. Look for CORS errors in console

### Charts not showing
**Problem**: Blank chart areas
**Solution**:
1. Check browser console for errors
2. Verify Chart.js is loading
3. Ensure API returns valid data

### Data not loading
**Problem**: Loading spinners never finish
**Solution**:
1. Open browser DevTools (F12)
2. Check Network tab for failed requests
3. Look at Console for JavaScript errors
4. Verify database has data

### Sidebar not responsive
**Problem**: Menu doesn't hide on mobile
**Solution**:
1. Clear browser cache
2. Hard refresh (Ctrl + F5)
3. Check for JavaScript errors

## 💡 Pro Tips

1. **Use Refresh Button**: Manual refresh is faster than waiting for auto-update
2. **Bookmark Sections**: Right-click any section to bookmark directly
3. **Export Regularly**: Download data for offline analysis
4. **Set Short Ranges**: Use 7 days for faster loading
5. **Monitor Escalations**: Check daily to catch issues early
6. **Review FAQs Weekly**: Keep knowledge base current
7. **Track Costs Monthly**: Set budgets and alerts
8. **Clean Up Cache**: Remove old entries monthly

## 🎯 Success Metrics

Track these KPIs using the Control Center:

### Performance
- **Cache Hit Rate**: Target 60%+
- **Avg Response Time**: Target <2000ms
- **Escalation Rate**: Target <5%

### Quality
- **Positive Sentiment**: Target 70%+
- **Unanswered Questions**: Target <10
- **FAQ Coverage**: Approve new FAQs weekly

### Efficiency
- **Cost per Request**: Monitor trends
- **Cache Savings**: Maximize through tuning
- **Active Sessions**: Track peak times

## 📊 Understanding the Charts

### Traffic Overview (Line Chart)
- **X-axis**: Dates
- **Y-axis**: Number of interactions
- **Use**: Identify busy periods, spot anomalies

### Sentiment Distribution (Pie Chart)
- **Segments**: Positive, Neutral, Negative, Angry, Urgent
- **Colors**: Green (good) to Red (urgent)
- **Use**: Monitor customer satisfaction

### Cost Breakdown (Doughnut Chart)
- **Segments**: Cost by AI provider
- **Use**: Identify expensive providers

### Performance Metrics (Dual-axis Line)
- **Left Y-axis**: Response time (ms)
- **Right Y-axis**: Cache hit rate (%)
- **Use**: Correlate performance with caching

## 🔐 Security Best Practices

1. **Enable Authentication**: Add login to admin dashboard
2. **Use HTTPS**: Encrypt all communications
3. **Restrict Access**: IP whitelist for admin
4. **Monitor Logs**: Check for suspicious activity
5. **Regular Backups**: Export data frequently
6. **Strong API Keys**: Use complex keys for production
7. **Rate Limit Admin**: Protect against brute force
8. **Audit Trail**: Log all admin actions

## 📚 Learn More

- **Full Documentation**: See `CONTROL-CENTER-README.md`
- **API Reference**: Check `QUICK_REFERENCE.md`
- **Project Overview**: Read `PROJECT_SUMMARY.md`
- **Installation Guide**: Follow `INSTALLATION.md`

## 🎉 You're All Set!

The Copilot Control Center puts all platform management at your fingertips. Explore each section, test the features, and optimize your AI customer service platform!

**Happy Monitoring! 🚀**

---

**Quick Links:**
- Dashboard: Main overview
- Analytics: Deep metrics
- Knowledge Base: FAQ management
- Costs: Financial tracking
- Settings: Configuration

**Need Help?**
- Check troubleshooting section
- Review full documentation
- Check backend logs
- Verify database connection
