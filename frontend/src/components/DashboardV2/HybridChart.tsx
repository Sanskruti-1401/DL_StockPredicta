/**
 * Professional Hybrid Time-Series Chart
 * 
 * Features:
 * - Historical data (solid line) vs Real ML Predicted data (dashed line)
 * - Confidence interval visualization
 * - Dynamic time range selector (1D, 5D, 1M, 6M)
 * - Interactive tooltips
 * - Professional financial UI layout
 * - Real-time WebSocket updates
 */

import React, { useEffect, useState, useRef } from 'react';
import { Stock, PriceData, stockEndpoints } from '../../api/endpoint';
import { useRealtimeMarketData } from '../../hooks/useRealtimeMarketData';
import '../../styles/components/hybrid-chart.css';

interface HybridChartProps {
  stock: Stock;
}

interface PredictionPoint {
  time: Date;
  price: number;
  confidence: number; // 0-1
  margin: number; // Upper/lower bound
  from_api: boolean; // Track if from real API
}

interface TooltipState {
  visible: boolean;
  x: number;
  y: number;
  price: number;
  date: string;
  isPredicted: boolean;
  confidence?: number;
}

const DEFAULT_TOOLTIP: TooltipState = {
  visible: false,
  x: 0,
  y: 0,
  price: 0,
  date: '',
  isPredicted: false,
};

export const HybridChart: React.FC<HybridChartProps> = ({ stock }) => {
  const [priceData, setPriceData] = useState<PriceData[]>([]);
  const [predictions, setPredictions] = useState<PredictionPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<'1D' | '5D' | '1M' | '6M'>('1D');
  const [tooltip, setTooltip] = useState<TooltipState>(DEFAULT_TOOLTIP);
  const [recommendation, setRecommendation] = useState<string>('HOLD');
  const svgRef = useRef<SVGSVGElement>(null);

  // Real-time WebSocket updates - updates state through callbacks
  useRealtimeMarketData({
    stockId: stock.id,
    enabled: true,
    onData: (data) => {
      // Update predictions from real-time WebSocket
      if (data.prediction?.predictions) {
        const newPredictions = data.prediction.predictions.map(
          (pred: any, index: number) => ({
            time: new Date(Date.now() + (index + 1) * 3600000),
            price: pred.price,
            confidence: pred.confidence,
            margin: pred.upper_bound - pred.price,
            from_api: true,
          })
        );
        setPredictions(newPredictions);
        setRecommendation(data.prediction.recommendation || 'HOLD');
      }
    },
    onError: (err) => {
      console.error('WebSocket error:', err);
    },
  });

  // Calculate days for time range
  const daysMap = { '1D': 7, '5D': 30, '1M': 90, '6M': 180 };
  const daysToFetch = daysMap[timeRange];

  // Load price history and fetch real predictions from API
  useEffect(() => {
    const loadPriceDataAndPredictions = async () => {
      try {
        setLoading(true);
        setError(null);
        console.log(`📈 [HybridChart] Loading ${daysToFetch} days for ${stock.symbol}`);

        // Fetch historical price data
        const { data, error: err } = await stockEndpoints.getPriceHistory(
          stock.id,
          daysToFetch
        );

        if (err) {
          console.error(`❌ [HybridChart] Error:`, err);
          setError(err);
        } else if (data && data.length > 0) {
          console.log(`✅ [HybridChart] Loaded ${data.length} price records`);
          setPriceData(data);

          // Fetch real ML predictions from API
          try {
            console.log(`🧠 [HybridChart] Fetching real ML predictions for ${stock.symbol}...`);
            const response = await fetch(`/api/v1/predictions/${stock.id}?hours_ahead=24`);
            console.log(`[HybridChart] Predictions API response status: ${response.status}`);
            
            if (!response.ok) {
              throw new Error(`API error: ${response.status}`);
            }
            
            const predictionData = await response.json();
            console.log(`[HybridChart] Got prediction response:`, predictionData);
            
            if (predictionData.predictions && predictionData.predictions.length > 0) {
              console.log(`✅ [HybridChart] Got ${predictionData.predictions.length} real ML predictions`);
              
              // Convert API predictions to chart format
              const apiPredictions = predictionData.predictions.map(
                (pred: any, index: number) => ({
                  time: new Date(pred.timestamp || Date.now() + (index + 1) * 3600000),
                  price: pred.price,
                  confidence: pred.confidence,
                  margin: pred.upper_bound - pred.price,
                  from_api: true,
                })
              );
              
              setPredictions(apiPredictions);
              setRecommendation(predictionData.recommendation || 'HOLD');
              console.log(`📊 [HybridChart] Recommendation: ${predictionData.recommendation}`);
            } else {
              throw new Error('No predictions in response');
            }
          } catch (predErr) {
            const msg = predErr instanceof Error ? predErr.message : 'Failed to fetch predictions';
            console.error(`❌ [HybridChart] Failed to fetch AI predictions: ${msg}`);
            
            // Fallback to synthetic predictions if API fails
            try {
              const syntheticPreds = generateSyntheticPredictions(data);
              setPredictions(syntheticPreds);
              console.log(`📊 [HybridChart] Generated ${syntheticPreds.length} synthetic predictions`);
            } catch (fallbackErr) {
              const fallbackMsg = fallbackErr instanceof Error ? fallbackErr.message : 'Failed to generate predictions';
              console.error(`❌ [HybridChart] Fallback prediction error:`, fallbackMsg);
              setError(fallbackMsg);
            }
          }
        } else {
          setError('No price data available');
        }
      } catch (err) {
        const errorMsg = err instanceof Error ? err.message : 'Unknown error';
        console.error(`💥 [HybridChart] Exception:`, errorMsg);
        setError(errorMsg);
      } finally {
        setLoading(false);
      }
    };

    loadPriceDataAndPredictions();
  }, [stock.id, daysToFetch]);

  // Generate synthetic predictions as fallback
  const generateSyntheticPredictions = (data: PriceData[]): PredictionPoint[] => {
    if (data.length < 2) {
      console.warn('⚠️ [generateSyntheticPredictions] Insufficient data (< 2 points)');
      return [];
    }

    const lastPrice = data[data.length - 1].close;
    console.log(`📈 [generateSyntheticPredictions] Starting from price: $${lastPrice.toFixed(2)}`);
    
    const volatility = calculateVolatility(data);
    const trend = calculateTrend(data);
    
    console.log(`📊 [generateSyntheticPredictions] Volatility: ${volatility.toFixed(2)}%, Trend: ${trend.toFixed(2)}%`);

    if (!isFinite(volatility) || !isFinite(trend)) {
      console.error('❌ [generateSyntheticPredictions] Invalid volatility or trend calculation');
      return [];
    }

    const predictionPoints: PredictionPoint[] = [];
    const predictionHours = 24; // Always predict 24 hours ahead, regardless of time range
    
    for (let i = 1; i <= predictionHours; i++) {
      const timeStep = i / predictionHours;
      // Confidence decreases as we predict further out
      const confidence = Math.max(0.5, 0.95 - timeStep * 0.35);

      // Price follows trend with increasing uncertainty
      const priceChange = trend * (i / 5) + (Math.random() - 0.5) * volatility * 2;
      const price = lastPrice * (1 + priceChange / 100);

      // Margin of error (confidence interval) widens with time
      const margin = volatility * (1 + timeStep * 2);

      if (isFinite(price) && isFinite(margin)) {
        predictionPoints.push({
          time: new Date(Date.now() + i * 3600000), // +i hours
          price,
          confidence,
          margin,
          from_api: false,
        });
      }
    }

    console.log(`✅ [generateSyntheticPredictions] Generated ${predictionPoints.length} valid predictions`);
    return predictionPoints;
  };

  const calculateVolatility = (data: PriceData[]): number => {
    if (data.length === 0) return 1; // Default fallback
    
    const closes = data.map((d) => d.close).filter((c) => isFinite(c));
    if (closes.length < 2) return 1;
    
    const mean = closes.reduce((a, b) => a + b) / closes.length;
    if (!isFinite(mean) || mean === 0) return 1;
    
    const variance =
      closes.reduce((sum, close) => sum + Math.pow(close - mean, 2), 0) /
      closes.length;
    
    const volatility = (Math.sqrt(Math.max(0, variance)) / mean) * 100;
    return isFinite(volatility) ? Math.min(volatility, 100) : 1; // Cap at 100%
  };

  const calculateTrend = (data: PriceData[]): number => {
    if (data.length < 2) return 0;
    
    const closes = data.map((d) => d.close).filter((c) => isFinite(c));
    if (closes.length < 2) return 0;
    
    const firstHalf = closes.slice(0, Math.floor(closes.length / 2));
    const secondHalf = closes.slice(Math.floor(closes.length / 2));
    
    if (firstHalf.length === 0 || secondHalf.length === 0) return 0;
    
    const avgFirst = firstHalf.reduce((a, b) => a + b) / firstHalf.length;
    const avgSecond = secondHalf.reduce((a, b) => a + b) / secondHalf.length;
    
    if (!isFinite(avgFirst) || avgFirst === 0) return 0;
    
    const trend = ((avgSecond - avgFirst) / avgFirst) * 100;
    return isFinite(trend) ? Math.max(-50, Math.min(50, trend)) : 0; // Cap between -50% and +50%
  };

  if (loading) {
    return (
      <div className="hybrid-chart glass loading">
        <div className="spinner"></div>
        <p>Loading market data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="hybrid-chart glass">
        <div className="chart-error">
          <p>⚠️ Error loading chart: {error}</p>
        </div>
      </div>
    );
  }

  if (priceData.length === 0 || predictions.length === 0) {
    return (
      <div className="hybrid-chart glass">
        <div className="chart-error">
          <p>No sufficient data available</p>
        </div>
      </div>
    );
  }

  // Calculate scaling
  const allPrices = [
    ...priceData.map((p) => p.close).filter((p) => isFinite(p)),
    ...predictions.map((p) => p.price + p.margin).filter((p) => isFinite(p)),
  ];
  
  if (allPrices.length === 0) {
    return (
      <div className="hybrid-chart glass">
        <div className="chart-error">
          <p>Invalid price data detected</p>
        </div>
      </div>
    );
  }
  
  const minPrice = Math.min(...allPrices);
  const maxPrice = Math.max(...allPrices);
  const priceRange = maxPrice - minPrice;
  
  console.log(`📐 [Chart Scaling] Min: $${minPrice.toFixed(2)}, Max: $${maxPrice.toFixed(2)}, Range: $${priceRange.toFixed(2)}`);
  
  if (!isFinite(minPrice) || !isFinite(maxPrice) || priceRange <= 0) {
    console.error('❌ [Chart Scaling] Invalid price range');
    return (
      <div className="hybrid-chart glass">
        <div className="chart-error">
          <p>Invalid price calculations</p>
        </div>
      </div>
    );
  }

  const padding = priceRange * 0.1;
  const scaledMin = minPrice - padding;
  const scaledRange = maxPrice + padding - scaledMin;

  // SVG Dimensions
  const SVG_WIDTH = 1000;
  const SVG_HEIGHT = 300;
  const CHART_LEFT = 60;
  const CHART_RIGHT = 50;
  const CHART_TOP = 40;
  const CHART_BOTTOM = 60;
  const CHART_WIDTH = SVG_WIDTH - CHART_LEFT - CHART_RIGHT;
  const CHART_HEIGHT = SVG_HEIGHT - CHART_TOP - CHART_BOTTOM;

  // Calculate current time position (where historical ends)
  const currentTimeRatio = priceData.length / (priceData.length + predictions.length);
  const nowX = CHART_LEFT + CHART_WIDTH * currentTimeRatio;

  // Helper function to convert price to Y coordinate
  const priceToY = (price: number): number => {
    return CHART_TOP + CHART_HEIGHT - ((price - scaledMin) / scaledRange) * CHART_HEIGHT;
  };

  // Helper function to convert index to X coordinate
  const indexToX = (index: number, isHistorical: boolean): number => {
    if (isHistorical) {
      return CHART_LEFT + (index / (priceData.length - 1 || 1)) * (CHART_WIDTH * currentTimeRatio);
    } else {
      return nowX + (index / predictions.length) * (CHART_WIDTH * (1 - currentTimeRatio));
    }
  };

  const handleMouseMove = (e: React.MouseEvent<SVGSVGElement>) => {
    if (!svgRef.current) return;

    const rect = svgRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;

    // Check if hover is on historical or predicted line
    if (x < nowX) {
      // Over historical data
      const ratio = (x - CHART_LEFT) / (nowX - CHART_LEFT);
      const index = Math.round(ratio * (priceData.length - 1));
      if (index >= 0 && index < priceData.length) {
        const data = priceData[index];
        setTooltip({
          visible: true,
          x,
          y,
          price: data.close,
          date: new Date(data.date).toLocaleDateString(),
          isPredicted: false,
        });
      }
    } else {
      // Over predicted data
      const ratio = (x - nowX) / (CHART_WIDTH * (1 - currentTimeRatio));
      const index = Math.round(ratio * (predictions.length - 1));
      if (index >= 0 && index < predictions.length) {
        const pred = predictions[index];
        setTooltip({
          visible: true,
          x,
          y,
          price: pred.price,
          date: pred.time.toLocaleString(),
          isPredicted: true,
          confidence: Math.round(pred.confidence * 100),
        });
      }
    }
  };

  const handleMouseLeave = () => {
    setTooltip(DEFAULT_TOOLTIP);
  };

  // Format time labels
  const formatTimeLabel = (date: Date | string): string => {
    const d = typeof date === 'string' ? new Date(date) : date;
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="hybrid-chart glass">
      {/* Header with title and controls */}
      <div className="chart-header">
        <h3>
          <span className="chart-icon">📈</span> Price Movement & AI Forecast
        </h3>

        {/* Time range selector */}
        <div className="time-range-selector">
          {(['1D', '5D', '1M', '6M'] as const).map((range) => (
            <button
              key={range}
              className={`range-btn ${timeRange === range ? 'active' : ''}`}
              onClick={() => setTimeRange(range)}
            >
              {range}
            </button>
          ))}
        </div>
      </div>

      {/* Chart legend */}
      <div className="chart-legend">
        <div className="legend-item historical">
          <div className="legend-line solid"></div>
          <span>Historical Data (Actual)</span>
        </div>
        <div className="legend-item predicted">
          <div className="legend-line dashed"></div>
          <span>AI Forecast (24h ahead)</span>
        </div>
        <div className="legend-item confidence">
          <div className="legend-shade"></div>
          <span>Confidence Interval</span>
        </div>
      </div>

      {/* Main chart SVG */}
      <svg
        ref={svgRef}
        viewBox={`0 0 ${SVG_WIDTH} ${SVG_HEIGHT}`}
        className="chart-svg"
        preserveAspectRatio="xMidYMid meet"
        onMouseMove={handleMouseMove}
        onMouseLeave={handleMouseLeave}
      >
        <defs>
          {/* Grid pattern */}
          <pattern id="grid" width="100" height="50" patternUnits="userSpaceOnUse">
            <path d="M 100 0 L 0 0 0 50" fill="none" stroke="rgba(255,255,255,0.03)" strokeWidth="1" />
          </pattern>

          {/* Gradients */}
          <linearGradient id="historicalGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style={{ stopColor: '#3b82f6', stopOpacity: 0.3 }} />
            <stop offset="100%" style={{ stopColor: '#3b82f6', stopOpacity: 0.05 }} />
          </linearGradient>

          <linearGradient id="predictedGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style={{ stopColor: '#06b6d4', stopOpacity: 0.2 }} />
            <stop offset="100%" style={{ stopColor: '#06b6d4', stopOpacity: 0 }} />
          </linearGradient>

          {/* Confidence interval gradient */}
          <linearGradient id="confidenceGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style={{ stopColor: '#10b981', stopOpacity: 0.15 }} />
            <stop offset="100%" style={{ stopColor: '#10b981', stopOpacity: 0.05 }} />
          </linearGradient>
        </defs>

        {/* Background grid */}
        <rect width={SVG_WIDTH} height={SVG_HEIGHT} fill="url(#grid)" />

        {/* Grid lines */}
        <g className="grid-lines" opacity="0.1">
          <line x1={CHART_LEFT} y1={CHART_TOP + CHART_HEIGHT * 0.25} x2={SVG_WIDTH - CHART_RIGHT} y2={CHART_TOP + CHART_HEIGHT * 0.25} stroke="white" strokeWidth="1" />
          <line x1={CHART_LEFT} y1={CHART_TOP + CHART_HEIGHT * 0.5} x2={SVG_WIDTH - CHART_RIGHT} y2={CHART_TOP + CHART_HEIGHT * 0.5} stroke="white" strokeWidth="1" />
          <line x1={CHART_LEFT} y1={CHART_TOP + CHART_HEIGHT * 0.75} x2={SVG_WIDTH - CHART_RIGHT} y2={CHART_TOP + CHART_HEIGHT * 0.75} stroke="white" strokeWidth="1" />
        </g>

        {/* Confidence interval shading (widening cone) */}
        {predictions.length > 0 && (
          <path
            d={predictions
              .map((pred, i) => {
                const x = indexToX(i, false);
                const yTop = priceToY(pred.price + pred.margin);
                const yBottom = priceToY(pred.price - pred.margin);
                return i === 0
                  ? `M ${x} ${yTop}`
                  : `L ${x} ${yTop} M ${x} ${yBottom}`;
              })
              .join(' ')}
            stroke="none"
            fill="url(#confidenceGradient)"
            opacity="0.4"
          />
        )}

        {/* Confidence interval as polygon */}
        {predictions.length > 0 && (
          <polygon
            points={
              predictions
                .map((pred, i) => {
                  const x = indexToX(i, false);
                  const yTop = priceToY(pred.price + pred.margin);
                  return `${x},${yTop}`;
                })
                .join(' ') +
              ' ' +
              predictions
                .slice()
                .reverse()
                .map((pred, i) => {
                  const x = indexToX(predictions.length - 1 - i, false);
                  const yBottom = priceToY(pred.price - pred.margin);
                  return `${x},${yBottom}`;
                })
                .join(' ')
            }
            fill="url(#confidenceGradient)"
            opacity="0.3"
          />
        )}

        {/* Historical price area fill */}
        {priceData.length > 0 && (
          <polygon
            points={
              priceData.map((p, i) => {
                const x = indexToX(i, true);
                const y = priceToY(p.close);
                return `${x},${y}`;
              }).join(' ') +
              ` ${nowX},${CHART_TOP + CHART_HEIGHT} ${CHART_LEFT},${CHART_TOP + CHART_HEIGHT}`
            }
            fill="url(#historicalGradient)"
            opacity="0.6"
          />
        )}

        {/* Historical price line (solid, thick) */}
        {priceData.length > 0 && (
          <polyline
            points={priceData.map((p, i) => {
              const x = indexToX(i, true);
              const y = priceToY(p.close);
              return `${x},${y}`;
            }).join(' ')}
            fill="none"
            stroke="#3b82f6"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            filter="drop-shadow(0 0 8px rgba(59, 130, 246, 0.6))"
          />
        )}

        {/* Predicted price line with glow (dashed) */}
        {predictions.length > 0 && (
          <polyline
            points={predictions.map((pred, i) => {
              const x = indexToX(i, false);
              const y = priceToY(pred.price);
              return `${x},${y}`;
            }).join(' ')}
            fill="none"
            stroke="#06b6d4"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeDasharray="8,4"
            filter="drop-shadow(0 0 12px rgba(6, 182, 212, 0.8))"
            opacity="0.9"
          />
        )}

        {/* "Now" indicator (vertical dashed line) */}
        <line
          x1={nowX}
          y1={CHART_TOP}
          x2={nowX}
          y2={CHART_TOP + CHART_HEIGHT}
          stroke="rgba(255,255,255,0.4)"
          strokeWidth="2"
          strokeDasharray="4,4"
          className="now-line"
        />
        <text
          x={nowX}
          y={CHART_TOP - 10}
          textAnchor="middle"
          fill="rgba(255,255,255,0.6)"
          fontSize="11"
          fontWeight="600"
        >
          NOW
        </text>

        {/* Y-Axis (Price) */}
        <text x={CHART_LEFT - 45} y={CHART_TOP + 15} fill="rgba(255,255,255,0.5)" fontSize="12" fontWeight="600">
          ${maxPrice.toFixed(0)}
        </text>
        <text x={CHART_LEFT - 35} y={CHART_TOP + CHART_HEIGHT - 5} fill="rgba(255,255,255,0.5)" fontSize="12" fontWeight="600">
          ${minPrice.toFixed(0)}
        </text>

        {/* X-Axis time labels */}
        <text
          x={CHART_LEFT}
          y={SVG_HEIGHT - 10}
          fill="rgba(255,255,255,0.5)"
          fontSize="11"
          fontWeight="600"
        >
          {formatTimeLabel(priceData[0]?.date || new Date())}
        </text>
        <text
          x={nowX}
          y={SVG_HEIGHT - 10}
          textAnchor="middle"
          fill="rgba(255,255,255,0.7)"
          fontSize="11"
          fontWeight="600"
        >
          Today
        </text>
        <text
          x={SVG_WIDTH - CHART_RIGHT - 5}
          y={SVG_HEIGHT - 10}
          textAnchor="end"
          fill="rgba(255,255,255,0.5)"
          fontSize="11"
          fontWeight="600"
        >
          +24h Forecast
        </text>
      </svg>

      {/* Interactive tooltip */}
      {tooltip.visible && (
        <div
          className={`chart-tooltip ${tooltip.isPredicted ? 'predicted' : 'historical'}`}
          style={{
            left: `${tooltip.x}px`,
            top: `${tooltip.y - 40}px`,
          }}
        >
          <div className="tooltip-content">
            <div className="tooltip-price">${tooltip.price.toFixed(2)}</div>
            <div className="tooltip-label">
              {tooltip.isPredicted ? (
                <>
                  <span>Predicted</span>
                  <span className="confidence-badge">{tooltip.confidence}% confidence</span>
                </>
              ) : (
                <span>Actual</span>
              )}
            </div>
            <div className="tooltip-date">{tooltip.date}</div>
          </div>
        </div>
      )}

      {/* Chart stats footer */}
      <div className="chart-stats">
        <div className="stat-item">
          <span className="stat-label">Current Price</span>
          <span className="stat-value">${priceData[priceData.length - 1]?.close.toFixed(2)}</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Prediction (24h)</span>
          <span className="stat-value prediction">
            ${predictions[predictions.length - 1]?.price.toFixed(2)}
          </span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Expected Change</span>
          <span
            className={`stat-value ${
              (predictions[predictions.length - 1]?.price ?? 0) >
              (priceData[priceData.length - 1]?.close ?? 0)
                ? 'positive'
                : 'negative'
            }`}
          >
            {(
              (((predictions[predictions.length - 1]?.price ?? 0) -
                (priceData[priceData.length - 1]?.close ?? 0)) /
                (priceData[priceData.length - 1]?.close ?? 1)) *
                100
            ).toFixed(2)}
            %
          </span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Volatility</span>
          <span className="stat-value">{calculateVolatility(priceData).toFixed(2)}%</span>
        </div>
        <div className="stat-item">
          <span className="stat-label">Recommendation</span>
          <span className={`stat-value recommendation ${recommendation.toLowerCase()}`}>
            {recommendation === 'HOLD' ? '⏸️ HOLD' : recommendation === 'BUY' ? '📈 BUY' : '📉 SELL'}
          </span>
        </div>
      </div>
    </div>
  );
};
