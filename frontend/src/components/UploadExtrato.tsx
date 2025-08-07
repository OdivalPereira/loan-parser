import { useState } from 'react'

interface Props {
  contractId: string
  onClose: () => void
}

export default function UploadExtrato({ contractId, onClose }: Props) {
  const [file, setFile] = useState<File | null>(null)
  const [status, setStatus] = useState<'idle' | 'uploading' | 'success' | 'error'>('idle')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!file) return
    const formData = new FormData()
    formData.append('file', file)
    formData.append('contract_id', contractId)
    try {
      setStatus('uploading')
      const res = await fetch('/uploads', {
        method: 'POST',
        body: formData,
      })
      if (!res.ok) throw new Error('Upload failed')
      setStatus('success')
    } catch (err) {
      console.error(err)
      setStatus('error')
    }
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center">
      <form onSubmit={handleSubmit} className="bg-white p-4 rounded space-y-4">
        <h2 className="text-lg font-bold">Importar Extrato</h2>
        <input
          type="file"
          onChange={(e) => setFile(e.target.files?.[0] ?? null)}
        />
        <div className="flex gap-2">
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 text-white rounded disabled:opacity-50"
            disabled={!file || status === 'uploading'}
          >
            Enviar
          </button>
          <button
            type="button"
            className="px-4 py-2"
            onClick={onClose}
            disabled={status === 'uploading'}
          >
            Cancelar
          </button>
        </div>
        {status === 'uploading' && <p>Enviando...</p>}
        {status === 'success' && <p className="text-green-600">Arquivo enviado!</p>}
        {status === 'error' && <p className="text-red-600">Erro ao enviar.</p>}
      </form>
    </div>
  )
}
