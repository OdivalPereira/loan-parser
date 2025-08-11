import { useEffect, useState } from 'react'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { api } from '@/lib/api'

interface Extrato {
  id: number
  status: string
}

export default function ExtratosContrato({
  contractId,
  onBack,
}: {
  contractId: string
  onBack: () => void
}) {
  const [extratos, setExtratos] = useState<Extrato[]>([])

  useEffect(() => {
    api(`/contracts/${contractId}/extratos`)
      .then((res) => res.json())
      .then(setExtratos)
      .catch((err) => console.error('Failed to load extratos', err))
  }, [contractId])

  return (
    <div className="p-4 space-y-4">
      <button
        className="px-2 py-1 bg-gray-300 rounded"
        onClick={onBack}
      >
        Voltar
      </button>
      <h1 className="text-2xl font-bold">Extratos</h1>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>ID</TableHead>
            <TableHead>Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {extratos.map((e) => (
            <TableRow key={e.id}>
              <TableCell>{e.id}</TableCell>
              <TableCell>{e.status}</TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

