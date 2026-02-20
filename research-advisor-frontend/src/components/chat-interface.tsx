import { useState, useRef, useEffect, useCallback } from 'react'
import { cn } from '@/lib/utils'

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  files?: File[]
}

interface ChatInterfaceProps {
  messages: ChatMessage[]
  onSendMessage: (message: string, files?: File[]) => void
  isLoading?: boolean
  disabled?: boolean
  placeholder?: string
}

const ACCEPTED_TYPES: Record<string, string> = {
  'application/pdf': '.pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
    '.docx',
  'text/plain': '.txt',
}

const ACCEPTED_EXTENSIONS = ['.pdf', '.docx', '.txt']

function isValidFile(file: File): boolean {
  if (ACCEPTED_TYPES[file.type]) return true
  const ext = file.name.toLowerCase().split('.').pop()
  return ACCEPTED_EXTENSIONS.includes(`.${ext}`)
}

export function ChatInterface({
  messages,
  onSendMessage,
  isLoading = false,
  disabled = false,
  placeholder = 'Type your response...',
}: ChatInterfaceProps) {
  const [input, setInput] = useState('')
  const [attachedFiles, setAttachedFiles] = useState<File[]>([])
  const [fileError, setFileError] = useState<string | null>(null)
  const [isDragOver, setIsDragOver] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  useEffect(() => {
    if (messagesEndRef.current?.scrollIntoView) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [messages, isLoading])

  useEffect(() => {
    if (!isLoading && !disabled) {
      textareaRef.current?.focus()
    }
  }, [messages.length, isLoading, disabled])

  const handleSend = () => {
    const trimmed = input.trim()
    if (!trimmed && attachedFiles.length === 0) return
    onSendMessage(trimmed, attachedFiles.length > 0 ? attachedFiles : undefined)
    setInput('')
    setAttachedFiles([])
    setFileError(null)
  }

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const addFiles = useCallback((newFiles: File[]) => {
    const valid: File[] = []
    let hasInvalid = false
    for (const file of newFiles) {
      if (isValidFile(file)) {
        valid.push(file)
      } else {
        hasInvalid = true
      }
    }
    if (hasInvalid) {
      setFileError('Only PDF, DOCX, and TXT files are accepted.')
    } else {
      setFileError(null)
    }
    if (valid.length > 0) {
      setAttachedFiles((prev) => [...prev, ...valid])
    }
  }, [])

  const removeFile = (index: number) => {
    setAttachedFiles((prev) => prev.filter((_, i) => i !== index))
    setFileError(null)
  }

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragOver(false)
      addFiles(Array.from(e.dataTransfer.files))
    },
    [addFiles],
  )

  return (
    <div
      className="flex h-full flex-col"
      onDragOver={(e) => {
        e.preventDefault()
        setIsDragOver(true)
      }}
      onDragLeave={() => setIsDragOver(false)}
      onDrop={handleDrop}
    >
      {/* Messages area */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="mx-auto max-w-3xl space-y-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                'flex',
                message.role === 'user' ? 'justify-end' : 'justify-start',
              )}
            >
              <div
                className={cn(
                  'max-w-[85%] rounded-2xl px-4 py-3 text-sm leading-relaxed',
                  message.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-900',
                )}
              >
                <div className="whitespace-pre-wrap">{message.content}</div>
                {message.files && message.files.length > 0 && (
                  <div className="mt-2 flex flex-wrap gap-1.5">
                    {message.files.map((f, i) => (
                      <span
                        key={i}
                        className={cn(
                          'inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs',
                          message.role === 'user'
                            ? 'bg-blue-500/30 text-blue-100'
                            : 'bg-gray-200 text-gray-600',
                        )}
                      >
                        <FileIcon />
                        {f.name}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}

          {isLoading && (
            <div className="flex justify-start">
              <div className="flex items-center gap-2 rounded-2xl bg-gray-100 px-4 py-3 text-sm text-gray-500">
                <span className="flex gap-1">
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 [animation-delay:0ms]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 [animation-delay:150ms]" />
                  <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-gray-400 [animation-delay:300ms]" />
                </span>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Drag overlay */}
      {isDragOver && (
        <div className="pointer-events-none absolute inset-0 z-10 flex items-center justify-center bg-blue-50/80">
          <div className="rounded-xl border-2 border-dashed border-blue-400 px-8 py-6 text-blue-600">
            Drop files here
          </div>
        </div>
      )}

      {/* Input area */}
      <div className="border-t border-gray-200 bg-white px-4 py-3">
        <div className="mx-auto max-w-3xl">
          {/* Attached files preview */}
          {attachedFiles.length > 0 && (
            <div className="mb-2 flex flex-wrap gap-2">
              {attachedFiles.map((file, index) => (
                <span
                  key={`${file.name}-${index}`}
                  className="inline-flex items-center gap-1.5 rounded-lg bg-gray-100 px-2.5 py-1 text-xs text-gray-700"
                >
                  <FileIcon />
                  <span className="max-w-[120px] truncate">{file.name}</span>
                  <button
                    onClick={() => removeFile(index)}
                    className="ml-0.5 text-gray-400 hover:text-gray-600"
                    aria-label="Remove file"
                  >
                    &times;
                  </button>
                </span>
              ))}
            </div>
          )}

          {fileError && (
            <p className="mb-2 text-xs text-red-500">{fileError}</p>
          )}

          <div className="flex items-end gap-2">
            {/* Attach button */}
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={isLoading || disabled}
              className="mb-0.5 flex-shrink-0 rounded-lg p-2 text-gray-400 hover:bg-gray-100 hover:text-gray-600 disabled:opacity-50"
              aria-label="Attach file"
            >
              <AttachIcon />
            </button>

            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.docx,.txt"
              multiple
              onChange={(e) => {
                if (e.target.files) {
                  addFiles(Array.from(e.target.files))
                  e.target.value = ''
                }
              }}
              className="hidden"
            />

            {/* Text input */}
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              className="max-h-36 min-h-[44px] flex-1 resize-none rounded-xl border border-gray-300 px-4 py-2.5 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 disabled:opacity-50"
              rows={1}
              disabled={isLoading || disabled}
            />

            {/* Send button */}
            <button
              onClick={handleSend}
              disabled={
                isLoading ||
                disabled ||
                (!input.trim() && attachedFiles.length === 0)
              }
              className="mb-0.5 flex-shrink-0 rounded-lg bg-blue-600 p-2 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              aria-label="Send message"
            >
              <SendIcon />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}

function FileIcon() {
  return (
    <svg
      className="h-3.5 w-3.5"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
      />
    </svg>
  )
}

function AttachIcon() {
  return (
    <svg
      className="h-5 w-5"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13"
      />
    </svg>
  )
}

function SendIcon() {
  return (
    <svg
      className="h-5 w-5"
      fill="none"
      viewBox="0 0 24 24"
      stroke="currentColor"
      strokeWidth={2}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M6 12L3.269 3.126A59.768 59.768 0 0121.485 12 59.77 59.77 0 013.27 20.876L5.999 12zm0 0h7.5"
      />
    </svg>
  )
}
