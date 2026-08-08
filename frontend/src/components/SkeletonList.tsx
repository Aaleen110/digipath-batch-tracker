export function SkeletonList() {
  return (
    <div className="grid grid-cols-1 gap-3" aria-hidden="true">
      {[0, 1, 2].map((i) => (
        <div
          key={i}
          className="relative animate-pulse overflow-hidden rounded-2xl border border-line bg-white"
        >
          <div className="absolute inset-y-0 left-0 w-1 bg-line" />
          <div className="p-5 pl-6 sm:p-6 sm:pl-7">
            <div className="mb-3 h-5 w-48 rounded bg-line" />
            <div className="mb-5 h-4 w-72 rounded bg-line" />
            <div className="grid grid-cols-1 gap-4 rounded-xl bg-paper/80 px-4 py-3.5 sm:grid-cols-3">
              {[0, 1, 2].map((j) => (
                <div key={j} className="h-8 rounded bg-line" />
              ))}
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
