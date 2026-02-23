import { useState, useCallback, useEffect } from 'react'
import { ChatInterface } from './components/chat-interface'
import type { ChatMessage } from './components/chat-interface'
import { LandingHero } from './components/landing-hero'
import { ResultsView } from './components/results-view'
import { useAnalyzeResearch, useGetAnalysis } from './hooks/useAnalysis'

type View = 'landing' | 'chat' | 'results'

/**
 * Guided question flow steps:
 * 0 = interests
 * 1 = research proposal
 * 2 = skills
 * 3 = analyzing
 * 4 = done (results)
 */
type Step = 0 | 1 | 2 | 3 | 4

const GUIDED_QUESTIONS: Record<number, string> = {
  0: 'What are your research interests? Tell me about the areas or topics you find most exciting.',
  1: 'What is your research proposal or question? Describe what you want to investigate.',
  2: 'What are your key skills and expertise? Include technical skills, methodologies, and domain knowledge.',
}

const STEP_PLACEHOLDERS: Record<number, string> = {
  0: 'e.g. I\'m interested in machine learning applications in healthcare...',
  1: 'e.g. I want to investigate whether transformer models can predict...',
  2: 'e.g. Python, statistical analysis, clinical trial design...',
}

function App() {
  const [view, setView] = useState<View>('landing')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [allFiles, setAllFiles] = useState<File[]>([])
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [step, setStep] = useState<Step>(0)

  const analyzeMutation = useAnalyzeResearch()
  const { data: recommendation, error: analysisError } = useGetAnalysis(
    sessionId,
  )

  // When analysis completes, move to results view
  useEffect(() => {
    if (recommendation && step === 3) {
      setStep(4)
      setView('results')
    }
  }, [recommendation, step])

  const handleSendMessage = useCallback(
    (content: string, files?: File[]) => {
      if (step >= 3) return

      // Add user message
      const userMsg: ChatMessage = {
        id: crypto.randomUUID(),
        role: 'user',
        content,
        files,
      }

      // Track files for the analyze call
      if (files && files.length > 0) {
        setAllFiles((prev) => [...prev, ...files])
      }

      const nextStep = (step + 1) as Step

      if (nextStep <= 2) {
        // Ask next question
        const assistantMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: GUIDED_QUESTIONS[nextStep],
        }
        setMessages((prev) => [...prev, userMsg, assistantMsg])
        setStep(nextStep)
      } else {
        // All questions answered — trigger analysis
        const analyzingMsg: ChatMessage = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content:
            'I have enough information. Analyzing your research — this may take a moment...',
        }
        setMessages((prev) => [...prev, userMsg, analyzingMsg])
        setStep(3)

        // Build messages for API (only user messages)
        const allMessages = [...messages, userMsg]
        const apiMessages = allMessages
          .filter((m) => m.role === 'user')
          .map(({ role, content }) => ({ role, content }))

        const filesToSend = [
          ...allFiles,
          ...(files || []),
        ]

        analyzeMutation.mutate(
          {
            messages: apiMessages,
            files: filesToSend.length > 0 ? filesToSend : undefined,
          },
          {
            onSuccess: (data) => {
              setSessionId(data.session_id)
            },
          },
        )
      }
    },
    [step, messages, allFiles, analyzeMutation],
  )

  const handleStart = () => {
    setView('chat')
    setMessages([
      {
        id: crypto.randomUUID(),
        role: 'assistant',
        content: GUIDED_QUESTIONS[0],
      },
    ])
    setStep(0)
  }

  const handleNewAnalysis = () => {
    setView('landing')
    setSessionId(null)
    setMessages([])
    setAllFiles([])
    setStep(0)
  }

  const isLoading = analyzeMutation.isPending || step === 3
  const mutationError = analyzeMutation.error

  // Landing view
  if (view === 'landing') {
    return (
      <div className="flex min-h-screen flex-col bg-gradient-to-b from-slate-50 via-white to-blue-50/20">
        <header className="flex items-center justify-between border-b border-gray-200/50 bg-white/80 px-6 py-3 backdrop-blur-sm">
          <h1 className="text-lg font-semibold text-gray-900">
            Research Pivot Advisor
          </h1>
        </header>
        <LandingHero onStart={handleStart} />
      </div>
    )
  }

  // Results view
  if (view === 'results' && recommendation) {
    return (
      <div className="flex h-screen flex-col bg-gray-50">
        <header className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-3">
          <h1 className="text-lg font-semibold text-gray-900">
            Research Pivot Advisor
          </h1>
          <button
            onClick={handleNewAnalysis}
            className="rounded-lg bg-gray-100 px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-200"
          >
            New Analysis
          </button>
        </header>

        <div className="flex-1 overflow-y-auto px-4 py-6">
          <div className="mx-auto max-w-3xl">
            <ResultsView data={recommendation} />
          </div>
        </div>
      </div>
    )
  }

  // Chat view
  return (
    <div className="relative flex h-screen flex-col bg-gray-50">
      <header className="flex items-center justify-between border-b border-gray-200 bg-white px-6 py-3">
        <h1 className="text-lg font-semibold text-gray-900">
          Research Pivot Advisor
        </h1>
        {step > 0 && step < 3 && (
          <span className="text-xs text-gray-400">
            Step {step + 1} of 3
          </span>
        )}
      </header>

      {(mutationError || analysisError) && (
        <div className="mx-auto mt-3 w-full max-w-3xl px-4">
          <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {mutationError instanceof Error
              ? mutationError.message
              : analysisError instanceof Error
                ? analysisError.message
                : 'An error occurred during analysis.'}
          </div>
        </div>
      )}

      <div className="flex-1 overflow-hidden">
        <ChatInterface
          messages={messages}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          disabled={step >= 3}
          placeholder={STEP_PLACEHOLDERS[step] || 'Type your response...'}
          showIntro={step === 0}
        />
      </div>
    </div>
  )
}

export default App
