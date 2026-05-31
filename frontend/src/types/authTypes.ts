export type AuthCredentials = {
  accessToken: string
  refreshToken?: string
  tokenType?: string
}

export type RegisterRequest = {
  email: string
  password: string
}

export type RegisterResponse = {
  accessToken: string
  refreshToken?: string
  tokenType?: string
}

export type LoginRequest = {
  email: string
  password: string
}

export type LoginResponse = {
  accessToken: string
  refreshToken?: string
  tokenType?: string
}

