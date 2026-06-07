import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { registerUser } from '@/services/authService'
import { useAuth } from '@/contexts/AuthContext'

type RegisterState = {
  email: string
  password: string
}

export function useRegisterLogic() {
  const [form, setForm] = useState<RegisterState>({ email: '', password: '' })
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const navigate = useNavigate()
  const { setAuth } = useAuth()

  const updateField = (field: keyof RegisterState, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)

    console.log(form)
    
    try {
      const response = await registerUser({
        email: form.email,
        password: form.password,
      })

      const token = response.accessToken
      if (!token) {
        throw new Error('Missing access token from server response.')
      }

      setAuth(token, { email: form.email })
      navigate('/profile')
    } catch (err: any) {
      setError(err?.message ?? 'Unable to create account. Try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return { form, error, isSubmitting, updateField, handleSubmit }
}
