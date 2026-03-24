import React, { useState } from 'react';
import { useShield } from '../context/ShieldContext';
import { Fingerprint } from 'lucide-react';
import { registerUser, loginUser, verifyKyc } from '../utils/api';

const KYC = () => {
  const { setView, userData, setUserData, setAuthToken, setKycData, setWorkflowError } = useShield();
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [localError, setLocalError] = useState('');

  const handleValidate = async () => {
    setLocalError('');
    setWorkflowError(null);
    setIsSubmitting(true);

    try {
      const normalizedName = (userData.name || '').trim();
      const normalizedAadhaar = (userData.aadhaar || '').trim();
      const syntheticEmail = `${normalizedAadhaar}@daksha.local`;
      const syntheticPassword = `daksha-${normalizedAadhaar}`;

      setUserData({
        ...userData,
        email: syntheticEmail,
        password: syntheticPassword
      });

      const payload = {
        email: syntheticEmail,
        password: syntheticPassword,
        name: normalizedName || syntheticEmail
      };

      try {
        await registerUser(payload);
      } catch (error) {
        if (!String(error.message || '').toLowerCase().includes('already exists')) {
          throw error;
        }
      }

      const loginResponse = await loginUser({
        email: syntheticEmail,
        password: syntheticPassword
      });

      setAuthToken(loginResponse.access_token);

      // Verify KYC and get mock DB data
      try {
        const kycResponse = await verifyKyc(loginResponse.access_token, {
          name: normalizedName,
          aadhaar: normalizedAadhaar,
          dob: userData.dob
        });
        
        if (kycResponse.verified && kycResponse.kyc_data) {
          setKycData(kycResponse.kyc_data);
          // Update userData with verified data
          setUserData({
            ...userData,
            ...kycResponse.kyc_data
          });
        }
      } catch (kycError) {
        console.warn('KYC verification failed, continuing without prefill:', kycError);
        // Continue even if KYC verification fails
      }

      setView('selection');
    } catch (error) {
      setLocalError(error.message || 'Failed to validate identity');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-xl mx-auto py-10 text-center px-6 animate-in zoom-in-95">
      <div className="w-20 h-20 bg-[#4B0082] rounded-[2.5rem] flex items-center justify-center mx-auto mb-6 pink-glow rotate-6">
        <Fingerprint className="text-[#F4C2C2]" size={48} />
      </div>
      <h2 className="text-3xl font-black text-[#4B0082] tracking-tighter mb-3 italic">Identity Quest</h2>
      <p className="text-slate-400 mb-8 font-medium">Verify your Aadhaar to enter the Daksha Nexus.</p>
      
      <div className="space-y-4 mb-8">
        <input
          type="text"
          placeholder="Full name"
          value={userData.name}
          onChange={(e) => setUserData({ ...userData, name: e.target.value })}
          className="w-full bg-white/50 border-4 border-white p-4 rounded-4xl text-center text-lg font-black text-[#4B0082] outline-none focus:border-[#F4C2C2] transition-all shadow-inner"
        />
        <input 
          type="text" 
          placeholder="0000 0000 0000" 
          maxLength="12" 
          value={userData.aadhaar}
          onChange={(e) => setUserData({ ...userData, aadhaar: e.target.value.replace(/\D/g, '') })}
          className="w-full bg-white/50 border-4 border-white p-6 rounded-[2.5rem] text-center text-3xl font-black text-[#4B0082] outline-none focus:border-[#F4C2C2] transition-all shadow-inner" 
        />
      </div>

      {localError ? (
        <div className="text-red-500 text-xs font-bold uppercase tracking-widest mb-6">{localError}</div>
      ) : null}
      
      <button 
        onClick={handleValidate}
        disabled={
          isSubmitting ||
          userData.aadhaar.length < 12 ||
          !userData.name
        }
        className="w-full py-6 brinjal-gradient text-[#533377] drop-shadow-sm rounded-4xl font-black uppercase tracking-widest shadow-xl hover:scale-[1.01] transition-all disabled:opacity-40"
      >
        {isSubmitting ? 'Validating...' : 'Validate Identity'}
      </button>
    </div>
  );
};

export default KYC;
