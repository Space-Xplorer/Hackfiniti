import React, { useState, useEffect, useRef } from 'react';
import { useShield } from '../context/ShieldContext';
import { Network, Loader2 } from 'lucide-react';
import GlassCard from '../components/GlassCard';
import AgentStatus from '../components/AgentStatus';
import { createApplication, submitWorkflow, getWorkflowStatus, getWorkflowResults } from '../utils/api';

const Analysis = () => {
  const {
    setView,
    service,
    authToken,
    applicantData,
    uploadedDocuments,
    loanType,
    userData,
    applicationId,
    setApplicationId,
    requestId,
    setRequestId,
    workflowStatus,
    setWorkflowStatus,
    setWorkflowResult,
    workflowError,
    setWorkflowError
  } = useShield();
  const [step, setStep] = useState(0);
  const [isRunning, setIsRunning] = useState(false);
  const [errorCount, setErrorCount] = useState(0);
  const pollRef = useRef(null);
  const runRef = useRef(false);
  const appIdRef = useRef(applicationId || null);

  useEffect(() => {
    appIdRef.current = applicationId || null;
  }, [applicationId]);

  const steps = [
    "KYC Agent: Verifying identity...",
    "Onboarding Agent: OCR extraction...",
    "Rules Agent: Checking underwriting rules...",
    "Fraud Agent: OCR fraud scan...",
    "Feature Engineering Agent: Deriving risk features...",
    "Compliance Agent: Regulatory checks...",
    "Underwriting Agent: Model inference...",
    "Verification Agent: Sanity checks...",
    "Transparency Agent: Explanation draft..."
  ];

  useEffect(() => {
    if (!authToken || !service || runRef.current || workflowStatus?.status === 'completed' || workflowError) {
      return;
    }

    let retryCount = 0;
    const MAX_RETRIES = 5;

    const clearPoll = () => {
      if (pollRef.current) {
        clearTimeout(pollRef.current);
        pollRef.current = null;
      }
    };

    const pollStatus = async (appId) => {
      try {
        const statusResponse = await getWorkflowStatus(authToken, appId);
        setWorkflowStatus(statusResponse);
        setStep((prev) => Math.min(prev + 1, steps.length - 1));
        retryCount = 0;
        setErrorCount(0);

        if (statusResponse.status === 'completed') {
          clearPoll();
          const results = await getWorkflowResults(authToken, appId);
          setWorkflowResult(results);
          setView('result');
          runRef.current = false;
          return;
        }
        if (statusResponse.status === 'failed') {
          clearPoll();
          setWorkflowError(statusResponse.error || 'Workflow failed');
          runRef.current = false;
          return;
        }

        pollRef.current = setTimeout(() => {
          pollStatus(appId);
        }, 2000);
      } catch (error) {
        retryCount += 1;
        setErrorCount(retryCount);

        if (retryCount >= MAX_RETRIES || String(error.message || '').toLowerCase().includes('404')) {
          clearPoll();
          setWorkflowError(error.message || 'Failed to fetch workflow status');
          setIsRunning(false);
          runRef.current = false;
          return;
        }

        pollRef.current = setTimeout(() => {
          pollStatus(appId);
        }, 2000);
      }
    };

    const runWorkflow = async () => {
      setIsRunning(true);
      setWorkflowError(null);
      setErrorCount(0);
      runRef.current = true;

      try {
        let appId = appIdRef.current;
        if (!appId) {
          const createPayload = {
            request_type: service,
            loan_type: service === 'loan' ? loanType : null,
            submitted_name: userData.name,
            submitted_dob: userData.dob,
            submitted_aadhaar: userData.aadhaar,
            applicant_data: applicantData,
            uploaded_documents: uploadedDocuments
          };

          const created = await createApplication(authToken, createPayload);
          appId = created.application.id;
          setApplicationId(appId);
          appIdRef.current = appId;
        }

        try {
          const submitResponse = await submitWorkflow(authToken, appId);
          setRequestId(submitResponse.request_id || requestId);
        } catch (error) {
          const message = String(error.message || '').toLowerCase();
          if (!message.includes('already submitted')) {
            throw error;
          }
        }

        clearPoll();
        pollStatus(appId);
      } catch (error) {
        setWorkflowError(error.message || 'Workflow initialization failed');
        setIsRunning(false);
        runRef.current = false;
      }
    };

    runWorkflow();

    // Cleanup function to clear interval on unmount or re-run
    return () => {
      clearPoll();
    };
  }, [
    authToken,
    service,
    loanType,
    applicantData,
    uploadedDocuments,
    userData,
    applicationId,
    setApplicationId,
    setRequestId,
    setWorkflowStatus,
    setWorkflowResult,
    setWorkflowError,
    setView,
    steps.length,
    isRunning
  ]);

  return (
    <div className="h-full w-full overflow-hidden px-6">
      <div className="h-full grid grid-cols-1 lg:grid-cols-[320px_1fr] items-stretch gap-10">
        <div className="flex items-center justify-center">
          <div className="relative w-40 h-40">
            <div className="absolute inset-0 border-8 border-[#4B0082]/10 rounded-full" />
            <div className="absolute inset-0 border-8 border-[#F4C2C2] border-t-transparent rounded-full animate-spin" />
            <div className="absolute inset-0 flex items-center justify-center text-[#4B0082]"><Network size={44} /></div>
          </div>
        </div>

        <div className="flex flex-col justify-center text-left">
          <h2 className="text-3xl font-black text-[#4B0082] italic uppercase tracking-[0.2em] mb-5">Agentic Orchestration</h2>
          <div className="bg-white p-6 rounded-4xl shadow-sm border border-slate-100 max-w-2xl">
            <p className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-2">Active Task</p>
            <p className="text-sm font-black text-[#4B0082] animate-pulse">{steps[step]}</p>
          </div>

          {workflowError ? (
            <div className="mt-6 text-red-500 text-xs font-bold uppercase tracking-widest">
              {workflowError}
            </div>
          ) : errorCount > 0 ? (
            <div className="mt-6 text-orange-500 text-xs font-bold uppercase tracking-widest">
              Connection retry {errorCount}/5
            </div>
          ) : null}

          <div className="mt-10">
            <GlassCard className="p-8 max-w-2xl">
              <h4 className="text-left font-black text-[#4B0082] mb-8 uppercase italic tracking-widest">
                Orchestration Pulse
              </h4>
              <div className="space-y-4">
                <AgentStatus name="KYC Agent" status="complete" />
                <AgentStatus name="Onboarding Agent" status="loading" />
                <AgentStatus name="Rules Agent" status="waiting" />
              </div>
            </GlassCard>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Analysis;
