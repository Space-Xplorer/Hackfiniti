import React from 'react';
import { useShield } from '../context/ShieldContext';
import { Landmark, Heart, ChevronRight } from 'lucide-react';

const Selection = () => {
  const { setView, setService, userData } = useShield();

const handleSelect = (type) => {
  setService(type);
  setView('prelim');
};

  return (
    <div className="max-w-4xl mx-auto py-6 px-6 animate-in slide-in-from-bottom-10">
      <div className="text-center mb-8">
        <h2 className="text-4xl font-black text-[#4B0082] tracking-tighter italic">Hi, {userData.name}!</h2>
        <p className="text-[10px] font-black uppercase tracking-[0.4em] text-slate-400 mt-2">Choose your protection shield</p>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        <div onClick={() => handleSelect('loan')} className="group glass-card p-8 rounded-[4rem] text-center cursor-pointer hover:border-[#4B0082] transition-all relative overflow-hidden">
          <div className="w-16 h-16 bg-[#F4C2C2] rounded-3xl flex items-center justify-center mx-auto mb-6 text-[#4B0082] group-hover:scale-110 transition shadow-sm"><Landmark size={34} /></div>
          <h3 className="text-2xl font-black text-[#4B0082] mb-4">Loan Shield</h3>
          <p className="text-slate-400 text-sm font-medium mb-6">Verify credit health and cash-flow roadmaps.</p>
          <ChevronRight className="mx-auto text-[#F4C2C2]" />
        </div>

        <div onClick={() => handleSelect('insurance')} className="group glass-card p-8 rounded-[4rem] text-center cursor-pointer hover:border-[#4B0082] transition-all relative overflow-hidden">
          <div className="w-16 h-16 bg-[#4B0082] rounded-3xl flex items-center justify-center mx-auto mb-6 text-[#F4C2C2] group-hover:scale-110 transition shadow-sm"><Heart size={34} /></div>
          <h3 className="text-2xl font-black text-[#4B0082] mb-4">Life Shield</h3>
          <p className="text-slate-400 text-sm font-medium mb-6">Assess biomarkers and life premiums.</p>
          <ChevronRight className="mx-auto text-[#F4C2C2]" />
        </div>
      </div>
    </div>
  );
};

export default Selection;
