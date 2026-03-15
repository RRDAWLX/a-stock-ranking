import React from 'react'

export default function WeightedReturnRankingTable({ data, loading }) {
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
          <th>收益率</th>
        </tr>
      </thead>
      <tbody>
        {data.map((item, index) => (
          <tr key={item.code}>
            <td>{index + 1}</td>
            <td className="stock-code">{item.code}</td>
            <td className="stock-name">{item.name}</td>
            <td
              className={item.return_rate >= 0 ? 'return-positive' : 'return-negative'}
            >
              {formatReturnRate(item.return_rate)}
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}