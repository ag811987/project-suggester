import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi } from 'vitest'
import { FileUpload } from './file-upload'

function createFile(name: string, type: string): File {
  return new File(['file content'], name, { type })
}

describe('FileUpload', () => {
  it('renders without crashing', () => {
    render(<FileUpload onFilesChange={vi.fn()} />)
    expect(screen.getByText(/drag.*drop/i)).toBeInTheDocument()
  })

  it('shows accepted file types', () => {
    render(<FileUpload onFilesChange={vi.fn()} />)
    expect(screen.getByText(/pdf.*docx.*txt/i)).toBeInTheDocument()
  })

  it('accepts valid PDF files via input', async () => {
    const onFilesChange = vi.fn()
    const user = userEvent.setup()
    render(<FileUpload onFilesChange={onFilesChange} />)

    const input = screen.getByTestId('file-input') as HTMLInputElement
    const file = createFile('paper.pdf', 'application/pdf')

    await user.upload(input, file)

    expect(onFilesChange).toHaveBeenCalledWith([file])
  })

  it('accepts valid DOCX files', async () => {
    const onFilesChange = vi.fn()
    const user = userEvent.setup()
    render(<FileUpload onFilesChange={onFilesChange} />)

    const input = screen.getByTestId('file-input') as HTMLInputElement
    const file = createFile(
      'paper.docx',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )

    await user.upload(input, file)

    expect(onFilesChange).toHaveBeenCalledWith([file])
  })

  it('accepts valid TXT files', async () => {
    const onFilesChange = vi.fn()
    const user = userEvent.setup()
    render(<FileUpload onFilesChange={onFilesChange} />)

    const input = screen.getByTestId('file-input') as HTMLInputElement
    const file = createFile('notes.txt', 'text/plain')

    await user.upload(input, file)

    expect(onFilesChange).toHaveBeenCalledWith([file])
  })

  it('rejects invalid file types', async () => {
    const onFilesChange = vi.fn()
    render(<FileUpload onFilesChange={onFilesChange} />)

    const dropzone = screen.getByTestId('dropzone')
    const invalidFile = createFile('image.png', 'image/png')

    const dataTransfer = {
      files: [invalidFile],
      items: [
        {
          kind: 'file',
          type: 'image/png',
          getAsFile: () => invalidFile,
        },
      ],
      types: ['Files'],
    }

    fireEvent.drop(dropzone, { dataTransfer })

    expect(screen.getByText(/only pdf, docx, and txt/i)).toBeInTheDocument()
  })

  it('displays selected file names', async () => {
    const user = userEvent.setup()
    render(<FileUpload onFilesChange={vi.fn()} />)

    const input = screen.getByTestId('file-input') as HTMLInputElement
    const file = createFile('paper.pdf', 'application/pdf')

    await user.upload(input, file)

    expect(screen.getByText('paper.pdf')).toBeInTheDocument()
  })

  it('allows removing a file', async () => {
    const onFilesChange = vi.fn()
    const user = userEvent.setup()
    render(<FileUpload onFilesChange={onFilesChange} />)

    const input = screen.getByTestId('file-input') as HTMLInputElement
    const file = createFile('paper.pdf', 'application/pdf')

    await user.upload(input, file)

    const removeButton = screen.getByRole('button', { name: /remove/i })
    await user.click(removeButton)

    expect(screen.queryByText('paper.pdf')).not.toBeInTheDocument()
    expect(onFilesChange).toHaveBeenLastCalledWith([])
  })

  it('handles drag and drop', () => {
    const onFilesChange = vi.fn()
    render(<FileUpload onFilesChange={onFilesChange} />)

    const dropzone = screen.getByTestId('dropzone')
    const file = createFile('paper.pdf', 'application/pdf')

    const dataTransfer = {
      files: [file],
      items: [
        {
          kind: 'file',
          type: 'application/pdf',
          getAsFile: () => file,
        },
      ],
      types: ['Files'],
    }

    fireEvent.drop(dropzone, { dataTransfer })

    expect(onFilesChange).toHaveBeenCalledWith([file])
  })
})
