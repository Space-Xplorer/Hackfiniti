import { useMemo } from 'react'
import { useShield } from '../context/ShieldContext'
import { AlertTriangle, TrendingUp, TrendingDown, Minus } from 'lucide-react'
import GlassCard from '../components/GlassCard'

// Human-readable labels + plain-English explanations for each feature
const FEATURE_META = {
  // Loan features
  credit_score:           { label: 'Credit Score',            explain: (v) => v > 0 ? 'Your credit history is strong, which significantly boosts approval confidence.' : 'A lower credit score reduces lender confidence in repayment.' },
  monthly_income:         { label: 'Monthly Income',          explain: (v) => v > 0 ? 'Your declared income comfortably supports the requested loan amount.' : 'Income appears insufficient relative to the loan size.' },
  emi_load:               { label: 'EMI Burden',              explain: (v) => v > 0 ? 'Your existing EMI obligations are low, leaving room for this loan.' : 'High existing EMIs reduce your repayment capacity (FOIR exceeded).' },
  loan_to_value:          { label: 'Loan-to-Value Ratio',     explain: (v) => v > 0 ? 'The property value provides strong collateral coverage.' : 'The loan amount is high relative to the property value (LTV risk).' },
  employment_stability:   { label: 'Employment Stability',    explain: (v) => v > 0 ? 'Stable employment history increases repayment reliability.' : 'Short tenure or frequent job changes raise repayment risk.' },
  debt_to_income:         { label: 'Debt-to-Income Ratio',    explain: (v) => v > 0 ? 'Your total debt is well within acceptable limits.' : 'Total debt obligations are high relative to your income.' },
  // Insurance features
  age:                    { label: 'Age',                     explain: (v) => v > 0 ? 'Your age falls in a lower-risk bracket, reducing premium.' : 'Older age increases actuarial risk, raising the premium estimate.' },
  smoker:                 { label: 'Smoking Status',          explain: (v) => v > 0 ? 'Non-smoker status significantly lowers your health risk profile.' : 'Smoking is a major risk factor and substantially increases premium.' },
  bmi:                    { label: 'BMI / Weight',            explain: (v) => v > 0 ? 'Your BMI is within a healthy range.' : 'BMI outside the healthy range increases health risk and premium.' },
  pre_existing_diseases:  { label: 'Pre-existing Conditions', explain: (v) => v > 0 ? 'No significant pre-existing conditions detected.' : 'Declared pre-existing conditions increase underwriting risk.' },
  family_history:         { label: 'Family Medical History',  explain: (v) => v > 0 ? 'No concerning family medical history reported.' : 'Family history of chronic illness raises long-term risk.' },
  sum_insured:            { label: 'Sum Insured',             explain: (v) => v > 0 ? 'The coverage amount is proportionate to your risk profile.' : 'High coverage relative to risk profile increases premium.' },
  // Fallback
  income:                 { label: 'Income',                  explain: (v) => v > 0 ? 'Income level supports the application.' : 'Income level is a limiting factor.' },
  weight:                 { label: 'Weight',                  explain: (v) => v > 0 ? 'Weight is within acceptable range.' : 'Weight raises health risk.' },
}

function getMeta(key) {
  return FEATURE_META[key] || {
    label: key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase()),
    explain: (v) => v > 0 ? 'This factor positively influenced the decision.' : 'This factor negatively influenced the decision.',
  }
}

const Result = () => {
  const { setView, service, workflowResult, workflowStatus, ocrPreviewData } = useShield()
  const isInsurance = service === 'insurance'
  const rejected = workflowStatus?.rejected || false
  const rejectionReason = workflowStatus?.rejection_reason
  const loanPrediction = workflowResult?.loan?.prediction
  const insurancePrediction = workflowResult?.insurance?.prediction
  const explanation = isInsurance ? workflowResult?.insurance?.explanation : workflowResult?.loan?.explanation
  const fallbackReason = rejectionReason || workflowStatus?.error

  const modelOutput = isInsurance ? workflowResult?.model_output?.insurance : workflowResult?.model_output?.loan
  const featureContributions = useMemo(() => {
    if (!modelOutput?.feature_contributions) return []
    return Object.entries(modelOutput.feature_contributions)
      .map(([key, value]) => ({ key, value: parseFloat(value), meta: getMeta(key) }))
      .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
  }, [modelOutput])

  const maxAbs = useMemo(() => Math.max(...featureContributions.map(f => Math.abs(f.value)), 0.01), [featureContributions])

  // OCR extracted summary — filter out internal _ keys
  const ocrSummary = useMemo(() => {
    if (!ocrPreviewData) return []
    const LABELS = {
      declared_monthly_income: 'Monthly Income',
      declared_existing_emi: 'Existing EMI',
      property_value: 'Property Value',
      employer_name: 'Employer',
      name: 'Name (ID)',
      dob: 'Date of Birth',
    }
    return Object.entries(LABELS)
      .filter(([k]) => ocrPreviewData[k])
      .map(([k, label]) => ({ label, value: ocrPreviewData[k] }))
  }, [ocrPreviewData])

  const ocrConfidence = ocrPreviewData?._ocr_status === 'success' ? ocrPreviewData?._ocr_confidence : null
  const ocrFlags = ocrPreviewData?._ocr_flags || []

  return (
    <div className="min-h-screen bg-[#f7faf9] py-12">
      <div className="max-w-3xl mx-auto px-4 space-y-6">

        {/* Hero decision card */}
        {rejected ? (
          <div className="bg-red-50 border border-red-200 rounded-3xl p-8">
            <h2 className="font-serif text-3xl font-bold text-red-700 mb-2" style={{ fontFamily: 'var(--font-serif)' }}>Application Not Approved</h2>
            {fallbackReason && <p className="text-red-600/80 text-sm leading-relaxed">{fallbackReason}</p>}
          </div>
        ) : isInsurance ? (
          <div className="bg-[#005b52] text-white rounded-3xl p-8">
            <p className="text-sm uppercase tracking-widest text-white/60 mb-1">Premium Estimate</p>
            <p className="text-5xl font-bold text-[#dbf226] mb-3">
              {insurancePrediction?.premium ? `₹ ${Number(insurancePrediction.premium).toLocaleString('en-IN')}` : 'Pending'}
            </p>
            <span className="bg-[#dbf226]/20 text-[#dbf226] border border-[#dbf226]/30 px-3 py-1 rounded-full text-sm font-mono font-bold">Health Risk Assessed</span>
          </div>
        ) : (
          <div className="bg-[#04221f] text-white rounded-3xl p-8">
            <h2 className="font-serif text-3xl font-bold mb-2" style={{ fontFamily: 'var(--font-serif)' }}>Loan Decision</h2>
            <p className="text-7xl font-bold text-[#dbf226] mb-3">
              {loanPrediction?.probability ? `${Math.round(Number(loanPrediction.probability) * 100)}%` : 'Pending'}
            </p>
            <span className="bg-[#dbf226]/20 text-[#dbf226] border border-[#dbf226]/30 px-3 py-1 rounded-full text-sm font-mono font-bold">
              {loanPrediction?.approved ? 'Approved' : 'Under Review'}
            </span>
            <p className="text-white/50 text-sm mt-3">Approval probability based on your risk profile</p>
          </div>
        )}

        {/* AI Explanation */}
        {!rejected && explanation && (
          <GlassCard className="p-6">
            <p className="text-xs font-bold uppercase tracking-widest text-[#005b52]/50 mb-2">AI Summary</p>
            <p className="text-[#04221f]/80 leading-relaxed text-sm">{explanation}</p>
          </GlassCard>
        )}

        {/* Feature explanations */}
        {!rejected && featureContributions.length > 0 && (
          <GlassCard className="p-6 space-y-5">
            <p className="text-xs font-bold uppercase tracking-widest text-[#005b52]/50">What drove this decision</p>
            {featureContributions.map(({ key, value, meta }) => {
              const pct = Math.round((Math.abs(value) / maxAbs) * 100)
              const positive = value > 0
              const neutral = Math.abs(value) < 0.03
              return (
                <div key={key} className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      {neutral
                        ? <Minus size={14} className="text-[#005b52]/40" />
                        : positive
                          ? <TrendingUp size={14} className="text-[#005b52]" />
                          : <TrendingDown size={14} className="text-red-500" />
                      }
                      <span className="text-sm font-semibold text-[#04221f]">{meta.label}</span>
                    </div>
                    <span className={`text-xs font-bold px-2 py-0.5 rounded-full ${
                      neutral ? 'bg-[#005b52]/10 text-[#005b52]/60'
                      : positive ? 'bg-[#005b52]/10 text-[#005b52]'
                      : 'bg-red-50 text-red-600'
                    }`}>
                      {positive ? '+' : ''}{value.toFixed(2)}
                    </span>
                  </div>
                  {/* Bar */}
                  <div className="h-2 w-full bg-[#005b52]/8 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-700"
                      style={{
                        width: `${pct}%`,
                        backgroundColor: neutral ? '#005b52' : positive ? '#005b52' : '#ef4444',
                        opacity: neutral ? 0.3 : 0.85,
                      }}
                    />
                  </div>
                  {/* Plain-English explanation */}
                  <p className="text-xs text-[#005b52]/60 leading-relaxed">{meta.explain(value)}</p>
                </div>
              )
            })}
          </GlassCard>
        )}

        {/* OCR extracted data summary */}
        {ocrSummary.length > 0 && (
          <GlassCard className="p-6">
            <div className="flex items-center justify-between mb-4">
              <p className="text-xs font-bold uppercase tracking-widest text-[#005b52]/50">OCR Extracted Data</p>
              {ocrConfidence && (
                <span className="text-xs bg-[#dbf226]/40 text-[#04221f] px-2 py-0.5 rounded-full font-semibold">
                  {Math.round(ocrConfidence * 100)}% confidence
                </span>
              )}
            </div>
            <div className="grid grid-cols-2 gap-3">
              {ocrSummary.map(({ label, value }) => (
                <div key={label} className="bg-[#f7faf9] rounded-xl px-4 py-3 border border-[#005b52]/10">
                  <p className="text-xs text-[#005b52]/50 font-medium mb-0.5">{label}</p>
                  <p className="text-sm font-semibold text-[#04221f]">
                    {typeof value === 'number' ? `₹ ${Number(value).toLocaleString('en-IN')}` : String(value)}
                  </p>
                </div>
              ))}
            </div>
            {ocrFlags.length > 0 && (
              <div className="mt-4 space-y-1.5">
                <p className="text-xs font-semibold text-amber-700 flex items-center gap-1"><AlertTriangle size={12} /> Document flags</p>
                {ocrFlags.map((f, i) => <p key={i} className="text-xs text-amber-600 pl-4">• {f}</p>)}
              </div>
            )}
          </GlassCard>
        )}

        <button
          onClick={() => setView('landing')}
          className="block mx-auto bg-[#04221f] text-white font-bold px-8 py-3 rounded-full hover:bg-[#dbf226] hover:text-[#04221f] transition-all duration-300 mt-4"
        >
          Start New Application
        </button>
      </div>
    </div>
  )
}

export default Result
