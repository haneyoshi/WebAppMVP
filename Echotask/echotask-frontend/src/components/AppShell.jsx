import { NavLink, Outlet } from 'react-router-dom'

const navigation = [
  { to: '/', label: 'Dashboard', end: true },
  { to: '/attendance', label: 'Attendance' },
  { to: '/supplies', label: 'Supplies' },
  { to: '/snow-logs', label: 'Snow Logs' },
  { to: '/events', label: 'Events' },
]

function AppShell({ user, onLogout }) {
  const canManageAssignments = user.role === 'coordinator' || user.role === 'supervisor'
  const links = [
    ...navigation.slice(0, 2),
    ...(canManageAssignments ? [{ to: '/assignments', label: 'Assignments' }] : []),
    ...navigation.slice(2),
    ...(user.role === 'supervisor' ? [{ to: '/accounts', label: 'Accounts' }] : []),
  ]

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">Caretaking operations</p>
          <h1>EchoTask</h1>
        </div>
        <div className="user-menu">
          <div>
            <strong>{user.name}</strong>
            <span>{user.role}</span>
          </div>
          <button type="button" className="secondary-button" onClick={onLogout}>
            Logout
          </button>
        </div>
      </header>

      <nav className="app-navigation" aria-label="Main navigation">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.end}
            className={({ isActive }) => isActive ? 'active' : undefined}
          >
            {link.label}
          </NavLink>
        ))}
      </nav>

      <main className="app-content">
        <Outlet />
      </main>
    </div>
  )
}

export default AppShell
