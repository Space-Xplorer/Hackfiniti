import { useState } from 'react'
import { ArrowLeft } from 'lucide-react'
import { useShield } from '../context/ShieldContext'
import GlassCard from '../components/GlassCard'

const Preliminary = () => {
  const { setView, service, applicantData, setApplicantData, loanType, setLoanType } = useShield();
  const [formData, setFormData] = useState({
    loan_type: loanType || 'home'
  });
  const [formError, setFormError] = useState('');

  const updateField = (field, value) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  const handleContinue = () => {
    setFormError('');

    if (service === 'loan') {
      const required = ['loan_type', 'loan_amount_requested', 'tenure_months'];
      const missing = required.filter((field) => !formData[field] && formData[field] !== 0);
      if (missing.length) {
        setFormError('Please complete the minimal details to proceed.');
        return;
      }
      if (formData.loan_type) {
        setLoanType(formData.loan_type);
      }
    }

    if (service === 'insurance') {
      const required = ['age', 'city', 'sum_insured'];
      const missing = required.filter((field) => !formData[field] && formData[field] !== 0);
      if (missing.length) {
        setFormError('Please complete the minimal details to proceed.');
        return;
      }
    }

    setApplicantData({ ...applicantData, ...formData });
    setView('upload');
  };

  return (
    <div className="min-h-screen bg-[#f7faf9] flex flex-col items-center justify-center p-8">
      <div className="w-full max-w-2xl">
        <div className="text-center mb-12">
          <h2 className="font-serif text-4xl font-bold text-[#04221f] mb-2" style={{ fontFamily: 'var(--font-serif)' }}>
            {service === 'loan' ? 'Select Loan Type' : 'Health Details'}
          </h2>
          <p className="text-[#005b52]/70">{service === 'loan' ? 'What kind of loan are you applying for?' : 'Tell us about your health profile'}</p>
        </div>
        <button onClick={() => setView('selection')} className="flex items-center gap-2 text-sm text-[#005b52]/60 hover:text-[#005b52] mb-6 transition-colors">
          <ArrowLeft size={16} /> Back
        </button>

      <GlassCard className="p-8">
        <div className="space-y-6">
          {service === 'loan' ? (
            <div className="grid md:grid-cols-2 gap-6">
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
                <Field label="Property Value">
                  <input
                    type="number"
                    value={formData.property_value || ''}
                    onChange={(e) => updateField('property_value', Number(e.target.value) || '')}
                    className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                  />
                </Field>
              ) : null}
            </div>
          ) : (
            <div className="grid md:grid-cols-2 gap-6">
              <Field label="Age" required>
                <input
                  type="number"
                  value={formData.age || ''}
                  onChange={(e) => updateField('age', Number(e.target.value) || '')}
                  className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                />
              </Field>
              <Field label="City" required>
                <input
                  type="text"
                  value={formData.city || ''}
                  onChange={(e) => updateField('city', e.target.value)}
                  className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                />
              </Field>
              <Field label="Sum Insured" required>
                <input
                  type="number"
                  value={formData.sum_insured || ''}
                  onChange={(e) => updateField('sum_insured', Number(e.target.value) || '')}
                  className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all"
                />
              </Field>
            </div>
          )}

          {formError ? (
            <div className="text-red-500 text-xs font-bold uppercase tracking-widest text-center">
              {formError}
            </div>
          ) : null}

          <button
            onClick={handleContinue}
            className="w-full bg-[#04221f] text-white font-bold py-3 rounded-full hover:bg-[#dbf226] hover:text-[#04221f] hover:-translate-y-0.5 transition-all duration-300 shadow-[0_4px_14px_rgba(4,34,31,0.2)]"
          >
            Continue to Upload
          </button>
        </div>
      </GlassCard>
      </div>
    </div>
  );
};

const Field = ({ label, required, children }) => (
  <div className="space-y-1">
    <label className="text-sm font-medium text-[#005b52]">
      {label}{required ? ' *' : ''}
    </label>
    {children}
  </div>
);

export default Preliminary;

