export default function ScoreRing({ value = 0, size = 52 }) {
  const radius = 20
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (Math.max(0, Math.min(100, value)) / 100) * circumference
  return (
    <div className="score-ring" style={{ width: size, height: size }} title={`Score ${value}/100`}>
      <svg viewBox="0 0 48 48" aria-hidden="true">
        <circle className="score-track" cx="24" cy="24" r={radius} />
        <circle className="score-value" cx="24" cy="24" r={radius} strokeDasharray={circumference} strokeDashoffset={offset} />
      </svg>
      <strong>{value}</strong>
    </div>
  )
}
