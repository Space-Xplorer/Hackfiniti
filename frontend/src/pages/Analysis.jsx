import { useState, useEffect, useRef } from 'react'
import { useShield } from '../context/ShieldContext'
import AgentStatus from '../components/AgentStatus'
import { createApplication, submitWorkflow, getWorkflowStatus, getWorkflowResults } from '../utils/api'

const agentSteps = [
  { name: 'KYC Agent', description: 'Verifying identity…' },
  { name: 'Onboarding Agent', description: 'OCR extraction…' },
  { name: 'Rules Agent', description: 'Checking underwriting rules…' },
  { name: 'Fraud Agent', description: 'OCR fraud scan…' },
  { name: 'Feature Engineering', description: 'Deriving risk features…' },
  { name: 'Compliance Agent', description: 'Regulatory checks…' },
  { name: 'Underwriting Agent', description: 'Model inference…' },
  { name: 'Verification Agent', description: 'Sanity checks…' },
  { name: 'Transparency Agent', description: 'Explanation draft…' },
]

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

  const steps = agentSteps.map((a) => a.description)

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
  ]);

  return (
    <div className="min-h-screen bg-[#04221f] flex flex-col items-center justify-center p-8">
      <div className="bg-white/5 border border-white/10 rounded-3xl p-8 w-full max-w-xl">
        <div className="text-center mb-6">
          <div className="w-3 h-3 bg-[#dbf226] rounded-full animate-pulse mx-auto mb-4" />
          <h2 className="font-serif text-2xl font-bold text-white" style={{ fontFamily: 'var(--font-serif)' }}>
            Daksha is analyzing your application
          </h2>
          {!workflowError && (
            <p className="text-white/50 text-sm mt-1">{steps[step]}</p>
          )}
        </div>

        <div className="space-y-2 mb-6">
          {agentSteps.map((agent, i) => {
            const status = i < step ? 'complete' : i === step ? 'running' : 'pending'
            return <AgentStatus key={agent.name} name={agent.name} description={agent.description} status={status} />
          })}
        </div>

        <div className="h-1 bg-white/10 rounded-full overflow-hidden">
          <div
            className="bg-[#dbf226] h-full rounded-full transition-all duration-500"
            style={{ width: `${(step / agentSteps.length) * 100}%` }}
          />
        </div>

        {workflowError && (
          <div className="mt-4 text-red-400 text-sm text-center">{workflowError}</div>
        )}
        {!workflowError && errorCount > 0 && (
          <div className="mt-4 text-amber-400 text-xs text-center">Connection retry {errorCount}/5</div>
        )}
      </div>
    </div>
  );
};

export default Analysis;

