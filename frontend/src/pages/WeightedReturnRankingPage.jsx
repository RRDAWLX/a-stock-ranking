import React, { useEffect } from 'react'
import { useApp } from '../context/AppContext'
import WeightedReturnFormulaForm from '../components/WeightedReturnFormulaForm'
import WeightedReturnRankingTable from '../components/WeightedReturnRankingTable'

const DEFAULT_FORMULA = [
  { days: 1, weight: 0.1 },
  { days: 5, weight: 0.4 },
  { days: 20, weight: 0.5 }
]

export default function WeightedReturnRankingPage() {
  const {
    rankingData,
    rankingLoading,
    rankingFormula,
    fetchWeightedReturnRanking,
    status
  } = useApp()

  // 初始加载数据
  useEffect(() => {
    if (status?.initialized && !rankingFormula) {
      fetchWeightedReturnRanking(DEFAULT_FORMULA)
    }
  }, [status, rankingFormula, fetchWeightedReturnRanking])

  const handleCalculate = (formula) => {
    fetchWeightedReturnRanking(formula)
  }

  return (
    <div className="page">
      <div className="content">
        <WeightedReturnFormulaForm
          title="加权收益排行计算公式"
          initialFormula={rankingFormula || DEFAULT_FORMULA}
          onCalculate={handleCalculate}
        />
        {status?.last_update && (
          <div className="info-banner">
            数据日期: {status.last_update}
          </div>
        )}
        <WeightedReturnRankingTable data={rankingData} loading={rankingLoading} />
      </div>
    </div>
  )
}