import { useMutation, useQuery } from '@tanstack/react-query'
import {
  analyzeResearch,
  getAnalysis,
  sendChatMessage,
} from '@/api/client'
import type { ChatMessage, SessionStatusResponse } from '@/types'

export function useAnalyzeResearch() {
  return useMutation({
    mutationFn: ({
      messages,
      files,
    }: {
      messages: ChatMessage[]
      files?: File[]
    }) => analyzeResearch(messages, files),
  })
}

const POLL_INTERVAL_MS = 2000

export function useGetAnalysis(sessionId: string | null) {
  return useQuery<SessionStatusResponse>({
    queryKey: ['analysis', sessionId],
    queryFn: () => getAnalysis(sessionId!),
    enabled: !!sessionId,
    refetchInterval: (query) => {
      const status = query.state.data?.status
      if (status === 'completed' || status === 'error') return false
      return POLL_INTERVAL_MS
    },
  })
}

export function useSendMessage() {
  return useMutation({
    mutationFn: ({
      sessionId,
      message,
    }: {
      sessionId: string
      message: string
    }) => sendChatMessage(sessionId, message),
  })
}

export const STAGE_LABELS: Record<string, string> = {
  extracting_profile: 'Extracting your research profile...',
  analyzing_novelty: 'Analyzing novelty with OpenAlex...',
  web_search: 'Searching the web for context...',
  retrieving_gaps: 'Retrieving high-impact research gaps...',
  matching_pivots: 'Matching pivots to your skills...',
  generating_report: 'Generating your report...',
  completed: 'Analysis complete',
  error: 'Something went wrong',
}
