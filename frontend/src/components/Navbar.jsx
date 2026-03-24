import React from 'react';
import { useShield } from '../context/ShieldContext';
import { Shield, Info, Terminal, Briefcase, Rocket, X } from 'lucide-react';

const Navbar = () => {
  const { setView, view } = useShield();
  const isQuestActive = !['landing', 'partner', 'about', 'how-it-works'].includes(view);

  return (
    <nav className="flex justify-between items-center px-8 py-4 z-50 border-b border-[#4B0082]/5 bg-[#FAF9F6]/80 backdrop-blur-md sticky top-0">
      <div className="flex items-center gap-3 cursor-pointer group" onClick={() => setView('landing')}>
        <div className="w-10 h-10 bg-[#4B0082] rounded-xl flex items-center justify-center rotate-3 shadow-lg group-hover:rotate-0 transition-all duration-500">
          <Shield className="text-[#F4C2C2]" size={20} fill="currentColor" />
        </div>
        <div className="flex flex-col">
          <span className="text-xl font-black tracking-tighter text-[#4B0082] uppercase italic leading-none">Daksha</span>
          <span className="text-[7px] font-black uppercase tracking-[0.3em] text-[#F4C2C2] mt-1">Explainable. Realiable. Responsible.</span>
        </div>
      </div>

      <div className="flex items-center gap-8">
        {!isQuestActive ? (
          <>
            <button onClick={() => setView('how')} className={`flex items-center gap-2 text-[10px] font-black uppercase tracking-widest transition-all ${view === 'how-it-works' ? 'text-[#4B0082]' : 'text-slate-400 hover:text-[#4B0082]'}`}>
              <Terminal size={14} /> How it Works
            </button>
            <button onClick={() => setView('about')} className={`flex items-center gap-2 text-[10px] font-black uppercase tracking-widest transition-all ${view === 'about' ? 'text-[#4B0082]' : 'text-slate-400 hover:text-[#4B0082]'}`}>
              <Info size={14} /> About
            </button>
            <button onClick={() => setView('partner')} className={`flex items-center gap-2 text-[10px] font-black uppercase tracking-widest transition-all ${view === 'partner' ? 'text-[#4B0082]' : 'text-slate-400 hover:text-[#4B0082]'}`}>
              <Briefcase size={14} /> Partners
            </button>
          </>
        ) : (
          <div className="px-3 py-1.5 bg-[#4B0082]/5 rounded-full border border-[#4B0082]/10 flex items-center gap-3">
            <div className="w-2 h-2 bg-[#F4C2C2] rounded-full animate-pulse" />
            <span className="text-[9px] font-black uppercase tracking-widest text-[#4B0082]">Quest in Progress</span>
          </div>
        )}
      </div>

      <div className="flex items-center gap-4">
        {isQuestActive ? (
          <button onClick={() => setView('landing')} className="flex items-center gap-2 bg-white border-2 border-slate-100 text-slate-400 px-3 py-2 rounded-2xl hover:bg-red-50 hover:text-red-500 hover:border-red-100 transition-all group" title="Exit Quest">
            <X size={20} className="group-hover:rotate-90 transition-transform" />
            <span className="text-[10px] font-black uppercase tracking-widest">Abort</span>
          </button>
        ) : (
          <button onClick={() => setView('kyc')} className="bg-[#4B0082] text-[#F4C2C2] border-2 border-[#4B0082] px-6 py-2.5 rounded-full font-black text-[10px] uppercase tracking-widest shadow-xl shadow-[#4B0082]/20 hover:scale-105 active:scale-95 transition-all flex items-center gap-3">
            Start Quest <Rocket size={14} />
          </button>
        )}
      </div>
    </nav>
  );
};

export default Navbar;
