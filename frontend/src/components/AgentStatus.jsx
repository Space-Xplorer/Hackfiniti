import React from 'react';
import { CheckCircle, Circle, Loader2 } from 'lucide-react';

const AgentStatus = ({ name, status, color = '#4B0082' }) => {
  return (
    <div className="flex items-center justify-between p-5 bg-white/60 rounded-3xl border border-white/80 shadow-sm transition-all hover:bg-white">
      <div className="flex items-center gap-4">
        <div className="w-2 h-2 rounded-full" style={{ backgroundColor: status === 'complete' ? '#10b981' : color }} />
        <span className="text-[10px] font-black uppercase tracking-widest text-slate-500">
          {name}
        </span>
      </div>

      <div className="flex items-center">
        {status === 'complete' && <CheckCircle size={18} className="text-emerald-500" />}
        {status === 'loading' && <Loader2 size={18} className="text-[#4B0082] animate-spin" />}
        {status === 'waiting' && <Circle size={18} className="text-slate-200" />}
      </div>
    </div>
  );
};

export default AgentStatus;
