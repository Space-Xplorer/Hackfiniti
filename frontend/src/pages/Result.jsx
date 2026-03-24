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
    <div className="min-h-screen bg-[#f7faf9] py-16 pt-32">
      <div className="max-w-4xl mx-auto px-6 space-y-8">

        {/* Decision Card */}
        {rejected ? (
          <div className="rounded-3xl p-10 md:p-14 bg-gradient-to-br from-red-50 to-red-50/50 border border-red-200/50 shadow-lg">
            <div className="flex items-start gap-4 mb-4">
              <div className="w-12 h-12 rounded-full bg-red-100 flex items-center justify-center shrink-0">
                <AlertTriangle size={24} className="text-red-600" />
              </div>
              <div>
                <h2 className="font-serif text-3xl md:text-4xl font-bold text-red-700 mb-2" style={{ fontFamily: 'var(--font-serif)' }}>
                  Application Not Approved
                </h2>
                {fallbackReason && <p className="text-red-600/80 text-base leading-relaxed">{fallbackReason}</p>}
              </div>
            </div>
          </div>
        ) : isInsurance ? (
          <div className="rounded-3xl p-10 md:p-14 bg-gradient-to-br from-[#005b52] to-[#005b52]/90 text-white shadow-2xl">
            <div className="flex flex-col gap-6">
              <div>
                <p className="text-sm uppercase tracking-widest text-white/60 font-semibold mb-3">Premium Estimate</p>
                <p className="text-6xl md:text-7xl font-bold text-[#dbf226] font-serif mb-4" style={{ fontFamily: 'var(--font-serif)' }}>
                  {insurancePrediction?.premium ? `₹ ${Number(insurancePrediction.premium).toLocaleString('en-IN')}` : 'Calculating…'}
                </p>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 rounded-full bg-[#dbf226]" />
                <span className="text-sm font-semibold text-white/70">Health Risk Assessment Complete</span>
              </div>
            </div>
          </div>
        ) : (
          <div className="rounded-3xl p-10 md:p-14 bg-gradient-to-br from-[#04221f] to-[#04221f]/95 text-white shadow-2xl">
            <div className="flex flex-col gap-6">
              <div>
                <p className="text-sm uppercase tracking-widest text-white/60 font-semibold mb-2">Approval Status</p>
                <h2 className="font-serif text-3xl md:text-4xl font-bold text-white mb-4" style={{ fontFamily: 'var(--font-serif)' }}>
                  {loanPrediction?.approved ? 'Approved' : 'Under Review'}
                </h2>
                <p className="text-7xl md:text-8xl font-bold text-[#dbf226] font-serif" style={{ fontFamily: 'var(--font-serif)' }}>
                  {loanPrediction?.probability ? `${Math.round(Number(loanPrediction.probability) * 100)}%` : '—'}
                </p>
              </div>
              <div className="flex items-center gap-3 pt-2">
                <div className="w-3 h-3 rounded-full bg-[#dbf226]" />
                <span className="text-sm font-semibold text-white/70">Approval confidence based on risk profile</span>
              </div>
            </div>
          </div>
        )}

        {/* AI Explanation */}
        {!rejected && explanation && (
          <div className="rounded-3xl p-8 bg-white border border-[#005b52]/10 shadow-md">
            <p className="text-xs font-bold uppercase tracking-widest text-[#005b52]/60 mb-4">Why This Decision</p>
            <p className="text-[#04221f]/80 leading-relaxed text-base">{explanation}</p>
          </div>
        )}

        {/* Feature Contributions */}
        {!rejected && featureContributions.length > 0 && (
          <div className="rounded-3xl p-8 bg-white border border-[#005b52]/10 shadow-md">
            <p className="text-xs font-bold uppercase tracking-widest text-[#005b52]/60 mb-8">What Influenced This Decision</p>
            <div className="space-y-6">
              {featureContributions.map(({ key, value, meta }) => {
                const pct = Math.round((Math.abs(value) / maxAbs) * 100)
                const positive = value > 0
                const neutral = Math.abs(value) < 0.03
                return (
                  <div key={key} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-3 min-w-0">
                        {neutral
                          ? <Minus size={16} className="text-[#005b52]/40 shrink-0" />
                          : positive
                            ? <TrendingUp size={16} className="text-[#005b52] shrink-0" />
                            : <TrendingDown size={16} className="text-red-500 shrink-0" />
                        }
                        <span className="text-sm font-semibold text-[#04221f]">{meta.label}</span>
                      </div>
                      <span className={`text-xs font-bold px-3 py-1 rounded-full shrink-0 ${
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
                    {/* Explanation */}
                    <p className="text-xs text-[#005b52]/60 leading-relaxed pl-6">{meta.explain(value)}</p>
                  </div>
                )
              })}
            </div>
          </div>
        )}

        {/* OCR Data Summary */}
        {ocrSummary.length > 0 && (
          <div className="rounded-3xl p-8 bg-white border border-[#005b52]/10 shadow-md">
            <div className="flex items-center justify-between mb-6">
              <p className="text-xs font-bold uppercase tracking-widest text-[#005b52]/60">Document Data Extracted</p>
              {ocrConfidence && (
                <span className="text-xs bg-[#005b52]/10 text-[#005b52] px-3 py-1 rounded-full font-semibold">
                  {Math.round(ocrConfidence * 100)}% confidence
                </span>
              )}
            </div>
            <div className="grid grid-cols-2 gap-4 mb-6">
              {ocrSummary.map(({ label, value }) => (
                <div key={label} className="rounded-2xl px-4 py-4 bg-[#f7faf9] border border-[#005b52]/5">
                  <p className="text-xs text-[#005b52]/50 font-semibold mb-1.5">{label}</p>
                  <p className="text-sm font-bold text-[#04221f]">
                    {typeof value === 'number' ? `₹ ${Number(value).toLocaleString('en-IN')}` : String(value)}
                  </p>
                </div>
              ))}
            </div>
            {ocrFlags.length > 0 && (
              <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200/50">
                <p className="text-xs font-semibold text-amber-700 flex items-center gap-2 mb-3">
                  <AlertTriangle size={14} /> Document Flags
                </p>
                <ul className="space-y-1.5">
                  {ocrFlags.map((f, i) => <li key={i} className="text-xs text-amber-600 pl-5">• {f}</li>)}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Action Button */}
        <div className="text-center pt-4">
          <button
            onClick={() => setView('landing')}
            className="bg-[#04221f] text-white font-bold px-8 py-3 rounded-full hover:bg-[#dbf226] hover:text-[#04221f] hover:-translate-y-0.5 transition-all duration-300 shadow-md hover:shadow-lg"
          >
            Start New Application
          </button>
        </div>
      </div>
    </div>
  )
}

export default Result
