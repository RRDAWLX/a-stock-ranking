import React, { useEffect } from 'react'
import { useApp } from '../context/AppContext'
import WeightedReturnFormulaForm from '../components/WeightedReturnFormulaForm'
import WeightedRankTable from '../components/WeightedRankTable'

const DEFAULT_FORMULA = [
  { days: 1, weight: 0.1 },
  { days: 5, weight: 0.4 },
  { days: 20, weight: 0.5 }
]

export default function WeightedRankPage() {
  const {
    weightedRankData,
    weightedRankLoading,
    weightedRankFormula,
    weightedRankTotalCount,
    fetchWeightedRank,
    status
  } = useApp()

  // 初始加载数据
  useEffect(() => {
    if (status?.initialized && !weightedRankFormula) {
      fetchWeightedRank(DEFAULT_FORMULA)
    }
  }, [status, weightedRankFormula, fetchWeightedRank])

  const handleCalculate = (formula) => {
    fetchWeightedRank(formula)
  }

  return (
    <div className="page">
      <div className="content">
        <WeightedReturnFormulaForm
          title="加权排行分计算公式"
          description="计算公式: 近N日收益率排行 × 权重，排行分越小表示收益越好"
          initialFormula={weightedRankFormula || DEFAULT_FORMULA}
          onCalculate={handleCalculate}
          showRank={true}
        />
        {status?.last_update && (
          <div className="info-banner">
            数据日期: {status.last_update} | 参与计算: {weightedRankTotalCount}只股票
          </div>
        )}
        <WeightedRankTable data={weightedRankData} loading={weightedRankLoading} formula={weightedRankFormula} />
      </div>
    </div>
  )
}