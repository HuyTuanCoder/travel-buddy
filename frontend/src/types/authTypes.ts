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
  credentials: AuthCredentials
}

export type LoginRequest = {
  email: string
  password: string
}

export type LoginResponse = {
  credentials: AuthCredentials
}

export const getRegisterRequest = (
  email: string,
  password: string,
): RegisterRequest => ({
  email,
  password,
})

export const getRegisterResponse = (
  credentials: AuthCredentials,
): RegisterResponse => ({
  credentials,
})

export const getLoginRequest = (
  email: string,
  password: string,
): LoginRequest => ({
  email,
  password,
})

export const getLoginResponse = (
  credentials: AuthCredentials,
): LoginResponse => ({
  credentials,
})
