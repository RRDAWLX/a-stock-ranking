import React, { createContext, useContext, useState, useEffect, useCallback } from 'react'
import { getInitStatus, calculateWeightedReturn, getWeightedReturnHeatmap, updateData, getUpdateStatus, cancelUpdate, calculateWeightedRank, getWeightedRankHeatmap } from '../api'

const AppContext = createContext(null)

export function AppProvider({ children }) {
  // 系统状态
  const [status, setStatus] = useState(null)
  const [statusLoading, setStatusLoading] = useState(true)

  // 更新相关
  const [updating, setUpdating] = useState(false)
  const [updateProgress, setUpdateProgress] = useState(0)
  const [updateMessage, setUpdateMessage] = useState('')

  // 排行榜数据
  const [rankingData, setRankingData] = useState([])
  const [rankingLoading, setRankingLoading] = useState(false)
  const [rankingFormula, setRankingFormula] = useState(null)

  // 热力图数据
  const [heatmapData, setHeatmapData] = useState({})
  const [heatmapDates, setHeatmapDates] = useState([])
  const [heatmapLoading, setHeatmapLoading] = useState(false)
  const [heatmapFormula, setHeatmapFormula] = useState(null)

  // 加权排行分数据
  const [weightedRankData, setWeightedRankData] = useState([])
  const [weightedRankLoading, setWeightedRankLoading] = useState(false)
  const [weightedRankFormula, setWeightedRankFormula] = useState(null)

  // 加权排行分热力图数据
  const [weightedRankHeatmapData, setWeightedRankHeatmapData] = useState({})
  const [weightedRankHeatmapDates, setWeightedRankHeatmapDates] = useState([])
  const [weightedRankHeatmapLoading, setWeightedRankHeatmapLoading] = useState(false)
  const [weightedRankHeatmapFormula, setWeightedRankHeatmapFormula] = useState(null)

  // 错误信息
  const [error, setError] = useState(null)

  // 加载初始化状态
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
      setStatusLoading(false)
    }
  }

  // 计算加权收益排行榜数据
  const fetchWeightedReturnRanking = useCallback(async (formula) => {
    setRankingLoading(true)
    setRankingFormula(formula)
    try {
      const result = await calculateWeightedReturn(formula)
      if (result.data) {
        setRankingData(result.data)
      }
    } catch (err) {
      console.error('计算失败:', err)
      setError('获取排行榜数据失败')
    }
    setRankingLoading(false)
  }, [])

  // 计算加权收益热力图数据
  const fetchWeightedReturnHeatmap = useCallback(async (formula, days = 10) => {
    setHeatmapLoading(true)
    setHeatmapFormula(formula)
    try {
      const result = await getWeightedReturnHeatmap(formula, days)
      if (result.data) {
        setHeatmapData(result.data)
        setHeatmapDates(result.dates || [])
      }
    } catch (err) {
      console.error('计算热力图失败:', err)
      setError('获取热力图数据失败')
    }
    setHeatmapLoading(false)
  }, [])

  // 计算加权排行分数据
  const fetchWeightedRank = useCallback(async (formula) => {
    setWeightedRankLoading(true)
    setWeightedRankFormula(formula)
    try {
      const result = await calculateWeightedRank(formula)
      if (result.data) {
        setWeightedRankData(result.data)
      }
    } catch (err) {
      console.error('计算加权排行分失败:', err)
      setError('获取加权排行分数据失败')
    }
    setWeightedRankLoading(false)
  }, [])

  // 计算加权排行分热力图数据
  const fetchWeightedRankHeatmap = useCallback(async (formula, days = 10) => {
    setWeightedRankHeatmapLoading(true)
    setWeightedRankHeatmapFormula(formula)
    try {
      const result = await getWeightedRankHeatmap(formula, days)
      if (result.data) {
        setWeightedRankHeatmapData(result.data)
        setWeightedRankHeatmapDates(result.dates || [])
      }
    } catch (err) {
      console.error('计算加权排行分热力图失败:', err)
      setError('获取加权排行分热力图数据失败')
    }
    setWeightedRankHeatmapLoading(false)
  }, [])

  // 处理数据更新
  const handleUpdate = useCallback(async (action = 'incremental') => {
    setUpdating(true)
    setError(null)
    setUpdateProgress(0)
    setUpdateMessage('正在启动更新...')

    try {
      const result = await updateData(action)
      if (result.success && result.async) {
        pollUpdateStatus()
      } else if (result.success) {
        const newStatus = await getInitStatus()
        setStatus(newStatus)
        setUpdating(false)
        setUpdateProgress(100)
        setUpdateMessage('更新完成')
      } else {
        setError(result.message || '更新失败')
        setUpdating(false)
      }
    } catch (err) {
      console.error('更新失败:', err)
      setError('网络错误，请检查后端服务是否正常运行')
      setUpdating(false)
    }
  }, [])

  // 轮询更新状态
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

  // 取消更新
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
    // 系统状态
    status,
    statusLoading,
    loadStatus,

    // 更新相关
    updating,
    updateProgress,
    updateMessage,
    handleUpdate,
    handleCancelUpdate,

    // 加权收益排行榜
    rankingData,
    rankingLoading,
    rankingFormula,
    fetchWeightedReturnRanking,

    // 加权收益热力图
    heatmapData,
    heatmapDates,
    heatmapLoading,
    heatmapFormula,
    fetchWeightedReturnHeatmap,

    // 加权排行分
    weightedRankData,
    weightedRankLoading,
    weightedRankFormula,
    fetchWeightedRank,

    // 加权排行分热力图
    weightedRankHeatmapData,
    weightedRankHeatmapDates,
    weightedRankHeatmapLoading,
    weightedRankHeatmapFormula,
    fetchWeightedRankHeatmap,

    // 错误
    error,
    setError
  }

  return <AppContext.Provider value={value}>{children}</AppContext.Provider>
}

export function useApp() {
  const context = useContext(AppContext)
  if (!context) {
    throw new Error('useApp must be used within AppProvider')
  }
  return context
}