import { useEffect, useState } from 'react'
import type React from 'react'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import UploadExtrato from '@/components/UploadExtrato'

interface Contract {
  id: string
  bank: string
  balance: number
  cet: number
  dueDate: string
}

export default function Contratos() {
  const [contracts, setContracts] = useState<Contract[]>([])
  const [bankFilter, setBankFilter] = useState('')
  const [dueFilter, setDueFilter] = useState('')
  const [startExport, setStartExport] = useState('')
  const [endExport, setEndExport] = useState('')
  const [uploadContract, setUploadContract] = useState<string | null>(null)

  useEffect(() => {
    fetch('/contracts')
      .then((res) => res.json())
      .then(setContracts)
      .catch((err) => console.error('Failed to load contracts', err))
  }, [])

  const filtered = contracts.filter((c) => {
    const matchesBank = bankFilter
      ? c.bank.toLowerCase().includes(bankFilter.toLowerCase())
      : true
    const matchesDue = dueFilter
      ? new Date(c.dueDate) <= new Date(dueFilter)
      : true
    return matchesBank && matchesDue
  })

  const handleExport = async () => {
    const params = new URLSearchParams({
      start_date: startExport,
      end_date: endExport,
    })
    const res = await fetch(`/accruals/export?${params.toString()}`)
    const blob = await res.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = 'accruals.csv'
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  }

  return (
    <div className="p-4 space-y-4">
      <h1 className="text-2xl font-bold">Contratos</h1>
      <div className="flex gap-4">
        <div className="space-y-2">
          <Label htmlFor="bank">Banco</Label>
          <Input
            id="bank"
            placeholder="Filtrar por banco"
            value={bankFilter}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setBankFilter(e.target.value)
            }
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="due">Vencimento até</Label>
          <Input
            id="due"
            type="date"
            value={dueFilter}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setDueFilter(e.target.value)
            }
          />
        </div>
      </div>
      <div className="flex gap-4 items-end">
        <div className="space-y-2">
          <Label htmlFor="start">Início</Label>
          <Input
            id="start"
            type="date"
            value={startExport}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setStartExport(e.target.value)
            }
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="end">Fim</Label>
          <Input
            id="end"
            type="date"
            value={endExport}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setEndExport(e.target.value)
            }
          />
        </div>
        <button
          className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
          onClick={handleExport}
          disabled={!startExport || !endExport}
        >
          Exportar juros
        </button>
      </div>
      <Table>
        <TableHeader>
          <TableRow>
          <TableHead>Banco</TableHead>
          <TableHead>Saldo</TableHead>
          <TableHead>CET</TableHead>
          <TableHead>Vencimento</TableHead>
          <TableHead>Ações</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {filtered.map((c) => (
            <TableRow key={c.id}>
              <TableCell>{c.bank}</TableCell>
              <TableCell>
              {c.balance.toLocaleString('pt-BR', {
                style: 'currency',
                currency: 'BRL',
              })}
            </TableCell>
            <TableCell>{c.cet}%</TableCell>
            <TableCell>{c.dueDate}</TableCell>
            <TableCell>
              <button
                className="px-2 py-1 bg-green-600 text-white rounded"
                onClick={() => setUploadContract(c.id)}
              >
                Importar Extrato
              </button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
    {uploadContract && (
      <UploadExtrato
        contractId={uploadContract}
        onClose={() => setUploadContract(null)}
      />
    )}
    </div>
  )
}
