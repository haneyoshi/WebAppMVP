import { useEffect, useState } from 'react'
import { Navigate, Route, Routes } from 'react-router-dom'
import './App.css'
import { getCurrentUser, login, logout } from './api/session'
import AppShell from './components/AppShell'
import AssignmentsPage from './pages/AssignmentsPage'
import AccountsPage from './pages/AccountsPage'
import AttendancePage from './pages/AttendancePage'
import DashboardPage from './pages/DashboardPage'
import EventsPage from './pages/EventsPage'
import LoginPage from './pages/LoginPage'
import SnowLogsPage from './pages/SnowLogsPage'
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
        {(user.role === 'coordinator' || user.role === 'supervisor') && (
          <Route path="assignments" element={<AssignmentsPage />} />
        )}
        <Route path="supplies" element={<SuppliesRequestPage user={user} />} />
        <Route path="snow-logs" element={<SnowLogsPage user={user} />} />
        <Route path="events" element={<EventsPage user={user} />} />
        {user.role === 'supervisor' && (
          <Route path="accounts" element={<AccountsPage currentUser={user} />} />
        )}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Route>
    </Routes>
  )
}

export default App
