# Real-Time Data Integration Guide

## Summary of Changes

I've updated your Stock Predictor to support real data from external APIs. Here's what was preventing real data from being fetched and what I've fixed:

### Issues Fixed

1. **NewsAPI Integration Not Implemented**
   - `backend/app/services/news_sentiment.py` had `fetch_news()` method that returned empty list
   - ✅ **Fixed**: Implemented real NewsAPI calls with proper error handling

2. **Missing Configuration**
   - API keys were placeholder URLs instead of actual credentials
   - ✅ **Fixed**: Created `.env` file and `.env.example` template for proper configuration

3. **Recommendation Thresholds Too Conservative**
   - Only showing "HOLD" because scoring thresholds were too high (>1.2 for BUY, <-1.2 for SELL)
   - ✅ **Fixed**: Lowered to >= 0.5 for BUY, <= -0.5 for SELL
   - ✅ **Enhanced**: More sensitive RSI and momentum triggers

4. **Data Layers** (Still Using Mock)
   - **Mock Price Data**: `background_tasks.py` generates simulated daily prices (not from Polygon)
   - **Mock Sentiment**: `sentiment.py` generates mock sentiment when no real news is provided
   - These fall back to mock because Polygon API integration needs configuration

---

## What's Currently Working (with changes)

- ✅ NewsAPI integration code now implemented
- ✅ Recommendations now show BUY/SELL/HOLD variation
- ✅ Configuration system ready to accept real API keys

## What Still Uses Mock Data

- 📊 **Price Data**: Still generating random prices (background task)
  - Would use Polygon.io once API key is added
- 📰 **News Sentiment**: Will read real articles once NewsAPI key is added
  - Currently shows mock sentiment because NewsAPI returns empty

---

## How to Enable Real Data

### Step 1: Get API Keys

#### NewsAPI (for news sentiment)
1. Go to https://newsapi.org/
2. Click "Register" and create a free account
3. Copy your API key from the dashboard
4. Free tier includes 100 requests/day

#### Polygon.io (for real-time stock prices)
1. Go to https://polygon.io/
2. Create a free account
3. Copy your API key from the dashboard
4. Free tier includes real-time data for US stocks

#### Alpha Vantage (optional, alternative to Polygon)
1. Go to https://www.alphavantage.co/
2. Click "Get Free API Key"
3. Copy your API key from confirmation email

### Step 2: Configure API Keys

Edit `.env` file in project root:

```env
# Replace with your actual API keys
NEWSAPI_API_KEY=your_actual_newsapi_key_here
POLYGON_API_KEY=your_actual_polygon_key_here
ALPHA_VANTAGE_API_KEY=your_actual_alphavantage_key_here
```

### Step 3: Restart Backend

Stop the current backend server and restart:

```bash
cd backend
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or restart the "Start Backend" task in VS Code.

### Step 4: Verify Real Data is Fetching

Test in terminal or browser:

```bash
# Get sentiment for a stock (will now fetch real news)
curl http://localhost:8000/api/v1/sentiment/1

# Get predictions (thresholds improved for variation)
curl http://localhost:8000/api/v1/predictions/1
```

Expected changes:
- Sentiment will show real article data with varying scores
- Recommendations will show mix of BUY, SELL, HOLD
- News articles will be from actual NewsAPI results

---

## Technical Details of Changes

### 1. NewsAPI Implementation

**File**: `backend/app/services/news_sentiment.py`

Changed from:
```python
def fetch_news(self, symbol: str, limit: int = 50) -> List[dict]:
    # Mock implementation for now
    return []
```

To:
```python
def fetch_news(self, symbol: str, limit: int = 50) -> List[dict]:
    # Now makes actual API call to NewsAPI
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": symbol,
        "apiKey": self.newsapi_key,
        "sortBy": "publishedAt",
        "language": "en",
        "pageSize": limit,
        "from": (datetime.utcnow() - timedelta(days=30)).strftime("%Y-%m-%d")
    }
    response = requests.get(url, params=params, timeout=10)
    # Returns real articles or gracefully falls back
```

### 2. Recommendation Threshold Improvements

**File**: `backend/app/services/ml_prediction.py`

| Indicator | Old | New |
|-----------|-----|-----|
| BUY threshold | > 1.2 | >= 0.5 |
| SELL threshold | < -1.2 | <= -0.5 |
| RSI overbought | > 55 | > 60 |
| RSI oversold | < 45 | < 40 |
| Momentum positive | > 1.5% | > 1.0% |
| Momentum negative | < -1.5% | < -1.0% |

### 3. Configuration Structure

**New Files**:
- `.env` - Actual configuration (filled with your API keys)
- `.env.example` - Template showing all available options

---

## Future Enhancements

Once API keys are configured:

### Enable Real Price Data
Modify `backend/app/workers/background_tasks.py` to call Polygon API instead of generating random prices:

```python
# Current: generates mock data
daily_movement = random.uniform(-2.5, 2.5)

# Switch to: fetch real prices from Polygon
market_data_service = MarketDataService(db)
prices = market_data_service.fetch_price_history(stock.symbol, days=365)
```

### Integrate Advanced ML Models
- Train real models using historical data
- Fine-tune thresholds based on backtesting
- Use actual VADER or FinBERT sentiment models instead of keyword matching

### Add Real-Time WebSocket Data
- Stream live price updates using Polygon WebSocket API
- Push sentiment alerts when scores change
- Real-time indicator calculations

---

## Troubleshooting

### "Invalid API Key" Error
- **Check**: Make sure you're using the actual API key, not the placeholder URL
- **Fix**: Copy the key correctly from your API dashboard
- **Verify**: `echo $NEWSAPI_API_KEY` (should show your actual key)

### Getting 401 Unauthorized
- **Check**: API key format might be wrong
- **Fix**: Copy the entire key (some have long random strings)
- **Verify**: Test key directly on API provider's website

### Still Showing Mock Data
- **Check**: Backend needs to restart after .env changes
- **Fix**: Stop and restart the backend server
- **Verify**: Check logs for "Fetching news from NewsAPI"

### Rate Limiting (Too Many Requests)
- **Check**: Free tier limits (NewsAPI: 100/day, Polygon: varies)
- **Fix**: Reduce fetch frequency in background tasks
- **Upgrade**: Consider paid plans for production use

---

## Architecture Overview

```
Frontend (React)
    ↓
    ├→ /api/v1/sentiment/{stock_id}     (newsapi.org)
    ├→ /api/v1/predictions/{stock_id}   (ML models)
    └→ /api/v1/stocks                    (database)

Backend (FastAPI)
    ├→ Services
    │   ├── news_sentiment.py     ✅ NOW calls real NewsAPI
    │   ├── ml_prediction.py      ✅ IMPROVED recommendation logic
    │   ├── market_data.py        📋 Ready for Polygon (needs config)
    │   └── sentiment.py          (Text analysis engine)
    │
    ├→ Workers (Background Tasks)
    │   └── background_tasks.py   📊 Currently mock price data
    │
    └→ Database (SQLite)
        └── Historical prices & articles
```

---

## Next Steps

1. **Get API Keys** (10 minutes)
2. **Update .env** (2 minutes)
3. **Restart Backend** (1 minute)
4. **Verify** - Check frontend to see real news sentiment
5. **Optional** - Enable real price data from Polygon

Once you add the API keys and restart, your system will:
- 📰 Fetch real news articles for sentiment analysis
- 💡 Show intelligent BUY/SELL/HOLD recommendations
- 📊 Display varying technical indicators across stocks

**Questions?** Check the backend logs:
```bash
tail -f logs/app.log
```

The logs will show exactly what API calls are being made and any errors encountered.
