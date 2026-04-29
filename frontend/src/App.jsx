import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { CheckCircle, AlertCircle, X, Info, Zap } from 'lucide-react';

import Sidebar from './components/Sidebar';
import Header from './components/Header';
import Orchestrator from './components/Orchestrator';

const API_BASE = '/api';

function App() {
  const [activeTab, setActiveTab] = useState('logs');
  const [logs, setLogs] = useState([]);
  const [config, setConfig] = useState({ is_running: false, running_mode: 'custom' });
  const [stats, setStats] = useState({ today: 0, total: 0 });
  const [sequences, setSequences] = useState([]);
  const [activeSequenceData, setActiveSequenceData] = useState({ loop: true, steps: [] });
  const [currentSequenceName, setCurrentSequenceName] = useState('smart.json');
  const [toasts, setToasts] = useState([]);
  const [isOnline, setIsOnline] = useState(true);
  
  const terminalRef = useRef(null);

  useEffect(() => {
    fetchConfig();
    fetchStats();
    fetchSequences();
    setupLogStream();
    
    const timer = setInterval(async () => {
      try {
        await axios.get(`${API_BASE}/ping`);
        setIsOnline(true);
      } catch (e) { setIsOnline(false); }
    }, 5000);
    return () => clearInterval(timer);
  }, []);

  const fetchConfig = async () => {
    try {
      const res = await axios.get(`${API_BASE}/config`);
      setConfig(res.data);
    } catch (e) { console.error(e); }
  };

  const fetchStats = async () => {
    try {
      const res = await axios.get(`${API_BASE}/stats`);
      setStats(res.data);
    } catch (e) { console.error(e); }
  };

  const clearStats = async () => {
    if (!window.confirm('确定要清除所有战斗统计吗？')) return;
    try {
      await axios.delete(`${API_BASE}/stats`);
      setStats({ today: 0, total: 0 });
      showToast('统计数据已重置');
    } catch (e) { showToast('重置失败', 'error'); }
  };

  const fetchSequences = async () => {
    try {
      const res = await axios.get(`${API_BASE}/sequences`);
      setSequences(res.data.sequences);
      const active = res.data.active || 'smart.json';
      setCurrentSequenceName(active);
      loadSequence(active);
    } catch (e) { console.error(e); }
  };

  const loadSequence = async (name) => {
    if (!name) return;
    try {
      const res = await axios.get(`${API_BASE}/sequences/${name}`);
      const stepsWithIds = (res.data.steps || []).map(s => ({ ...s, id: s.id || Math.random().toString(36).substr(2, 9) }));
      setActiveSequenceData({ ...res.data, steps: stepsWithIds });
    } catch (e) { 
      if (e.response && e.response.status === 404) {
        setActiveSequenceData({ loop: true, steps: [] });
      }
    }
  };

  const setupLogStream = () => {
    const eventSource = new EventSource(`${API_BASE}/logs`);
    eventSource.onmessage = (event) => {
      setLogs(prev => [...prev.slice(-200), event.data]);
    };
    return () => eventSource.close();
  };

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  const showToast = (message, type = 'success') => {
    const id = Date.now();
    setToasts(prev => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts(prev => prev.filter(t => t.id !== id));
    }, 3000);
  };

  const toggleRunning = async () => {
    const nextStatus = !config.is_running;
    try {
      await axios.post(`${API_BASE}/config`, { 
        settings: { ...config, is_running: nextStatus, active_sequence: currentSequenceName, running_mode: 'custom' } 
      });
      setConfig(prev => ({ ...prev, is_running: nextStatus, running_mode: 'custom' }));
      showToast(nextStatus ? '脚本运行中...' : '已停止', nextStatus ? 'success' : 'error');
    } catch (e) { showToast('操作失败', 'error'); }
  };

  return (
    <div className="container">
      {/* Toast Overlay */}
      <div style={{ position: 'fixed', top: '2rem', right: '2rem', zIndex: 9999, display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
        <AnimatePresence>
          {toasts.map(t => (
            <motion.div key={t.id} initial={{ opacity: 0, x: 50 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, scale: 0.95 }} className="glass-card p-4" style={{ minWidth: '200px', display: 'flex', alignItems: 'center', gap: '0.75rem', background: t.type === 'success' ? 'rgba(34, 197, 94, 0.2)' : 'rgba(239, 68, 68, 0.2)', borderColor: t.type === 'success' ? 'rgba(34, 197, 94, 0.5)' : 'rgba(239, 68, 68, 0.5)' }}>
              {t.type === 'success' ? <CheckCircle size={18} color="#22c55e" /> : <AlertCircle size={18} color="#ef4444" />}
              <span style={{ fontSize: '0.875rem' }}>{t.message}</span>
              <button onClick={() => setToasts(prev => prev.filter(toast => toast.id !== t.id))} style={{ background: 'transparent', padding: '4px', marginLeft: 'auto' }}>
                <X size={14} color="#94a3b8" />
              </button>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} config={config} toggleRunning={toggleRunning} isOnline={isOnline} />

      <div className="main-content">
        <Header activeTab={activeTab} currentSequenceName={currentSequenceName} activeSequenceData={activeSequenceData} stats={stats} clearStats={clearStats} />

        <AnimatePresence mode="wait">
          {activeTab === 'logs' && (
            <motion.div key="logs" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="glass-card p-6">
              <div className="terminal" ref={terminalRef}>
                {logs.map((log, i) => (
                  <div key={i} className={`log-line ${log.includes('WARNING') ? 'log-warning' : log.includes('ERROR') ? 'log-error' : 'log-info'}`}>
                    {log}
                  </div>
                ))}
              </div>
            </motion.div>
          )}

          {activeTab === 'config' && (
            <motion.div key="config" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }} className="glass-card p-6">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '2rem' }}>
                <section>
                  <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Info size={18} /> 基础设置</h3>
                  <div className="form-group">
                    <label className="label">轮询间隔 (秒)</label>
                    <input type="number" step="0.1" value={config.poll_interval_sec || ''} onChange={e => setConfig({...config, poll_interval_sec: parseFloat(e.target.value)})} />
                  </div>
                  <div className="form-group">
                    <label className="label">匹配阈值 (0-1)</label>
                    <input type="number" step="0.01" value={config.match_threshold || ''} onChange={e => setConfig({...config, match_threshold: parseFloat(e.target.value)})} />
                  </div>
                </section>
                <section>
                  <h3 style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Zap size={18} /> 战斗设置</h3>
                  <div className="form-group">
                    <label className="label">默认触发键</label>
                    <input type="text" value={config.press_key || ''} onChange={e => setConfig({...config, press_key: e.target.value})} />
                  </div>
                  <div className="form-group">
                    <label className="label">全局冷却 (秒)</label>
                    <input type="number" step="0.1" value={config.trigger_cooldown_sec || ''} onChange={e => setConfig({...config, trigger_cooldown_sec: parseFloat(e.target.value)})} />
                  </div>
                </section>
              </div>
              <div style={{ marginTop: '2rem', display: 'flex', justifyContent: 'flex-end' }}>
                <button className="btn-primary" onClick={async () => {
                  try {
                    await axios.post(`${API_BASE}/config`, { settings: config });
                    showToast('配置已保存');
                  } catch (e) { showToast('保存失败', 'error'); }
                }}>保存配置</button>
              </div>
            </motion.div>
          )}

          {activeTab === 'orchestrator' && (
            <motion.div key="orchestrator" initial={{ opacity: 0, x: 20 }} animate={{ opacity: 1, x: 0 }} exit={{ opacity: 0, x: -20 }}>
              <Orchestrator 
                sequences={sequences} 
                currentSequenceName={currentSequenceName} 
                setCurrentSequenceName={setCurrentSequenceName}
                loadSequence={loadSequence}
                createNewSequence={() => {
                  let name = prompt('请输入新脚本名称:');
                  if (!name) return;
                  if (!name.endsWith('.json')) name += '.json';
                  if (sequences.includes(name)) return showToast('名称已存在', 'error');
                  setSequences([...sequences, name]);
                  setCurrentSequenceName(name);
                  setActiveSequenceData({ loop: true, steps: [] });
                }}
                deleteSequence={async (name) => {
                  if (sequences.length <= 1) return showToast('至少需要保留一个脚本', 'error');
                  if (!window.confirm(`确定要彻底删除脚本 ${name} 吗？`)) return;
                  try {
                    await axios.delete(`${API_BASE}/sequences/${name}`);
                    showToast(`脚本 ${name} 已删除`);
                    const nextSequences = sequences.filter(s => s !== name);
                    setSequences(nextSequences);
                    const nextActive = nextSequences[0];
                    setCurrentSequenceName(nextActive);
                    loadSequence(nextActive);
                  } catch (e) { showToast('删除失败', 'error'); }
                }}
                activeSequenceData={activeSequenceData}
                setActiveSequenceData={setActiveSequenceData}
                saveActiveSequence={async () => {
                  try {
                    await axios.post(`${API_BASE}/sequences/${currentSequenceName}`, activeSequenceData);
                    showToast(`脚本 ${currentSequenceName} 已保存`);
                  } catch (e) { showToast('保存失败', 'error'); }
                }}
                updateStep={(idx, field, val) => {
                  const next = [...activeSequenceData.steps];
                  next[idx][field] = val;
                  setActiveSequenceData({...activeSequenceData, steps: next});
                }}
                removeSequenceStep={(idx) => {
                  const next = [...activeSequenceData.steps];
                  next.splice(idx, 1);
                  setActiveSequenceData({...activeSequenceData, steps: next});
                }}
                addSequenceStep={() => {
                  setActiveSequenceData({
                    ...activeSequenceData,
                    steps: [...activeSequenceData.steps, { id: Math.random().toString(36).substr(2, 9), action: 'press', key: 'x', delay: 1.0, condition: '' }]
                  });
                }}
                handleReorder={(newSteps) => setActiveSequenceData({...activeSequenceData, steps: newSteps})}
              />
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  );
}

export default App;
