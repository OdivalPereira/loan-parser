import { useState } from 'react'
import Contratos from './pages/Contratos'
import Login from './pages/Login'
import ExtratosContrato from './pages/ExtratosContrato'

function App() {
  const [token, setToken] = useState(() =>
    typeof localStorage !== 'undefined' ? localStorage.getItem('token') : null,
  )
  const [extratosContract, setExtratosContract] = useState<string | null>(null)

  if (!token) {
    return <Login onLogin={setToken} />
  }

  if (extratosContract) {
    return (
      <ExtratosContrato
        contractId={extratosContract}
        onBack={() => setExtratosContract(null)}
      />
    )
  }

  return <Contratos onViewExtratos={setExtratosContract} />
}

export default App
