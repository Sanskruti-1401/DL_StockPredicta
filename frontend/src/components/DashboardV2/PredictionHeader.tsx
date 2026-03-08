/**
 * Prediction Header Component
 * Shows AI prediction and confidence gauge
 */

import React, { useState, useEffect } from 'react';
import { Stock } from '../../api/endpoint';
import '../../styles/components/prediction-header.css';

interface PredictionHeaderProps {
  stock: Stock;
}

export const PredictionHeader: React.FC<PredictionHeaderProps> = ({ stock }) => {
  const [currentPrice, setCurrentPrice] = useState(0);
  const [predictedPrice, setPredictedPrice] = useState(0);
  const [confidence, setConfidence] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);

        // Fetch price history to get current price
        const priceResponse = await fetch(
          `http://localhost:8000/api/v1/stocks/${stock.id}/price-history?days=30`
        );
        if (priceResponse.ok) {
          const priceData = await priceResponse.json();
          if (priceData.length > 0) {
            // Get the last (most recent) price
            const lastPrice = priceData[priceData.length - 1];
            setCurrentPrice(lastPrice.close || 0);
          }
        }

        // Fetch AI prediction
        const predResponse = await fetch(
          `http://localhost:8000/api/v1/predictions/${stock.id}?hours_ahead=24`
        );
        if (predResponse.ok) {
          const predData = await predResponse.json();
          if (predData.predictions && predData.predictions.length > 0) {
            // Get the last (furthest) prediction
            const lastPred = predData.predictions[predData.predictions.length - 1];
            setPredictedPrice(lastPred.price);
            setConfidence(Math.round((lastPred.confidence || 0.8) * 100));
          }
        }
      } catch (error) {
        console.error('[PredictionHeader] Error fetching data:', error);
        // No fallback - only display real API data
        setCurrentPrice(0);
        setPredictedPrice(0);
        setConfidence(0);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [stock.id, stock.pe_ratio, stock.beta]);

  const priceChange = predictedPrice - currentPrice;
  const percentChange = currentPrice > 0 && predictedPrice > 0 ? (priceChange / currentPrice) * 100 : 0;

  // Check if we have valid price data
  const hasValidData = predictedPrice > 0 && currentPrice > 0;

  return (
    <div className="prediction-header glass">
      <div className="stock-title">
        <h2 className="stock-symbol">{stock.symbol}</h2>
        <p className="stock-name">{stock.name}</p>
      </div>

      <div className="prediction-left">
        <div className="prediction-label">AI Prediction (Next 24h)</div>
        <div className="prediction-price">
          {!hasValidData ? '...' : `$${predictedPrice.toFixed(2)}`}
        </div>
        <div className={`prediction-change ${priceChange >= 0 ? 'positive' : 'negative'}`}>
          {!hasValidData ? '...' : (
            <>
              {priceChange >= 0 ? '▲' : '▼'} ${Math.abs(priceChange).toFixed(2)} ({percentChange.toFixed(2)}%)
            </>
          )}
        </div>
      </div>

      {confidence > 0 && (
        <div className="confidence-gauge">
          <div className="gauge-container">
            <svg viewBox="0 0 100 60" className="gauge-svg">
              {/* Background arc */}
              <path
                d="M 10 50 A 40 40 0 0 1 90 50"
                fill="none"
                stroke="rgba(255, 255, 255, 0.1)"
                strokeWidth="8"
              />
              {/* Confidence arc */}
              <path
                d="M 10 50 A 40 40 0 0 1 90 50"
                fill="none"
                stroke="#4ade80"
                strokeWidth="8"
                strokeDasharray={`${(confidence / 100) * 126.4} 126.4`}
              />
            </svg>
            <div className="gauge-percentage">{loading ? '...' : `${confidence}%`}</div>
          </div>
          <div className="gauge-label">Model Confidence</div>
        </div>
      )}
    </div>
  );
};

