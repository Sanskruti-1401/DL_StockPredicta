/**
 * Utility functions for dashboard components
 */

export function getMiniSparkline(): string {
  // Generate random sparkline data for demo
  // In production, this would use actual price data
  const points: [number, number][] = [];
  let y = 15;

  for (let i = 0; i < 20; i++) {
    const x = (i / 20) * 100;
    y = y + (Math.random() - 0.5) * 8;
    y = Math.max(5, Math.min(25, y)); // Keep within bounds
    points.push([x, y]);
  }

  return points.map(([x, y]) => `${x},${y}`).join(' ');
}
