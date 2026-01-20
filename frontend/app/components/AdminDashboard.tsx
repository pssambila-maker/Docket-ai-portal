'use client'

import { useState, useEffect } from 'react'
import {
  User,
  UserStats,
  AdminDashboard as AdminDashboardData,
  getAdminUsers,
  getAdminStats,
  updateUserRole,
  deleteUser,
} from '../lib/api'

interface AdminDashboardProps {
  user: User
  onBack: () => void
}

export default function AdminDashboard({ user, onBack }: AdminDashboardProps) {
  const [users, setUsers] = useState<UserStats[]>([])
  const [stats, setStats] = useState<AdminDashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [activeTab, setActiveTab] = useState<'overview' | 'users' | 'usage'>('overview')

  useEffect(() => {
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError('')

    const [usersResult, statsResult] = await Promise.all([
      getAdminUsers(),
      getAdminStats(7),
    ])

    if (usersResult.error) {
      setError(usersResult.error)
    } else {
      setUsers(usersResult.data || [])
    }

    if (statsResult.data) {
      setStats(statsResult.data)
    }

    setLoading(false)
  }

  const handleRoleChange = async (userId: number, newRole: string) => {
    const result = await updateUserRole(userId, newRole)
    if (result.error) {
      alert(result.error)
    } else {
      loadData()
    }
  }

  const handleDeleteUser = async (userId: number, email: string) => {
    if (!confirm(`Are you sure you want to delete user ${email}? This cannot be undone.`)) {
      return
    }
    const result = await deleteUser(userId)
    if (result.error) {
      alert(result.error)
    } else {
      loadData()
    }
  }

  const formatNumber = (num: number) => {
    return num.toLocaleString()
  }

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString()
  }

  if (loading) {
    return (
      <div style={styles.container}>
        <div style={styles.loading}>Loading admin data...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={styles.container}>
        <div style={styles.error}>
          <h2>Access Denied</h2>
          <p>{error}</p>
          <button onClick={onBack} style={styles.backButton}>
            Back to Chat
          </button>
        </div>
      </div>
    )
  }

  return (
    <div style={styles.container}>
      <header style={styles.header}>
        <div style={styles.headerLeft}>
          <button onClick={onBack} style={styles.backButton}>
            &larr; Back
          </button>
          <h1 style={styles.title}>Admin Dashboard</h1>
        </div>
        <div style={styles.headerRight}>
          <span style={styles.userBadge}>{user.email}</span>
        </div>
      </header>

      <nav style={styles.tabs}>
        <button
          style={{...styles.tab, ...(activeTab === 'overview' ? styles.tabActive : {})}}
          onClick={() => setActiveTab('overview')}
        >
          Overview
        </button>
        <button
          style={{...styles.tab, ...(activeTab === 'users' ? styles.tabActive : {})}}
          onClick={() => setActiveTab('users')}
        >
          Users ({users.length})
        </button>
        <button
          style={{...styles.tab, ...(activeTab === 'usage' ? styles.tabActive : {})}}
          onClick={() => setActiveTab('usage')}
        >
          Usage Stats
        </button>
      </nav>

      <main style={styles.main}>
        {activeTab === 'overview' && stats && (
          <div style={styles.overview}>
            <div style={styles.statsGrid}>
              <div style={styles.statCard}>
                <div style={styles.statValue}>{formatNumber(stats.stats.total_users)}</div>
                <div style={styles.statLabel}>Total Users</div>
              </div>
              <div style={styles.statCard}>
                <div style={styles.statValue}>{formatNumber(stats.stats.total_requests)}</div>
                <div style={styles.statLabel}>Total Requests</div>
              </div>
              <div style={styles.statCard}>
                <div style={styles.statValue}>{formatNumber(stats.stats.total_tokens)}</div>
                <div style={styles.statLabel}>Total Tokens</div>
              </div>
              <div style={{...styles.statCard, ...styles.statCardHighlight}}>
                <div style={styles.statValue}>{formatNumber(stats.stats.active_users_today)}</div>
                <div style={styles.statLabel}>Active Today</div>
              </div>
              <div style={{...styles.statCard, ...styles.statCardHighlight}}>
                <div style={styles.statValue}>{formatNumber(stats.stats.requests_today)}</div>
                <div style={styles.statLabel}>Requests Today</div>
              </div>
              <div style={{...styles.statCard, ...styles.statCardHighlight}}>
                <div style={styles.statValue}>{formatNumber(stats.stats.tokens_today)}</div>
                <div style={styles.statLabel}>Tokens Today</div>
              </div>
            </div>

            <div style={styles.section}>
              <h2 style={styles.sectionTitle}>Usage by Model</h2>
              <div style={styles.tableContainer}>
                <table style={styles.table}>
                  <thead>
                    <tr>
                      <th style={styles.th}>Model</th>
                      <th style={styles.thRight}>Requests</th>
                      <th style={styles.thRight}>Total Tokens</th>
                      <th style={styles.thRight}>Prompt</th>
                      <th style={styles.thRight}>Completion</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.usage_by_model.map((m) => (
                      <tr key={m.model}>
                        <td style={styles.td}>{m.model}</td>
                        <td style={styles.tdRight}>{formatNumber(m.request_count)}</td>
                        <td style={styles.tdRight}>{formatNumber(m.total_tokens)}</td>
                        <td style={styles.tdRight}>{formatNumber(m.prompt_tokens)}</td>
                        <td style={styles.tdRight}>{formatNumber(m.completion_tokens)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'users' && (
          <div style={styles.section}>
            <h2 style={styles.sectionTitle}>User Management</h2>
            <div style={styles.tableContainer}>
              <table style={styles.table}>
                <thead>
                  <tr>
                    <th style={styles.th}>ID</th>
                    <th style={styles.th}>Email</th>
                    <th style={styles.th}>Role</th>
                    <th style={styles.thRight}>Requests</th>
                    <th style={styles.thRight}>Tokens</th>
                    <th style={styles.th}>Created</th>
                    <th style={styles.th}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {users.map((u) => (
                    <tr key={u.id}>
                      <td style={styles.td}>{u.id}</td>
                      <td style={styles.td}>{u.email}</td>
                      <td style={styles.td}>
                        <select
                          value={u.role}
                          onChange={(e) => handleRoleChange(u.id, e.target.value)}
                          style={styles.roleSelect}
                          disabled={u.id === user.id}
                        >
                          <option value="user">user</option>
                          <option value="admin">admin</option>
                        </select>
                      </td>
                      <td style={styles.tdRight}>{formatNumber(u.total_requests)}</td>
                      <td style={styles.tdRight}>{formatNumber(u.total_tokens)}</td>
                      <td style={styles.td}>{formatDate(u.created_at)}</td>
                      <td style={styles.td}>
                        {u.id !== user.id && (
                          <button
                            onClick={() => handleDeleteUser(u.id, u.email)}
                            style={styles.deleteButton}
                          >
                            Delete
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {activeTab === 'usage' && stats && (
          <div>
            <div style={styles.section}>
              <h2 style={styles.sectionTitle}>Top Users by Token Usage</h2>
              <div style={styles.tableContainer}>
                <table style={styles.table}>
                  <thead>
                    <tr>
                      <th style={styles.th}>User</th>
                      <th style={styles.thRight}>Requests</th>
                      <th style={styles.thRight}>Total Tokens</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.usage_by_user.map((u) => (
                      <tr key={u.user_id}>
                        <td style={styles.td}>{u.email}</td>
                        <td style={styles.tdRight}>{formatNumber(u.request_count)}</td>
                        <td style={styles.tdRight}>{formatNumber(u.total_tokens)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div style={styles.section}>
              <h2 style={styles.sectionTitle}>Daily Usage (Last 7 Days)</h2>
              <div style={styles.tableContainer}>
                <table style={styles.table}>
                  <thead>
                    <tr>
                      <th style={styles.th}>Date</th>
                      <th style={styles.thRight}>Requests</th>
                      <th style={styles.thRight}>Tokens</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.daily_usage.map((d) => (
                      <tr key={d.date}>
                        <td style={styles.td}>{d.date}</td>
                        <td style={styles.tdRight}>{formatNumber(d.request_count)}</td>
                        <td style={styles.tdRight}>{formatNumber(d.total_tokens)}</td>
                      </tr>
                    ))}
                    {stats.daily_usage.length === 0 && (
                      <tr>
                        <td colSpan={3} style={{...styles.td, textAlign: 'center'}}>
                          No usage data available
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}

const styles: { [key: string]: React.CSSProperties } = {
  container: {
    minHeight: '100vh',
    background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
    color: '#e4e4e7',
  },
  loading: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
    fontSize: '1.25rem',
  },
  error: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: '100vh',
    textAlign: 'center',
    padding: '2rem',
  },
  header: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '1rem 2rem',
    borderBottom: '1px solid rgba(255,255,255,0.1)',
    background: 'rgba(0,0,0,0.2)',
  },
  headerLeft: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },
  backButton: {
    background: 'rgba(255,255,255,0.1)',
    border: 'none',
    color: '#e4e4e7',
    padding: '0.5rem 1rem',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '0.9rem',
  },
  title: {
    fontSize: '1.5rem',
    fontWeight: '600',
    margin: 0,
  },
  userBadge: {
    background: 'rgba(139, 92, 246, 0.3)',
    padding: '0.5rem 1rem',
    borderRadius: '20px',
    fontSize: '0.85rem',
  },
  tabs: {
    display: 'flex',
    gap: '0.5rem',
    padding: '1rem 2rem',
    borderBottom: '1px solid rgba(255,255,255,0.1)',
  },
  tab: {
    background: 'transparent',
    border: 'none',
    color: '#a1a1aa',
    padding: '0.75rem 1.5rem',
    borderRadius: '6px',
    cursor: 'pointer',
    fontSize: '0.95rem',
    transition: 'all 0.2s',
  },
  tabActive: {
    background: 'rgba(139, 92, 246, 0.3)',
    color: '#e4e4e7',
  },
  main: {
    padding: '2rem',
    maxWidth: '1400px',
    margin: '0 auto',
  },
  overview: {
    display: 'flex',
    flexDirection: 'column',
    gap: '2rem',
  },
  statsGrid: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
    gap: '1rem',
  },
  statCard: {
    background: 'rgba(255,255,255,0.05)',
    borderRadius: '12px',
    padding: '1.5rem',
    textAlign: 'center',
  },
  statCardHighlight: {
    background: 'rgba(139, 92, 246, 0.2)',
    border: '1px solid rgba(139, 92, 246, 0.3)',
  },
  statValue: {
    fontSize: '2rem',
    fontWeight: '700',
    color: '#fff',
    marginBottom: '0.5rem',
  },
  statLabel: {
    fontSize: '0.9rem',
    color: '#a1a1aa',
  },
  section: {
    background: 'rgba(255,255,255,0.03)',
    borderRadius: '12px',
    padding: '1.5rem',
    marginBottom: '1.5rem',
  },
  sectionTitle: {
    fontSize: '1.1rem',
    fontWeight: '600',
    marginTop: 0,
    marginBottom: '1rem',
    color: '#e4e4e7',
  },
  tableContainer: {
    overflowX: 'auto',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
  },
  th: {
    textAlign: 'left',
    padding: '0.75rem 1rem',
    borderBottom: '1px solid rgba(255,255,255,0.1)',
    color: '#a1a1aa',
    fontWeight: '500',
    fontSize: '0.85rem',
  },
  thRight: {
    textAlign: 'right',
    padding: '0.75rem 1rem',
    borderBottom: '1px solid rgba(255,255,255,0.1)',
    color: '#a1a1aa',
    fontWeight: '500',
    fontSize: '0.85rem',
  },
  td: {
    padding: '0.75rem 1rem',
    borderBottom: '1px solid rgba(255,255,255,0.05)',
    fontSize: '0.9rem',
  },
  tdRight: {
    textAlign: 'right',
    padding: '0.75rem 1rem',
    borderBottom: '1px solid rgba(255,255,255,0.05)',
    fontSize: '0.9rem',
    fontFamily: 'monospace',
  },
  roleSelect: {
    background: 'rgba(255,255,255,0.1)',
    border: '1px solid rgba(255,255,255,0.2)',
    borderRadius: '4px',
    color: '#e4e4e7',
    padding: '0.25rem 0.5rem',
    cursor: 'pointer',
  },
  deleteButton: {
    background: 'rgba(239, 68, 68, 0.2)',
    border: '1px solid rgba(239, 68, 68, 0.4)',
    color: '#ef4444',
    padding: '0.25rem 0.75rem',
    borderRadius: '4px',
    cursor: 'pointer',
    fontSize: '0.8rem',
  },
}
