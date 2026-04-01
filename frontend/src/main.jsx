import React, { Suspense } from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AppProvider } from './context/AppContext'
import App from './App.jsx'
import './index.css'

// 懒加载页面组件
const WeightedReturnHeatmapPage = React.lazy(() => import('./pages/WeightedReturnHeatmapPage.jsx'))
const WeightedReturnRankingPage = React.lazy(() => import('./pages/WeightedReturnRankingPage.jsx'))
const WeightedRankPage = React.lazy(() => import('./pages/WeightedRankPage.jsx'))
const WeightedRankHeatmapPage = React.lazy(() => import('./pages/WeightedRankHeatmapPage.jsx'))

// 加载中的占位组件
function LoadingFallback() {
  return (
    <div className="loading">
      <div className="loading-spinner"></div>
      <span>加载中...</span>
    </div>
  )
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <AppProvider>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<Navigate to="/weighted-rank-heatmap" replace />} />
          <Route
            path="weighted-return-heatmap"
            element={
              <Suspense fallback={<LoadingFallback />}>
                <WeightedReturnHeatmapPage />
              </Suspense>
            }
          />
          <Route
            path="weighted-return-ranking"
            element={
              <Suspense fallback={<LoadingFallback />}>
                <WeightedReturnRankingPage />
              </Suspense>
            }
          />
          <Route
            path="weighted-rank-heatmap"
            element={
              <Suspense fallback={<LoadingFallback />}>
                <WeightedRankHeatmapPage />
              </Suspense>
            }
          />
          <Route
            path="weighted-rank"
            element={
              <Suspense fallback={<LoadingFallback />}>
                <WeightedRankPage />
              </Suspense>
            }
          />
        </Route>
      </Routes>
    </AppProvider>
  </BrowserRouter>
)