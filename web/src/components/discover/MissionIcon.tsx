export function MissionIcon({ kind }: { kind: string }) {
  return <svg viewBox="0 0 64 64" fill="none" stroke="currentColor" strokeWidth="1.4" aria-hidden>
    <path d="M4 51h56M8 55h7m29 0h12" opacity=".25" />
    {kind === "rover" ? <><path d="M15 39h32l-5-12H22l-7 12Zm17-12V15h12m-8 0v-5M10 41h44M17 34l-7-6"/><circle cx="19" cy="45" r="5"/><circle cx="45" cy="45" r="5"/><path d="M28 28v10m9-10v10"/></> :
     kind === "base" ? <><path d="M9 48V33l23-21 23 21v15H9Zm0-15h46M24 48V34h16v14M32 12v-7m0 0h11v7H32"/><path d="M17 37v5m30-5v5"/></> :
     kind === "rock" ? <><path d="m12 48-4-16 14-16 21 5 13 19-10 8H12Zm10-32 5 19 16-14M8 32l19 3-15 13m15-13 19 13 10-8M27 35l7-10"/></> :
     <><circle cx="43" cy="18" r="7"/><path d="M43 3v4m0 22v4M28 18h4m22 0h5M32 7l3 3m16 16 3 3m0-22-3 3M6 48l11-23 9 23H6Zm20 0 31-9M24 42l28-6"/></>}
  </svg>;
}
