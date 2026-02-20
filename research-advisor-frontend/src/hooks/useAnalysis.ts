import { useMutation, useQuery } from '@tanstack/react-query'
import {
  analyzeResearch,
  getAnalysis,
  sendChatMessage,
} from '@/api/client'
import type { ChatMessage } from '@/types'

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

export function useGetAnalysis(sessionId: string | null) {
  return useQuery({
    queryKey: ['analysis', sessionId],
    queryFn: () => getAnalysis(sessionId!),
    enabled: !!sessionId,
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
