import { render, screen } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it } from 'vitest'
import App from './App'

const renderApp = (entry: string) => render(<QueryClientProvider client={new QueryClient()}><MemoryRouter initialEntries={[entry]}><App /></MemoryRouter></QueryClientProvider>)

describe('StockPilot application shell', () => {
  it('renders the public operating message', () => {
    renderApp('/')

    expect(screen.getByText(/See the signal before it becomes a/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /open workspace/i })).toBeInTheDocument()
  })

  it('renders an honest empty workspace state', () => {
    renderApp('/app')

    expect(screen.getByText(/This is a clean workspace/i)).toBeInTheDocument()
    expect(screen.getByText(/No movement data yet/i)).toBeInTheDocument()
  })
})
