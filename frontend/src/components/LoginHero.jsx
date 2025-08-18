// frontend/src/components/LoginHero.jsx
export default function LoginHero() {
  return (
    <div className="hidden md:block">
      <div className="relative rounded-2xl overflow-hidden shadow-lg border">
        <img
          src="/logo.png"
          alt="Learning Spanish — комиксы и упражнения"
          className="w-full h-[420px] object-cover"
          loading="lazy"
        />
        {/* мягкий градиент, чтобы текст читался */}
        <div className="absolute inset-0 bg-gradient-to-t from-white/85 via-white/20 to-transparent" />
        <div className="absolute bottom-4 left-4 right-4">
          <div className="text-lg font-semibold">Комиксы + упражнения</div>
          <p className="text-slate-700 text-sm">
            Учите слова и грамматику играючи — уровни A1–C1
          </p>
        </div>
      </div>
    </div>
  )
}
