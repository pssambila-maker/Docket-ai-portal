export default function Home() {
  return (
    <main style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '100vh',
      padding: '2rem'
    }}>
      <h1>AI Portal</h1>
      <p>Welcome to the AI Portal MVP</p>
      <p style={{ color: '#666', marginTop: '1rem' }}>
        Frontend scaffolding complete. Full UI coming in Task 3.
      </p>
    </main>
  )
}
