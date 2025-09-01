import React, { useEffect, useMemo, useState } from 'react'
import { motion } from 'framer-motion'
import { Wallet, LogIn, LogOut, BookOpenCheck, Book, History, Settings, Coins, Sparkles, Play, Trash2, ChevronRight } from 'lucide-react'
import { decodeJwt } from './utils'
import { 
  apiLogin, apiRegister, apiGetBalance, apiWalletHistory, apiGetThemes, apiPredictSync, apiListUsers, apiRefill, apiCreateTheme, apiDeleteTheme
} from './api'
import PanelBlock from '@/components/PanelBlock' 

function Section({ title, children, actions }) {
  return (
    <div className="card p-4 md:p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="h2">{title}</h2>
        {actions}
      </div>
      <div>{children}</div>
    </div>
  )
}

function useAuth() {
  const [token, setToken] = useState(() => localStorage.getItem('token') || '')
  const payload = useMemo(() => decodeJwt(token), [token])
  const isAuthed = !!payload?.user_id

  function logout() {
    localStorage.removeItem('token')
    setToken('')
  }

  return { token, setToken, payload, isAuthed, logout }
}

function AuthPanel({ onSuccess }) {
  const [tab, setTab] = useState('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  async function submit(e) {
    e.preventDefault()
    setLoading(true); setError('')
    const fn = tab === 'login' ? apiLogin : apiRegister
    const { ok, error } = await fn({ email, password })
    setLoading(false)
    if (!ok) { setError(error); return }
    if (tab === 'register') {
      // After registration, auto-login
      const { ok: ok2, error: err2 } = await apiLogin({ email, password })
      if (!ok2) { setError(err2); return }
    }
    onSuccess(localStorage.getItem('token'))
  }

  return (
    <div className="max-w-md mx-auto">
      <div className="flex gap-2 mb-4">
        <button className={tab==='login'?'btn btn-primary':'btn'} onClick={()=>setTab('login')}><LogIn size={16}/> Войти</button>
        <button className={tab==='register'?'btn btn-primary':'btn'} onClick={()=>setTab('register')}>Регистрация</button>
      </div>
      <form onSubmit={submit} className="space-y-3">
        <div>
          <label className="label">Email</label>
          <input className="input" type="email" value={email} onChange={e=>setEmail(e.target.value)} required />
        </div>
        <div>
          <label className="label">Пароль</label>
          <input className="input" type="password" value={password} onChange={e=>setPassword(e.target.value)} minLength={8} required />
        </div>
        {error && <div className="text-red-600 text-sm">{error}</div>}
        <button className="btn btn-primary w-full" disabled={loading}>
          {loading ? 'Подождите…' : (tab==='login' ? 'Войти' : 'Зарегистрироваться')}
        </button>
      </form>
    </div>
  )
}

function BalanceCard({ userId }) {
  const [balance, setBalance] = useState(null)
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')

  async function load() {
    setLoading(true); setErr('')
    const { ok, data, error } = await apiGetBalance(userId)
    setLoading(false)
    if (!ok) { setErr(error); return }
    setBalance(data.balance ?? data?.data?.balance ?? 0)
  }
  useEffect(()=>{ load() },[userId])

  return (
    <Section title="Баланс" actions={<button className="btn" onClick={load}>Обновить</button>}>
      {err && <div className="text-red-600 mb-2">{err}</div>}
      <div className="flex items-center gap-3">
        <Wallet/>
        <div className="text-3xl font-bold">{balance ?? '—'}</div>
        <Coins className="opacity-70" />
      </div>
    </Section>
  )
}

function HistoryTable({ rows }) {
  if (!rows?.length) return <div className="text-slate-500">Пока пусто</div>
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="text-left text-slate-600">
          <tr><th className="py-2">Время</th><th>Операция</th><th>Сумма</th><th>Причина</th></tr>
        </thead>
        <tbody>
          {rows.map((r, i)=>(
            <tr key={i} className="border-t">
              <td className="py-2">{new Date(r.timestamp || r.recommended_at || Date.now()).toLocaleString()}</td>
              <td>{r.operation || '—'}</td>
              <td>{r.amount ?? r.credits_spent ?? '—'}</td>
              <td>{r.reason || r.theme_name || r.model_name || '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

function WalletHistory({ userId }) {
  const [rows, setRows] = useState([])
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  async function load() {
    setLoading(true); setErr('')
    const { ok, data, error } = await apiWalletHistory(userId)
    setLoading(false)
    if (!ok) { setErr(error); return }
    setRows(data)
  }
  useEffect(()=>{ load() },[userId])

  return (
    <Section title="История кошелька" actions={<button className="btn" onClick={load}><History size={16}/> Обновить</button>}>
      {err && <div className="text-red-600 mb-2">{err}</div>}
      <HistoryTable rows={rows} />
    </Section>
  )
}

function ThemesPicker({ value, onChange }) {
  const [themes, setThemes] = useState([])
  const [err, setErr] = useState('')

  useEffect(()=>{
    (async ()=>{
      const { ok, data, error } = await apiGetThemes()
      if (!ok) setErr(error)
      else setThemes(data)
    })()
  },[])

  return (
    <div>
      <label className="label">Тема</label>
      <select className="input" value={value||''} onChange={e=>onChange(+e.target.value || null)}>
        <option value="">— Выберите тему —</option>
        {themes.map(t=>(
          <option key={t.id} value={t.id}>{t.level} • {t.name}</option>
        ))}
      </select>
      {err && <div className="text-red-600 text-sm mt-1">{err}</div>}
    </div>
  )
}

function PredictPanel({ userId }) {
  const [themeId, setThemeId] = useState(null)
  const [isBonus, setIsBonus] = useState(false)
  const [result, setResult] = useState(null)
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)
  const [verbsOnly, setVerbsOnly] = useState(true)

  async function run() {
    if (!themeId) { setErr('Выберите тему'); return }
    setLoading(true); setErr(''); setResult(null)
    const { ok, data, error, path } = await apiPredictSync({ userId, themeId, isBonus })
    setLoading(false)
    if (!ok) { setErr(error); return }
    setResult({ ...data, _path: path })
  }

  const vocab = useMemo(()=>{
    let list = result?.vocabulary || []
    if (verbsOnly) {
      // простая фильтрация: оставим слова, похожие на глаголы из примера (ser/soy/eres/es)
      const re = /^(ser|soy|eres|es|estoy|estas|esta|estar|tengo|tienes|tiene|ir|voy|vas|va|hacer|hago|haces|hace)$/i
      list = list.filter(w => re.test(w))
    }
    return list
  }, [result, verbsOnly])

  return (
    <>
    <Section title="Генерация задания (комикс)"
      actions={<button className="btn btn-primary" onClick={run} disabled={loading || !themeId}><Play size={16}/> {loading? 'Генерация…' : 'Сгенерировать'}</button>}
    >
      <div className="grid md:grid-cols-2 gap-4">
        <div className="space-y-3">
          <ThemesPicker value={themeId} onChange={setThemeId} />
          <label className="inline-flex items-center gap-2">
            <input type="checkbox" checked={isBonus} onChange={e=>setIsBonus(e.target.checked)} />
            Бонусный комикс
          </label>
          {err && <div className="text-red-600 text-sm">{err}</div>}
          {result?.credits_spent != null && (
            <div className="text-slate-600 text-sm">
              Списано кредитов: <b>{result.credits_spent}</b>, баланс после: <b>{result.balance_after}</b>
              {result._path && <div className="text-xs opacity-70">endpoint: {result._path}</div>}
            </div>
          )}
        </div>
        <div className="space-y-3">
          {result ? (
            <motion.div initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} className="card p-4">
              <div className="h3 mb-2"><BookOpenCheck className="inline mr-2" />Пояснение</div>
              <div className="whitespace-pre-wrap">{result.explanation}</div>
              <div className="mt-4 flex items-center gap-2">
                <label className="inline-flex items-center gap-2">
                  <input type="checkbox" checked={verbsOnly} onChange={()=>setVerbsOnly(v=>!v)} />
                  Тренировать только глаголы
                </label>
              </div>
              <div className="mt-2">
                <div className="h3 mb-1">Словарь</div>
                <div className="flex flex-wrap gap-2">
                  {vocab.map((w,i)=> (
                    <span key={i} className="px-2 py-1 rounded-xl bg-slate-100 border">{w}</span>
                  ))}
                </div>
              </div>
            </motion.div>
          ) : (
            <div className="text-slate-500">Сгенерируйте задание, и здесь появится результат</div>
          )}
        </div>
      </div>
    </Section>
     {/* НОВЫЙ БЛОК — панель тестов с вариантами ответов */}
    <Section title="Тест с выбором ответа (панель)">
      <PanelBlock />
    </Section>
  </>
  )
}

function AdminPanel({ me }) {
  const admin = !!me?.is_admin;  

  const [users, setUsers] = useState([])
  const [err, setErr] = useState('')
  const [userId, setUserId] = useState('')
  const [amount, setAmount] = useState('')
  const [rmsg, setRmsg] = useState('')

  const [tName, setTName] = useState('')
  const [tLevel, setTLevel] = useState('A1')
  const [tBase, setTBase] = useState('base.png')
  const [tBonus, setTBonus] = useState('')
  const [themes, setThemes] = useState([])

  async function loadUsers() {
    const { ok, data, error } = await apiListUsers()
    if (!ok) setErr(error); else setUsers(data)
  }
  async function loadThemes() {
    const { ok, data, error } = await apiGetThemes()
    if (!ok) setErr(error); else setThemes(data)
  }
  useEffect(() => {
    if (!admin) return
    ;(async () => {
      await loadUsers()
      await loadThemes()
    })()
  }, [admin])

  if (!admin) return null

  async function topup() {
    setRmsg('')
    const uid = parseInt(userId, 10)
    const amt = parseFloat(amount)
    if (!uid || !amt) { setRmsg('Укажите корректные значения'); return }
    const { ok, data, error } = await apiRefill({ userId: uid, amount: amt, reason: 'Админское пополнение' })
    setRmsg(ok ? 'Пополнено' : error)
  }

  async function addTheme() {
    const bonus = tBonus.split(',').map(s=>s.trim()).filter(Boolean)
    const { ok, error } = await apiCreateTheme({ name: tName, level: tLevel, base_comic: tBase, bonus_comics: bonus })
    if (!ok) setErr(error); else { setTName(''); setTBonus(''); loadThemes() }
  }

  async function delTheme(id) {
    const { ok, error } = await apiDeleteTheme(id)
    if (!ok) alert(error); else loadThemes()
  }

  return (
    <Section title="Администрирование">
      <div className="grid md:grid-cols-2 gap-4">
        <div className="card p-4 space-y-3">
          <div className="h3">Пополнение баланса</div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="label">User ID</label>
              <input className="input" value={userId} onChange={e=>setUserId(e.target.value)} placeholder="1" />
            </div>
            <div>
              <label className="label">Сумма</label>
              <input className="input" value={amount} onChange={e=>setAmount(e.target.value)} placeholder="10" />
            </div>
          </div>
          <button className="btn btn-primary" onClick={topup}><Coins size={16}/> Пополнить</button>
          {rmsg && <div className="text-sm text-slate-600">{rmsg}</div>}

          <div className="h3 mt-6">Пользователи</div>
          <div className="text-sm text-slate-500 mb-2">Всего: {users.length}</div>
          <div className="max-h-48 overflow-auto border rounded-xl">
            <table className="w-full text-sm">
              <thead><tr className="text-left text-slate-600"><th className="py-2 px-2">ID</th><th>Email</th><th>Admin</th></tr></thead>
              <tbody>
                {users.map(u=>(<tr key={u.id} className="border-t"><td className="py-1 px-2">{u.id}</td><td>{u.email}</td><td>{u.is_admin?'да':'нет'}</td></tr>))}
              </tbody>
            </table>
          </div>
        </div>

        <div className="card p-4 space-y-3">
          <div className="h3">Темы</div>
          <div className="grid md:grid-cols-2 gap-3">
            <div>
              <label className="label">Название</label>
              <input className="input" value={tName} onChange={e=>setTName(e.target.value)} placeholder="глагол ser" />
            </div>
            <div>
              <label className="label">Уровень</label>
              <select className="input" value={tLevel} onChange={e=>setTLevel(e.target.value)}>
                <option>A1</option><option>A2</option><option>B1</option><option>B2</option><option>C1</option>
              </select>
            </div>
            <div>
              <label className="label">Базовый комикс (файл)</label>
              <input className="input" value={tBase} onChange={e=>setTBase(e.target.value)} />
            </div>
            <div>
              <label className="label">Бонусные (через запятую)</label>
              <input className="input" value={tBonus} onChange={e=>setTBonus(e.target.value)} placeholder="bonus1.png, bonus2.png" />
            </div>
          </div>
          <button className="btn btn-primary" onClick={addTheme}><Sparkles size={16}/> Добавить тему</button>

          <div className="mt-4">
            <div className="h3 mb-2">Список тем</div>
            <div className="max-h-56 overflow-auto border rounded-xl">
              <table className="w-full text-sm">
                <thead><tr className="text-left text-slate-600"><th className="py-2 px-2">ID</th><th>Уровень</th><th>Название</th><th>Действия</th></tr></thead>
                <tbody>
                  {themes.map(t=>(
                    <tr key={t.id} className="border-t">
                      <td className="py-1 px-2">{t.id}</td>
                      <td>{t.level}</td>
                      <td>{t.name}</td>
                      <td>
                        <button className="btn" onClick={()=>delTheme(t.id)}><Trash2 size={16}/> удалить</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </Section>
  )
}

export default function App() {
  const auth = useAuth()
  const me = auth.payload ? { id: auth.payload.user_id, email: auth.payload.email, is_admin: !!auth.payload.is_admin } : null

  if (!auth.isAuthed) {
  return (
    <div className="max-w-6xl mx-auto p-6 md:p-10">
      <div className="grid gap-10 md:grid-cols-[360px,1fr] items-start">
        <div className="hidden md:flex justify-center">
          <img
            src="/logo.png"
            alt="Spanola"
            className="w-[320px] h-[320px] object-contain drop-shadow-lg select-none"
          />
        </div>

        <div>
          <div className="md:hidden flex justify-center mb-4">
            <img src="/logo.png" alt="Spanola" className="w-16 h-16 object-contain" />
          </div>

          <header className="mb-6">
            <h1 className="h1 text-center md:text-left">
              Spanola — обучение испанскому через комиксы
            </h1>
          </header>

          <AuthPanel onSuccess={(t) => auth.setToken(t)} />
        </div>
      </div>

  
      {import.meta.env.DEV && (
        <footer className="text-center text-xs text-slate-500 pt-6">
          © Spanola {new Date().getFullYear()}
        </footer>
      )}
    </div>
  )
}

  return (
    <div className="max-w-6xl mx-auto p-4 md:p-8 space-y-6">
      <header className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <img src="/logo.png" alt="Spanola" className="w-14 h-14 md:w-20 md:h-20 rounded-full object-contain shrink-0"
          />
          <div>
            <div className="h1">Spanola</div>
            <div className="text-slate-500 text-sm">Вы вошли как <b>{me.email}</b>{me.is_admin?' (админ)':''}</div>
          </div>
        </div>
        <button className="btn" onClick={auth.logout}><LogOut size={16}/> Выйти</button>
      </header>

      <div className="grid md:grid-cols-2 gap-4">
        <BalanceCard userId={me.id} />
        <WalletHistory userId={me.id} />
      </div>

      <PredictPanel userId={me.id} />

      <AdminPanel me={me} />

      <footer className="text-center text-xs text-slate-500 pt-6">
        © Spanola {new Date().getFullYear()}
      </footer>
    </div>
  )
}
