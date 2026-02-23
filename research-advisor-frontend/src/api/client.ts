import axios from 'axios'
import type {
  AnalyzeResponse,
  ChatMessage,
  ResearchRecommendation,
} from '@/types'

const apiClient = axios.create({
  baseURL: 'http://localhost:8000/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
})

apiClient.interceptors.request.use((config) => {
  // #region agent log
  fetch('http://127.0.0.1:7244/ingest/f5509612-4742-480c-85cb-5f617b3e8047',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'src/api/client.ts:apiClient.request',message:'API request',data:{hypothesis:'H2_BASEURL',runId:'pre-fix',origin:globalThis?.location?.origin,baseURL:apiClient.defaults.baseURL,url:config.url,method:config.method},timestamp:Date.now(),runId:'pre-fix',hypothesisId:'H2_BASEURL'})}).catch(()=>{});
  // #endregion
  return config
})

apiClient.interceptors.response.use(
  (response) => {
    // #region agent log
    fetch('http://127.0.0.1:7244/ingest/f5509612-4742-480c-85cb-5f617b3e8047',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'src/api/client.ts:apiClient.response',message:'API response',data:{hypothesis:'H1_CORS',runId:'pre-fix',origin:globalThis?.location?.origin,baseURL:apiClient.defaults.baseURL,url:response.config?.url,method:response.config?.method,status:response.status,acao:response.headers?.['access-control-allow-origin']},timestamp:Date.now(),runId:'pre-fix',hypothesisId:'H1_CORS'})}).catch(()=>{});
    // #endregion
    return response
  },
  (error) => {
    // #region agent log
    fetch('http://127.0.0.1:7244/ingest/f5509612-4742-480c-85cb-5f617b3e8047',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'src/api/client.ts:apiClient.error',message:'API error',data:{hypothesis:'H1_CORS',runId:'pre-fix',origin:globalThis?.location?.origin,baseURL:apiClient.defaults.baseURL,url:error?.config?.url,method:error?.config?.method,message:error?.message,code:error?.code,hasResponse:Boolean(error?.response),status:error?.response?.status},timestamp:Date.now(),runId:'pre-fix',hypothesisId:'H1_CORS'})}).catch(()=>{});
    // #endregion
    return Promise.reject(error)
  },
)

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
  // Use axios directly: apiClient defaults to Content-Type: application/json which
  // breaks FormData parsing (server expects multipart/form-data with boundary).
  try {
    // #region agent log
    fetch('http://127.0.0.1:7244/ingest/f5509612-4742-480c-85cb-5f617b3e8047',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'src/api/client.ts:analyzeResearch',message:'Analyze request (FormData)',data:{hypothesis:'H1_CORS',runId:'pre-fix',origin:globalThis?.location?.origin,url:`${apiClient.defaults.baseURL}/analyze`,method:'post',hasFiles:Boolean(files && files.length>0)},timestamp:Date.now(),runId:'pre-fix',hypothesisId:'H1_CORS'})}).catch(()=>{});
    // #endregion
    const response = await axios.post<AnalyzeResponse>(
      `${apiClient.defaults.baseURL}/analyze`,
      formData,
    )
    return response.data
  } catch (error: unknown) {
    const e = error as any
    // #region agent log
    fetch('http://127.0.0.1:7244/ingest/f5509612-4742-480c-85cb-5f617b3e8047',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({location:'src/api/client.ts:analyzeResearch.catch',message:'Analyze error (FormData)',data:{hypothesis:'H1_CORS',runId:'pre-fix',origin:globalThis?.location?.origin,url:e?.config?.url || `${apiClient.defaults.baseURL}/analyze`,method:e?.config?.method || 'post',message:e?.message,code:e?.code,hasResponse:Boolean(e?.response),status:e?.response?.status},timestamp:Date.now(),runId:'pre-fix',hypothesisId:'H1_CORS'})}).catch(()=>{});
    // #endregion
    throw error
  }
}

export async function getAnalysis(
  sessionId: string,
): Promise<ResearchRecommendation> {
  const response = await apiClient.get<ResearchRecommendation>(
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
