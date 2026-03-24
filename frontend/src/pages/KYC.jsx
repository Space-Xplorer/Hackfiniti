import { useState, useEffect, useRef } from 'react'
import { useShield } from '../context/ShieldContext'
import { registerUser, loginUser, verifyKyc, sendOtp, verifyOtp } from '../utils/api'

const KYC = () => {
  const { setView, userData, setUserData, setAuthToken, setKycData, setWorkflowError } = useShield()
  const [step, setStep] = useState('form') // 'form' | 'otp'
  const [mobile, setMobile] = useState('')
  const [otp, setOtp] = useState('')
  const [otpError, setOtpError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [localError, setLocalError] = useState('')
  const [countdown, setCountdown] = useState(0)
  const timerRef = useRef(null)

  useEffect(() => {
    if (countdown <= 0) return
    timerRef.current = setInterval(() => {
      setCountdown((c) => {
        if (c <= 1) { clearInterval(timerRef.current); return 0 }
        return c - 1
      })
    }, 1000)
    return () => clearInterval(timerRef.current)
  }, [countdown])

  const handleSendOtp = async () => {
    setLocalError('')
    setIsSubmitting(true)
    try {
      const res = await sendOtp(mobile)
      setCountdown(120)
      setStep('otp')
    } catch (err) {
      setLocalError(err.message || 'Failed to send OTP')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleVerifyOtp = async () => {
    setOtpError('')
    setIsSubmitting(true)
    try {
      await verifyOtp(mobile, otp)
      await completeKyc()
    } catch (err) {
      setOtpError(err.message || 'Invalid OTP')
    } finally {
      setIsSubmitting(false)
    }
  }

  const completeKyc = async () => {
    const normalizedName = (userData.name || '').trim()
    const normalizedAadhaar = (userData.aadhaar || '').trim()
    const syntheticEmail = `${normalizedAadhaar}@daksha.local`
    const syntheticPassword = `daksha-${normalizedAadhaar}`
    setUserData({ ...userData, email: syntheticEmail, password: syntheticPassword, mobile })
    try {
      await registerUser({ email: syntheticEmail, password: syntheticPassword, name: normalizedName || syntheticEmail })
    } catch (err) {
      if (!String(err.message || '').toLowerCase().includes('already exists')) throw err
    }
    const loginResponse = await loginUser({ email: syntheticEmail, password: syntheticPassword })
    setAuthToken(loginResponse.access_token)
    try {
      const kycResponse = await verifyKyc(loginResponse.access_token, {
        name: normalizedName, aadhaar: normalizedAadhaar, dob: userData.dob,
      })
      if (kycResponse.verified && kycResponse.kyc_data) {
        setKycData(kycResponse.kyc_data)
        setUserData({ ...userData, ...kycResponse.kyc_data, mobile })
      }
    } catch (e) {
      console.warn('KYC verify failed, continuing:', e)
    }
    setWorkflowError(null)
    setView('selection')
  }

  const formValid = userData.aadhaar.length === 12 && userData.name.trim() && mobile.length === 10

  return (
    <div className="min-h-screen bg-[#f7faf9] flex items-center justify-center p-8">
      <div className="w-full max-w-md bg-white border border-[#005b52]/10 rounded-3xl p-10 space-y-6 shadow-xl shadow-black/5">
        <div className="text-center space-y-1">
          <p className="font-serif text-2xl font-bold text-[#005b52]" style={{ fontFamily: 'var(--font-serif)' }}>Daksha</p>
          <h2 className="text-3xl font-bold text-[#04221f]">Identity Verification</h2>
          <p className="text-[#005b52]/70 text-sm">
            {step === 'form' ? 'Verify your Aadhaar to begin' : `Enter the OTP sent to +91 ${mobile}`}
          </p>
        </div>

        {step === 'form' ? (
          <div className="space-y-4">
            <Field label="Full Name">
              <input
                type="text"
                placeholder="Enter your full name"
                value={userData.name}
                onChange={(e) => setUserData({ ...userData, name: e.target.value })}
                className={inputCls}
              />
            </Field>
            <Field label="Aadhaar Number">
              <input
                type="text"
                placeholder="0000 0000 0000"
                maxLength="12"
                value={userData.aadhaar}
                onChange={(e) => setUserData({ ...userData, aadhaar: e.target.value.replace(/\D/g, '') })}
                className={`${inputCls} text-center text-2xl tracking-[0.3em] font-mono placeholder:text-base placeholder:tracking-normal`}
              />
            </Field>
            <Field label="Mobile Number">
              <div className="flex">
                <span className="flex items-center px-3 rounded-l-xl border border-r-0 border-[#005b52]/20 bg-[#f7faf9] text-[#005b52] text-sm font-medium">+91</span>
                <input
                  type="tel"
                  placeholder="10-digit mobile"
                  maxLength="10"
                  value={mobile}
                  onChange={(e) => setMobile(e.target.value.replace(/\D/g, ''))}
                  className={`${inputCls} rounded-l-none flex-1`}
                />
              </div>
            </Field>

            {localError && <ErrorBox msg={localError} />}

            <button
              onClick={handleSendOtp}
              disabled={isSubmitting || !formValid}
              className={btnCls}
            >
              {isSubmitting ? 'Sending OTP…' : 'Send OTP'}
            </button>
          </div>
        ) : (
          <div className="space-y-4">
            <Field label="Enter OTP">
              <input
                type="text"
                placeholder="6-digit OTP"
                maxLength="6"
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                className={`${inputCls} text-center text-3xl tracking-[0.4em] font-mono placeholder:text-base placeholder:tracking-normal`}
                autoFocus
              />
            </Field>

            <div className="flex items-center justify-between text-xs text-[#005b52]/60">
              <span>{countdown > 0 ? `Expires in ${Math.floor(countdown / 60)}:${String(countdown % 60).padStart(2, '0')}` : 'OTP expired'}</span>
              {countdown === 0 && (
                <button onClick={handleSendOtp} className="text-[#005b52] font-semibold underline">Resend</button>
              )}
            </div>

            {otpError && <ErrorBox msg={otpError} />}

            <button
              onClick={handleVerifyOtp}
              disabled={isSubmitting || otp.length < 6 || countdown === 0}
              className={btnCls}
            >
              {isSubmitting ? 'Verifying…' : 'Verify OTP'}
            </button>

            <button
              onClick={() => { setStep('form'); setOtp(''); setOtpError('') }}
              className="w-full text-sm text-[#005b52]/60 hover:text-[#005b52] transition-colors"
            >
              ← Change details
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

const inputCls = "w-full px-4 py-3 rounded-xl border border-[#005b52]/20 bg-white text-[#04221f] focus:border-[#005b52] focus:outline-2 focus:outline-[#dbf226] transition-all placeholder:text-[#005b52]/30"
const btnCls = "w-full bg-[#04221f] text-white font-bold py-3 rounded-full hover:bg-[#dbf226] hover:text-[#04221f] hover:-translate-y-0.5 transition-all duration-300 shadow-[0_4px_14px_rgba(4,34,31,0.2)] disabled:opacity-40 disabled:cursor-not-allowed disabled:hover:translate-y-0"

const Field = ({ label, children }) => (
  <div>
    <label className="block text-sm font-medium text-[#005b52] mb-1">{label}</label>
    {children}
  </div>
)

const ErrorBox = ({ msg }) => (
  <div className="text-red-700 bg-red-50 border border-red-200 p-3 rounded-xl text-sm">{msg}</div>
)

export default KYC
