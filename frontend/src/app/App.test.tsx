import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import App from './App'

describe('StockPilot application shell', () => {
  it('renders the public operating message', () => {
    render(
      <MemoryRouter initialEntries={['/']}>
        <App />
      </MemoryRouter>,
    )

    expect(screen.getByText(/See the signal before it becomes a/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /open workspace/i })).toBeInTheDocument()
  })

  it('renders an honest empty workspace state', () => {
    render(
      <MemoryRouter initialEntries={['/app']}>
        <App />
      </MemoryRouter>,
    )

    expect(screen.getByText(/This is a clean workspace/i)).toBeInTheDocument()
    expect(screen.getByText(/No movement data yet/i)).toBeInTheDocument()
  })
})
