import { BrowserRouter, Route, Routes } from 'react-router-dom'
import Analysis from './pages/Analysis'
import Config from './pages/Config'
import KYC from './pages/KYC'
import Landing from './pages/Landing'
import Preliminary from './pages/Preliminary'
import Result from './pages/Result'
import Selection from './pages/Selection'
import Upload from './pages/Upload'

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/selection" element={<Selection />} />
        <Route path="/upload" element={<Upload />} />
        <Route path="/preliminary" element={<Preliminary />} />
        <Route path="/kyc" element={<KYC />} />
        <Route path="/analysis" element={<Analysis />} />
        <Route path="/config" element={<Config />} />
        <Route path="/result" element={<Result />} />
      </Routes>
    </BrowserRouter>
  )
}
