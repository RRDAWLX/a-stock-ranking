import React, { useState, useEffect } from 'react'

const DEFAULT_FORMULA = [
  { days: 1, weight: 0.1 },
  { days: 5, weight: 0.4 },
  { days: 20, weight: 0.5 }
]

export default function WeightedReturnFormulaForm({ title = '收益计算公式', description, initialFormula, onCalculate, showRank = false }) {
  const [formula, setFormula] = useState(initialFormula || DEFAULT_FORMULA)

  // 当 initialFormula 变化时更新
  useEffect(() => {
    if (initialFormula) {
      setFormula(initialFormula)
    }
  }, [initialFormula])

  const handleDaysChange = (index, value) => {
    const newFormula = [...formula]
    newFormula[index] = { ...newFormula[index], days: parseInt(value) || 0 }
    setFormula(newFormula)
  }

  const handleWeightChange = (index, value) => {
    const newFormula = [...formula]
    newFormula[index] = { ...newFormula[index], weight: parseFloat(value) || 0 }
    setFormula(newFormula)
  }

  const handleAdd = () => {
    setFormula([...formula, { days: 10, weight: 0.1 }])
  }

  const handleRemove = (index) => {
    if (formula.length > 1) {
      const newFormula = formula.filter((_, i) => i !== index)
      setFormula(newFormula)
    }
  }

  const handleCalculate = () => {
    onCalculate(formula)
  }

  const totalWeight = formula.reduce((sum, item) => sum + item.weight, 0)
  const isValid = Math.abs(totalWeight - 1) < 0.01

  const rateLabel = showRank ? '日收益率排行 × ' : '日收益率 × '

  return (
    <div className="formula-form">
      <h3>{title}</h3>
      {description && <p className="formula-description">{description}</p>}
      {formula.map((item, index) => (
        <div key={index} className="formula-item">
          <label>近</label>
          <input
            type="number"
            value={item.days}
            onChange={(e) => handleDaysChange(index, e.target.value)}
            min="1"
          />
          <span className="unit">{rateLabel}</span>
          <input
            type="number"
            value={item.weight}
            onChange={(e) => handleWeightChange(index, e.target.value)}
            min="0"
            max="1"
            step="0.1"
          />
          <span className="unit">权重</span>
          <button className="btn-remove" onClick={() => handleRemove(index)}>
            删除
          </button>
        </div>
      ))}
      <div style={{ display: 'flex', alignItems: 'center', marginTop: '16px', paddingTop: '16px', borderTop: '1px solid #30363d', gap: '12px' }}>
        <button className="btn-add" onClick={handleAdd}>
          + 添加
        </button>
        <button
          className="btn-calculate"
          onClick={handleCalculate}
          disabled={!isValid}
        >
          计算
        </button>
        <span className={`total-weight ${isValid ? '' : 'invalid'}`}>
          总权重: {(totalWeight * 100).toFixed(0)}%
        </span>
      </div>
    </div>
  )
}