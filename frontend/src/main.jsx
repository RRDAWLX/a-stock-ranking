import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AppProvider } from './context/AppContext'
import App from './App.jsx'
import WeightedReturnHeatmapPage from './pages/WeightedReturnHeatmapPage.jsx'
import WeightedReturnRankingPage from './pages/WeightedReturnRankingPage.jsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <AppProvider>
      <Routes>
        <Route path="/" element={<App />}>
          <Route index element={<Navigate to="/weighted-return-heatmap" replace />} />
          <Route path="weighted-return-heatmap" element={<WeightedReturnHeatmapPage />} />
          <Route path="weighted-return-ranking" element={<WeightedReturnRankingPage />} />
        </Route>
      </Routes>
    </AppProvider>
  </BrowserRouter>
)