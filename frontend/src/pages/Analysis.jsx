import { useState, useEffect, useRef } from 'react'
import { useShield } from '../context/ShieldContext'
import AgentStatus from '../components/AgentStatus'
import { createApplication, submitWorkflow, getWorkflowStatus, getWorkflowResults } from '../utils/api'
import useWorkflowStream from '../hooks/useWorkflowStream'

const agentSteps = [
  { name: 'KYC Agent', description: 'Verifying identity…' },
  { name: 'Onboarding Agent', description: 'OCR extraction…' },
  { name: 'Fraud Agent', description: 'OCR fraud scan…' },
  { name: 'Feature Engineering', description: 'Deriving risk features…' },
  { name: 'Compliance Agent', description: 'Regulatory checks…' },
  { name: 'Underwriting Agent', description: 'Model inference…' },
  { name: 'Verification Agent', description: 'Sanity checks…' },
  { name: 'Transparency Agent', description: 'Explanation draft…' },
  { name: 'Supervisor Agent', description: 'Final decision orchestration…' },
]

const AGENT_INDEX_BY_EVENT = {
  kyc: 0,
  onboarding: 1,
  fraud: 2,
  feature_engineering: 3,
  compliance: 4,
  underwriting: 5,
  verification: 6,
  transparency: 7,
  supervisor: 8,
}

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
  const { events: streamEvents } = useWorkflowStream(authToken, applicationId);

  useEffect(() => {
    appIdRef.current = applicationId || null;
  }, [applicationId]);

  const steps = agentSteps.map((a) => a.description)

  useEffect(() => {
    if (!streamEvents.length) return

    const nonTerminalEvents = streamEvents.filter((evt) => evt && !evt.done)
    if (!nonTerminalEvents.length) return

    const failedEvent = nonTerminalEvents.find((evt) => evt.status === 'failed')
    if (failedEvent?.error) {
      setWorkflowError(failedEvent.error)
    }

    const lastAgentEvent = [...nonTerminalEvents].reverse().find((evt) => evt.agent)
    if (!lastAgentEvent) return

    const idx = AGENT_INDEX_BY_EVENT[lastAgentEvent.agent]
    if (typeof idx === 'number') {
      const nextStep = lastAgentEvent.status === 'complete'
        ? Math.min(idx + 1, agentSteps.length - 1)
        : idx
      setStep((prev) => Math.max(prev, nextStep))
    }
  }, [streamEvents, setWorkflowError])

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
          const backendError =
            statusResponse.rejection_reason
            || (Array.isArray(statusResponse.agent_errors) && statusResponse.agent_errors[0])
            || statusResponse.error
            || 'Workflow failed';
          setWorkflowError(backendError);
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
    <div className="min-h-screen bg-[#04221f] flex flex-col items-center justify-center p-6 pt-32">
      <div className="w-full max-w-2xl">
        {/* Header section */}
        <div className="text-center mb-12">
          <div className="mb-6 inline-flex items-center gap-2 px-4 py-2 rounded-full border border-[#dbf226]/20 bg-[#dbf226]/5">
            <div className="w-2 h-2 bg-[#dbf226] rounded-full animate-pulse" />
            <span className="text-xs font-semibold tracking-wider text-[#dbf226]">ANALYZING</span>
          </div>
          <h1 className="font-serif text-5xl md:text-6xl font-bold text-white mb-3" style={{ fontFamily: 'var(--font-serif)' }}>
            Daksha
          </h1>
          <p className="text-lg text-white/60 font-medium">
            {workflowError ? 'Analysis encountered an issue' : 'Analyzing your application…'}
          </p>
          {!workflowError && (
            <p className="text-white/40 text-sm mt-3">{steps[step]}</p>
          )}
        </div>

        {/* Main card */}
        <div className="rounded-3xl p-10 bg-white/[0.02] border border-white/10 backdrop-blur-sm">
          {/* Progress section */}
          <div className="mb-10">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-bold uppercase tracking-widest text-white/50">Progress</span>
              <span className="text-xs font-semibold text-[#dbf226]">{Math.round((step / agentSteps.length) * 100)}%</span>
            </div>
            <div className="h-2 bg-white/10 rounded-full overflow-hidden">
              <div
                className="bg-gradient-to-r from-[#dbf226] to-[#dbf226]/80 h-full rounded-full transition-all duration-700"
                style={{ width: `${(step / agentSteps.length) * 100}%` }}
              />
            </div>
          </div>

          {/* Agent steps */}
          <div className="space-y-3 mb-8">
            {agentSteps.map((agent, i) => {
              const status = i < step ? 'complete' : i === step ? 'running' : 'pending'
              return <AgentStatus key={agent.name} name={agent.name} description={agent.description} status={status} />
            })}
          </div>

          {/* Error display */}
          {workflowError && (
            <div className="mt-8 p-4 rounded-2xl bg-red-500/10 border border-red-500/20">
              <p className="text-red-400 text-sm leading-relaxed">{workflowError}</p>
            </div>
          )}
          {!workflowError && errorCount > 0 && (
            <div className="mt-4 text-amber-400 text-xs text-center font-medium">Connection retry {errorCount}/5</div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Analysis;

