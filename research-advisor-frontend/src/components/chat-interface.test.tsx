import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import { ChatInterface } from './chat-interface'

describe('ChatInterface', () => {
  const defaultProps = {
    messages: [],
    onSendMessage: vi.fn(),
  }

  it('renders without crashing', () => {
    render(<ChatInterface {...defaultProps} />)
    expect(screen.getByPlaceholderText(/type your response/i)).toBeInTheDocument()
  })

  it('renders the send button', () => {
    render(<ChatInterface {...defaultProps} />)
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument()
  })

  it('allows user to type a message', async () => {
    const user = userEvent.setup()
    render(<ChatInterface {...defaultProps} />)

    const textarea = screen.getByPlaceholderText(/type your response/i)
    await user.type(textarea, 'My research is about quantum computing')

    expect(textarea).toHaveValue('My research is about quantum computing')
  })

  it('calls onSendMessage when send button is clicked', async () => {
    const onSend = vi.fn()
    const user = userEvent.setup()
    render(<ChatInterface {...defaultProps} onSendMessage={onSend} />)

    const textarea = screen.getByPlaceholderText(/type your response/i)
    await user.type(textarea, 'Test message')
    await user.click(screen.getByRole('button', { name: /send/i }))

    expect(onSend).toHaveBeenCalledWith('Test message', undefined)
  })

  it('clears input after sending a message', async () => {
    const user = userEvent.setup()
    render(<ChatInterface {...defaultProps} />)

    const textarea = screen.getByPlaceholderText(/type your response/i)
    await user.type(textarea, 'Test message')
    await user.click(screen.getByRole('button', { name: /send/i }))

    expect(textarea).toHaveValue('')
  })

  it('does not send empty messages', async () => {
    const onSend = vi.fn()
    const user = userEvent.setup()
    render(<ChatInterface {...defaultProps} onSendMessage={onSend} />)

    await user.click(screen.getByRole('button', { name: /send/i }))

    expect(onSend).not.toHaveBeenCalled()
  })

  it('disables input when loading', () => {
    render(<ChatInterface {...defaultProps} isLoading={true} />)
    expect(screen.getByPlaceholderText(/type your response/i)).toBeDisabled()
  })

  it('disables send button when loading', () => {
    render(<ChatInterface {...defaultProps} isLoading={true} />)
    expect(screen.getByRole('button', { name: /send/i })).toBeDisabled()
  })

  it('displays messages in the message list', () => {
    const messages = [
      { id: '1', role: 'user' as const, content: 'Hello' },
      { id: '2', role: 'assistant' as const, content: 'Hi there!' },
    ]
    render(<ChatInterface {...defaultProps} messages={messages} />)

    expect(screen.getByText('Hello')).toBeInTheDocument()
    expect(screen.getByText('Hi there!')).toBeInTheDocument()
  })

  it('distinguishes user and assistant messages visually', () => {
    const messages = [
      { id: '1', role: 'user' as const, content: 'User message' },
      { id: '2', role: 'assistant' as const, content: 'Assistant message' },
    ]
    render(<ChatInterface {...defaultProps} messages={messages} />)

    // The bubble is the parent of the content wrapper div
    const userBubble = screen.getByText('User message').parentElement
    const assistantBubble = screen.getByText('Assistant message').parentElement

    expect(userBubble?.className).not.toBe(assistantBubble?.className)
  })

  it('renders attach button', () => {
    render(<ChatInterface {...defaultProps} />)
    expect(screen.getByRole('button', { name: /attach/i })).toBeInTheDocument()
  })

  it('uses custom placeholder', () => {
    render(<ChatInterface {...defaultProps} placeholder="Custom placeholder..." />)
    expect(screen.getByPlaceholderText('Custom placeholder...')).toBeInTheDocument()
  })

  it('shows intro when showIntro is true', () => {
    render(<ChatInterface {...defaultProps} showIntro={true} />)
    expect(
      screen.getByText(/we'll ask 3 quick questions to understand your research/i),
    ).toBeInTheDocument()
  })

  it('does not show intro when showIntro is false', () => {
    render(<ChatInterface {...defaultProps} showIntro={false} />)
    expect(
      screen.queryByText(/we'll ask 3 quick questions to understand your research/i),
    ).not.toBeInTheDocument()
  })
})
