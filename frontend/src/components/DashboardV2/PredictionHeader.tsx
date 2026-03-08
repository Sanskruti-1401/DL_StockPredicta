/**
 * Prediction Header Component
 * Shows AI prediction and confidence gauge
 */

import React from 'react';
import { Stock } from '../../api/endpoint';
import '../../styles/components/prediction-header.css';

interface PredictionHeaderProps {
  stock: Stock;
}

export const PredictionHeader: React.FC<PredictionHeaderProps> = ({ stock }) => {
  // Generate stock-specific mock data based on PE ratio (seeded variation)
  const seed = stock.id || 1;
  const baseConfidence = 70 + (seed % 25);
  const priceMultiplier = 1 + ((seed % 10) / 100); // 1% to 10% change
  
  // Estimate current price based on PE ratio (rough estimate)
  const betaValue = stock.beta ?? 1;
  const estimatedCurrentPrice = stock.pe_ratio ? stock.pe_ratio * betaValue * 100 : 185.50;
  const predictedPrice = estimatedCurrentPrice * priceMultiplier;
  const confidence = baseConfidence;
  const currentPrice = estimatedCurrentPrice;
  const priceChange = predictedPrice - currentPrice;
  const percentChange = (priceChange / currentPrice) * 100;

  return (
    <div className="prediction-header glass">
      <div className="stock-title">
        <h2 className="stock-symbol">{stock.symbol}</h2>
        <p className="stock-name">{stock.name}</p>
      </div>

      <div className="prediction-left">
        <div className="prediction-label">AI Prediction (Next 24h)</div>
        <div className="prediction-price">
          ${predictedPrice.toFixed(2)}
        </div>
        <div className={`prediction-change ${priceChange >= 0 ? 'positive' : 'negative'}`}>
          {priceChange >= 0 ? '▲' : '▼'} ${Math.abs(priceChange).toFixed(2)} ({percentChange.toFixed(2)}%)
        </div>
      </div>

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
          <div className="gauge-percentage">{confidence}%</div>
        </div>
        <div className="gauge-label">Model Confidence</div>
      </div>
    </div>
  );
};
