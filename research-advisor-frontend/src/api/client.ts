import axios from 'axios'
import type {
  AnalyzeResponse,
  ChatMessage,
  SessionStatusResponse,
} from '@/types'

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

export async function analyzeResearch(
  messages: ChatMessage[],
  files?: File[],
): Promise<AnalyzeResponse> {
  const formData = new FormData()
  formData.append('messages', JSON.stringify(messages))
  if (files && files.length > 0) {
    for (const file of files) {
      formData.append('files', file)
    }
  }
  const response = await axios.post<AnalyzeResponse>(
    `${apiClient.defaults.baseURL}/analyze`,
    formData,
  )
  return response.data
}

export async function getAnalysis(
  sessionId: string,
): Promise<SessionStatusResponse> {
  const response = await apiClient.get<SessionStatusResponse>(
    `/analysis/${sessionId}`,
  )
  return response.data
}

export async function sendChatMessage(
  sessionId: string,
  message: string,
): Promise<ChatMessage> {
  const response = await apiClient.post<ChatMessage>('/chat', {
    session_id: sessionId,
    message,
  })
  return response.data
}

export async function deleteSession(
  sessionId: string,
): Promise<{ success: boolean }> {
  const response = await apiClient.delete<{ success: boolean }>(
    `/session/${sessionId}`,
  )
  return response.data
}

export { apiClient }
