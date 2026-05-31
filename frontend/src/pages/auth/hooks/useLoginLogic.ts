import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { loginUser } from '@/services/authService'
import { useAuth } from '@/contexts/AuthContext'

type LoginState = {
  email: string
  password: string
}

export const useLoginLogic = () => {
  const [form, setForm] = useState<LoginState>({ email: '', password: '' })
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const navigate = useNavigate()
  const { setAuth } = useAuth()

  const updateField = (field: keyof LoginState, value: string) => {
    setForm((prev) => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setError(null)
    setIsSubmitting(true)

    console.log(form)

    try {
      const response = await loginUser({
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
      setError(err?.message ?? 'Unable to sign in. Try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return { form, error, isSubmitting, updateField, handleSubmit }
}
