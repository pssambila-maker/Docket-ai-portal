'use client'

import { useState, useEffect, useRef } from 'react'
import { sendChat, getModels, getChatHistory, User, ChatHistoryItem } from '../lib/api'
import styles from './Chat.module.css'

interface ChatProps {
  user: User
  onLogout: () => void
}

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  model?: string
  timestamp: Date
}

export default function Chat({ user, onLogout }: ChatProps) {
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [model, setModel] = useState('')
  const [models, setModels] = useState<string[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const messagesEndRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // Load available models
    getModels().then((result) => {
      if (result.data) {
        setModels(result.data)
        setModel(result.data[0] || '')
      }
    })

    // Load chat history
    getChatHistory(20).then((result) => {
      if (result.data) {
        const historyMessages: Message[] = []
        result.data.reverse().forEach((item: ChatHistoryItem) => {
          historyMessages.push({
            id: `user-${item.id}`,
            role: 'user',
            content: item.prompt,
            timestamp: new Date(item.created_at),
          })
          historyMessages.push({
            id: `assistant-${item.id}`,
            role: 'assistant',
            content: item.response,
            model: item.model,
            timestamp: new Date(item.created_at),
          })
        })
        setMessages(historyMessages)
      }
    })
  }, [])

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || loading) return

    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
    }

    setMessages((prev) => [...prev, userMessage])
    setInput('')
    setLoading(true)
    setError('')

    const result = await sendChat(userMessage.content, model)

    if (result.error) {
      setError(result.error)
    } else if (result.data) {
      const assistantMessage: Message = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: result.data.response,
        model: result.data.model,
        timestamp: new Date(),
      }
      setMessages((prev) => [...prev, assistantMessage])
    }

    setLoading(false)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div className={styles.headerLeft}>
          <h1>AI Portal</h1>
          <select
            value={model}
            onChange={(e) => setModel(e.target.value)}
            className={styles.modelSelect}
          >
            {models.map((m) => (
              <option key={m} value={m}>
                {m}
              </option>
            ))}
          </select>
        </div>
        <div className={styles.headerRight}>
          <span className={styles.userEmail}>{user.email}</span>
          <button onClick={onLogout} className={styles.logoutButton}>
            Logout
          </button>
        </div>
      </header>

      <main className={styles.main}>
        <div className={styles.messages}>
          {messages.length === 0 && (
            <div className={styles.welcome}>
              <h2>Welcome to AI Portal</h2>
              <p>Start a conversation by typing a message below.</p>
            </div>
          )}
          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`${styles.message} ${
                msg.role === 'user' ? styles.userMessage : styles.assistantMessage
              }`}
            >
              <div className={styles.messageContent}>
                <div className={styles.messageHeader}>
                  <span className={styles.messageRole}>
                    {msg.role === 'user' ? 'You' : 'Assistant'}
                  </span>
                  {msg.model && <span className={styles.messageModel}>{msg.model}</span>}
                </div>
                <div className={styles.messageText}>{msg.content}</div>
              </div>
            </div>
          ))}
          {loading && (
            <div className={`${styles.message} ${styles.assistantMessage}`}>
              <div className={styles.messageContent}>
                <div className={styles.typing}>
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      </main>

      <footer className={styles.footer}>
        {error && <div className={styles.error}>{error}</div>}
        <form onSubmit={handleSubmit} className={styles.inputForm}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your message..."
            className={styles.input}
            disabled={loading}
            rows={1}
          />
          <button
            type="submit"
            className={styles.sendButton}
            disabled={loading || !input.trim()}
          >
            {loading ? 'Sending...' : 'Send'}
          </button>
        </form>
      </footer>
    </div>
  )
}
