import React, { useEffect, useState } from 'react'
// если alias '@' настроен — оставь эту строку; если нет, замени на '../shared/api'
import { apiGeneratePanel, apiSubmitPanel, apiGetThemes, apiGetBalance } from '../api'

export default function PanelBlock({ userId }) {
  const [level, setLevel] = useState('A1')
  const [themes, setThemes] = useState([])
  const [themeId, setThemeId] = useState('')

  const [exercise, setExercise] = useState(null)   // { exercise_id, questions: [...] }
  const [answers, setAnswers] = useState({})       // { [qid]: choice }
  const [result, setResult] = useState(null)       // { score, reward, ... }

  const [count, setCount] = useState(10)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  useEffect(() => {
    (async () => {
      const r = await apiGetThemes()
      if (r.ok) setThemes(r.data || [])
    })()
  }, [])

  const handleGenerate = async () => {
    if (!themeId) { setError('Выберите тему'); return }
    setLoading(true); setError(null); setResult(null); setAnswers({})
    const r = await apiGeneratePanel({ themeId: Number(themeId), count, level })
    setLoading(false)
    if (!r.ok) { setError(r.error); return }
    setExercise(r.data)
  }

  const pick = (qid, choice) => setAnswers(prev => ({ ...prev, [qid]: choice }))

  const handleSubmit = async () => {
    if (!exercise) return
    setLoading(true); setError(null)
    const r = await apiSubmitPanel({ exerciseId: exercise.exercise_id, answers })
    setLoading(false)
    if (!r.ok) { setError(r.error); return }
    setResult(r.data)
    if (userId) await apiGetBalance(userId) // обновить виджет баланса, если он есть
  }

  const themesFiltered = themes.filter(t =>
    !level || String(t.level).toUpperCase().startsWith(level)
  )

  return (
    <div className="rounded-2xl p-4 border mt-6">
      <h3 className="font-semibold text-lg mb-3">Тест (панель с ответами)</h3>

      <div className="grid gap-3 md:grid-cols-4">
        <label className="flex flex-col">
          <span className="text-sm text-gray-500 mb-1">Уровень</span>
          <select value={level} onChange={(e)=>setLevel(e.target.value)} className="border rounded p-2">
            {['A1','A2','B1','B2'].map(l => <option key={l} value={l}>{l}</option>)}
          </select>
        </label>

        <label className="flex flex-col">
          <span className="text-sm text-gray-500 mb-1">Тема</span>
          <select value={themeId} onChange={e=>setThemeId(e.target.value)} className="border rounded p-2">
            <option value="">— выберите тему —</option>
            {themesFiltered.map(t => (
              <option key={t.id} value={t.id}>{t.level} • {t.name}</option>
            ))}
          </select>
        </label>

        <label className="flex flex-col">
          <span className="text-sm text-gray-500 mb-1">Кол-во вопросов</span>
          <input type="number" min={3} max={20} value={count}
                 onChange={e=>setCount(Number(e.target.value) || 10)}
                 className="border rounded p-2" />
        </label>

        <div className="flex items-end">
          <button onClick={handleGenerate} disabled={loading || !themeId}
                  className="px-4 py-2 rounded bg-black text-white w-full">
            Сгенерировать
          </button>
        </div>
      </div>

      {error && <div className="text-red-600 mt-3">{error}</div>}

      {exercise && (
        <div className="mt-5 space-y-4">
          <div className="text-sm text-gray-600">{exercise.instructions}</div>

          {exercise.questions.map((q, idx) => (
            <div key={q.id} className="border rounded p-3">
              <div className="font-medium mb-2">{idx+1}. {q.prompt}</div>
              <div className="flex flex-wrap gap-2">
                {(q.choices || []).map((c) => {
                  const active = answers[q.id] === c
                  return (
                    <button key={c}
                            onClick={()=>pick(q.id, c)}
                            className={`px-3 py-1 border rounded ${active ? 'bg-black text-white' : ''}`}>
                      {c}
                    </button>
                  )
                })}
              </div>
            </div>
          ))}

          <button onClick={handleSubmit} disabled={loading}
                  className="px-4 py-2 rounded bg-emerald-600 text-white">
            Отправить
          </button>
        </div>
      )}

      {result && (
        <div className="mt-4 p-3 rounded bg-gray-50">
          <div>Результат: <b>{result.correct}/{result.total}</b> ({result.score}%)</div>
          <div>Начисление: <b>{result.reward}</b></div>
        </div>
      )}
    </div>
  )
}
