import { useEffect, useState } from 'react'
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
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Banco</TableHead>
            <TableHead>Saldo</TableHead>
            <TableHead>CET</TableHead>
            <TableHead>Vencimento</TableHead>
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
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
