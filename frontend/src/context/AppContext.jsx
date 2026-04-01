import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { getInitStatus, updateData, getUpdateStatus, cancelUpdate } from '../api'

// SystemContext: 系统状态、更新功能、错误处理
const SystemContext = createContext(null)

export function SystemProvider({ children }) {
  const [status, setStatus] = useState(null)
  const [statusLoading, setStatusLoading] = useState(true)
  const [updating, setUpdating] = useState(false)
  const [updateProgress, setUpdateProgress] = useState(0)
  const [updateMessage, setUpdateMessage] = useState('')
  const [error, setError] = useState(null)

  useEffect(() => {
    loadStatus()
  }, [])

  const loadStatus = async () => {
    try {
      const data = await getInitStatus()
      setStatus(data)
      setStatusLoading(false)
    } catch (err) {
      console.error('加载状态失败:', err)
      setError(err.message)
      setStatusLoading(false)
    }
  }

  const handleUpdate = useCallback(async () => {
    setUpdating(true)
    setError(null)
    setUpdateProgress(0)
    setUpdateMessage('正在启动更新...')

    try {
      const result = await updateData()
      if (result.async) {
        pollUpdateStatus()
      } else {
        const newStatus = await getInitStatus()
        setStatus(newStatus)
        setUpdating(false)
        setUpdateProgress(100)
        setUpdateMessage('更新完成')
      }
    } catch (err) {
      console.error('更新失败:', err)
      setError(err.message)
      setUpdating(false)
    }
  }, [])

  const pollUpdateStatus = useCallback(async () => {
    try {
      const updateStatus = await getUpdateStatus()
      setUpdateProgress(updateStatus.progress)
      setUpdateMessage(updateStatus.message)

      if (updateStatus.running) {
        setTimeout(pollUpdateStatus, 1000)
      } else {
        if (updateStatus.error) {
          setError(updateStatus.error)
        } else {
          const newStatus = await getInitStatus()
          setStatus(newStatus)
        }
        setUpdating(false)
      }
    } catch (err) {
      console.error('获取更新状态失败:', err)
      setTimeout(pollUpdateStatus, 2000)
    }
  }, [])

  const handleCancelUpdate = useCallback(async () => {
    try {
      await cancelUpdate()
      setUpdating(false)
      setUpdateProgress(0)
      setUpdateMessage('')
    } catch (err) {
      console.error('取消更新失败:', err)
    }
  }, [])

  const value = {
    status,
    statusLoading,
    loadStatus,
    updating,
    updateProgress,
    updateMessage,
    handleUpdate,
    handleCancelUpdate,
    error,
    setError
  }

  return <SystemContext.Provider value={value}>{children}</SystemContext.Provider>
}

export function useSystem() {
  const context = useContext(SystemContext)
  if (!context) {
    throw new Error('useSystem must be used within SystemProvider')
  }
  return context
}

// WeightedReturnContext: 加权收益相关
const WeightedReturnContext = createContext(null)

export function WeightedReturnProvider({ children }) {
  const [rankingData, setRankingData] = useState([])
  const [rankingLoading, setRankingLoading] = useState(false)
  const [rankingFormula, setRankingFormula] = useState(null)
  const [rankingTotalCount, setRankingTotalCount] = useState(0)

  const [heatmapData, setHeatmapData] = useState({})
  const [heatmapDates, setHeatmapDates] = useState([])
  const [heatmapLoading, setHeatmapLoading] = useState(false)
  const [heatmapFormula, setHeatmapFormula] = useState(null)
  const [heatmapTotalCount, setHeatmapTotalCount] = useState(0)

  const fetchRanking = useCallback(async (formula) => {
    setRankingLoading(true)
    setRankingFormula(formula)
    try {
      const result = await import('../api').then(m => m.calculateWeightedReturn(formula))
      setRankingData(result.items || result.data || [])
      setRankingTotalCount(result.total_count || 0)
    } catch (err) {
      console.error('计算失败:', err)
    }
    setRankingLoading(false)
  }, [])

  const fetchHeatmap = useCallback(async (formula, days = 10) => {
    setHeatmapLoading(true)
    setHeatmapFormula(formula)
    try {
      const result = await import('../api').then(m => m.getWeightedReturnHeatmap(formula, days))
      setHeatmapData(result.items || result.data || {})
      setHeatmapDates(result.dates || [])
      setHeatmapTotalCount(result.total_count || 0)
    } catch (err) {
      console.error('计算热力图失败:', err)
    }
    setHeatmapLoading(false)
  }, [])

  const value = {
    rankingData,
    rankingLoading,
    rankingFormula,
    rankingTotalCount,
    fetchRanking,
    heatmapData,
    heatmapDates,
    heatmapLoading,
    heatmapFormula,
    heatmapTotalCount,
    fetchHeatmap
  }

  return <WeightedReturnContext.Provider value={value}>{children}</WeightedReturnContext.Provider>
}

export function useWeightedReturn() {
  const context = useContext(WeightedReturnContext)
  if (!context) {
    throw new Error('useWeightedReturn must be used within WeightedReturnProvider')
  }
  return context
}

// WeightedRankContext: 加权排行分相关
const WeightedRankContext = createContext(null)

export function WeightedRankProvider({ children }) {
  const [rankData, setRankData] = useState([])
  const [rankLoading, setRankLoading] = useState(false)
  const [rankFormula, setRankFormula] = useState(null)
  const [rankTotalCount, setRankTotalCount] = useState(0)

  const [heatmapData, setHeatmapData] = useState({})
  const [heatmapDates, setHeatmapDates] = useState([])
  const [heatmapLoading, setHeatmapLoading] = useState(false)
  const [heatmapFormula, setHeatmapFormula] = useState(null)
  const [heatmapTotalCount, setHeatmapTotalCount] = useState(0)

  const fetchRank = useCallback(async (formula) => {
    setRankLoading(true)
    setRankFormula(formula)
    try {
      const result = await import('../api').then(m => m.calculateWeightedRank(formula))
      setRankData(result.items || result.data || [])
      setRankTotalCount(result.total_count || 0)
    } catch (err) {
      console.error('计算加权排行分失败:', err)
    }
    setRankLoading(false)
  }, [])

  const fetchHeatmap = useCallback(async (formula, days = 10) => {
    setHeatmapLoading(true)
    setHeatmapFormula(formula)
    try {
      const result = await import('../api').then(m => m.getWeightedRankHeatmap(formula, days))
      setHeatmapData(result.items || result.data || {})
      setHeatmapDates(result.dates || [])
      setHeatmapTotalCount(result.total_count || 0)
    } catch (err) {
      console.error('计算加权排行分热力图失败:', err)
    }
    setHeatmapLoading(false)
  }, [])

  const value = {
    rankData,
    rankLoading,
    rankFormula,
    rankTotalCount,
    fetchRank,
    heatmapData,
    heatmapDates,
    heatmapLoading,
    heatmapFormula,
    heatmapTotalCount,
    fetchHeatmap
  }

  return <WeightedRankContext.Provider value={value}>{children}</WeightedRankContext.Provider>
}

export function useWeightedRank() {
  const context = useContext(WeightedRankContext)
  if (!context) {
    throw new Error('useWeightedRank must be used within WeightedRankProvider')
  }
  return context
}

// 组合Provider，便于使用
export function AppProvider({ children }) {
  return (
    <SystemProvider>
      <WeightedReturnProvider>
        <WeightedRankProvider>
          {children}
        </WeightedRankProvider>
      </WeightedReturnProvider>
    </SystemProvider>
  )
}

// 兼容旧的useApp hook（deprecated，建议使用具体的useXxx hook）
export function useApp() {
  const system = useSystem()
  const weightedReturn = useWeightedReturn()
  const weightedRank = useWeightedRank()

  return {
    ...system,
    rankingData: weightedReturn.rankingData,
    rankingLoading: weightedReturn.rankingLoading,
    rankingFormula: weightedReturn.rankingFormula,
    rankingTotalCount: weightedReturn.rankingTotalCount,
    fetchWeightedReturnRanking: weightedReturn.fetchRanking,
    heatmapData: weightedReturn.heatmapData,
    heatmapDates: weightedReturn.heatmapDates,
    heatmapLoading: weightedReturn.heatmapLoading,
    heatmapFormula: weightedReturn.heatmapFormula,
    heatmapTotalCount: weightedReturn.heatmapTotalCount,
    fetchWeightedReturnHeatmap: weightedReturn.fetchHeatmap,
    weightedRankData: weightedRank.rankData,
    weightedRankLoading: weightedRank.rankLoading,
    weightedRankFormula: weightedRank.rankFormula,
    weightedRankTotalCount: weightedRank.rankTotalCount,
    fetchWeightedRank: weightedRank.fetchRank,
    weightedRankHeatmapData: weightedRank.heatmapData,
    weightedRankHeatmapDates: weightedRank.heatmapDates,
    weightedRankHeatmapLoading: weightedRank.heatmapLoading,
    weightedRankHeatmapFormula: weightedRank.heatmapFormula,
    weightedRankHeatmapTotalCount: weightedRank.heatmapTotalCount,
    fetchWeightedRankHeatmap: weightedRank.fetchHeatmap
  }
}