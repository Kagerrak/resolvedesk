export function Brand({ compact = false }: { compact?: boolean }) {
  return (
    <span className="brand">
      <svg viewBox="0 0 32 32" aria-hidden="true" fill="none">
        <path
          d="M8 25H5V5h22v20H15l-7 5v-5Z"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinejoin="round"
        />
        <path
          d="M11 12h10M11 18h6l3-3"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
      {!compact && <span>ResolveDesk</span>}
    </span>
  );
}
