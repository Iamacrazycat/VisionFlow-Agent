import React from 'react';
import { Terminal, Zap, Settings, Square, Play, Wifi } from 'lucide-react';

const Sidebar = ({ activeTab, setActiveTab, config, toggleRunning, isOnline }) => {
  const navItems = [
    { id: 'logs', label: '实时日志', icon: Terminal },
    { id: 'orchestrator', label: '脚本编排', icon: Zap },
    { id: 'config', label: '配置设置', icon: Settings },
  ];

  return (
    <div className="sidebar glass-card p-4">
      <div style={{ padding: '1rem', marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: '#38bdf8' }}>RocoBot</h1>
        <p style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Automation Dashboard</p>
      </div>
      
      {navItems.map(item => (
        <div 
          key={item.id}
          className={`nav-item ${activeTab === item.id ? 'active' : ''}`} 
          onClick={() => setActiveTab(item.id)}
        >
          <item.icon size={20} />
          <span>{item.label}</span>
        </div>
      ))}

      <div style={{ marginTop: 'auto', padding: '1rem', display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        <button 
          className={`btn-${config.is_running ? 'error' : 'primary'}`} 
          onClick={toggleRunning}
          disabled={!isOnline}
          style={{ width: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', opacity: isOnline ? 1 : 0.5 }}
        >
          {config.is_running ? <Square size={18} /> : <Play size={18} />}
          {config.is_running ? '停止脚本' : '运行当前脚本'}
        </button>
        
        <div className="status-badge" style={{ background: isOnline ? (config.is_running ? 'rgba(34, 197, 94, 0.1)' : 'rgba(239, 68, 68, 0.1)') : 'rgba(148, 163, 184, 0.1)', color: isOnline ? (config.is_running ? '#22c55e' : '#ef4444') : '#94a3b8' }}>
          {isOnline ? (
            <>
              <div style={{ width: 8, height: 8, borderRadius: '50%', background: config.is_running ? '#22c55e' : '#ef4444' }} />
              {config.is_running ? '脚本执行中' : '空闲'}
            </>
          ) : (
            <>
              <Wifi size={14} style={{ marginRight: '4px' }} />
              离线
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default Sidebar;
