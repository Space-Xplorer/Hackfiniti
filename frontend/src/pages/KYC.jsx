import { useState } from 'react'
import { useShield } from '../context/ShieldContext'
import { registerUser, loginUser, verifyKyc } from '../utils/api'

const KYC = () => {
  const { setView, userData, setUserData, setAuthToken, setKycData, setWorkflowError } = useShield()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [localError, setLocalError] = useState('')

  const handleValidate = async () => {
    setLocalError('')
    setWorkflowError(null)
    setIsSubmitting(true)
    try {
      const normalizedName = (userData.name || '').trim()
      const normalizedAadhaar = (userData.aadhaar || '').trim()
      const syntheticEmail = `${normalizedAadhaar}@daksha.local`
      const syntheticPassword = `daksha-${normalizedAadhaar}`

      setUserData({ ...userData, email: syntheticEmail, password: syntheticPassword })

      try {
        await registerUser({ email: syntheticEmail, password: syntheticPassword, name: normalizedName || syntheticEmail })
      } catch (error) {
        if (!String(error.message || '').toLowerCase().includes('already exists')) throw error
      }

      const loginResponse = await loginUser({ email: syntheticEmail, password: syntheticPassword })
      setAuthToken(loginResponse.access_token)

      try {
        const kycResponse = await verifyKyc(loginResponse.access_token, {
          name: normalizedName, aadhaar: normalizedAadhaar, dob: userData.dob,
        })
        if (kycResponse.verified && kycResponse.kyc_data) {
          setKycData(kycResponse.kyc_data)
          setUserData({ ...userData, ...kycResponse.kyc_data })
        }
      } catch (kycError) {
        console.warn('KYC verification failed, continuing:', kycError)
      }

      setView('selection')
    } catch (error) {
      setLocalError(error.message || 'Failed to validate identity')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#f7faf9] flex items-center justify-center p-8">
      <div className="w-full max-w-md bg-white border border-[#005b52]/10 rounded-3xl p-10 space-y-6 shadow-xl shadow-black/5">
        <div className="text-center space-y-1">
          <p className="font-serif text-2xl font-bold text-[#005b52]" style={{ fontFamily: 'var(--font-serif)' }}>Daksha</p>
          <h2 className="text-3xl font-bold text-[#04221f]">Identity Verification</h2>
          <p className="text-[#005b52]/70 text-sm">Verify your Aadhaar to begin</p>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-[#005b52] mb-1">Full Name</label>
            <input
              type="text"
              placeholder="Enter your full name"
              value={userData.name}
              onChange={(e) => setUserData({ ...userData, name: e.target.value })}
              className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all placeholder:text-[#005b52]/30"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-[#005b52] mb-1">Aadhaar Number</label>
            <input
              type="text"
              placeholder="0000 0000 0000"
              maxLength="12"
              value={userData.aadhaar}
              onChange={(e) => setUserData({ ...userData, aadhaar: e.target.value.replace(/\D/g, '') })}
              className="w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] text-center text-2xl tracking-[0.3em] font-mono focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all placeholder:text-[#005b52]/30 placeholder:text-base placeholder:tracking-normal"
            />
          </div>
        </div>

        {localError && (
          <div className="text-red-700 bg-red-50 border border-red-200 p-3 rounded-xl text-sm">{localError}</div>
        )}

        <button
          onClick={handleValidate}
          disabled={isSubmitting || userData.aadhaar.length < 12 || !userData.name}
          className="w-full bg-[#04221f] text-white font-bold py-3 rounded-full hover:bg-[#dbf226] hover:text-[#04221f] hover:-translate-y-0.5 transition-all duration-300 shadow-[0_4px_14px_rgba(4,34,31,0.2)] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:translate-y-0"
        >
          {isSubmitting ? 'Validating…' : 'Validate Identity'}
        </button>
      </div>
    </div>
  )
}

export default KYC

