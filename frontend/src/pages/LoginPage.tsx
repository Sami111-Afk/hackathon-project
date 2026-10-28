import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { login } from '@/lib/auth'
import { apiUrl } from '@/lib/config'

export function LoginPage() {
  const nav = useNavigate()
  const [name, setName] = useState('')
  const [token, setToken] = useState('')

  function submit(e: FormEvent) {
    e.preventDefault()
    if (!name.trim() || !token.trim()) return
    login(token, name)
    nav('/dashboard')
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-4">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl">🔒 ORB — autentificare</CardTitle>
          <p className="text-sm text-slate-500">Backend: {apiUrl()}</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">Numele tău (apare pe decizii)</Label>
              <Input id="name" value={name} onChange={(e) => setName(e.target.value)} autoComplete="name" />
            </div>
            <div className="space-y-2">
              <Label htmlFor="token">Token de acces</Label>
              <Input id="token" type="password" value={token} onChange={(e) => setToken(e.target.value)} autoComplete="off" />
            </div>
            <Button type="submit" size="lg" className="w-full">Intră</Button>
            <a href="/cases/case_maria?mock=1" className="block text-center text-sm text-slate-500 underline">
              Demo fără backend (replay Maria)
            </a>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
