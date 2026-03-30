import React, { useState } from 'react'
import { getStockUrl } from '../utils/stockUrl'

// 预设颜色列表，确保相邻颜色有明显差异
const colorPalette = [
  '#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7',
  '#DDA0DD', '#98D8C8', '#F7DC6F', '#BB8FCE', '#85C1E9',
  '#F8B500', '#00CED1', '#FF6347', '#32CD32', '#9370DB',
  '#FF69B4', '#00FA9A', '#FFD700', '#6B8E23', '#8A2BE2',
  '#FF4500', '#2E8B57', '#1E90FF', '#D2691E', '#8B008B',
  '#00FF7F', '#FF1493', '#4682B4', '#DAA520', '#A0522D'
]

// 根据股票代码生成固定索引
function getStockColorIndex(stockCode) {
  let hash = 0
  for (let i = 0; i < stockCode.length; i++) {
    hash = stockCode.charCodeAt(i) + ((hash << 5) - hash)
  }
  return Math.abs(hash) % colorPalette.length
}

// 获取股票颜色
function getStockColor(stockCode) {
  const index = getStockColorIndex(stockCode)
  return colorPalette[index]
}

// 根据收益率调整颜色亮度
function adjustColorBrightness(hexColor, returnRate) {
  const hex = hexColor.replace('#', '')
  const r = parseInt(hex.substring(0, 2), 16)
  const g = parseInt(hex.substring(2, 4), 16)
  const b = parseInt(hex.substring(4, 6), 16)

  const intensity = Math.min(Math.abs(returnRate) * 2 + 0.3, 1)

  const newR = Math.floor(r * intensity + 240 * (1 - intensity))
  const newG = Math.floor(g * intensity + 240 * (1 - intensity))
  const newB = Math.floor(b * intensity + 240 * (1 - intensity))

  return `rgb(${newR}, ${newG}, ${newB})`
}

function formatDate(dateStr) {
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}-${date.getDate()}`
}

function formatReturnRate(rate) {
  if (rate === null || rate === undefined) return '-'
  const percentage = (rate * 100).toFixed(1)
  return `${percentage}%`
}

export default function WeightedReturnHeatmap({ data, dates, loading }) {
  const [hoveredStock, setHoveredStock] = useState(null)

  // loading 状态优先显示加载动画
  if (loading) {
    return (
      <div style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        padding: '48px',
        minHeight: '400px',
        backgroundColor: '#161b22',
        position: 'relative',
        zIndex: 100
      }}>
        <div style={{
          width: '40px',
          height: '40px',
          border: '4px solid rgba(88, 166, 255, 0.3)',
          borderTop: '4px solid #58a6ff',
          borderRadius: '50%',
          animation: 'spin 0.8s linear infinite'
        }}></div>
        <span style={{ color: '#6e7681', marginTop: '16px', fontSize: '16px' }}>加载中...</span>
      </div>
    )
  }

  // dates 为空数组时（loading 结束但数据还未返回的短暂时刻）
  if (!dates || dates.length === 0) {
    return <div className="no-data">暂无数据</div>
  }

  if (!data || Object.keys(data).length === 0) {
    return <div className="no-data">暂无数据</div>
  }

  return (
    <div className="heatmap-wrapper">
      <div className="heatmap-grid">
        {dates.map((date) => (
          <div key={date} className="heatmap-column">
            <div className="heatmap-date-header">
              {formatDate(date)}
            </div>
            <div className="heatmap-stocks">
              {data[date]?.map((stock, index) => {
                const baseColor = getStockColor(stock.code)
                const bgColor = adjustColorBrightness(baseColor, stock.return_rate)
                const isDimmed = hoveredStock && hoveredStock !== stock.code

                return (
                  <div
                    key={`${date}-${stock.code}`}
                    className={`heatmap-stock-item ${isDimmed ? 'item-dimmed' : ''}`}
                    style={{ backgroundColor: bgColor }}
                    onMouseEnter={() => setHoveredStock(stock.code)}
                    onMouseLeave={() => setHoveredStock(null)}
                    onClick={() => window.open(getStockUrl(stock.code), '_blank')}
                  >
                    <div className="stock-rank">#{index + 1}</div>
                    <div className="stock-info">
                      <div className="stock-name">{stock.name}</div>
                      <div className="stock-code">{stock.code}</div>
                    </div>
                    <div className="stock-return">
                      {formatReturnRate(stock.return_rate)}
                    </div>
                  </div>
                )
              }) || <div className="no-data">-</div>}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}