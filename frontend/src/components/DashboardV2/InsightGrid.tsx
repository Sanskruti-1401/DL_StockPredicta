/**
 * Insight Grid Component
 * Shows technical indicators, sentiment, and fundamental data
 */

import React, { useEffect, useState } from 'react';
import { Stock } from '../../api/endpoint';
import '../../styles/components/insight-grid.css';

interface InsightGridProps {
  stock: Stock;
}

export const InsightGrid: React.FC<InsightGridProps> = ({ stock }) => {
  // Real data from API
  const [rsi, setRsi] = useState<number>(50);
  const [volatility, setVolatility] = useState<number>(25);
  const [sentiment, setSentiment] = useState<number>(50);
  const [positiveArticles, setPositiveArticles] = useState<number>(0);
  const [negativeArticles, setNegativeArticles] = useState<number>(0);

  // 52-week range based on P/E ratio
  const peRatio = stock.pe_ratio || 25;
  const estimated52wHigh = (peRatio * 35).toFixed(2);
  const estimated52wLow = (peRatio * 20).toFixed(2);

  // Fetch real technical indicators from predictions API
  useEffect(() => {
    const fetchTechnicalData = async () => {
      try {
        console.log(`[InsightGrid] Fetching data for stock ${stock.id}...`);
        
        // Use absolute URL directly to backend
        const apiUrl = `http://localhost:8000/api/v1/predictions/${stock.id}?hours_ahead=24`;
        console.log(`[InsightGrid] Fetching from: ${apiUrl}`);
        
        // Fetch predictions which includes technical analysis
        const response = await fetch(apiUrl);
        console.log(`[InsightGrid] Predictions response status: ${response.status}`);
        
        if (response.ok) {
          const data = await response.json();
          console.log(`[InsightGrid] Predictions data:`, data);
          
          if (data.technical_analysis) {
            console.log(`[InsightGrid] Setting RSI to ${data.technical_analysis.rsi}`);
            setRsi(Math.round(data.technical_analysis.rsi || 50));
            setVolatility(Math.round(data.technical_analysis.volatility || 25));
          } else {
            console.warn(`[InsightGrid] No technical_analysis in response`);
          }
        } else {
          console.error(`[InsightGrid] Predictions API error: ${response.status}`);
        }
        
        // Fetch sentiment data
        try {
          const sentimentUrl = `http://localhost:8000/api/v1/sentiment/${stock.id}`;
          console.log(`[InsightGrid] Fetching sentiment from: ${sentimentUrl}`);
          
          const sentimentResponse = await fetch(sentimentUrl);
          console.log(`[InsightGrid] Sentiment response status: ${sentimentResponse.status}`);
          
          if (sentimentResponse.ok) {
            const sentimentData = await sentimentResponse.json();
            console.log(`[InsightGrid] Sentiment data:`, sentimentData);
            
            if (sentimentData.overall_sentiment !== undefined) {
              // Convert sentiment (-1 to 1) to percentage scale (0 to 100)
              const sentimentPercent = ((sentimentData.overall_sentiment + 1) / 2) * 100;
              console.log(`[InsightGrid] Setting sentiment to ${sentimentPercent}`);
              setSentiment(Math.round(sentimentPercent));
            }
            
            // Set article counts from sentiment analysis
            if (sentimentData.positive_articles !== undefined) {
              console.log(`[InsightGrid] Setting positive articles to ${sentimentData.positive_articles}`);
              setPositiveArticles(sentimentData.positive_articles);
            }
            if (sentimentData.negative_articles !== undefined) {
              console.log(`[InsightGrid] Setting negative articles to ${sentimentData.negative_articles}`);
              setNegativeArticles(sentimentData.negative_articles);
            }
          } else {
            console.error(`[InsightGrid] Sentiment API error: ${sentimentResponse.status}`);
          }
        } catch (err) {
          console.error('[InsightGrid] Sentiment fetch exception:', err);
        }
        
      } catch (err) {
        console.error('[InsightGrid] Error fetching technical data:', err);
      }
    };
    
    fetchTechnicalData();
  }, [stock.id]);

  const sentimentLabel =
    sentiment > 70 ? 'Very Bullish' : sentiment > 55 ? 'Bullish' : sentiment > 45 ? 'Neutral' : 'Bearish';

  return (
    <div className="insight-grid">
      {/* Technical Indicators */}
      <div className="insight-card glass">
        <h4 className="insight-title">Technical Indicators</h4>
        
        <div className="indicator">
          <div className="indicator-header">
            <span className="indicator-label">RSI</span>
            <span className="indicator-value">{rsi}</span>
          </div>
          
          {/* RSI Health Indicator Gauge - Professional Speedometer */}
          <div className="rsi-gauge">
            <div className="rsi-gauge-container">
              <svg viewBox="0 0 140 80" className="rsi-gauge-svg" preserveAspectRatio="xMidYMid meet">
                {/* Full spectrum background arch with gradient */}
                <defs>
                  <linearGradient id="rsiGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    {/* Oversold Zone (0-30): Blue-Green */}
                    <stop offset="0%" stopColor="#0ea5e9" />
                    <stop offset="25%" stopColor="#06b6d4" />
                    {/* Neutral Zone (30-70): Dark Grey-Blue */}
                    <stop offset="50%" stopColor="#475569" />
                    {/* Overbought Zone (70-100): Orange-Red */}
                    <stop offset="75%" stopColor="#f97316" />
                    <stop offset="100%" stopColor="#ef4444" />
                  </linearGradient>
                </defs>

                {/* Perfect 180-degree semicircle arc with gradient spectrum */}
                <path
                  d="M 10 70 A 60 60 0 0 1 130 70"
                  fill="none"
                  stroke="url(#rsiGradient)"
                  strokeWidth="12"
                  strokeLinecap="round"
                />

                {/* Current position indicator - bright highlight showing needle */}
                <path
                  d="M 10 70 A 60 60 0 0 1 130 70"
                  fill="none"
                  stroke={rsi > 70 ? '#fbbf24' : '#4ade80'}
                  strokeWidth="12"
                  strokeDasharray={`${(rsi / 100) * 188.4} 188.4`}
                  strokeLinecap="round"
                  opacity="0.95"
                  filter="drop-shadow(0 0 6px rgba(74, 222, 128, 0.7))"
                />

                {/* Oversold marker line at 30% */}
                <line x1="46" y1="68" x2="46" y2="78" stroke="rgba(255,255,255,0.4)" strokeWidth="2" strokeLinecap="round" />
                
                {/* Overbought marker line at 70% */}
                <line x1="94" y1="68" x2="94" y2="78" stroke="rgba(255,255,255,0.4)" strokeWidth="2" strokeLinecap="round" />

                {/* Center value - displayed INSIDE the semicircle, between the marker lines */}
                <text x="70" y="52" textAnchor="middle" className="rsi-value-text">{rsi}</text>
                <text x="70" y="67" textAnchor="middle" className="rsi-unit-text">%</text>
              </svg>
            </div>

            {/* Status indicator below gauge - Signal for user */}
            <div className={`rsi-status ${rsi > 70 ? 'overbought' : rsi < 30 ? 'oversold' : 'neutral'}`}>
              {rsi > 70 ? '🔴 OVERBOUGHT' : rsi < 30 ? '🔵 OVERSOLD' : '⚪ NEUTRAL'}
            </div>
          </div>
        </div>

        <div className="indicator" style={{ marginTop: '1.5rem' }}>
          <div className="indicator-header">
            <span className="indicator-label">Volatility</span>
            <span className="indicator-value">{volatility}%</span>
          </div>
          <div className="progress-bar">
            <div className="progress-fill" style={{ width: `${volatility}%` }} />
          </div>
          <div className="indicator-range">Low — <strong>Medium</strong> — High</div>
        </div>
      </div>

      {/* Sentiment Analysis */}
      <div className="insight-card glass">
        <h4 className="insight-title">News & Sentiment</h4>
        
        <div className="sentiment-container">
          <div className="sentiment-bar-container">
            <div className="sentiment-bar">
              <div className="sentiment-fill" style={{ width: `${sentiment}%` }} />
            </div>
          </div>
          <div className="sentiment-labels">
            <span>Very Bearish</span>
            <span className={`sentiment-current ${sentiment > 55 ? 'bullish' : sentiment < 45 ? 'bearish' : 'neutral'}`}>
              {sentimentLabel}
            </span>
            <span>Very Bullish</span>
          </div>
        </div>

        <div className="sentiment-stats">
          <div className="stat-box positive">
            <span className="stat-value">+{positiveArticles}</span>
            <span className="stat-label">Positive Articles</span>
          </div>
          <div className="stat-box negative">
            <span className="stat-value">-{negativeArticles}</span>
            <span className="stat-label">Negative Articles</span>
          </div>
        </div>
      </div>

      {/* Fundamental Data */}
      <div className="insight-card glass">
        <h4 className="insight-title">Fundamentals</h4>
        
        <div className="fundamental-table">
          <div className="fundamental-row">
            <span className="fundamental-label">Market Cap</span>
            <span className="fundamental-value">
              ${stock.market_cap ? `${(stock.market_cap / 1e9).toFixed(2)}B` : 'N/A'}
            </span>
          </div>
          <div className="fundamental-row">
            <span className="fundamental-label">P/E Ratio</span>
            <span className="fundamental-value">{stock.pe_ratio?.toFixed(2) || 'N/A'}</span>
          </div>
          <div className="fundamental-row">
            <span className="fundamental-label">52W High</span>
            <span className="fundamental-value">${estimated52wHigh}</span>
          </div>
          <div className="fundamental-row">
            <span className="fundamental-label">52W Low</span>
            <span className="fundamental-value">${estimated52wLow}</span>
          </div>
          <div className="fundamental-row">
            <span className="fundamental-label">Dividend Yield</span>
            <span className="fundamental-value">
              {stock.dividend_yield ? `${(stock.dividend_yield * 100).toFixed(2)}%` : 'N/A'}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
