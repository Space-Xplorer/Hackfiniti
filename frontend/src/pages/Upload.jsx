import React, { useRef, useState } from 'react';
import { useShield } from '../context/ShieldContext';
import { ArrowLeft, FileText, CheckCircle, Loader2 } from 'lucide-react';
import { previewOcr } from '../utils/api';

const Upload = () => {
  const { setView, service, loanType, authToken, applicantData, uploadedDocs, setUploadedDocs, uploadedDocuments, setUploadedDocuments, setOcrPreviewData, kycData } = useShield();
  const inputRefs = useRef({});
  const [errorMessage, setErrorMessage] = useState('');
  const [ocrLoading, setOcrLoading] = useState(false);

  const loanDocs = [
    { label: "Bank Statement (6 months)", type: "bank_statement", required: true },
    { label: "Salary Slip (last 3 months)", type: "salary_slip", required: true },
    { label: "Existing Loan Statements", type: "loan_statement", required: false },
    { label: "Property Documents", type: "property_document", required: loanType === 'home' },
    { label: "ID Proof", type: "aadhaar_card", required: true }
  ];

  const insuranceDocs = [
    { label: "Medical Reports", type: "diagnostic_report", required: true },
    { label: "ID Proof", type: "aadhaar_card", required: true },
    { label: "Income Proof (optional)", type: "itr", required: false }
  ];

  const currentDocs = service === 'loan' ? loanDocs : insuranceDocs;

  const handleUploadClick = (docLabel) => {
    const input = inputRefs.current[docLabel];
    if (input) {
      input.click();
    }
  };

  const handleFileChange = (doc, event) => {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }

    if (file.size > 1024 * 1024) {
      setErrorMessage('Each file must be 1MB or smaller.');
      event.target.value = '';
      return;
    }

    setErrorMessage('');

    const reader = new FileReader();
    reader.onload = () => {
      const result = String(reader.result || "");
      const base64 = result.includes(",") ? result.split(",")[1] : result;
      const docType = doc.type || "unknown";

      setUploadedDocs(prev => ({ ...prev, [doc.label]: true }));
      setUploadedDocuments([
        ...uploadedDocuments,
        {
          type: docType,
          name: file.name,
          mime_type: file.type,
          content_base64: base64
        }
      ]);
    };
    reader.readAsDataURL(file);
  };

  const isComplete = currentDocs
    .filter((doc) => doc.required)
    .every((doc) => uploadedDocs[doc.label]);

  return (
    <div className="max-w-3xl mx-auto py-6 px-6 animate-in fade-in">
      <div className="flex items-center gap-4 mb-6">
        <button onClick={() => setView('selection')} className="p-3 bg-white rounded-2xl text-[#4B0082] shadow-sm"><ArrowLeft size={20} /></button>
        <h2 className="text-3xl font-black text-[#4B0082] italic tracking-tighter">Vault: {service === 'loan' ? 'Loan Quest' : 'Life Quest'}</h2>
      </div>

      {ocrLoading ? (
        <div className="mb-8 flex items-center justify-center gap-3 bg-[#4B0082]/10 text-[#4B0082] rounded-2xl py-3 text-xs font-black uppercase tracking-widest">
          <Loader2 size={16} className="animate-spin" />
          OCR extraction in progress
        </div>
      ) : null}

      <div className="space-y-4 mb-8">
        {currentDocs.map((doc, i) => (
          <div key={i} className="flex items-center justify-between p-4 glass-card rounded-3xl">
            <div className="flex items-center gap-4">
              <FileText className="text-[#4B0082]" size={20} />
              <div>
                <span className="font-bold text-[#4B0082] text-sm">{doc.label}</span>
                {!doc.required ? (
                  <p className="text-[10px] uppercase tracking-widest text-slate-400 font-black">Optional</p>
                ) : null}
              </div>
            </div>
            {uploadedDocs[doc.label] ? (
              <div className="flex items-center gap-2 text-emerald-500 font-black text-[10px] uppercase"><CheckCircle size={16} /> Verified</div>
            ) : (
              <button onClick={() => handleUploadClick(doc.label)} className="bg-white px-6 py-2 rounded-xl text-[10px] font-black uppercase tracking-widest text-[#4B0082] border border-[#4B0082]/10 hover:bg-[#F4C2C2] transition-all">Upload</button>
            )}
            <input
              type="file"
              ref={(node) => { inputRefs.current[doc.label] = node; }}
              onChange={(event) => handleFileChange(doc, event)}
              className="hidden"
              accept=".pdf,.jpg,.jpeg,.png"
            />
          </div>
        ))}
      </div>

      {errorMessage ? (
        <div className="mb-6 text-red-500 text-xs font-bold uppercase tracking-widest text-center">
          {errorMessage}
        </div>
      ) : null}

      <button 
        onClick={async () => {
          if (!authToken) {
            setErrorMessage('Please complete Identity Quest first.');
            return;
          }

          try {
            setErrorMessage('');
            setOcrLoading(true);
            const response = await previewOcr(authToken, {
              request_type: service,
              declared_data: applicantData,
              uploaded_documents: uploadedDocuments,
              kyc_data: kycData
            });
            console.log('OCR Preview Response:', response);
            console.log('Declared Prefill:', response.declared_prefill);
            console.log('OCR Extracted Data:', response.ocr_extracted_data);
            setOcrPreviewData(response.declared_prefill || response.ocr_extracted_data || {});
            setView('config');
          } catch (error) {
            setErrorMessage(error.message || 'Failed to extract documents.');
          } finally {
            setOcrLoading(false);
          }
        }}
        disabled={!isComplete || ocrLoading}
        className={`w-full py-6 brinjal-gradient text-white rounded-[2.5rem] font-black uppercase tracking-widest shadow-2xl flex items-center justify-center gap-3 ${
          ocrLoading ? 'opacity-100' : 'disabled:opacity-30'
        }`}
      >
        {ocrLoading ? (
          <>
            <Loader2 size={18} className="animate-spin" />
            Extracting OCR...
          </>
        ) : (
          'Continue to Declaration'
        )}
      </button>
    </div>
  );
};

export default Upload;
