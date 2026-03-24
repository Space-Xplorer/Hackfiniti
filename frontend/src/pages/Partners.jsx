import React from 'react';
import { useShield } from '../context/ShieldContext';
import { 
  Network, BarChart3, ShieldCheck, Zap, Layers, Globe, 
  Cpu, Code, Lock, ArrowRight, CheckCircle2 
} from 'lucide-react';
import GlassCard from '../components/GlassCard';

const Partners = () => {
  const { setView } = useShield();

  const useCases = [
    { title: "Digital Lending", desc: "Automate 'New-to-Credit' profiling with alternative data points.", icon: <Zap /> },
    { title: "Health Insurance", desc: "Dynamic premium calculation based on real-time biomarker extraction.", icon: <Layers /> },
    { title: "Micro-Finance", desc: "Enable low-cost underwriting for Tier 2 and Tier 3 Indian markets.", icon: <Globe /> }
  ];

  return (
    <div className="px-8 py-10 max-w-7xl mx-auto animate-in fade-in duration-1000">
      
      {/* --- HERO SECTION --- */}
      <div className="grid lg:grid-cols-2 gap-12 items-center mb-24">
        <div>
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#4B0082]/5 border border-[#4B0082]/10 text-[10px] font-black uppercase tracking-[0.2em] text-[#4B0082] mb-6">
            <Cpu size={14} className="text-[#4B0082]" fill="currentColor" /> Enterprise Nexus
          </div>
          <h2 className="text-5xl font-black text-[#4B0082] tracking-tighter leading-[0.9] mb-6">
            Underwriting,<br /><span className="italic text-[#4B0082]">at Machine Scale.</span>
          </h2>
          <p className="text-lg text-slate-500 font-medium leading-relaxed mb-8 max-w-lg">
            Daksha is a plug-and-play **Underwriting-as-a-Service (UaaS)** layer. Shift from subjective manual audits to objective, agentic glass-box decisions in milliseconds.
          </p>
          <div className="flex gap-4">
            <button className="brinjal-gradient text-[#4B0082] border-2 border-[#4B0082] px-8 py-4 rounded-full font-black uppercase tracking-widest text-xs shadow-2xl hover:scale-105 transition-all">
              Request API Access
            </button>
            <button className="px-8 py-4 rounded-full font-black uppercase tracking-widest text-xs border-2 border-slate-100 text-slate-400 hover:bg-slate-50 transition-all">
              View Docs
            </button>
          </div>
        </div>

        {/* --- PERFORMANCE BENCHMARKS (CONTRAST FIXED) --- */}
        <div className="brinjal-gradient rounded-[4rem] p-8 text-white shadow-3xl relative overflow-hidden group isolate">
          {/* Background Blur Efx */}
          <div className="absolute top-0 right-0 w-64 h-64 bg-[#4B0082]/20 rounded-full blur-[100px] group-hover:scale-150 transition-transform duration-1000 -z-10" />
          <div className="absolute bottom-[-10%] left-[-10%] w-64 h-64 bg-[#4B0082]/80 rounded-full blur-[100px] -z-10" />

          <h3 className="text-xl font-black text-[#391e4f] mb-8 italic tracking-tight flex items-center gap-3 drop-shadow-sm">
            <BarChart3 className="text-[#391e4f]" /> Performance Benchmarks
          </h3>

          <div className="grid grid-cols-2 gap-4 mb-8">
            {/* Box 1: High Contrast Audit Reduction */}
            <div className="bg-[#2a004a]/60 p-6 rounded-3xl border-2 border-[#4B0082]/30 backdrop-blur-md shadow-lg hover:border-[#4B0082]/60 transition-all group/box">
              <p className="text-[10px] font-bold text-pink-200/80 uppercase tracking-widest mb-2">Audit Reduction</p>
              <p className="text-4xl font-black italic text-[#4B0082] drop-shadow-[0_0_10px_rgba(244,194,194,0.4)] group-hover/box:scale-110 transition-transform">84%</p>
            </div>

            {/* Box 2: High Contrast Latency */}
            <div className="bg-[#2a004a]/60 p-6 rounded-3xl border-2 border-[#4B0082]/30 backdrop-blur-md shadow-lg hover:border-[#4B0082]/60 transition-all group/box">
              <p className="text-[10px] font-bold text-pink-200/80 uppercase tracking-widest mb-2">Extraction Latency</p>
              <p className="text-4xl font-black italic text-white drop-shadow-sm group-hover/box:scale-110 transition-transform">~1.2s</p>
            </div>
          </div>

          {/* Bottom Progress Bar Container */}
          <div className="space-y-4 p-4 bg-[#2a004a]/40 rounded-3xl border border-[#4B0082]/20">
              <div className="flex justify-between text-[10px] font-black uppercase tracking-widest">
                <span className="text-pink-200/80">Model Bias Mitigation (EBM)</span>
                <span className="text-[#4B0082] font-black italic">Optimal</span>
              </div>
              <div className="h-2 w-full bg-[#4B0082]/50 rounded-full overflow-hidden border border-[#4B0082]/30">
                <div className="h-full bg-gradient-to-r from-[#4B0082] to-[#4B0082] w-[98%] animate-pulse shadow-[0_0_15px_#4B0082]" />
              </div>
          </div>
        </div>
      </div>

      {/* --- SECTOR USE CASES --- */}
      <div className="mb-24">
        <h4 className="text-[10px] font-black uppercase tracking-[0.4em] text-slate-400 mb-12 text-center">Target Industry Verticals</h4>
        <div className="grid md:grid-cols-3 gap-8">
          {useCases.map((uc, i) => (
            <GlassCard key={i} className="p-8 hover:border-[#4B0082]/20 transition-all group">
              <div className="w-14 h-14 bg-[#4B0082]/5 rounded-2xl flex items-center justify-center text-[#4B0082] mb-6 group-hover:bg-[#4B0082] group-hover:text-[#4B0082] transition-all duration-500">
                {uc.icon}
              </div>
              <h5 className="text-lg font-black text-[#4B0082] mb-3 uppercase italic">{uc.title}</h5>
              <p className="text-sm text-slate-500 font-medium leading-relaxed">{uc.desc}</p>
            </GlassCard>
          ))}
        </div>
      </div>

      {/* --- API INTEGRATION PREVIEW --- */}
      <div className="grid lg:grid-cols-2 gap-12 items-center mb-24">
        <div className="order-2 lg:order-1">
          <div className="bg-[#1a1a1a] rounded-[3rem] p-8 shadow-2xl relative border-t-8 border-[#4B0082]">
            <div className="flex gap-2 mb-6">
              <div className="w-3 h-3 rounded-full bg-red-500/20" />
              <div className="w-3 h-3 rounded-full bg-yellow-500/20" />
              <div className="w-3 h-3 rounded-full bg-green-500/20" />
            </div>
            <pre className="text-xs font-mono text-pink-200/70 overflow-x-auto leading-relaxed">
              <code>{`
// Initialize Daksha SDK
const daksha = new DakshaClient(process.env.DAKSHA_KEY);

// Push Document for Agentic Audit
const response = await daksha.audit({
  type: 'LOAN_APPLICATION',
  docs: [bank_statement_pdf],
  mode: 'glass-box'
});

// Access EBM Reasoning Trace
console.log(response.reasoning_trace);
// Output: "Salary stability verified in P3..."
              `}</code>
            </pre>
          </div>
        </div>
        <div className="order-1 lg:order-2">
          <h3 className="text-3xl font-black text-[#4B0082] italic tracking-tighter mb-6 underline decoration-[#4B0082] underline-offset-8">Developer-First Integration</h3>
          <p className="text-slate-500 font-medium mb-8 leading-relaxed">
            Our SDK allows you to plug Daksha into your existing onboarding flow with just 4 lines of code. Get real-time JSON responses containing both the final risk score and the **Reasoning Trace** for your internal CRM.
          </p>
          <div className="space-y-4">
            {["RESTful API Architecture", "Webhook Notifications", "Sandbox Environment"].map((item, i) => (
              <div key={i} className="flex items-center gap-3 font-black text-[10px] uppercase tracking-widest text-[#4B0082]">
                <CheckCircle2 size={16} className="text-[#4B0082]" /> {item}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* --- TRUST & COMPLIANCE --- */}
      <GlassCard className="p-10 text-center border-b-[16px] border-[#4B0082]">
        <div className="w-16 h-16 bg-[#4B0082] rounded-full flex items-center justify-center mx-auto mb-6 text-[#4B0082] shadow-xl">
            <Lock size={32} />
         </div>
        <h3 className="text-3xl font-black text-[#4B0082] italic tracking-tighter mb-4">Enterprise-Grade Security</h3>
        <p className="text-slate-500 font-medium max-w-2xl mx-auto mb-8">
            We operate on a **Zero-Knowledge Architecture**. Daksha extracts features without storing sensitive PII on our servers. Fully compliant with RBI digital lending guidelines and the DPDP Act 2023.
         </p>
         <button className="text-[10px] font-black uppercase tracking-[0.4em] text-[#4B0082] flex items-center gap-2 mx-auto hover:gap-6 transition-all duration-300">
            Download Security Whitepaper <ArrowRight size={16} />
          </button>
      </GlassCard>

    </div>
  );
};

export default Partners;