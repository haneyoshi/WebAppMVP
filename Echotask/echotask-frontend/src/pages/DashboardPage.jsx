const dashboardSections = [
  { title: "Today's Operations", message: 'Operational summary will appear here when dashboard data is connected.' },
  { title: 'Attendance / Worker Availability', message: 'Attendance and shared availability are not connected in this foundation slice.' },
  { title: 'Area Coverage', message: 'Regular and temporary area coverage will appear here. Interactive map work is deferred.' },
  { title: "Today's Events", message: 'Event reminders are not connected yet.' },
]

function DashboardPage() {
  return (
    <section aria-labelledby="dashboard-title">
      <div className="page-heading">
        <p className="eyebrow">Daily overview</p>
        <h2 id="dashboard-title">Dashboard</h2>
        <p className="muted-text">A shared operational view of attendance, availability, and area coverage.</p>
      </div>
      <div className="dashboard-grid">
        {dashboardSections.map((section) => (
          <article className="dashboard-card" key={section.title}>
            <h3>{section.title}</h3>
            <p className="empty-state">{section.message}</p>
          </article>
        ))}
      </div>
    </section>
  )
}

export default DashboardPage
