/**
 * Dashboard V2 - New Single Page Layout
 * 2-Column: Stock Selector (30%) + Prediction Focus Area (70%)
 */

import React, { useState } from 'react';
import { StockSelector } from '../components/DashboardV2/StockSelector';
import { StockPredictionView } from '../components/DashboardV2/StockPredictionView';
import { Stock } from '../api/endpoint';
import '../styles/dashboardv2.css';

export const DashboardV2: React.FC = () => {
  const [selectedStock, setSelectedStock] = useState<Stock | null>(null);
  const [stocks, setStocks] = useState<Stock[]>([]);
  const [loading, setLoading] = useState(true);

  return (
    <div className="dashboard-v2">
      {/* Left Panel: Stock Selector */}
      <div className="dashboard-v2-left">
        <StockSelector 
          stocks={stocks} 
          setStocks={setStocks}
          selectedStock={selectedStock}
          onSelectStock={setSelectedStock}
          loading={loading}
          setLoading={setLoading}
        />
      </div>

      {/* Right Panel: Prediction Focus Area */}
      <div className="dashboard-v2-right">
        {selectedStock ? (
          <StockPredictionView stock={selectedStock} />
        ) : (
          <div className="focus-placeholder">
            <h2>Select a stock to view predictions</h2>
            <p>Choose from the Pentagon 10 on the left to get started</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default DashboardV2;
