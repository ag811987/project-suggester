import { describe, it, expect, vi, beforeEach } from 'vitest'
import axios from 'axios'
import {
  analyzeResearch,
  getAnalysis,
  sendChatMessage,
  deleteSession,
  apiClient,
} from './client'
import type { ChatMessage } from '@/types'

const { mockPost } = vi.hoisted(() => ({
  mockPost: vi.fn(),
}))

vi.mock('axios', () => {
  const mockAxiosInstance = {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
    defaults: { baseURL: 'http://localhost:8000/api/v1' },
    interceptors: {
      request: { use: vi.fn() },
      response: { use: vi.fn() },
    },
  }
  return {
    default: {
      create: vi.fn(() => mockAxiosInstance),
      post: mockPost,
    },
  }
})

const mockClient = apiClient as unknown as {
  get: ReturnType<typeof vi.fn>
  post: ReturnType<typeof vi.fn>
  delete: ReturnType<typeof vi.fn>
}

describe('API Client', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('apiClient configuration', () => {
    it('exports an axios instance', () => {
      expect(apiClient).toBeDefined()
      expect(apiClient.get).toBeDefined()
      expect(apiClient.post).toBeDefined()
      expect(apiClient.delete).toBeDefined()
    })
  })

  describe('analyzeResearch', () => {
    const messages: ChatMessage[] = [
      { role: 'user', content: 'My research is about quantum computing' },
    ]

    it('sends POST to /analyze with messages as FormData', async () => {
      const mockResponse = {
        data: { session_id: 'abc-123', status: 'processing' },
      }
      mockPost.mockResolvedValueOnce(mockResponse)

      const result = await analyzeResearch(messages)

      expect(mockPost).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/analyze',
        expect.any(FormData),
      )
      const formData = mockPost.mock.calls[0][1] as FormData
      expect(formData.get('messages')).toBe(JSON.stringify(messages))
      expect(result).toEqual(mockResponse.data)
    })

    it('sends multipart form data when files are provided', async () => {
      const mockResponse = {
        data: { session_id: 'abc-123', status: 'processing' },
      }
      mockPost.mockResolvedValueOnce(mockResponse)

      const file = new File(['content'], 'paper.pdf', {
        type: 'application/pdf',
      })
      const result = await analyzeResearch(messages, [file])

      expect(mockPost).toHaveBeenCalledWith(
        'http://localhost:8000/api/v1/analyze',
        expect.any(FormData),
      )
      const formData = mockPost.mock.calls[0][1] as FormData
      expect(formData.get('messages')).toBe(JSON.stringify(messages))
      expect(result).toEqual(mockResponse.data)
    })

    it('propagates errors from the API', async () => {
      const error = new Error('Network Error')
      mockPost.mockRejectedValueOnce(error)

      await expect(analyzeResearch(messages)).rejects.toThrow('Network Error')
    })
  })

  describe('getAnalysis', () => {
    it('sends GET to /analysis/:sessionId', async () => {
      const mockResult = {
        recommendation: 'CONTINUE',
        confidence: 0.85,
        narrative_report: '# Report',
        novelty_assessment: {
          score: 0.7,
          verdict: 'NOVEL',
          evidence: [],
          reasoning: 'Novel research',
          related_papers_count: 5,
          average_fwci: 1.5,
          fwci_percentile: 75.0,
          citation_percentile_min: 60,
          citation_percentile_max: 90,
          impact_assessment: 'HIGH',
          impact_reasoning: 'High impact area',
        },
        pivot_suggestions: [],
        evidence_citations: [],
      }
      mockClient.get.mockResolvedValueOnce({ data: mockResult })

      const result = await getAnalysis('abc-123')

      expect(mockClient.get).toHaveBeenCalledWith('/analysis/abc-123')
      expect(result).toEqual(mockResult)
    })

    it('returns ResearchRecommendation directly', async () => {
      const mockResult = {
        recommendation: 'CONTINUE',
        confidence: 0.85,
        narrative_report: '# Report',
        novelty_assessment: {
          score: 0.7,
          verdict: 'NOVEL',
          evidence: [],
          reasoning: 'Novel research',
          related_papers_count: 5,
          average_fwci: 1.5,
          fwci_percentile: 75.0,
          citation_percentile_min: 60,
          citation_percentile_max: 90,
          impact_assessment: 'HIGH',
          impact_reasoning: 'High impact area',
        },
        pivot_suggestions: [],
        evidence_citations: [],
      }
      mockClient.get.mockResolvedValueOnce({ data: mockResult })

      const result = await getAnalysis('abc-123')

      expect(result.recommendation).toBe('CONTINUE')
      expect(result.narrative_report).toBe('# Report')
    })

    it('propagates errors from the API', async () => {
      const error = new Error('Not Found')
      mockClient.get.mockRejectedValueOnce(error)

      await expect(getAnalysis('invalid-id')).rejects.toThrow('Not Found')
    })
  })

  describe('sendChatMessage', () => {
    it('sends POST to /chat with session_id and message', async () => {
      const mockResponse = {
        data: { role: 'assistant', content: 'Here is my analysis...' },
      }
      mockClient.post.mockResolvedValueOnce(mockResponse)

      const result = await sendChatMessage('abc-123', 'Tell me more')

      expect(mockClient.post).toHaveBeenCalledWith('/chat', {
        session_id: 'abc-123',
        message: 'Tell me more',
      })
      expect(result).toEqual(mockResponse.data)
    })

    it('propagates errors from the API', async () => {
      const error = new Error('Server Error')
      mockClient.post.mockRejectedValueOnce(error)

      await expect(sendChatMessage('abc-123', 'hello')).rejects.toThrow(
        'Server Error',
      )
    })
  })

  describe('deleteSession', () => {
    it('sends DELETE to /session/:sessionId', async () => {
      const mockResponse = { data: { success: true } }
      mockClient.delete.mockResolvedValueOnce(mockResponse)

      const result = await deleteSession('abc-123')

      expect(mockClient.delete).toHaveBeenCalledWith('/session/abc-123')
      expect(result).toEqual({ success: true })
    })

    it('propagates errors from the API', async () => {
      const error = new Error('Forbidden')
      mockClient.delete.mockRejectedValueOnce(error)

      await expect(deleteSession('abc-123')).rejects.toThrow('Forbidden')
    })
  })
})
