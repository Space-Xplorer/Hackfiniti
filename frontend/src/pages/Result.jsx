import React, { useMemo } from 'react';
import { useShield } from '../context/ShieldContext';
import { ShieldCheck, BrainCircuit, Sparkles, Activity, AlertTriangle } from 'lucide-react';

const Result = () => {
  const { setView, service, workflowResult, workflowStatus } = useShield();
  const isInsurance = service === 'insurance';
  const rejected = workflowStatus?.rejected || false;
  const rejectionReason = workflowStatus?.rejection_reason;
  const loanPrediction = workflowResult?.loan?.prediction;
  const insurancePrediction = workflowResult?.insurance?.prediction;
  const explanation = isInsurance
    ? workflowResult?.insurance?.explanation
    : workflowResult?.loan?.explanation;
  const description = isInsurance
    ? workflowResult?.insurance?.description
    : workflowResult?.loan?.description;
  const fallbackReason = rejectionReason || workflowStatus?.error;
  const advisoryFallback = fallbackReason
    ? `Rejected: ${fallbackReason} To improve approval odds, align your inputs with the rule thresholds (e.g., reduce loan amount, increase property value, or adjust declared income) and resubmit.`
    : null;

  const decisionLabel = rejected
    ? 'Rejected'
    : (isInsurance ? 'Approved' : (loanPrediction?.approved ? 'Approved' : 'Review'));
  const amountLabel = isInsurance ? 'Estimated Premium' : 'Approval Probability';
  const amountValue = isInsurance
    ? insurancePrediction?.premium
    : loanPrediction?.probability;

  // Extract feature contributions from model output
  const modelOutput = isInsurance 
    ? workflowResult?.model_output?.insurance 
    : workflowResult?.model_output?.loan;
  
  const featureContributions = useMemo(() => {
    if (!modelOutput?.feature_contributions) return [];
    
    const contributions = Object.entries(modelOutput.feature_contributions)
      .map(([name, value]) => ({
        name: name
          .replace(/_/g, ' ')
          .replace(/^\w/, c => c.toUpperCase()),
        value: parseFloat(value),
        absValue: Math.abs(parseFloat(value))
      }))
      .sort((a, b) => b.absValue - a.absValue)
      .slice(0, 3);
    
    return contributions;
  }, [modelOutput]);

  const rawModelExplanation = modelOutput?.feature_contributions
    ? Object.entries(modelOutput.feature_contributions).map(([name, value]) => (
        `${name}: ${value}`
      ))
    : null;

  // Calculate normalized percentages for visualization (0-100%)
  const maxContribution = useMemo(() => {
    if (featureContributions.length === 0) return 1;
    return Math.max(...featureContributions.map(c => c.absValue));
  }, [featureContributions]);

  const normalizeToPercent = (value) => {
    if (maxContribution === 0) return 50;
    const normalized = (Math.abs(value) / maxContribution) * 100;
    return Math.min(Math.max(normalized, 5), 100); // Keep between 5-100% for visibility
  };

  // Get OCR confidence warnings
  const ocrConfidenceScores = workflowResult?.ocr_confidence_scores || {};
  const flaggedDocuments = useMemo(() => {
    return Object.entries(ocrConfidenceScores)
      .filter(([_, confidence]) => confidence < 50)
      .map(([docType, confidence]) => ({
        name: docType.replace(/_/g, ' ').toUpperCase(),
        confidence
      }));
  }, [ocrConfidenceScores]);

  return (
    <div className="max-w-4xl mx-auto py-6 px-6 animate-in zoom-in-95">
      <div className="glass-card rounded-[4rem] p-10 border-b-16 border-[#F4C2C2]">
        <div className="flex justify-center mb-8">
          <div className="bg-[#4B0082] text-[#F4C2C2] px-6 py-2 rounded-full text-[10px] font-black uppercase tracking-[0.3em] flex items-center gap-3 shadow-lg">
            <ShieldCheck size={20} /> Daksha Verified
          </div>
        </div>

        <div className="text-center mb-8">
          <h2 className="text-6xl font-black text-[#4B0082] tracking-tighter italic mb-2 uppercase">{decisionLabel}</h2>
          <p className="text-xs font-black uppercase tracking-[0.6em] text-slate-400">Total Shield Level: Optimal</p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          <div className="bg-white/50 p-8 rounded-[3rem] border border-white">
            <h5 className="font-black text-[#4B0082] flex items-center gap-3 mb-6 italic"><BrainCircuit size={20} /> EBM Reasoning Trace</h5>
            <div className="space-y-6">
              {featureContributions.length > 0 ? (
                featureContributions.map((feature, i) => (
                  <div key={i}>
                    <div className="flex justify-between text-[9px] font-black uppercase text-slate-400 mb-2">
                      <span>{feature.name}</span>
                      <span>{normalizeToPercent(feature.value).toFixed(0)}%</span>
                    </div>
                    <div className="h-2 w-full bg-slate-100 rounded-full overflow-hidden">
                      <div 
                        className="h-full transition-all duration-1000" 
                        style={{
                          width: `${normalizeToPercent(feature.value)}%`,
                          backgroundColor: feature.value > 0 ? '#4B0082' : '#F4C2C2'
                        }} 
                      />
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-xs text-slate-400">Feature contributions not available</p>
              )}
            </div>

            {/* OCR Confidence Warnings */}
            {flaggedDocuments.length > 0 && (
              <div className="mt-8 pt-6 border-t border-slate-200">
                <div className="space-y-3">
                  {flaggedDocuments.map((doc, i) => (
                    <div key={i} className="flex items-start gap-3 p-3 bg-amber-50 rounded-lg border border-amber-200">
                      <AlertTriangle size={16} className="text-amber-600 flex-shrink-0 mt-0.5" />
                      <div className="text-xs">
                        <p className="font-bold text-amber-900">{doc.name}</p>
                        <p className="text-amber-700">OCR confidence: {doc.confidence.toFixed(0)}% - Low confidence detected</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="space-y-4">
            <div className="p-6 bg-white/80 rounded-[3rem] border border-white">
              <div className="flex items-center gap-3 mb-4"><Activity className="text-[#4B0082]" /><h6 className="font-black text-[#4B0082] italic">Daksha Advisor</h6></div>
              <p className="text-sm text-slate-500 font-medium leading-relaxed italic">
                {explanation || advisoryFallback || 'Decision explanation will appear here once the workflow completes.'}
              </p>
            </div>
            <div className="p-6 bg-white/80 rounded-[3rem] border border-white">
              <div className="flex items-center gap-3 mb-4"><Sparkles className="text-[#4B0082]" /><h6 className="font-black text-[#4B0082] italic">Decision Description</h6></div>
              {description ? (
                <p className="text-sm text-slate-500 font-medium leading-relaxed italic">
                  {description}
                </p>
              ) : (
                <p className="text-sm text-slate-500 font-medium leading-relaxed italic">
                  {advisoryFallback || 'Decision description will appear here once the workflow completes.'}
                </p>
              )}
              {rawModelExplanation ? (
                <ul className="mt-3 text-sm text-slate-500 font-medium leading-relaxed italic list-disc pl-5 space-y-1">
                  {rawModelExplanation.map((item, index) => (
                    <li key={index}>{item}</li>
                  ))}
                </ul>
              ) : null}
            </div>
            <div className="p-6 bg-[#4B0082] text-white rounded-[3rem] shadow-xl">
              <p className="text-[10px] font-black uppercase tracking-widest opacity-60">
                 {amountLabel}
              </p>
               <p className="text-4xl font-black italic">
                 {amountValue
                   ? (isInsurance ? `₹ ${Number(amountValue).toFixed(0)}` : `${Math.round(Number(amountValue) * 100)}%`)
                   : 'Pending'}
               </p>
            </div>
          </div>
        </div>

        {rejected && rejectionReason ? (
          <div className="mt-10 bg-red-50 border border-red-100 text-red-600 rounded-4xl p-6 text-xs font-bold uppercase tracking-widest text-center">
            {rejectionReason}
          </div>
        ) : null}

        <button onClick={() => setView('landing')} className="w-full mt-8 py-6 bg-[#FAF9F6] border-2 border-[#4B0082]/10 text-[#4B0082] rounded-[2.5rem] font-black uppercase tracking-widest text-xs hover:bg-white transition-all">Return to Lobby</button>
      </div>
    </div>
  );
};

export default Result;