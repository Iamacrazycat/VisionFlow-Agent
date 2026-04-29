import React, { useState } from 'react';
import { 
  Save, 
  Plus, 
  GripVertical, 
  Trash2, 
  AlignLeft, 
  Repeat, 
  Sword, 
  Coffee, 
  HelpCircle, 
  ChevronRight,
  ChevronDown,
  Info,
  ShieldAlert,
  Compass
} from 'lucide-react';
import { motion, AnimatePresence, Reorder } from 'framer-motion';

const Orchestrator = ({ 
  sequences, 
  currentSequenceName, 
  setCurrentSequenceName, 
  loadSequence, 
  createNewSequence, 
  deleteSequence,
  activeSequenceData, 
  setActiveSequenceData, 
  saveActiveSequence,
  updateStep,
  removeSequenceStep,
  addSequenceStep,
  handleReorder
}) => {
  const [expandedId, setExpandedId] = useState('lifecycle_a');

  const lifecycleConfig = [
    { 
      id: 'idle', 
      label: '空闲状态 (Idle)', 
      desc: '未匹配到任何特征时的默认循环执行逻辑。',
      icon: Compass, 
      color: '#38bdf8' 
    },
    { 
      id: 'lifecycle_a', 
      label: '特征匹配状态 A', 
      desc: '识别到视觉特征 A 时触发执行。',
      icon: ShieldAlert, 
      color: '#f472b6' 
    },
    { 
      id: 'lifecycle_b', 
      label: '特征匹配状态 B', 
      desc: '识别到视觉特征 B 时触发执行。',
      icon: Sword, 
      color: '#4ade80' 
    },
    { 
      id: 'other', 
      label: '其他未知状态', 
      desc: '无法识别当前具体状态时的兜底执行逻辑。',
      icon: HelpCircle, 
      color: '#94a3b8' 
    },
  ];

  const onUpdateStep = (tabId, idx, field, val) => {
    const nextSteps = [...(activeSequenceData[tabId] || [])];
    nextSteps[idx][field] = val;
    setActiveSequenceData({ ...activeSequenceData, [tabId]: nextSteps });
  };

  const onRemoveStep = (tabId, idx) => {
    const nextSteps = [...(activeSequenceData[tabId] || [])];
    nextSteps.splice(idx, 1);
    setActiveSequenceData({ ...activeSequenceData, [tabId]: nextSteps });
  };

  const onAddStep = (tabId) => {
    const newStep = { id: Math.random().toString(36).substr(2, 9), action: 'press', key: 'x', delay: 1.0, repeat: 1 };
    setActiveSequenceData({ ...activeSequenceData, [tabId]: [...(activeSequenceData[tabId] || []), newStep] });
  };

  const onReorderSteps = (tabId, newSteps) => {
    setActiveSequenceData({ ...activeSequenceData, [tabId]: newSteps });
  };

  return (
    <div className="orchestrator-root" style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* 顶部工具栏 */}
      <div className="glass-card p-4" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <select style={{ width: '220px' }} value={currentSequenceName} onChange={(e) => { setCurrentSequenceName(e.target.value); loadSequence(e.target.value); }}>
            {sequences.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
          <button onClick={createNewSequence} style={{ padding: '0.6rem', background: 'rgba(56, 189, 248, 0.1)', color: '#38bdf8', borderRadius: '10px' }} title="新建脚本"><Plus size={18} /></button>
          <button onClick={() => deleteSequence(currentSequenceName)} disabled={sequences.length <= 1} style={{ padding: '0.6rem', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444', borderRadius: '10px', opacity: sequences.length <= 1 ? 0.3 : 1 }} title="删除当前脚本"><Trash2 size={18} /></button>
        </div>
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
          <div style={{ fontSize: '0.875rem', color: '#94a3b8', background: 'rgba(255,255,255,0.05)', padding: '0.5rem 1rem', borderRadius: '10px' }}>
            生命周期脚本系统
          </div>
          <button className="btn-primary" onClick={saveActiveSequence}><Save size={18} style={{ marginRight: '0.5rem', verticalAlign: 'middle' }} />保存修改</button>
        </div>
      </div>

      {/* 脚本简介 */}
      <div className="glass-card p-5" style={{ background: 'linear-gradient(to right, rgba(56, 189, 248, 0.05), transparent)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem', color: '#38bdf8' }}>
          <AlignLeft size={18} />
          <span style={{ fontWeight: 600 }}>脚本说明</span>
        </div>
        <textarea 
          placeholder="给你的脚本写一点备注吧..."
          value={activeSequenceData.description || ''}
          onChange={(e) => setActiveSequenceData({...activeSequenceData, description: e.target.value})}
          style={{ width: '100%', background: 'transparent', border: 'none', color: '#e2e8f0', fontSize: '0.95rem', resize: 'none', outline: 'none', lineHeight: 1.6 }}
          rows={2}
        />
      </div>

      {/* 核心生命周期板块 */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
        {lifecycleConfig.map((lifecycle) => (
          <div key={lifecycle.id} className="glass-card" style={{ overflow: 'hidden', border: expandedId === lifecycle.id ? `1px solid ${lifecycle.color}40` : '1px solid rgba(255,255,255,0.05)' }}>
            {/* 卡片头部 */}
            <div 
              onClick={() => setExpandedId(expandedId === lifecycle.id ? null : lifecycle.id)}
              style={{ 
                padding: '1.25rem 1.5rem', 
                cursor: 'pointer', 
                display: 'flex', 
                alignItems: 'center', 
                gap: '1.25rem',
                background: expandedId === lifecycle.id ? `${lifecycle.color}08` : 'transparent',
                transition: 'background 0.3s'
              }}
            >
              <div style={{ 
                padding: '0.75rem', 
                borderRadius: '12px', 
                background: `${lifecycle.color}15`, 
                color: lifecycle.color,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <lifecycle.icon size={24} />
              </div>
              
              <div style={{ flex: 1 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <h3 style={{ fontSize: '1.1rem', fontWeight: 700, color: expandedId === lifecycle.id ? lifecycle.color : '#f1f5f9' }}>
                    {lifecycle.label}
                  </h3>
                  <span style={{ fontSize: '0.75rem', background: 'rgba(255,255,255,0.05)', color: '#94a3b8', padding: '0.2rem 0.5rem', borderRadius: '6px' }}>
                    {(activeSequenceData[lifecycle.id] || []).length} 个动作
                  </span>
                </div>
                <p style={{ fontSize: '0.85rem', color: '#64748b', marginTop: '0.25rem' }}>{lifecycle.desc}</p>
              </div>

              <div style={{ color: '#475569' }}>
                {expandedId === lifecycle.id ? <ChevronDown size={20} /> : <ChevronRight size={20} />}
              </div>
            </div>

            {/* 卡片内容：动作编辑器 */}
            <AnimatePresence>
              {expandedId === lifecycle.id && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3 }}
                >
                  <div style={{ padding: '0 1.5rem 1.5rem 1.5rem', borderTop: '1px solid rgba(255,255,255,0.05)' }}>
                    <div style={{ marginTop: '1.5rem' }}>
                      <Reorder.Group axis="y" values={activeSequenceData[lifecycle.id] || []} onReorder={(steps) => onReorderSteps(lifecycle.id, steps)} style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', listStyle: 'none', padding: 0 }}>
                        {(activeSequenceData[lifecycle.id] || []).map((step, idx) => (
                          <Reorder.Item key={step.id} value={step}>
                            <div className="glass-card" style={{ padding: '0.75rem 1rem', display: 'flex', alignItems: 'center', gap: '1rem', background: 'rgba(255,255,255,0.02)', border: '1px solid rgba(255,255,255,0.03)' }}>
                              <div style={{ color: '#334155', cursor: 'grab' }}><GripVertical size={18} /></div>
                              
                              <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '130px 1fr 1fr 100px', gap: '1rem', alignItems: 'center' }}>
                                <select value={step.action} onChange={(e) => onUpdateStep(lifecycle.id, idx, 'action', e.target.value)} style={{ fontSize: '0.85rem', padding: '0.4rem' }}>
                                  <option value="press">键盘按键</option>
                                  <option value="click">坐标点击</option>
                                  <option value="template_click">找图点击</option>
                                  <option value="wait">延时等待</option>
                                </select>
                                
                                <div style={{ display: 'flex', gap: '0.5rem' }}>
                                  {step.action === 'press' && <input placeholder="按键 (如 x)" value={step.key} onChange={(e) => onUpdateStep(lifecycle.id, idx, 'key', e.target.value)} />}
                                  {step.action === 'click' && <input type="number" placeholder="X" value={step.x} onChange={(e) => onUpdateStep(lifecycle.id, idx, 'x', parseInt(e.target.value))} />}
                                  {step.action === 'template_click' && <input type="number" step="0.01" placeholder="阈值 (0.8)" value={step.threshold} onChange={(e) => onUpdateStep(lifecycle.id, idx, 'threshold', parseFloat(e.target.value))} />}
                                </div>

                                <div style={{ display: 'flex', gap: '0.5rem' }}>
                                  {step.action === 'press' && <input type="number" step="0.1" placeholder="延迟 (秒)" value={step.delay} onChange={(e) => onUpdateStep(lifecycle.id, idx, 'delay', parseFloat(e.target.value))} />}
                                  {step.action === 'click' && <input type="number" placeholder="Y" value={step.y} onChange={(e) => onUpdateStep(lifecycle.id, idx, 'y', parseInt(e.target.value))} />}
                                  {step.action === 'wait' && <input type="number" step="0.1" placeholder="时长 (秒)" value={step.duration} onChange={(e) => onUpdateStep(lifecycle.id, idx, 'duration', parseFloat(e.target.value))} />}
                                </div>

                                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(255,255,255,0.03)', padding: '0.4rem', borderRadius: '8px' }}>
                                  <Repeat size={14} color="#64748b" />
                                  <input 
                                    type="number" 
                                    placeholder="次数" 
                                    value={step.repeat === -1 ? '' : (step.repeat || 1)} 
                                    onChange={(e) => onUpdateStep(lifecycle.id, idx, 'repeat', e.target.value === '' ? -1 : parseInt(e.target.value))}
                                    style={{ width: '40px', background: 'transparent', border: 'none', padding: 0, fontSize: '0.75rem', textAlign: 'center' }}
                                    title="输入 -1 表示无限循环"
                                  />
                                </div>
                              </div>

                              <button style={{ background: 'transparent', color: '#475569', padding: '0.4rem' }} onClick={() => onRemoveStep(lifecycle.id, idx)}>
                                <Trash2 size={16} />
                              </button>
                            </div>
                          </Reorder.Item>
                        ))}
                      </Reorder.Group>
                      
                      <button 
                        style={{ 
                          width: '100%', 
                          padding: '0.75rem', 
                          marginTop: '1rem', 
                          border: `1px dashed ${lifecycle.color}40`, 
                          background: `${lifecycle.color}05`, 
                          color: lifecycle.color, 
                          borderRadius: '12px',
                          fontSize: '0.85rem',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          gap: '0.5rem'
                        }} 
                        onClick={() => onAddStep(lifecycle.id)}
                      >
                        <Plus size={16} /> 添加动作到 {lifecycle.label}
                      </button>
                    </div>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        ))}
      </div>
      
      <div className="glass-card p-4" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', color: '#94a3b8', fontSize: '0.85rem' }}>
        <Info size={16} />
        <span>提示：Agent 会根据当前界面的实际画面状态，自动匹配视觉特征并执行上方对应的生命周期板块。</span>
      </div>
    </div>
  );
};

export default Orchestrator;
