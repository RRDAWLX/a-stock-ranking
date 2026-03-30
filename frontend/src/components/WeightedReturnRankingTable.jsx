import React from 'react'
import { getStockUrl } from '../utils/stockUrl'

export default function WeightedReturnRankingTable({ data, loading, formula }) {
  if (loading) {
    return (
      <div className="loading">
        <div className="loading-spinner"></div>
        <span>加载中...</span>
      </div>
    )
  }

  if (!data || data.length === 0) {
    return <div className="no-data">暂无数据</div>
  }

  const formatReturnRate = (rate) => {
    if (rate === null || rate === undefined) return '-'
    const percentage = (rate * 100).toFixed(2)
    return `${percentage}%`
  }

  return (
    <table className="stock-table">
      <thead>
        <tr>
          <th>排名</th>
          <th>股票代码</th>
          <th>股票名称</th>
          <th>加权收益率</th>
          {formula && formula.map(item => (
            <th key={item.days}>近{item.days}日收益率</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((stock, index) => (
          <tr key={stock.code}>
            <td>{index + 1}</td>
            <td className="stock-code">{stock.code}</td>
            <td className="stock-name">
              <a
                href={getStockUrl(stock.code)}
                target="_blank"
                rel="noopener noreferrer"
              >
                {stock.name}
              </a>
            </td>
            <td
              className={stock.return_rate >= 0 ? 'return-positive' : 'return-negative'}
            >
              {formatReturnRate(stock.return_rate)}
            </td>
            {formula && formula.map(term => (
              <td
                key={term.days}
                className={stock.period_returns && stock.period_returns[term.days] >= 0 ? 'return-positive' : 'return-negative'}
              >
                {formatReturnRate(stock.period_returns?.[term.days])}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}