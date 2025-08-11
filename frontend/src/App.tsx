import { useState } from 'react'
import Contratos from './pages/Contratos'
import Login from './pages/Login'

function App() {
  const [token, setToken] = useState(() =>
    typeof localStorage !== 'undefined' ? localStorage.getItem('token') : null,
  )

  if (!token) {
    return <Login onLogin={setToken} />
  }

  return <Contratos />
}

export default App
