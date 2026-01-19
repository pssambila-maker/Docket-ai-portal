'use client'

import { useState } from 'react'
import { login, register } from '../lib/api'
import styles from './Auth.module.css'

interface LoginProps {
  onLogin: (token: string) => void
}

export default function Login({ onLogin }: LoginProps) {
  const [isRegister, setIsRegister] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [success, setSuccess] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')

    if (!email || !password) {
      setError('Please fill in all fields')
      return
    }

    if (isRegister && password !== confirmPassword) {
      setError('Passwords do not match')
      return
    }

    setLoading(true)

    try {
      if (isRegister) {
        const result = await register(email, password)
        if (result.error) {
          setError(result.error)
        } else {
          setSuccess('Registration successful! Please login.')
          setIsRegister(false)
          setPassword('')
          setConfirmPassword('')
        }
      } else {
        const result = await login(email, password)
        if (result.error) {
          setError(result.error)
        } else if (result.data) {
          localStorage.setItem('token', result.data.access_token)
          onLogin(result.data.access_token)
        }
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <h1 className={styles.title}>AI Portal</h1>
        <h2 className={styles.subtitle}>{isRegister ? 'Create Account' : 'Welcome Back'}</h2>

        <form onSubmit={handleSubmit} className={styles.form}>
          <div className={styles.field}>
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              disabled={loading}
            />
          </div>

          <div className={styles.field}>
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              disabled={loading}
            />
          </div>

          {isRegister && (
            <div className={styles.field}>
              <label htmlFor="confirmPassword">Confirm Password</label>
              <input
                id="confirmPassword"
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm your password"
                disabled={loading}
              />
            </div>
          )}

          {error && <div className={styles.error}>{error}</div>}
          {success && <div className={styles.success}>{success}</div>}

          <button type="submit" className={styles.button} disabled={loading}>
            {loading ? 'Please wait...' : isRegister ? 'Register' : 'Login'}
          </button>
        </form>

        <div className={styles.switch}>
          {isRegister ? (
            <p>
              Already have an account?{' '}
              <button onClick={() => { setIsRegister(false); setError(''); setSuccess(''); }}>
                Login
              </button>
            </p>
          ) : (
            <p>
              Don&apos;t have an account?{' '}
              <button onClick={() => { setIsRegister(true); setError(''); setSuccess(''); }}>
                Register
              </button>
            </p>
          )}
        </div>
      </div>
    </div>
  )
}
