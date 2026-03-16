import React from 'react'

// 生成东方财富网股票详情页URL
const getStockUrl = (code) => {
  if (code.startsWith('6')) {
    return `https://quote.eastmoney.com/sh${code}.html`
  } else {
    return `https://quote.eastmoney.com/sz${code}.html`
  }
}

export default function WeightedRankTable({ data, loading, formula }) {
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

  // 从公式中获取周期顺序
  const periodOrder = formula ? formula.map(item => item.days) : []

  // 如果没有公式，则从数据中提取
  const periodKeys = periodOrder.length > 0
    ? periodOrder
    : (data.length > 0 && data[0].rank_details
        ? Object.keys(data[0].rank_details).map(key => key.replace('rank_', ''))
        : [])

  return (
    <table className="stock-table">
      <thead>
        <tr>
          <th>排行分排名</th>
          <th>股票代码</th>
          <th>股票名称</th>
          <th>加权排行分</th>
          {periodKeys.map(days => (
            <th key={days}>近{days}日排行</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {data.map((item, index) => (
          <tr key={item.code}>
            <td>{index + 1}</td>
            <td className="stock-code">{item.code}</td>
            <td className="stock-name">
              <a href={getStockUrl(item.code)} target="_blank" rel="noopener noreferrer">
                {item.name}
              </a>
            </td>
            <td className="ranking-score">{item.ranking_score?.toFixed(1)}</td>
            {periodKeys.map(days => (
              <td key={days}>{item.rank_details?.[`rank_${days}`] || '-'}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  )
}