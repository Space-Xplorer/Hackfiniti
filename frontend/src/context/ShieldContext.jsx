import React, { createContext, useContext, useState } from 'react';

const ShieldContext = createContext();

export const ShieldProvider = ({ children }) => {
  const [view, setView] = useState('landing');
  const [service, setService] = useState(null);
  const [userData, setUserData] = useState({
    aadhaar: '',
    name: '',
    dob: '',
    email: '',
    password: ''
  });
  const [uploadedDocs, setUploadedDocs] = useState({});
  const [uploadedDocuments, setUploadedDocuments] = useState([]);
  const [applicantData, setApplicantData] = useState({});
  const [kycData, setKycData] = useState({});
  const [ocrPreviewData, setOcrPreviewData] = useState({});
  const [loanType, setLoanType] = useState('home');
  const [authToken, setAuthToken] = useState(null);
  const [applicationId, setApplicationId] = useState(null);
  const [requestId, setRequestId] = useState(null);
  const [workflowStatus, setWorkflowStatus] = useState(null);
  const [workflowResult, setWorkflowResult] = useState(null);
  const [workflowError, setWorkflowError] = useState(null);

  return (
    <ShieldContext.Provider
      value={{
        view, setView, service, setService,
        userData, setUserData,
        uploadedDocs, setUploadedDocs,
        uploadedDocuments, setUploadedDocuments,
        applicantData, setApplicantData,
        kycData, setKycData,
        ocrPreviewData, setOcrPreviewData,
        loanType, setLoanType,
        authToken, setAuthToken,
        applicationId, setApplicationId,
        requestId, setRequestId,
        workflowStatus, setWorkflowStatus,
        workflowResult, setWorkflowResult,
        workflowError, setWorkflowError
      }}
    >
      {children}
    </ShieldContext.Provider>
  );
};

export const useShield = () => useContext(ShieldContext);
