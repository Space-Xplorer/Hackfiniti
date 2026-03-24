import React from 'react';
import { useShield } from '../context/ShieldContext';
import { Rocket, Shield, BrainCircuit, Sparkles, Zap, Activity, ShieldCheck } from 'lucide-react';
import GlassCard from '../components/GlassCard';

const Landing = () => {
  const { setView } = useShield();

  return (
    <div className="relative min-h-screen flex items-center px-8 overflow-hidden">
      <div className="grid lg:grid-cols-2 gap-10 items-center w-full relative z-10">
        
        {/* --- LEFT CONTENT --- */}
        <div className="animate-in slide-in-from-left-10 duration-1000">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#4B0082]/5 border border-[#4B0082]/10 text-[10px] font-black uppercase tracking-[0.2em] text-[#4B0082] mb-6 shadow-sm">
            <Zap size={14} className="text-[#F4C2C2]" fill="currentColor" /> 
            AI-Powered Underwriting
          </div>
          
          <h1 className="text-[8.5vw] lg:text-[6.5vw] font-black leading-[0.85] tracking-tighter text-[#4B0082] mb-6">
            FAIR RISK.<br />
            <span className="text-transparent bg-clip-text bg-linear-to-r from-[#4B0082] via-[#F4C2C2] to-[#4B0082] bg-size-[200%_auto] animate-[shine_3s_linear_infinite] italic">
              DECODED.
            </span>
          </h1>

          <p className="max-w-md text-slate-500 font-medium text-lg mb-8 leading-relaxed">
            No more "Black Box" rejections. Get verified, see the math, and unlock your true potential with <strong>Daksha Agentic Intelligence</strong>.
          </p>

          <div className="flex flex-wrap gap-6">
            <button 
              onClick={() => setView('kyc')} 
              className="brinjal-gradient text-[#4b2d67] px-10 py-5 rounded-full font-black uppercase tracking-[0.2em] text-xs flex items-center gap-4 hover:scale-105 transition-all shadow-2xl shadow-[#4B0082]/30 pink-glow border-2 border-[#4B0082]"
            >
              Initialize Quest <Rocket size={20} />
            </button>
            
          </div>
        </div>

        {/* --- RIGHT VISUAL (The Animated Scanner) --- */}
        <div className="relative animate-in zoom-in-95 duration-1000">
          <div className="absolute inset-0 bg-[#4B0082] rounded-[4rem] rotate-3 opacity-5 scale-105 blur-2xl" />
          
          <GlassCard className="p-10 border-2 border-white/80 relative group">
            {/* The Scanner Line Animation */}
            <div className="absolute inset-0 overflow-hidden rounded-[3rem]">
               <div className="h-0.5 w-full bg-linear-to-r from-transparent via-[#F4C2C2] to-transparent absolute top-0 left-0 shadow-[0_0_15px_#F4C2C2] animate-[scan_4s_ease-in-out_infinite] z-20" />
            </div>

            <div className="flex justify-between items-start mb-10">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-2xl bg-[#4B0082] flex items-center justify-center text-[#F4C2C2] shadow-xl rotate-3">
                  <BrainCircuit size={28} />
                </div>
                <div>
                  <h4 className="font-black text-[#4B0082] italic text-lg leading-none">Daksha V1</h4>
                  <span className="text-[9px] font-bold uppercase tracking-[0.3em] text-[#F4C2C2]">Agentic Core</span>
                </div>
              </div>
              <div className="px-4 py-2 rounded-xl bg-emerald-50 text-emerald-600 text-[10px] font-black uppercase tracking-widest border border-emerald-100 flex items-center gap-2">
                <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" /> Live Audit
              </div>
            </div>

            <div className="space-y-4">
              {[
                { label: "Identity Sync", icon: <Shield size={14} /> },
                { label: "OCR Extraction", icon: <Sparkles size={14} /> },
                { label: "EBM Logic Engine", icon: <Activity size={14} /> }
              ].map((agent, i) => (
                <div key={i} className="flex items-center justify-between p-4 bg-white/60 rounded-3xl border border-white/50 group-hover:translate-x-2 transition-transform duration-500">
                  <div className="flex items-center gap-4">
                    <div className="text-[#4B0082]">{agent.icon}</div>
                    <span className="text-[10px] font-black uppercase tracking-widest text-slate-400">{agent.label}</span>
                  </div>
                  <div className="h-1.5 w-16 bg-[#4B0082]/5 rounded-full overflow-hidden">
                    <div className="h-full bg-[#4B0082] rounded-full w-full" />
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-8 flex items-center justify-center gap-2 text-[9px] font-black uppercase tracking-[0.4em] text-[#4B0082]/30 italic">
              <ShieldCheck size={14} /> Transparent Underwriting Protocol
            </div>
          </GlassCard>
        </div>
      </div>

      {/* --- CSS FOR SHINE AND SCAN (In case not in GlobalStyles) --- */}
      <style>{`
        @keyframes shine { to { background-position: 200% center; } }
        @keyframes scan {
          0% { top: 0%; opacity: 0; }
          50% { opacity: 1; }
          100% { top: 100%; opacity: 0; }
        }
      `}</style>
    </div>
  );
};

export default Landing;