import React from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { useApp } from './context/AppContext'

export default function App() {
  const {
    status,
    updating,
    updateProgress,
    updateMessage,
    error,
    setError,
    handleUpdate,
    handleCancelUpdate
  } = useApp()

  return (
    <div className="app">
      <div className="header">
        <h1>A股股票收益排行系统</h1>
        {error && (
          <div className="error-message">
            {error}
            <button className="close-error" onClick={() => setError(null)}>×</button>
          </div>
        )}
        <div className="header-info">
          <div className="status-bar">
            <div className="status-item">
              <span
                className={`status-dot ${status?.initialized ? 'active' : 'inactive'}`}
              ></span>
              <span>数据状态: {status?.initialized ? '已初始化' : '未初始化'}</span>
            </div>
            <div className="status-item">
              <span>股票数量: {status?.stock_count || 0}</span>
            </div>
            <div className="status-item">
              <span>最近更新: {status?.last_update || '-'}</span>
            </div>
            <button
              className="btn btn-primary"
              onClick={() => handleUpdate('full')}
              disabled={updating}
            >
              {updating ? `${updateMessage} (${updateProgress}%)` : '更新数据'}
            </button>
            {updating && (
              <button
                className="btn btn-secondary"
                onClick={handleCancelUpdate}
                style={{ marginLeft: '8px' }}
              >
                取消
              </button>
            )}
          </div>
        </div>
      </div>

      <nav className="nav-tabs">
        <NavLink
          to="/weighted-return-heatmap"
          className={({ isActive }) => `nav-tab ${isActive ? 'active' : ''}`}
        >
          加权收益热力图
        </NavLink>
        <NavLink
          to="/weighted-return-ranking"
          className={({ isActive }) => `nav-tab ${isActive ? 'active' : ''}`}
        >
          加权收益排行
        </NavLink>
        <NavLink
          to="/weighted-rank-heatmap"
          className={({ isActive }) => `nav-tab ${isActive ? 'active' : ''}`}
        >
          加权排行分热力图
        </NavLink>
        <NavLink
          to="/weighted-rank"
          className={({ isActive }) => `nav-tab ${isActive ? 'active' : ''}`}
        >
          加权排行分
        </NavLink>
      </nav>

      <Outlet />
    </div>
  )
}