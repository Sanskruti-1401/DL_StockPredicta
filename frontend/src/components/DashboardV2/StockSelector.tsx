/**
 * Stock Selector Panel (Left Column)
 * Shows "Pentagon 10" stock list with scrollable cards
 */

import React, { useEffect } from 'react';
import { Stock, stockEndpoints } from '../../api/endpoint';
import { StockCard } from './StockCard';
import '../../styles/components/stock-selector.css';

interface StockSelectorProps {
  stocks: Stock[];
  setStocks: (stocks: Stock[]) => void;
  selectedStock: Stock | null;
  onSelectStock: (stock: Stock) => void;
  loading: boolean;
  setLoading: (loading: boolean) => void;
}

export const StockSelector: React.FC<StockSelectorProps> = ({
  stocks,
  setStocks,
  selectedStock,
  onSelectStock,
  loading,
  setLoading,
}) => {
  useEffect(() => {
    const loadStocks = async () => {
      try {
        setLoading(true);
        const { data } = await stockEndpoints.listStocks(0, 10);
        if (data) {
          setStocks(data);
          if (data.length > 0 && !selectedStock) {
            onSelectStock(data[0]);
          }
        }
      } catch (err) {
        console.error('Failed to load stocks:', err);
      } finally {
        setLoading(false);
      }
    };

    loadStocks();
  }, []);

  return (
    <div className="stock-selector">
      {/* Header */}
      <div className="selector-header">
        <h1 className="selector-title">Pentagon 10</h1>
        <p className="selector-subtitle">Real-time AI Stock Predictor</p>
      </div>

      {/* Stock List */}
      <div className="stock-cards-container">
        {loading ? (
          <div className="loading-message">Loading stocks...</div>
        ) : (
          stocks.map((stock) => (
            <StockCard
              key={stock.id}
              stock={stock}
              isActive={selectedStock?.id === stock.id}
              onClick={() => onSelectStock(stock)}
            />
          ))
        )}
      </div>
    </div>
  );
};
