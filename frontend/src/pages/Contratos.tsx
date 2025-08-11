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
import { api } from '@/lib/api'

interface Contract {
  id: string
  bank: string
  balance: number
  cet: number
  dueDate: string
}

export default function Contratos({
  onViewExtratos,
}: {
  onViewExtratos?: (id: string) => void
}) {
  const [contracts, setContracts] = useState<Contract[]>([])
  const [bankFilter, setBankFilter] = useState('')
  const [dueFilter, setDueFilter] = useState('')
  const [startExport, setStartExport] = useState('')
  const [endExport, setEndExport] = useState('')
  const [empresaExport, setEmpresaExport] = useState('')
  const [transStart, setTransStart] = useState('')
  const [transEnd, setTransEnd] = useState('')
  const [isTransExporting, setIsTransExporting] = useState(false)
  const [uploadContract, setUploadContract] = useState<string | null>(null)
  const [isExporting, setIsExporting] = useState(false)
  const [formOpen, setFormOpen] = useState(false)
  const [editing, setEditing] = useState<Contract | null>(null)
  const [form, setForm] = useState({
    empresaId: '',
    numero: '',
    bank: '',
    balance: '',
    cet: '',
    dueDate: '',
  })

  const loadContracts = () => {
    api('/contracts')
      .then((res) => res.json())
      .then(setContracts)
      .catch((err) => console.error('Failed to load contracts', err))
  }

  useEffect(() => {
    loadContracts()
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
    setIsExporting(true)
    console.log('Iniciando exportação', { startExport, endExport })
    try {
      const params = new URLSearchParams({
        start_date: startExport,
        end_date: endExport,
      })
      const res = await api(`/accruals/export?${params.toString()}`)
      if (!res.ok) {
        let message = 'Não foi possível exportar os juros. Tente novamente mais tarde.'
        try {
          const data = await res.json()
          message = data.detail ?? message
        } catch {
          // ignore
        }
        throw new Error(message)
      }
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'accruals.csv'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      console.log('Exportação concluída com sucesso')
    } catch (err) {
      console.error('Erro ao exportar juros', err)
      const message =
        err instanceof Error
          ? err.message
          : 'Não foi possível exportar os juros. Tente novamente mais tarde.'
      alert(message)
    } finally {
      setIsExporting(false)
    }
  }

  const handleTransactionsExport = async () => {
    setIsTransExporting(true)
    try {
      const params = new URLSearchParams({
        empresa_id: empresaExport,
        start_date: transStart,
        end_date: transEnd,
      })
      const res = await api(`/transactions/export?${params.toString()}`)
      if (!res.ok) {
        let message =
          'Não foi possível exportar as transações. Tente novamente mais tarde.'
        try {
          const data = await res.json()
          message = data.detail ?? message
        } catch {
          // ignore
        }
        throw new Error(message)
      }
      const blob = await res.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = 'transactions.txt'
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Erro ao exportar transações', err)
      const message =
        err instanceof Error
          ? err.message
          : 'Não foi possível exportar as transações. Tente novamente mais tarde.'
      alert(message)
    } finally {
      setIsTransExporting(false)
    }
  }

  const openNew = () => {
    setEditing(null)
    setForm({
      empresaId: '',
      numero: '',
      bank: '',
      balance: '',
      cet: '',
      dueDate: '',
    })
    setFormOpen(true)
  }

  const openEdit = (c: Contract) => {
    setEditing(c)
    setForm({
      empresaId: '',
      numero: '',
      bank: c.bank,
      balance: String(c.balance),
      cet: String(c.cet),
      dueDate: c.dueDate,
    })
    setFormOpen(true)
  }

  const updateForm = (field: string, value: string) =>
    setForm((f) => ({ ...f, [field]: value }))

  const handleFormSubmit = async () => {
    const payload = {
      empresa_id: Number(form.empresaId),
      numero: form.numero,
      bank: form.bank,
      balance: parseFloat(form.balance),
      cet: parseFloat(form.cet),
      dueDate: form.dueDate,
    }
    const method = editing ? 'PUT' : 'POST'
    const url = editing ? `/contracts/${editing.id}` : '/contracts'
    await api(url, {
      method,
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    setFormOpen(false)
    loadContracts()
  }

  return (
    <div className="p-4 space-y-4">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold">Contratos</h1>
        <button
          className="px-4 py-2 bg-green-600 text-white rounded"
          onClick={openNew}
        >
          Novo Contrato
        </button>
      </div>
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
          disabled={!startExport || !endExport || isExporting}
        >
          {isExporting ? 'Exportando...' : 'Exportar juros'}
        </button>
      </div>
      <div className="flex gap-4 items-end">
        <div className="space-y-2">
          <Label htmlFor="empresa-export">Empresa ID</Label>
          <Input
            id="empresa-export"
            value={empresaExport}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setEmpresaExport(e.target.value)
            }
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="start-trans">Início</Label>
          <Input
            id="start-trans"
            type="date"
            value={transStart}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setTransStart(e.target.value)
            }
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="end-trans">Fim</Label>
          <Input
            id="end-trans"
            type="date"
            value={transEnd}
            onChange={(e: React.ChangeEvent<HTMLInputElement>) =>
              setTransEnd(e.target.value)
            }
          />
        </div>
        <button
          className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
          onClick={handleTransactionsExport}
          disabled={
            !empresaExport || !transStart || !transEnd || isTransExporting
          }
        >
          {isTransExporting ? 'Exportando...' : 'Exportar transações'}
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
              <div className="flex gap-2">
                <button
                  className="px-2 py-1 bg-blue-600 text-white rounded"
                  onClick={() => onViewExtratos?.(c.id)}
                >
                  Extratos
                </button>
                <button
                  className="px-2 py-1 bg-yellow-600 text-white rounded"
                  onClick={() => openEdit(c)}
                >
                  Editar
                </button>
                <button
                  className="px-2 py-1 bg-green-600 text-white rounded"
                  onClick={() => setUploadContract(c.id)}
                >
                  Importar Extrato
                </button>
              </div>
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
    {formOpen && (
      <div className="p-4 border space-y-2">
        <h2 className="text-xl font-bold">
          {editing ? 'Editar' : 'Novo'} Contrato
        </h2>
        <div className="space-y-2">
          <Label htmlFor="empresa">Empresa ID</Label>
          <Input
            id="empresa"
            value={form.empresaId}
            onChange={(e) => updateForm('empresaId', e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="numero">Número</Label>
          <Input
            id="numero"
            value={form.numero}
            onChange={(e) => updateForm('numero', e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="bank-form">Banco</Label>
          <Input
            id="bank-form"
            value={form.bank}
            onChange={(e) => updateForm('bank', e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="balance-form">Saldo</Label>
          <Input
            id="balance-form"
            type="number"
            value={form.balance}
            onChange={(e) => updateForm('balance', e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="cet-form">CET</Label>
          <Input
            id="cet-form"
            type="number"
            value={form.cet}
            onChange={(e) => updateForm('cet', e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="due-form">Data</Label>
          <Input
            id="due-form"
            type="date"
            value={form.dueDate}
            onChange={(e) => updateForm('dueDate', e.target.value)}
          />
        </div>
        <div className="flex gap-2 pt-2">
          <button
            className="px-2 py-1 bg-blue-600 text-white rounded"
            onClick={handleFormSubmit}
          >
            Salvar
          </button>
          <button
            className="px-2 py-1 bg-gray-300 rounded"
            onClick={() => setFormOpen(false)}
          >
            Cancelar
          </button>
        </div>
      </div>
    )}
    </div>
  )
}
