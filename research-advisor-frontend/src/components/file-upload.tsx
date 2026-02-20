import { useState, useCallback, useRef } from 'react'
import { cn } from '@/lib/utils'

const ACCEPTED_TYPES: Record<string, string> = {
  'application/pdf': '.pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document': '.docx',
  'text/plain': '.txt',
}

const ACCEPTED_EXTENSIONS = ['.pdf', '.docx', '.txt']

function isValidFile(file: File): boolean {
  if (ACCEPTED_TYPES[file.type]) return true
  const ext = file.name.toLowerCase().split('.').pop()
  return ACCEPTED_EXTENSIONS.includes(`.${ext}`)
}

interface FileUploadProps {
  onFilesChange: (files: File[]) => void
}

export function FileUpload({ onFilesChange }: FileUploadProps) {
  const [files, setFiles] = useState<File[]>([])
  const [error, setError] = useState<string | null>(null)
  const [isDragOver, setIsDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  const addFiles = useCallback(
    (newFiles: File[]) => {
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
        setError('Only PDF, DOCX, and TXT files are accepted.')
      } else {
        setError(null)
      }

      if (valid.length > 0) {
        const updated = [...files, ...valid]
        setFiles(updated)
        onFilesChange(updated)
      }
    },
    [files, onFilesChange]
  )

  const removeFile = (index: number) => {
    const updated = files.filter((_, i) => i !== index)
    setFiles(updated)
    onFilesChange(updated)
    setError(null)
  }

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setIsDragOver(false)
      const droppedFiles = Array.from(e.dataTransfer.files)
      addFiles(droppedFiles)
    },
    [addFiles]
  )

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragOver(true)
  }

  const handleDragLeave = () => {
    setIsDragOver(false)
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const selectedFiles = Array.from(e.target.files)
      addFiles(selectedFiles)
    }
  }

  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
      <h2 className="mb-3 text-lg font-semibold text-gray-900">
        Upload Documents
      </h2>

      <div
        data-testid="dropzone"
        onClick={() => inputRef.current?.click()}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        className={cn(
          'cursor-pointer rounded-lg border-2 border-dashed p-8 text-center transition-colors',
          isDragOver
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-gray-400'
        )}
      >
        <p className="text-sm text-gray-600">
          Drag &amp; drop files here, or click to browse
        </p>
        <p className="mt-1 text-xs text-gray-400">
          Accepts PDF, DOCX, and TXT files
        </p>
      </div>

      <input
        ref={inputRef}
        data-testid="file-input"
        type="file"
        accept=".pdf,.docx,.txt"
        multiple
        onChange={handleInputChange}
        className="hidden"
      />

      {error && (
        <p className="mt-2 text-sm text-red-600">{error}</p>
      )}

      {files.length > 0 && (
        <ul className="mt-3 space-y-2">
          {files.map((file, index) => (
            <li
              key={`${file.name}-${index}`}
              className="flex items-center justify-between rounded-md bg-gray-50 px-3 py-2 text-sm"
            >
              <span className="truncate text-gray-700">{file.name}</span>
              <button
                onClick={() => removeFile(index)}
                className="ml-2 text-xs text-red-500 hover:text-red-700"
                aria-label="Remove"
              >
                Remove
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
