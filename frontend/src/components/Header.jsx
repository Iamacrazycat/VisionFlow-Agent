import React from 'react';
import { RotateCcw, Info } from 'lucide-react';

const Header = ({ activeTab, currentSequenceName, activeSequenceData, stats, clearStats }) => {
  const getTitle = () => {
    switch (activeTab) {
      case 'logs': return '实时运行状态';
      case 'config': return '全局参数配置';
      case 'orchestrator': return '脚本步骤编排';
      default: return '仪表盘';
    }
  };

  return (
    <header className="header animate-in">
      <div style={{ flex: 1 }}>
        <h2 style={{ fontSize: '1.5rem' }}>{getTitle()}</h2>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem', alignItems: 'center', marginTop: '0.5rem' }}>
          <span style={{ color: '#94a3b8', fontSize: '0.875rem' }}>{new Date().toLocaleDateString()}</span>
          {activeTab === 'logs' && (
            <>
              <div style={{ fontSize: '0.875rem', color: '#38bdf8', background: 'rgba(56, 189, 248, 0.1)', padding: '0.25rem 0.75rem', borderRadius: '6px' }}>
                当前脚本: {currentSequenceName}
              </div>
              {activeSequenceData?.description && (
                <div style={{ fontSize: '0.875rem', color: '#94a3b8', display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                  <Info size={14} />
                  {activeSequenceData.description}
                </div>
              )}
            </>
          )}
        </div>
      </div>
      
      <div className="dashboard-grid" style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
        <div className="glass-card stat-card" style={{ padding: '0.75rem 1.5rem', minWidth: '150px', position: 'relative' }}>
          <div className="stat-label">今日战斗</div>
          <div className="stat-value" style={{ fontSize: '1.25rem' }}>{stats.today}</div>
        </div>
        <button 
          onClick={clearStats}
          style={{ background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', padding: '0.75rem', borderRadius: '12px' }}
          title="清除统计"
        >
          <RotateCcw size={20} />
        </button>
      </div>
    </header>
  );
};

export default Header;
