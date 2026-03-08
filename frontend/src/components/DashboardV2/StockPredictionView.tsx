/**
 * Stock Prediction View (Right Column)
 * Shows prediction header, hybrid chart, and insights
 */

import React from 'react';
import { Stock } from '../../api/endpoint';
import { PredictionHeader } from './PredictionHeader';
import { HybridChart } from './HybridChart';
import { InsightGrid } from './InsightGrid';
import '../../styles/components/stock-prediction-view.css';

interface StockPredictionViewProps {
  stock: Stock;
}

export const StockPredictionView: React.FC<StockPredictionViewProps> = ({
  stock,
}) => {
  return (
    <div className="stock-prediction-view">
      {/* Prediction Header */}
      <PredictionHeader stock={stock} />

      {/* Hybrid Chart */}
      <HybridChart stock={stock} />

      {/* Insight Grid */}
      <InsightGrid stock={stock} />
    </div>
  );
};

export default StockPredictionView;
