import { useState, useEffect } from 'react'
import { useShield } from '../context/ShieldContext'
import { ArrowLeft } from 'lucide-react'
import GlassCard from '../components/GlassCard'

const pedOptions = [
  'Diabetes',
  'Hypertension',
  'Asthma',
  'Cardiac',
  'Thyroid',
  'None'
];

const Config = () => {
  const { setView, service, userData, setUserData, applicantData, setApplicantData, loanType, setLoanType, ocrPreviewData, kycData } = useShield();
  // Track which fields were populated by OCR
  const ocrFields = new Set(Object.keys(ocrPreviewData).filter(k => !k.startsWith('_') && ocrPreviewData[k]))
  const [formData, setFormData] = useState({
    loan_type: loanType || 'home',
    employment_type: 'Salaried',
    employer_category: 'MNC',
    alcohol: 'None',
    smoker: 'No',
    pre_existing_diseases: [],
    ...kycData,
    ...applicantData,
    ...ocrPreviewData
  });
  const [formError, setFormError] = useState('');

  // Update form data when OCR preview data or KYC data changes
  useEffect(() => {
    if (Object.keys(ocrPreviewData).length > 0 || Object.keys(kycData).length > 0) {
      console.log('Updating form data with:', { kycData, ocrPreviewData });
      setFormData(prev => ({
        ...prev,
        ...kycData,
        ...ocrPreviewData
      }));
    }
  }, [ocrPreviewData, kycData]);

  useEffect(() => {
    console.log('Config form data:', formData);
  }, [formData]);

  const updateField = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const togglePed = (value) => {
    setFormData((prev) => {
      const current = prev.pre_existing_diseases || [];
      if (value === 'None') {
        return { ...prev, pre_existing_diseases: ['None'] };
      }
      const next = current.includes(value)
        ? current.filter((item) => item !== value)
        : [...current.filter((item) => item !== 'None'), value];
      return { ...prev, pre_existing_diseases: next };
    });
  };

  const handleNext = () => {
    setFormError('');

    if (service === 'loan') {
      const requiredFields = ['age', 'gender', 'city', 'loan_type', 'loan_amount_requested', 'tenure_months', 'declared_monthly_income', 'declared_existing_emi'];
      const missing = requiredFields.filter((field) => !formData[field] && formData[field] !== 0);
      if (missing.length) {
        setFormError('Please complete all required fields before continuing.');
        return;
      }
      if (formData.loan_type) {
        setLoanType(formData.loan_type);
      }
    }

    if (service === 'insurance') {
      const requiredFields = ['age', 'gender', 'city', 'height', 'weight', 'sum_insured'];
      const missing = requiredFields.filter((field) => !formData[field] && formData[field] !== 0);
      if (missing.length) {
        setFormError('Please complete all required fields before continuing.');
        return;
      }
    }

    setUserData({ ...userData, ...formData });
    setApplicantData({ ...applicantData, ...formData });
    setView('analysis');
  };

  return (
    <div className="min-h-screen bg-[#f7faf9]">
      <div className="max-w-2xl mx-auto px-4 py-12">
        <button onClick={() => setView('upload')} className="flex items-center gap-2 text-sm text-[#005b52]/60 hover:text-[#005b52] mb-6 transition-colors">
          <ArrowLeft size={16} /> Back
        </button>
        <GlassCard className="p-8 space-y-6">
          <div>
            <h2 className="font-serif text-3xl font-bold text-[#04221f]" style={{ fontFamily: 'var(--font-serif)' }}>Declaration Form</h2>
            <p className="text-[#005b52]/70 mt-1">
              Confirm your details
              {ocrPreviewData._ocr_confidence && (
                <span className="ml-2 text-xs bg-[#dbf226]/30 text-[#04221f] px-2 py-0.5 rounded-full font-medium">
                  OCR confidence: {Math.round(ocrPreviewData._ocr_confidence * 100)}%
                </span>
              )}
            </p>
            {ocrPreviewData._ocr_flags?.length > 0 && (
              <div className="mt-3 bg-amber-50 border border-amber-200 rounded-xl p-3 text-xs text-amber-700 space-y-1">
                <p className="font-semibold">⚠ Document flags from OCR scan:</p>
                {ocrPreviewData._ocr_flags.map((f, i) => <p key={i}>• {f}</p>)}
              </div>
            )}
          </div>
          <div className="space-y-8">
          {service === 'loan' ? (
            <div className="space-y-8">
              <div>
                <h3 className="text-xs font-bold uppercase tracking-widest text-[#005b52]/50 mb-4 border-b border-[#005b52]/10 pb-2">Personal Profile</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  <Field label="Age" required>
                    <input
                      type="number"
                      value={formData.age || ''}
                      onChange={(e) => updateField('age', Number(e.target.value) || '')}
                      className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                    />
                  </Field>
                  <Field label="Gender" required>
                    <select
                      value={formData.gender || ''}
                      onChange={(e) => updateField('gender', e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                    >
                      <option value="">Select gender</option>
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                      <option value="Other">Other</option>
                    </select>
                  </Field>
                  <Field label="City" required>
                    <input
                      type="text"
                      value={formData.city || ''}
                      onChange={(e) => updateField('city', e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                    />
                  </Field>
                  <Field label="Marital Status">
                    <input
                      type="text"
                      value={formData.marital_status || ''}
                      onChange={(e) => updateField('marital_status', e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                    />
                  </Field>
                  <Field label="Employment Type">
                    <select
                      value={formData.employment_type || 'Salaried'}
                      onChange={(e) => updateField('employment_type', e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                    >
                      <option value="Salaried">Salaried</option>
                      <option value="Self-employed">Self-employed</option>
                    </select>
                  </Field>
                  <Field label="Employer Category">
                    <select
                      value={formData.employer_category || 'MNC'}
                      onChange={(e) => updateField('employer_category', e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                    >
                      <option value="Govt">Govt</option>
                      <option value="MNC">MNC</option>
                      <option value="Pvt Ltd">Pvt Ltd</option>
                      <option value="Small firm">Small firm</option>
                    </select>
                  </Field>
                  <Field label="Total Work Experience (years)">
                    <input
                      type="number"
                      value={formData.total_work_experience || ''}
                      onChange={(e) => updateField('total_work_experience', Number(e.target.value) || '')}
                      className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                    />
                  </Field>
                  <Field label="Current Company Tenure (years)">
                    <input
                      type="number"
                      value={formData.current_company_tenure || ''}
                      onChange={(e) => updateField('current_company_tenure', Number(e.target.value) || '')}
                      className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                    />
                  </Field>
                  <Field label="Residential Status">
                    <input
                      type="text"
                      value={formData.residential_status || ''}
                      onChange={(e) => updateField('residential_status', e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                    />
                  </Field>
                </div>
              </div>

              <div>
                <h3 className="text-xs font-bold uppercase tracking-widest text-[#005b52]/50 mb-4 border-b border-[#005b52]/10 pb-2">Loan Details</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  <Field label="Loan Type" required>
                    <select
                      value={formData.loan_type || 'home'}
                      onChange={(e) => updateField('loan_type', e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                    >
                      <option value="home">Home</option>
                      <option value="personal">Personal</option>
                    </select>
                  </Field>
                  <Field label="Loan Amount Requested" required>
                    <input
                      type="number"
                      value={formData.loan_amount_requested || ''}
                      onChange={(e) => updateField('loan_amount_requested', Number(e.target.value) || '')}
                      className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                    />
                  </Field>
                  <Field label="Tenure (months)" required>
                    <input
                      type="number"
                      value={formData.tenure_months || ''}
                      onChange={(e) => updateField('tenure_months', Number(e.target.value) || '')}
                      className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                    />
                  </Field>
                  {formData.loan_type === 'home' ? (
                    <>
                      <Field label="Property Value" ocr={ocrFields.has('property_value')}>
                        <input
                          type="number"
                          value={formData.property_value || ''}
                          onChange={(e) => updateField('property_value', Number(e.target.value) || '')}
                          className={`w-full px-4 py-3 rounded-xl border bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all ${ocrFields.has('property_value') ? 'border-[#dbf226] bg-[#dbf226]/5' : 'border-[#005b52]/20'}`}
                        />
                      </Field>
                      <Field label="Property City">
                        <input
                          type="text"
                          value={formData.property_city || ''}
                          onChange={(e) => updateField('property_city', e.target.value)}
                          className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                        />
                      </Field>
                      <Field label="Property Type">
                        <input
                          type="text"
                          value={formData.property_type || ''}
                          onChange={(e) => updateField('property_type', e.target.value)}
                          className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                        />
                      </Field>
                    </>
                  ) : null}
                </div>
              </div>

              <div>
                <h3 className="text-xs font-bold uppercase tracking-widest text-[#005b52]/50 mb-4 border-b border-[#005b52]/10 pb-2">Financial Declaration</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  <Field label="Declared Monthly Income" required ocr={ocrFields.has('declared_monthly_income')}>
                    <input
                      type="number"
                      value={formData.declared_monthly_income || ''}
                      onChange={(e) => updateField('declared_monthly_income', Number(e.target.value) || '')}
                      className={`w-full px-4 py-3 rounded-xl border bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all ${ocrFields.has('declared_monthly_income') ? 'border-[#dbf226] bg-[#dbf226]/5' : 'border-[#005b52]/20'}`}
                    />
                  </Field>
                  <Field label="Declared Existing EMI" required ocr={ocrFields.has('declared_existing_emi')}>
                    <input
                      type="number"
                      value={formData.declared_existing_emi || ''}
                      onChange={(e) => updateField('declared_existing_emi', Number(e.target.value) || '')}
                      className={`w-full px-4 py-3 rounded-xl border bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all ${ocrFields.has('declared_existing_emi') ? 'border-[#dbf226] bg-[#dbf226]/5' : 'border-[#005b52]/20'}`}
                    />
                  </Field>
                  <Field label="Credit Score (mock)" required>
                    <input
                      type="number"
                      value={formData.credit_score || ''}
                      onChange={(e) => updateField('credit_score', Number(e.target.value) || '')}
                      className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                    />
                  </Field>
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-8">
              <div>
                <h3 className="text-xs font-bold uppercase tracking-widest text-[#005b52]/50 mb-4 border-b border-[#005b52]/10 pb-2">Health Profile</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  <Field label="Age" required>
                    <input
                      type="number"
                      value={formData.age || ''}
                      onChange={(e) => updateField('age', Number(e.target.value) || '')}
                      className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                    />
                  </Field>
                  <Field label="Gender" required>
                    <select
                      value={formData.gender || ''}
                      onChange={(e) => updateField('gender', e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                    >
                      <option value="">Select gender</option>
                      <option value="Male">Male</option>
                      <option value="Female">Female</option>
                      <option value="Other">Other</option>
                    </select>
                  </Field>
                  <Field label="City" required>
                    <input
                      type="text"
                      value={formData.city || ''}
                      onChange={(e) => updateField('city', e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                    />
                  </Field>
                  <Field label="Family Size">
                    <input
                      type="number"
                      value={formData.family_size || ''}
                      onChange={(e) => updateField('family_size', Number(e.target.value) || '')}
                      className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                    />
                  </Field>
                  <Field label="Height (cm)" required>
                    <input
                      type="number"
                      value={formData.height || ''}
                      onChange={(e) => updateField('height', Number(e.target.value) || '')}
                      className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                    />
                  </Field>
                  <Field label="Weight (kg)" required>
                    <input
                      type="number"
                      value={formData.weight || ''}
                      onChange={(e) => updateField('weight', Number(e.target.value) || '')}
                      className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                    />
                  </Field>
                  <Field label="Smoker">
                    <select
                      value={formData.smoker || 'No'}
                      onChange={(e) => updateField('smoker', e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                    >
                      <option value="No">No</option>
                      <option value="Yes">Yes</option>
                    </select>
                  </Field>
                  <Field label="Alcohol">
                    <select
                      value={formData.alcohol || 'None'}
                      onChange={(e) => updateField('alcohol', e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                    >
                      <option value="None">None</option>
                      <option value="Moderate">Moderate</option>
                      <option value="High">High</option>
                    </select>
                  </Field>
                </div>
              </div>

              <div>
                <h3 className="text-xs font-bold uppercase tracking-widest text-[#005b52]/50 mb-4 border-b border-[#005b52]/10 pb-2">Medical History</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  <Field label="Pre-existing Diseases">
                    <div className="grid grid-cols-2 gap-3">
                      {pedOptions.map((option) => (
                        <label key={option} className="flex items-center gap-2 text-xs font-bold text-[#4B0082]">
                          <input
                            type="checkbox"
                            checked={(formData.pre_existing_diseases || []).includes(option)}
                            onChange={() => togglePed(option)}
                            className="accent-[#4B0082]"
                          />
                          {option}
                        </label>
                      ))}
                    </div>
                  </Field>
                  <Field label="Family History">
                    <input
                      type="text"
                      value={formData.family_history || ''}
                      onChange={(e) => updateField('family_history', e.target.value)}
                      className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                    />
                  </Field>
                </div>
              </div>

              <div>
                <h3 className="text-xs font-bold uppercase tracking-widest text-[#005b52]/50 mb-4 border-b border-[#005b52]/10 pb-2">Coverage</h3>
                <div className="grid md:grid-cols-2 gap-4">
                  <Field label="Sum Insured" required>
                    <input
                      type="number"
                      value={formData.sum_insured || ''}
                      onChange={(e) => updateField('sum_insured', Number(e.target.value) || '')}
                      className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                    />
                  </Field>
                  <Field label="Deductible">
                    <input
                      type="number"
                      value={formData.deductible || ''}
                      onChange={(e) => updateField('deductible', Number(e.target.value) || '')}
                      className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                    />
                  </Field>
                </div>
              </div>
            </div>
          )}

          {formError && (
            <div className="text-red-700 bg-red-50 border border-red-200 p-3 rounded-xl text-sm text-center">{formError}</div>
          )}

          <button
            onClick={handleNext}
            className="w-full bg-[#04221f] text-white font-bold py-3 rounded-full hover:bg-[#dbf226] hover:text-[#04221f] hover:-translate-y-0.5 transition-all duration-300 shadow-[0_4px_14px_rgba(4,34,31,0.2)]"
          >
            Confirm Details & Proceed
          </button>
          </div>
        </GlassCard>
      </div>
    </div>
  )
}

const Field = ({ label, required, ocr, children }) => (
  <div className="space-y-1">
    <label className="text-sm font-medium text-[#005b52] flex items-center gap-2">
      {label}{required ? ' *' : ''}
      {ocr && <span className="text-xs bg-[#dbf226]/40 text-[#04221f] px-1.5 py-0.5 rounded font-semibold">OCR</span>}
    </label>
    {children}
  </div>
)

export default Config

