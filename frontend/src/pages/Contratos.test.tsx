import { vi, describe, it, expect } from 'vitest'
import '@testing-library/jest-dom/vitest'
import { render, screen } from '@testing-library/react'

import Contratos from './Contratos'

vi.mock('@/lib/api', () => ({
  api: vi.fn().mockResolvedValue({ json: () => Promise.resolve([]) }),
}))

describe('Contratos', () => {
  it('renderiza título', () => {
    render(<Contratos />)
    expect(screen.getByText('Contratos')).toBeInTheDocument()
  })
})
