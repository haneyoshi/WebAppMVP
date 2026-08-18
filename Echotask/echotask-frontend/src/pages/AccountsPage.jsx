import { useCallback, useEffect, useState } from 'react'
import { getAreas } from '../api/locations'
import { createUser, getUsers, updateUser } from '../api/users'

const emptyForm = { name: '', email: '', password: '', role: 'worker', area_id: '' }

export default function AccountsPage({ currentUser }) {
  const [users, setUsers] = useState([])
  const [areas, setAreas] = useState([])
  const [form, setForm] = useState(emptyForm)
  const [editingId, setEditingId] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true); setError('')
    try {
      const [userRows, areaRows] = await Promise.all([getUsers(), getAreas()])
      setUsers(userRows); setAreas(areaRows)
    } catch (requestError) { setError(requestError.message) }
    finally { setLoading(false) }
  }, [])

  useEffect(() => { load() }, [load])

  function beginEdit(user) {
    setEditingId(user.user_id)
    setForm({ name: user.name, email: user.email, password: '', role: user.role, area_id: user.area_id ?? '' })
    setError('')
  }

  function cancel() { setEditingId(null); setForm(emptyForm); setError('') }

  async function submit(event) {
    event.preventDefault(); setSaving(true); setError('')
    const payload = { name: form.name, email: form.email, role: form.role, area_id: form.role === 'worker' ? Number(form.area_id) : null }
    if (form.password) payload.password = form.password
    try {
      if (editingId) await updateUser(editingId, payload)
      else await createUser({ ...payload, password: form.password })
      cancel(); await load()
    } catch (requestError) { setError(requestError.message) }
    finally { setSaving(false) }
  }

  async function toggleActive(user) {
    setSaving(true); setError('')
    try { await updateUser(user.user_id, { is_active: !user.is_active }); await load() }
    catch (requestError) { setError(requestError.message) }
    finally { setSaving(false) }
  }

  return <section>
    <div className="page-heading"><p className="eyebrow">Administration</p><h2>Accounts</h2><p className="muted-text">Create and maintain EchoTask user accounts.</p></div>
    <form className="account-form" onSubmit={submit}>
      <h3>{editingId ? 'Edit account' : 'New account'}</h3>
      <label>Name<input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} /></label>
      <label>Email<input required type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} /></label>
      <label>Password<input required={!editingId} type="password" value={form.password} onChange={(e) => setForm({ ...form, password: e.target.value })} placeholder={editingId ? 'Leave blank to keep current password' : ''} /></label>
      <label>Role<select value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value, area_id: e.target.value === 'worker' ? form.area_id : '' })}><option value="worker">Worker</option><option value="coordinator">Coordinator</option><option value="supervisor">Supervisor</option></select></label>
      {form.role === 'worker' && <label>Regular area<select required value={form.area_id} onChange={(e) => setForm({ ...form, area_id: e.target.value })}><option value="">Select an area</option>{areas.map((area) => {
        const assignedUser = users.find((user) => user.user_id === area.assigned_user_id)
        const isOccupiedByAnotherWorker = area.assigned_user_id !== null && area.assigned_user_id !== editingId
        const assignmentLabel = assignedUser ? ` (Assigned to ${assignedUser.name})` : ' (Assigned)'
        return <option key={area.area_id} value={area.area_id} disabled={isOccupiedByAnotherWorker}>{area.building_name} — {area.area_name}{isOccupiedByAnotherWorker ? assignmentLabel : ''}</option>
      })}</select></label>}
      <div className="account-actions"><button disabled={saving}>{saving ? 'Saving...' : editingId ? 'Save changes' : 'Create account'}</button>{editingId && <button type="button" className="secondary-button" onClick={cancel}>Cancel</button>}</div>
    </form>
    {error && <p className="form-error" role="alert">{error}</p>}
    {loading && <p className="muted-text">Loading accounts&hellip;</p>}
    {!loading && users.length === 0 && <p className="empty-state">No accounts found.</p>}
    {!loading && <ul className="account-list">{users.map((user) => <li key={user.user_id}><div><h3>{user.name}</h3><p>{user.email} · {user.role}{user.area_name ? ` · ${user.area_name}` : ''}</p></div><div className="account-actions"><span className={`status-badge${user.is_active ? '' : ' status-badge--inactive'}`}>{user.is_active ? 'Active' : 'Inactive'}</span><button type="button" className="secondary-button" disabled={saving} onClick={() => beginEdit(user)}>Edit</button><button type="button" className="secondary-button" disabled={saving || user.user_id === currentUser.user_id} onClick={() => toggleActive(user)}>{user.is_active ? 'Deactivate' : 'Reactivate'}</button></div></li>)}</ul>}
  </section>
}
