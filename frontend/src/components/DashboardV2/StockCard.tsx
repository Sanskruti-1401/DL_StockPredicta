/**
 * Stock Card Component
 * Individual stock card for the selector panel
 */

import React, { useEffect, useState } from 'react';
import { Stock, stockEndpoints } from '../../api/endpoint';
import { getMiniSparkline } from '../../utils/sparkline';
import '../../styles/components/stock-card.css';

interface StockCardProps {
  stock: Stock;
  isActive: boolean;
  onClick: () => void;
}

export const StockCard: React.FC<StockCardProps> = ({
  stock,
  isActive,
  onClick,
}) => {
  const [currentPrice, setCurrentPrice] = useState<number>(150.25);
  const [priceChange, setPriceChange] = useState<number>(0);

  // Fetch actual current price for this stock
  useEffect(() => {
    const fetchPrice = async () => {
      try {
        // Fetch latest price records (last 7 days to calculate change)
        const { data, error } = await stockEndpoints.getPriceHistory(stock.id, 7);
        
        if (error) {
          console.error(`Error fetching price for ${stock.symbol}:`, error);
          return;
        }

        if (data && Array.isArray(data) && data.length > 0) {
          // Sort by date to ensure chronological order
          const sortedData = [...data].sort((a, b) => 
            new Date(a.date).getTime() - new Date(b.date).getTime()
          );
          
          // Get today's price (last item)
          const today = sortedData[sortedData.length - 1];
          const currentPriceVal = parseFloat(String(today.close));
          
          if (!isNaN(currentPriceVal) && currentPriceVal > 0) {
            setCurrentPrice(currentPriceVal);
            
            // Calculate price change percentage from first to last
            if (sortedData.length > 1) {
              const firstDay = sortedData[0];
              const firstPrice = parseFloat(String(firstDay.close));
              
              if (!isNaN(firstPrice) && firstPrice > 0) {
                const change = ((currentPriceVal - firstPrice) / firstPrice) * 100;
                setPriceChange(isNaN(change) ? 0 : change);
              }
            }
          }
        } else {
          console.warn(`No price data for ${stock.symbol}:`, data);
        }
      } catch (err) {
        console.error(`Exception fetching price for ${stock.symbol}:`, err);
      }
    };

    fetchPrice();
  }, [stock.id, stock.symbol]);

  // Get first letter for logo
  const logoLetter = stock.symbol.charAt(0);
  const isPositive = priceChange >= 0;

  const sparklineData = getMiniSparkline();

  return (
    <div
      className={`stock-card ${isActive ? 'active' : ''}`}
      onClick={onClick}
    >
      {/* Logo Circle */}
      <div className="stock-logo">{logoLetter}</div>

      {/* Stock Info */}
      <div className="stock-info">
        <div className="stock-ticker">{stock.symbol}</div>
        <div className="stock-name">{stock.name}</div>
      </div>

      {/* Sparkline */}
      <div className="stock-sparkline">
        <svg viewBox="0 0 100 30" className={`sparkline ${isPositive ? 'positive' : 'negative'}`}>
          <polyline
            fill="none"
            stroke="currentColor"
            strokeWidth="1.5"
            points={sparklineData}
          />
        </svg>
      </div>

      {/* Price Info */}
      <div className="stock-price-info">
        <div className="stock-price">
          ${currentPrice > 0 ? currentPrice.toFixed(2) : '--'}
        </div>
        <div className={`stock-change ${isPositive ? 'positive' : 'negative'}`}>
          {currentPrice > 0 ? (
            <>
              {isPositive ? '▲' : '▼'} {Math.abs(priceChange).toFixed(2)}%
            </>
          ) : (
            '-- --'
          )}
        </div>
      </div>
    </div>
  );
};
