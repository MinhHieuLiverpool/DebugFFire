import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import AppLayout from './layouts/AppLayout'
import NotFoundPage from './pages/NotFoundPage'
import ZoneAnalyzerPage from './pages/ZoneAnalyzerPage'
import ZoneOverlayPage from './pages/ZoneOverlayPage'

const App = () => (
  <BrowserRouter>
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<ZoneAnalyzerPage />} />
        <Route path="analyzer" element={<Navigate to="/" replace />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
      <Route path="/overlay" element={<ZoneOverlayPage />} />
    </Routes>
  </BrowserRouter>
)

export default App
