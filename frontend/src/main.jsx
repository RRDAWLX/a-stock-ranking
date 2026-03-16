import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AppProvider } from './context/AppContext'
import App from './App.jsx'
import WeightedReturnHeatmapPage from './pages/WeightedReturnHeatmapPage.jsx'
import WeightedReturnRankingPage from './pages/WeightedReturnRankingPage.jsx'
import WeightedRankPage from './pages/WeightedRankPage.jsx'
import WeightedRankHeatmapPage from './pages/WeightedRankHeatmapPage.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <AppProvider>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<Navigate to="/weighted-rank-heatmap" replace />} />
          <Route path="weighted-return-heatmap" element={<WeightedReturnHeatmapPage />} />
          <Route path="weighted-return-ranking" element={<WeightedReturnRankingPage />} />
          <Route path="weighted-rank-heatmap" element={<WeightedRankHeatmapPage />} />
          <Route path="weighted-rank" element={<WeightedRankPage />} />
        </Route>
      </Routes>
    </AppProvider>
  </BrowserRouter>
)