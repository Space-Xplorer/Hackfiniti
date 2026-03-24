import React from 'react';
import { 
  Network, BrainCircuit, FileSearch, MessageSquareQuote, 
  ShieldCheck, ArrowRight, Binary, Fingerprint, Dna, Cpu 
} from 'lucide-react';
import GlassCard from '../components/GlassCard';

const HowItWorks = () => {
  const agentFlow = [
    { 
      step: "01", 
      title: "Identity Agent", 
      tag: "Security",
      desc: "Anchors the session using Aadhaar XML. It generates a unique Zero-Knowledge identifier so we audit the data, not the person.",
      icon: <Fingerprint /> 
    },
    { 
      step: "02", 
      title: "Extraction Agent", 
      tag: "Computer Vision",
      desc: "Uses custom OCR agents to parse messy Bank Statements and Medical PDFs into a clean Feature Matrix (X).",
      icon: <FileSearch /> 
    },
    { 
      step: "03", 
      title: "EBM Engine", 
      tag: "Core Math",
      desc: "The 'Brain'. It runs interaction logic to find how features (like Income vs. Spending) affect your total risk score.",
      icon: <BrainCircuit /> 
    },
    { 
      step: "04", 
      title: "Advisor Agent", 
      tag: "NLP",
      desc: "Translates complex EBM shape functions into 'Reasoning Traces'—human sentences that tell you exactly why.",
      icon: <MessageSquareQuote /> 
    }
  ];

  return (
    <div className="min-h-screen bg-[#f7faf9] px-6 py-12 max-w-7xl mx-auto">
      
      {/* --- HEADER --- */}
      <div className="text-center mb-20">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-[#04221f]/5 border border-[#005b52]/10 text-[10px] font-black uppercase tracking-[0.3em] text-[#04221f] mb-8">
          <Binary size={14} className="text-[#dbf226]" /> The Technical Blueprint
        </div>
        <h2 className="text-[5.5vw] lg:text-[4.5vw] font-black text-[#04221f] tracking-tighter italic leading-none mb-6">
          AGENTIC<br /><span className="text-[#dbf226]">ORCHESTRATION.</span>
        </h2>
        <p className="text-lg text-slate-500 font-medium max-w-2xl mx-auto">
          Daksha isn't a single model. It's a symphony of specialized agents working in a strict, verifiable pipeline.
        </p>
      </div>

      {/* --- PIPELINE VISUALIZATION --- */}
      <div className="relative mb-24">
        {/* Connection Line */}
        <div className="absolute top-1/2 left-0 w-full h-1 bg-[#04221f]/5 -z-10 hidden lg:block" />
        
        <div className="grid lg:grid-cols-4 gap-6">
          {agentFlow.map((agent, i) => (
            <div key={i} className="relative group">
              <div className="bg-white p-6 rounded-[3rem] border-2 border-slate-100 hover:border-[#F4C2C2] transition-all duration-500 shadow-sm hover:shadow-xl">
                <div className="w-14 h-14 bg-[#04221f] rounded-2xl flex items-center justify-center text-[#dbf226] mb-6 shadow-lg group-hover:rotate-12 transition-transform">
                  {agent.icon}
                </div>
                <span className="text-[10px] font-black text-[#dbf226] bg-[#04221f] px-3 py-1 rounded-full uppercase tracking-widest mb-4 inline-block">
                  {agent.tag}
                </span>
                <h4 className="text-lg font-black text-[#04221f] mb-3 uppercase italic">{agent.title}</h4>
                <p className="text-sm text-slate-500 font-medium leading-relaxed">
                  {agent.desc}
                </p>
                <div className="mt-8 flex items-center gap-2 text-[10px] font-black text-[#04221f]/20 uppercase tracking-[0.3em]">
                  Phase {agent.step} <ArrowRight size={12} />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* --- EBM DEEP DIVE (THE MATH) --- */}
      <div className="grid lg:grid-cols-2 gap-12 items-center mb-24">
        <div className="bg-[#04221f] rounded-[4rem] p-10 text-[#dbf226] shadow-3xl relative overflow-hidden">
           <div className="absolute top-[-10%] right-[-10%] w-64 h-64 bg-white/10 rounded-full blur-3xl" />
           <Cpu size={40} className="mb-8 opacity-50" />
           <h3 className="text-2xl font-black italic mb-6 text-white uppercase tracking-tighter">The GA2M Engine</h3>
           <div className="bg-[#2a004a]/60 p-6 rounded-3xl border border-[#F4C2C2]/30 backdrop-blur-md mb-6">
              <code className="text-lg md:text-xl font-bold text-white block text-center">
                g(E[y]) = &sum; f<sub>i</sub>(x<sub>i</sub>) + &sum; f<sub>ij</sub>(x<sub>i</sub>, x<sub>j</sub>)
              </code>
           </div>
           <p className="text-pink-50/80 font-medium leading-relaxed mb-4">
             Most AI uses "Deep Learning," which is accurate but unexplainable. Daksha uses **Explainable Boosting Machines (EBM)**.
           </p>
           <ul className="space-y-4">
              <li className="flex gap-3 text-sm font-bold">
                 <ShieldCheck className="shrink-0" /> 
                 <span><strong>Main Effects:</strong> Each feature (Income, Age) has its own measurable impact.</span>
              </li>
              <li className="flex gap-3 text-sm font-bold">
                 <ShieldCheck className="shrink-0" /> 
                 <span><strong>Interactions:</strong> We capture how pairs of features interact (e.g., how 'Debt' feels different at 'Age 25' vs 'Age 50').</span>
              </li>
           </ul>
        </div>

        <div>
           <h3 className="text-3xl font-black text-[#04221f] italic tracking-tighter mb-6 underline decoration-[#F4C2C2] underline-offset-8 uppercase">Why Glass-Box?</h3>
           <div className="space-y-10">
              <div className="flex gap-6">
                 <div className="w-12 h-12 shrink-0 rounded-2xl bg-[#dbf226]/20 flex items-center justify-center text-[#04221f] shadow-sm"><Dna /></div>
                 <div>
                    <h5 className="font-black text-[#04221f] uppercase mb-2">Editable Intelligence</h5>
                    <p className="text-sm text-slate-500 font-medium">Because EBMs are additive, we can 'edit' the model if we find a bias, without retraining the whole brain.</p>
                 </div>
              </div>
              <div className="flex gap-6">
                 <div className="w-12 h-12 shrink-0 rounded-2xl bg-[#dbf226]/20 flex items-center justify-center text-[#04221f] shadow-sm"><Network /></div>
                 <div>
                    <h5 className="font-black text-[#04221f] uppercase mb-2">Audit-Ready Logs</h5>
                    <p className="text-sm text-slate-500 font-medium">Every decision produces a 'Shape Function' graph. It's not a guess; it's a mathematical certainty.</p>
                 </div>
              </div>
           </div>
        </div>
      </div>

      {/* --- WORKFLOW SUMMARY --- */}
      <GlassCard className="p-10 text-center border-b-4 border-[#dbf226]">
        <h3 className="text-3xl font-black text-[#04221f] italic mb-4 uppercase">The Agentic Handshake</h3>
        <p className="text-slate-500 font-medium max-w-3xl mx-auto mb-8">
            In standard systems, data is just a number. In Daksha, our agents 'talk' to each other. The **Extraction Agent** passes a feature matrix to the **EBM Engine**, which then hands its math to the **Advisor Agent** to write your report.
         </p>
         <div className="flex justify-center flex-wrap gap-4">
            {["Verifiable", "Deterministic", "Privacy-First", "Bias-Aware"].map((tag, i) => (
              <span key={i} className="px-6 py-2 bg-[#04221f] text-[#dbf226] rounded-full text-[10px] font-black uppercase tracking-widest shadow-lg">
                {tag}
              </span>
            ))}
         </div>
      </GlassCard>

    </div>
  );
};

export default HowItWorks;

