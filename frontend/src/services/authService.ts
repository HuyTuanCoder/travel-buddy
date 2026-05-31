import api from './api'
import type {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
} from '@/types/authTypes'

export const registerUser = async (
  payload: RegisterRequest,
): Promise<RegisterResponse> => {
  try {
    const response = await api.post('/auth/register', payload)
    return response.data as RegisterResponse
  } catch (error: any) {
    throw error.response?.data ?? error
  }
}

export const loginUser = async (
  payload: LoginRequest,
): Promise<LoginResponse> => {
  try {
    const response = await api.post('/auth/login', payload)
    return response.data as LoginResponse
  } catch (error: any) {
    throw error.response?.data ?? error
  }
}

export const authApi = api
