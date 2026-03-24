import React, { useState } from 'react';
import { ArrowLeft } from 'lucide-react';
import { useShield } from '../context/ShieldContext';
import GlassCard from '../components/GlassCard';

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
    <div className="max-w-3xl mx-auto py-6 px-6 animate-in slide-in-from-bottom-10">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => setView('selection')} className="p-3 bg-white rounded-2xl text-[#4B0082] shadow-sm">
          <ArrowLeft size={20} />
        </button>
        <h2 className="text-3xl font-black text-[#4B0082] italic tracking-tighter">
          {service === 'loan' ? 'Preliminary Loan Details' : 'Preliminary Health Details'}
        </h2>
      </div>

      <GlassCard className="p-8">
        <div className="space-y-6">
          {service === 'loan' ? (
            <div className="grid md:grid-cols-2 gap-6">
              <Field label="Loan Type" required>
                <select
                  value={formData.loan_type || 'home'}
                  onChange={(e) => updateField('loan_type', e.target.value)}
                  className="w-full bg-[#FAF9F6] p-4 rounded-3xl outline-none focus:ring-2 ring-[#F4C2C2] font-bold text-[#4B0082]"
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
                  className="w-full bg-[#FAF9F6] p-4 rounded-3xl outline-none focus:ring-2 ring-[#F4C2C2] font-bold text-[#4B0082]"
                />
              </Field>
              <Field label="Tenure (months)" required>
                <input
                  type="number"
                  value={formData.tenure_months || ''}
                  onChange={(e) => updateField('tenure_months', Number(e.target.value) || '')}
                  className="w-full bg-[#FAF9F6] p-4 rounded-3xl outline-none focus:ring-2 ring-[#F4C2C2] font-bold text-[#4B0082]"
                />
              </Field>
              {formData.loan_type === 'home' ? (
                <Field label="Property Value">
                  <input
                    type="number"
                    value={formData.property_value || ''}
                    onChange={(e) => updateField('property_value', Number(e.target.value) || '')}
                    className="w-full bg-[#FAF9F6] p-4 rounded-3xl outline-none focus:ring-2 ring-[#F4C2C2] font-bold text-[#4B0082]"
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
                  className="w-full bg-[#FAF9F6] p-4 rounded-3xl outline-none focus:ring-2 ring-[#F4C2C2] font-bold text-[#4B0082]"
                />
              </Field>
              <Field label="City" required>
                <input
                  type="text"
                  value={formData.city || ''}
                  onChange={(e) => updateField('city', e.target.value)}
                  className="w-full bg-[#FAF9F6] p-4 rounded-3xl outline-none focus:ring-2 ring-[#F4C2C2] font-bold text-[#4B0082]"
                />
              </Field>
              <Field label="Sum Insured" required>
                <input
                  type="number"
                  value={formData.sum_insured || ''}
                  onChange={(e) => updateField('sum_insured', Number(e.target.value) || '')}
                  className="w-full bg-[#FAF9F6] p-4 rounded-3xl outline-none focus:ring-2 ring-[#F4C2C2] font-bold text-[#4B0082]"
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
            className="w-full py-6 brinjal-gradient text-[#533377] drop-shadow-sm rounded-4xl font-black uppercase tracking-widest shadow-xl hover:scale-[1.01] transition-all"
          >
            Continue to Upload
          </button>
        </div>
      </GlassCard>
    </div>
  );
};

const Field = ({ label, required, children }) => (
  <div className="space-y-3">
    <label className="text-[10px] font-black text-slate-400 uppercase tracking-widest ml-2">
      {label}{required ? ' *' : ''}
    </label>
    {children}
  </div>
);

export default Preliminary;
