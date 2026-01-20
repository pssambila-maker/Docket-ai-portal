'use client'

import { useState, useEffect } from 'react'
import Login from './components/Login'
import Chat from './components/Chat'
import AdminDashboard from './components/AdminDashboard'
import { getMe, User } from './lib/api'

export default function Home() {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [showAdmin, setShowAdmin] = useState(false)

  useEffect(() => {
    // Check for existing token on mount
    const token = localStorage.getItem('token')
    if (token) {
      getMe().then((result) => {
        if (result.data) {
          setUser(result.data)
        } else {
          // Invalid token, remove it
          localStorage.removeItem('token')
        }
        setLoading(false)
      })
    } else {
      setLoading(false)
    }
  }, [])

  const handleLogin = (token: string) => {
    // Fetch user info after login using the token directly
    getMe(token).then((result) => {
      if (result.data) {
        setUser(result.data)
      }
    })
  }

  const handleLogout = () => {
    localStorage.removeItem('token')
    setUser(null)
    setShowAdmin(false)
  }

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #1a1a2e 0%, #16213e 100%)',
        color: 'white',
        fontSize: '1.25rem'
      }}>
        Loading...
      </div>
    )
  }

  if (!user) {
    return <Login onLogin={handleLogin} />
  }

  if (showAdmin) {
    return <AdminDashboard user={user} onBack={() => setShowAdmin(false)} />
  }

  return (
    <Chat
      user={user}
      onLogout={handleLogout}
      onAdminClick={() => setShowAdmin(true)}
    />
  )
}
