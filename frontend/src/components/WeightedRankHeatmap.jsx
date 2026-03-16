import React, { useState } from 'react'

// 预设颜色列表
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

// 根据排行分调整颜色亮度（排行分越小颜色越亮）
function adjustColorBrightness(hexColor, rankingScore, maxScore = 100) {
  const hex = hexColor.replace('#', '')
  const r = parseInt(hex.substring(0, 2), 16)
  const g = parseInt(hex.substring(2, 4), 16)
  const b = parseInt(hex.substring(4, 6), 16)

  // 排行分越小，intensity越高（颜色越亮）
  const intensity = Math.max(0.3, 1 - (rankingScore / maxScore) * 0.7)

  const newR = Math.floor(r * intensity + 240 * (1 - intensity))
  const newG = Math.floor(g * intensity + 240 * (1 - intensity))
  const newB = Math.floor(b * intensity + 240 * (1 - intensity))

  return `rgb(${newR}, ${newG}, ${newB})`
}

function formatDate(dateStr) {
  const date = new Date(dateStr)
  return `${date.getMonth() + 1}-${date.getDate()}`
}

// 生成东方财富网股票详情页URL
const getStockUrl = (code) => {
  if (code.startsWith('6')) {
    return `https://quote.eastmoney.com/sh${code}.html`
  } else {
    return `https://quote.eastmoney.com/sz${code}.html`
  }
}

export default function WeightedRankHeatmap({ data, dates, loading, formula }) {
  const [hoveredStock, setHoveredStock] = useState(null)

  // 从公式中获取周期顺序
  const periodOrder = formula ? formula.map(item => item.days) : []

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

  if (!dates || dates.length === 0) {
    return <div className="no-data">暂无数据</div>
  }

  if (!data || Object.keys(data).length === 0) {
    return <div className="no-data">暂无数据</div>
  }

  // 获取周期列标题
  const periodKeys = periodOrder.length > 0
    ? periodOrder
    : (data[dates[0]]?.[0]?.rank_details
        ? Object.keys(data[dates[0]][0].rank_details).map(key => key.replace('rank_', ''))
        : [])

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
                const bgColor = adjustColorBrightness(baseColor, stock.ranking_score)
                const isDimmed = hoveredStock && hoveredStock !== stock.code

                return (
                  <div
                    key={`${date}-${stock.code}`}
                    className={`heatmap-stock-item ${isDimmed ? 'item-dimmed' : ''}`}
                    style={{ backgroundColor: bgColor }}
                    onMouseEnter={() => setHoveredStock(stock.code)}
                    onMouseLeave={() => setHoveredStock(null)}
                  >
                    <div className="stock-rank">#{index + 1}</div>
                    <div className="stock-info">
                      <div className="stock-name">
                        <a href={getStockUrl(stock.code)} target="_blank" rel="noopener noreferrer">
                          {stock.name}
                        </a>
                      </div>
                      <div className="stock-code">{stock.code}</div>
                    </div>
                    <div className="stock-return">
                      {stock.ranking_score?.toFixed(1)}
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