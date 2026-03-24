import { useRef, useState } from 'react'
import { useShield } from '../context/ShieldContext'
import { ArrowLeft, FileText, CheckCircle, Loader2, AlertTriangle, XCircle } from 'lucide-react'
import { previewOcr } from '../utils/api'
import { ocrDocument, validateOcrResults } from '../utils/ocr'

export default function Upload() {
  const { setView, service, loanType, authToken, applicantData, uploadedDocs, setUploadedDocs,
    uploadedDocuments, setUploadedDocuments, setOcrPreviewData, kycData } = useShield()
  const inputRefs = useRef({})
  const [errorMessage, setErrorMessage] = useState('')
  const [ocrLoading, setOcrLoading] = useState(false)
  // Per-doc OCR state: { [docLabel]: 'idle'|'running'|'done'|'error' }
  const [ocrStatus, setOcrStatus] = useState({})
  // Per-doc extracted data keyed by doc.type
  const [ocrResults, setOcrResults] = useState([])
  // Consistency flags from cross-doc validation
  const [consistencyFlags, setConsistencyFlags] = useState([])

  const loanDocs = [
    { label: 'Bank Statement (6 months)', type: 'bank_statement', required: true },
    { label: 'Salary Slip (last 3 months)', type: 'salary_slip', required: true },
    { label: 'Existing Loan Statements', type: 'loan_statement', required: false },
    { label: 'Property Documents', type: 'property_document', required: loanType === 'home' },
    { label: 'ID Proof', type: 'aadhaar_card', required: true },
  ]
  const insuranceDocs = [
    { label: 'Medical Reports', type: 'diagnostic_report', required: true },
    { label: 'ID Proof', type: 'aadhaar_card', required: true },
    { label: 'Income Proof (optional)', type: 'itr', required: false },
  ]
  const currentDocs = service === 'loan' ? loanDocs : insuranceDocs

  const handleUploadClick = (docLabel) => inputRefs.current[docLabel]?.click()

  const handleFileChange = async (doc, event) => {
    const file = event.target.files?.[0]
    if (!file) return
    if (file.size > 5 * 1024 * 1024) {
      setErrorMessage('Each file must be 5MB or smaller.')
      event.target.value = ''
      return
    }
    setErrorMessage('')
    setConsistencyFlags([])

    // Mark uploaded in UI
    setUploadedDocs((prev) => ({ ...prev, [doc.label]: true }))

    // Store base64 for backend
    const reader = new FileReader()
    reader.onload = () => {
      const result = String(reader.result || '')
      const base64 = result.includes(',') ? result.split(',')[1] : result
      setUploadedDocuments((prev) => {
        const filtered = prev.filter((d) => d.type !== doc.type)
        return [...filtered, { type: doc.type, name: file.name, mime_type: file.type, content_base64: base64 }]
      })
    }
    reader.readAsDataURL(file)

    // Run Puter.js OCR in browser
    if (typeof window.puter === 'undefined') {
      // Puter not loaded — skip client OCR, backend will handle
      return
    }
    setOcrStatus((prev) => ({ ...prev, [doc.label]: 'running' }))
    const result = await ocrDocument(file, doc.type)
    setOcrStatus((prev) => ({ ...prev, [doc.label]: result.error ? 'error' : 'done' }))
    setOcrResults((prev) => {
      const filtered = prev.filter((r) => r.docType !== doc.type)
      return [...filtered, result]
    })
  }

  const isComplete = currentDocs.filter((d) => d.required).every((d) => uploadedDocs[d.label])
  const isOcrRunning = Object.values(ocrStatus).some((s) => s === 'running')

  const handleContinue = async () => {
    if (!authToken) { setErrorMessage('Please complete Identity Verification first.'); return }
    setErrorMessage('')
    setConsistencyFlags([])

    // If we have client-side OCR results, validate them first
    if (ocrResults.length > 0) {
      const validation = validateOcrResults(ocrResults)
      if (validation.consistency_flags.length > 0) {
        setConsistencyFlags(validation.consistency_flags)
        // Don't block — show flags as warnings but allow continue
      }
      // Merge OCR-extracted data into ocrPreviewData directly
      const merged = {
        ...applicantData,
        ...validation.raw_by_type.aadhaar_card && {
          name: validation.raw_by_type.aadhaar_card.full_name,
          dob: validation.raw_by_type.aadhaar_card.dob,
        },
        ...(validation.extracted_data.monthly_income && { declared_monthly_income: validation.extracted_data.monthly_income }),
        ...(validation.extracted_data.existing_emi && { declared_existing_emi: validation.extracted_data.existing_emi }),
        ...(validation.extracted_data.property_value && { property_value: validation.extracted_data.property_value }),
        ...(validation.extracted_data.employer_name && { employer_name: validation.extracted_data.employer_name }),
        _ocr_confidence: validation.confidence_score,
        _ocr_flags: validation.consistency_flags,
        _ocr_freshness: validation.document_freshness_passed,
      }
      setOcrPreviewData(merged)
      setView('config')
      return
    }

    // Fallback: send to backend preview-ocr
    try {
      setOcrLoading(true)
      const response = await previewOcr(authToken, {
        request_type: service, declared_data: applicantData,
        uploaded_documents: uploadedDocuments, kyc_data: kycData,
      })
      setOcrPreviewData(response.declared_prefill || response.ocr_extracted_data || {})
      setView('config')
    } catch (err) {
      let msg = err.message || 'Failed to extract documents.'
      try {
        const parsed = JSON.parse(err.message)
        if (parsed?.errors?.length) msg = parsed.errors.join(' • ')
        else if (parsed?.message) msg = parsed.message
      } catch (_) { /* plain string */ }
      setErrorMessage(msg)
    } finally {
      setOcrLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[#f7faf9]">
      <div className="max-w-3xl mx-auto px-4 py-12 space-y-8">
        <div>
          <button onClick={() => setView('prelim')} className="flex items-center gap-2 text-sm text-[#005b52]/60 hover:text-[#005b52] mb-4 transition-colors">
            <ArrowLeft size={16} /> Back
          </button>
          <h2 className="font-serif text-3xl font-bold text-[#04221f]" style={{ fontFamily: 'var(--font-serif)' }}>Upload Documents</h2>
          <p className="text-[#005b52]/70 mt-1">Documents are scanned in your browser — nothing is stored externally</p>
        </div>

        <div className="space-y-3">
          {currentDocs.map((doc, i) => {
            const status = ocrStatus[doc.label] || 'idle'
            const uploaded = uploadedDocs[doc.label]
            return (
              <div
                key={i}
                onClick={() => !uploaded && handleUploadClick(doc.label)}
                className={`bg-white rounded-2xl border-2 border-dashed p-5 transition-all ${
                  uploaded ? 'border-[#dbf226] bg-[#dbf226]/5 cursor-default' : 'border-[#005b52]/20 hover:border-[#005b52] cursor-pointer'
                }`}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <FileText size={20} className={uploaded ? 'text-[#005b52]' : 'text-[#005b52]/30'} />
                    <div>
                      <p className="font-semibold text-[#04221f] text-sm">{doc.label}</p>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${doc.required ? 'bg-red-50 text-red-600' : 'bg-[#005b52]/5 text-[#005b52]'}`}>
                        {doc.required ? 'Required' : 'Optional'}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {status === 'running' && <Loader2 size={18} className="text-[#005b52] animate-spin" />}
                    {status === 'done' && <span className="text-xs text-[#005b52] font-medium bg-[#005b52]/10 px-2 py-0.5 rounded-full">OCR ✓</span>}
                    {status === 'error' && <span className="text-xs text-amber-600 font-medium bg-amber-50 px-2 py-0.5 rounded-full">OCR skipped</span>}
                    {uploaded
                      ? <CheckCircle size={20} className="text-[#005b52]" />
                      : <span className="text-[#005b52]/30 text-2xl">↑</span>
                    }
                  </div>
                </div>
                <input
                  type="file"
                  ref={(node) => { inputRefs.current[doc.label] = node }}
                  onChange={(e) => handleFileChange(doc, e)}
                  className="hidden"
                  accept=".pdf,.jpg,.jpeg,.png"
                />
              </div>
            )
          })}
        </div>

        {/* OCR extracted data panel — shown after at least one doc is scanned */}
        {ocrResults.some(r => r.extracted) && (
          <div className="bg-white rounded-2xl border border-[#005b52]/10 p-5 space-y-4">
            <p className="text-xs font-bold uppercase tracking-widest text-[#005b52]/50">Extracted from your documents</p>
            {ocrResults.filter(r => r.extracted).map((r, i) => {
              const DOC_LABELS = {
                bank_statement: 'Bank Statement',
                salary_slip: 'Salary Slip',
                loan_statement: 'Loan Statement',
                property_document: 'Property Document',
                aadhaar_card: 'ID Proof',
                diagnostic_report: 'Medical Report',
                itr: 'ITR',
              }
              const FIELD_LABELS = {
                account_name: 'Account Name', current_balance: 'Current Balance',
                avg_monthly_balance: 'Avg Monthly Balance', recurring_salary_deposits: 'Salary Deposits',
                statement_date: 'Statement Date', bank_name: 'Bank',
                employee_name: 'Employee Name', employer_name: 'Employer',
                net_income: 'Net Income', slip_date: 'Slip Date',
                current_emi: 'Current EMI', outstanding_balance: 'Outstanding Balance',
                property_value: 'Property Value', owner_name: 'Owner Name',
                full_name: 'Full Name', dob: 'Date of Birth', id_number: 'ID Number',
                patient_name: 'Patient Name', report_date: 'Report Date', diagnosis: 'Diagnosis',
                taxpayer_name: 'Taxpayer Name', annual_income: 'Annual Income',
              }
              const fields = Object.entries(r.extracted).filter(([, v]) => v !== null && v !== '')
              if (!fields.length) return null
              return (
                <div key={i}>
                  <p className="text-xs font-semibold text-[#005b52] mb-2">{DOC_LABELS[r.docType] || r.docType}</p>
                  <div className="grid grid-cols-2 gap-2">
                    {fields.map(([k, v]) => (
                      <div key={k} className="bg-[#f7faf9] rounded-lg px-3 py-2 border border-[#005b52]/8">
                        <p className="text-[10px] text-[#005b52]/50 font-medium">{FIELD_LABELS[k] || k}</p>
                        <p className="text-xs font-semibold text-[#04221f] truncate">
                          {typeof v === 'number' ? `₹ ${Number(v).toLocaleString('en-IN')}` : String(v)}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {consistencyFlags.length > 0 && (
          <div className="bg-amber-50 border border-amber-200 rounded-2xl p-4 space-y-2">
            <div className="flex items-center gap-2 text-amber-700 font-semibold text-sm">
              <AlertTriangle size={16} /> Document Inconsistencies Detected
            </div>
            <ul className="space-y-1">
              {consistencyFlags.map((flag, i) => (
                <li key={i} className="text-xs text-amber-700 flex items-start gap-2">
                  <XCircle size={12} className="mt-0.5 shrink-0" /> {flag}
                </li>
              ))}
            </ul>
            <p className="text-xs text-amber-600">You can still continue — these will be reviewed during underwriting.</p>
          </div>
        )}

        {errorMessage && (
          <div className="text-red-700 bg-red-50 border border-red-200 p-3 rounded-xl text-sm">{errorMessage}</div>
        )}

        <button
          onClick={handleContinue}
          disabled={!isComplete || isOcrRunning || ocrLoading}
          className="w-full bg-[#04221f] text-white font-bold py-4 rounded-full hover:bg-[#dbf226] hover:text-[#04221f] transition-all duration-300 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {(isOcrRunning || ocrLoading)
            ? <><Loader2 size={18} className="animate-spin" /> Scanning documents…</>
            : 'Continue to Declaration Form'
          }
        </button>
      </div>
    </div>
  )
}
