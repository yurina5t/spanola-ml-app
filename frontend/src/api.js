import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err?.response?.status === 401) {
      // токен протух — чистим и отправляем на логин
      localStorage.removeItem('token')
      // либо мягко «перерисовать»: window.location.reload()
      window.location.href = '/'     // у тебя после очистки токена покажется форма логина
    }
    return Promise.reject(err)
  }
)

function normalizeErr(err) {
  if (err.response?.data?.detail) return err.response.data.detail
  return err.message || 'Неизвестная ошибка'
}

// Endpoints kept in one place so paths are easy to adjust to your backend
export const endpoints = {
  // users
  register:  () => '/users/signup',    // JSON: { email, password }
  login:     () => '/users/signin',    // JSON: { email, password }
  listUsers: () => '/users/',          

  // wallet
  walletBalance: (userId) => `/wallet/${userId}`,
  walletHistory: (userId) => `/wallet/history/${userId}`,
  walletTopUp:   () => '/wallet/top_up',          // обычное пополнение
  walletRefill:  () => '/wallet/admin_top_up',    // админ-пополнение
  walletCanSpend:(userId, amount) => `/wallet/can_spend/${userId}/${amount}`,
  walletSpendBonus: () => '/wallet/spend_on_bonus',

  // themes
  themes:        () => '/themes/',                // список
  themeById:     (id) => `/themes/${id}`,
  themesByLevel: (level) => `/themes/level/${level}`,

  // predictions (синхронно)
  predictSync:        () => '/predictions/',      // POST
  predictionHistory:  (userId) => `/predictions/history/${userId}`,

   // tasks
  taskHistory:  (userId) => `/tasks/history/${userId}`,
  taskById:     (taskId) => `/tasks/${taskId}`,
  taskSubmit:   () => '/tasks/submit',
}

// Auth
export async function apiRegister({ email, password }) {
  try {
    const { data } = await api.post(endpoints.register(), { email, password });
    return { ok: true, data };
  } catch (e) { return { ok: false, error: (e.response?.data?.detail || e.message) }; }
}

export async function apiLogin({ email, password }) {
  try {
    const { data } = await api.post(endpoints.login(), { email, password });
    const t = data.access_token || data.token || data.jwt;
    if (t) localStorage.setItem('token', t);
    return { ok: true, data };
  } catch (e) { return { ok: false, error: (e.response?.data?.detail || e.message) }; }
}

// Users
export async function apiListUsers() {
  try {
    const { data } = await api.get(endpoints.listUsers())
    return { ok: true, data }
  } catch (e) { return { ok: false, error: normalizeErr(e) } }
}

// Wallet
export async function apiGetBalance(userId) {
  try {
    const { data } = await api.get(endpoints.walletBalance(userId))
    return { ok: true, data }
  } catch (e) { return { ok: false, error: normalizeErr(e) } }
}

export async function apiWalletHistory(userId) {
  try {
    const { data } = await api.get(endpoints.walletHistory(userId))
    return { ok: true, data }
  } catch (e) { return { ok: false, error: normalizeErr(e) } }
}

export async function apiRefill({ userId, amount, reason }) {
  try {
    const { data } = await api.post(endpoints.walletRefill(), { user_id: userId, amount, reason })
    return { ok: true, data }
  } catch (e) { return { ok: false, error: normalizeErr(e) } }
}

// Themes
export async function apiGetThemes() {
  try {
    const { data } = await api.get(endpoints.themes())
    return { ok: true, data }
  } catch (e) { return { ok: false, error: normalizeErr(e) } }
}

export async function apiCreateTheme({ name, level, base_comic, bonus_comics }) {
  try {
    const { data } = await api.post(endpoints.themes(), { name, level, base_comic, bonus_comics })
    return { ok: true, data }
  } catch (e) { return { ok: false, error: normalizeErr(e) } }
}

export async function apiDeleteTheme(id) {
  try {
    const { data } = await api.delete(endpoints.themeById(id))
    return { ok: true, data }
  } catch (e) { return { ok: false, error: normalizeErr(e) } }
}

// Predictions (sync). We try multiple endpoints to be compatible with your backend.
export async function apiPredictSync({ userId, themeId, isBonus }) {
  try {
    const { data } = await api.post(endpoints.predictSync(), {
      user_id: userId, theme_id: themeId, is_bonus: !!isBonus
    });
    return { ok: true, data };
  } catch (e) { return { ok: false, error: (e.response?.data?.detail || e.message) }; }
}


export default api
