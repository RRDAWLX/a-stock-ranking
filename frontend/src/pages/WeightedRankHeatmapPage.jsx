import React, { useEffect } from 'react'
import { useApp } from '../context/AppContext'
import WeightedReturnFormulaForm from '../components/WeightedReturnFormulaForm'
import WeightedRankHeatmap from '../components/WeightedRankHeatmap'

const DEFAULT_FORMULA = [
  { days: 1, weight: 0.1 },
  { days: 5, weight: 0.4 },
  { days: 20, weight: 0.5 }
]

export default function WeightedRankHeatmapPage() {
  const {
    weightedRankHeatmapData,
    weightedRankHeatmapDates,
    weightedRankHeatmapLoading,
    weightedRankHeatmapFormula,
    weightedRankHeatmapTotalCount,
    fetchWeightedRankHeatmap,
    status
  } = useApp()

  // 初始加载数据
  useEffect(() => {
    if (status?.initialized && !weightedRankHeatmapFormula) {
      fetchWeightedRankHeatmap(DEFAULT_FORMULA, 10)
    }
  }, [status, weightedRankHeatmapFormula, fetchWeightedRankHeatmap])

  const handleCalculate = (formula) => {
    fetchWeightedRankHeatmap(formula, 10)
  }

  return (
    <div className="page">
      <div className="content">
        <WeightedReturnFormulaForm
          title="加权排行分热力图计算公式"
          description="计算公式: 近N日收益率排行 × 权重，排行分越小表示收益越好"
          initialFormula={weightedRankHeatmapFormula || DEFAULT_FORMULA}
          onCalculate={handleCalculate}
          showRank={true}
        />
        {status?.last_update && (
          <div className="info-banner">
            数据日期: {status.last_update} | 参与计算: {weightedRankHeatmapTotalCount}只股票
          </div>
        )}
        <WeightedRankHeatmap
          data={weightedRankHeatmapData}
          dates={weightedRankHeatmapDates}
          loading={weightedRankHeatmapLoading}
          formula={weightedRankHeatmapFormula}
        />
      </div>
    </div>
  )
}