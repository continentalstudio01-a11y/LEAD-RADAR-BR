import { Radar } from 'lucide-react'

export default function EmptyState({ title, text, action }) {
  return (
    <div className="empty-state glass">
      <div className="empty-icon"><Radar size={22} /></div>
      <h3>{title}</h3>
      <p>{text}</p>
      {action}
    </div>
  )
}
