import { useEffect, useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import { getCurrentUser, login, logout } from './api/session'
import AppShell from './components/AppShell'
import AttendancePage from './pages/AttendancePage'
import DashboardPage from './pages/DashboardPage'
import LoginPage from './pages/LoginPage'
import PlaceholderPage from './pages/PlaceholderPage'
import SuppliesRequestPage from './pages/SuppliesRequestPage'

function App() {
  const [user, setUser] = useState(null)
  const [isBootstrapping, setIsBootstrapping] = useState(true)

  useEffect(() => {
    let isActive = true

    getCurrentUser()
      .then((currentUser) => {
        if (isActive) setUser(currentUser)
      })
      .catch(() => {
        if (isActive) setUser(null)
      })
      .finally(() => {
        if (isActive) setIsBootstrapping(false)
      })

    return () => {
      isActive = false
    }
  }, [])

  async function handleLogin(credentials) {
    const currentUser = await login(credentials)
    setUser(currentUser)
  }

  async function handleLogout() {
    try {
      await logout()
    } finally {
      setUser(null)
    }
  }

  if (isBootstrapping) {
    return <div className="centered-state">Checking your EchoTask session…</div>
  }

  if (!user) {
    return <LoginPage onLogin={handleLogin} />
  }

  return (
    <Routes>
      <Route element={<AppShell user={user} onLogout={handleLogout} />}>
        <Route index element={<DashboardPage user={user} />} />
        <Route path="attendance" element={<AttendancePage user={user} />} />
        <Route path="supplies" element={<SuppliesRequestPage />} />
        <Route path="snow-logs" element={<PlaceholderPage title="Snow Logs" />} />
        <Route path="events" element={<PlaceholderPage title="Events" />} />
        {user.role === 'supervisor' && (
          <Route path="accounts" element={<PlaceholderPage title="Accounts" />} />
        )}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

export default App
