interface FieldProps {
  label: string
  value?: string | number | null
  mono?: boolean
}

export function Field({ label, value, mono }: FieldProps) {
  return (
    <div className="min-w-0">
      <p className="text-[11px] font-medium uppercase tracking-wide text-slate2">
        {label}
      </p>
      <p
        className={`mt-0.5 truncate text-ink ${
          mono ? 'font-mono text-[13px]' : 'text-sm'
        }`}
      >
        {value === undefined || value === null || value === '' ? '—' : value}
      </p>
    </div>
  )
}
