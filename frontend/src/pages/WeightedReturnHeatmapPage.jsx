import React, { useEffect } from 'react'
import { useApp } from '../context/AppContext'
import WeightedReturnFormulaForm from '../components/WeightedReturnFormulaForm'
import WeightedReturnHeatmap from '../components/WeightedReturnHeatmap'

const DEFAULT_FORMULA = [
  { days: 1, weight: 0.1 },
  { days: 5, weight: 0.4 },
  { days: 20, weight: 0.5 }
]

export default function WeightedReturnHeatmapPage() {
  const {
    heatmapData,
    heatmapDates,
    heatmapLoading,
    heatmapFormula,
    fetchWeightedReturnHeatmap,
    status
  } = useApp()

  // 初始加载数据
  useEffect(() => {
    if (status?.initialized && !heatmapFormula) {
      fetchWeightedReturnHeatmap(DEFAULT_FORMULA, 10)
    }
  }, [status, heatmapFormula, fetchWeightedReturnHeatmap])

  const handleCalculate = (formula) => {
    fetchWeightedReturnHeatmap(formula, 10)
  }

  return (
    <div className="page">
      <div className="content">
        <WeightedReturnFormulaForm
          title="加权收益热力图计算公式"
          initialFormula={heatmapFormula || DEFAULT_FORMULA}
          onCalculate={handleCalculate}
        />
        <WeightedReturnHeatmap data={heatmapData} dates={heatmapDates} loading={heatmapLoading} />
      </div>
    </div>
  )
}