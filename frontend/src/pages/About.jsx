import React from 'react';
import { 
  Shield, Target, Users, Zap, Heart, 
  Code2, Sparkles, Milestone, ArrowUpRight 
} from 'lucide-react';
import GlassCard from '../components/GlassCard';

const About = () => {
  const values = [
    { 
      title: "Eliminating Bias", 
      desc: "Legacy AI rejections often stem from 'Black Box' correlations. We use EBMs to ensure every decision is rooted in explainable, ethical math.",
      icon: <Target className="text-[#dbf226]" /> 
    },
    { 
      title: "Financial Inclusion", 
      desc: "Over 190M Indians are credit-invisible. We bridge this gap by verifying alternative data through autonomous agents.",
      icon: <Users className="text-[#dbf226]" /> 
    },
    { 
      title: "Radical Transparency", 
      desc: "A 'No' without a 'Why' is a failure. Daksha provides a roadmap for every user, turning rejection into a growth strategy.",
      icon: <Sparkles className="text-[#dbf226]" /> 
    }
  ];

  return (
    <div className="min-h-screen bg-[#f7faf9] px-6 py-12 max-w-6xl mx-auto">
      
      {/* --- HERO SECTION --- */}
      <div className="text-center mb-20 relative">
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-64 h-64 bg-[#dbf226]/20/10 blur-[100px] -z-10" />
        <span className="text-[10px] font-black text-[#04221f] bg-[#dbf226]/20 px-4 py-1 rounded-full uppercase tracking-[0.3em] mb-8 inline-block shadow-sm">
          The Genesis
        </span>
        <h2 className="text-[6.5vw] lg:text-[4.5vw] font-black text-[#04221f] tracking-tighter italic leading-none mb-6">
          TRUST THROUGH<br /><span className="text-transparent bg-clip-text bg-gradient-to-r from-[#4B0082] via-[#6A0DAD] to-[#4B0082] bg-[length:200%_auto] animate-[shine_3s_linear_infinite]">EXPLAINABILITY.</span>
        </h2>
        <p className="text-lg text-slate-500 font-medium max-w-3xl mx-auto leading-relaxed">
          Daksha started as a challenge: Could we make AI as transparent as a human auditor? Today, itΓÇÖs a multi-agent framework designed to protect and empower the Indian consumer.
        </p>
      </div>

      {/* --- MISSION CORE --- */}
      <div className="grid lg:grid-cols-3 gap-8 mb-24">
        {values.map((val, i) => (
          <GlassCard key={i} className="p-8 border-b-8 border-[#005b52]/10 hover:border-[#005b52] transition-all duration-500 group">
            <div className="w-14 h-14 bg-[#04221f] rounded-2xl flex items-center justify-center mb-8 shadow-lg group-hover:rotate-6 transition-transform">
              {val.icon}
            </div>
            <h4 className="text-xl font-black text-[#04221f] mb-4 uppercase italic">{val.title}</h4>
            <p className="text-sm text-slate-500 leading-relaxed font-medium">
              {val.desc}
            </p>
          </GlassCard>
        ))}
      </div>

      {/* --- THE STUDENT VISION (Personal Touch) --- */}
      <div className="grid lg:grid-cols-2 gap-12 items-center mb-24">
        <div className="relative">
           <div className="absolute -inset-4 bg-[#dbf226]/20/20 rounded-[4rem] blur-2xl rotate-3" />
           <div className="bg-[#04221f] rounded-[3.5rem] p-8 text-[#dbf226] relative overflow-hidden">
              <Code2 size={40} className="mb-8 opacity-50" />
              <h3 className="text-2xl font-black italic mb-4 text-white">Built by Engineers,<br />for the People.</h3>
              <p className="text-base font-medium leading-relaxed opacity-90 text-pink-50 mb-6">
                "We didn't just want to build another model. We wanted to build a 'Guardian' (Daksha) that stands between the user and the complexities of modern underwriting."
              </p>
              <div className="flex items-center gap-4">
                 <div className="w-12 h-12 rounded-full bg-white/20 backdrop-blur-md border border-white/30" />
                 <div>
                    <p className="text-sm font-black uppercase tracking-widest text-white">Project Daksha Team</p>
                    <p className="text-[10px] font-bold uppercase tracking-widest opacity-60">Engineering Excellence '26</p>
                 </div>
              </div>
           </div>
        </div>
        <div>
            <h3 className="text-3xl font-black text-[#04221f] italic tracking-tighter mb-6 underline decoration-[#F4C2C2] underline-offset-8">Why EBM?</h3>
            <p className="text-slate-500 font-medium mb-6 leading-relaxed">
              Standard neural networks are 'Black Boxes'. If they reject you, nobody knows why. We chose **Explainable Boosting Machines (EBM)** because they are 'Glass Boxes' by nature. 
           </p>
           <ul className="space-y-4">
              {[
                "100% Intrinsic Transparency",
                "Regulatory-Ready Explanations",
                "Mathematically Isolated Features",
                "Bias-Aware Risk Modeling"
              ].map((item, i) => (
                <li key={i} className="flex items-center gap-3 text-xs font-black uppercase tracking-widest text-[#04221f]">
                   <div className="w-1.5 h-1.5 bg-[#dbf226]/20 rounded-full" /> {item}
                </li>
              ))}
           </ul>
        </div>
      </div>

      {/* --- ROADMAP / TIMELINE --- */}
      <div className="text-center mb-16">
        <h3 className="text-3xl font-black text-[#04221f] italic mb-10 uppercase tracking-widest">Our Evolution</h3>
        <div className="grid md:grid-cols-4 gap-4 relative">
          <div className="absolute top-1/2 left-0 w-full h-0.5 bg-slate-100 -z-10 hidden md:block" />
          {[
            { label: "Conceptualization", date: "Phase 1" },
            { label: "EBM Engine Dev", date: "Phase 2" },
            { label: "Agentic Integration", date: "Phase 3" },
            { label: "Nexus Launch", date: "Current" }
          ].map((item, i) => (
            <div key={i} className="bg-white p-4 rounded-3xl border border-slate-100 shadow-sm hover:shadow-md transition-shadow">
               <p className="text-[9px] font-black text-[#dbf226] uppercase mb-2">{item.date}</p>
               <p className="text-xs font-black text-[#04221f] uppercase">{item.label}</p>
            </div>
          ))}
        </div>
      </div>

      {/* --- CALL TO ACTION --- */}
      <GlassCard className="p-10 text-center border-t-4 border-[#dbf226]">
         <Heart className="text-[#04221f] mx-auto mb-8 animate-pulse" fill="#F4C2C2" size={40} />
        <h3 className="text-3xl font-black text-[#04221f] italic tracking-tighter mb-4 uppercase">Ready to join the Mission?</h3>
         <div className="flex justify-center gap-6">
          <button onClick={() => window.scrollTo(0,0)} className="bg-[#04221f] text-[#dbf226] border-2 border-[#005b52] px-8 py-4 rounded-full font-black uppercase tracking-widest text-xs shadow-xl">
               Back to Top
            </button>
            <button className="text-[10px] font-black uppercase tracking-[0.4em] text-[#04221f] flex items-center gap-2 hover:gap-4 transition-all">
               View GitHub Repo <ArrowUpRight size={16} />
            </button>
         </div>
      </GlassCard>

      <style>{`
        @keyframes shine { to { background-position: 200% center; } }
      `}</style>
    </div>
  );
};

export default About;

