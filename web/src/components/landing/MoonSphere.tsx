import type { ReactNode } from "react";

// The hero Moon. The 3D Moon (children) is drawn over a CSS stand-in lit the same way, which stays
// visible while three.js loads and is the fallback without WebGL. The stand-in texture is the real
// LOLA polar hillshade from app/data/img.
export function MoonSphere({ texture, ready, children }: { texture: string | null; ready?: boolean; children?: ReactNode }) {
  return (
    <div className={`l-moon ${ready ? "ready" : ""}`} aria-hidden>
      <svg className="l-orbit" viewBox="0 0 1000 1000">
        <g transform="rotate(-18 500 500)">
          <ellipse cx="500" cy="500" rx="495" ry="150" />
          <circle className="l-orbit-dot" r="4" cx="0" cy="0">
            <animateMotion dur="90s" repeatCount="indefinite" path="M 5 500 a 495 150 0 1 0 990 0 a 495 150 0 1 0 -990 0" />
          </circle>
        </g>
      </svg>
      <div className="l-moon-body">
        {texture && <div className="l-moon-tex" style={{ backgroundImage: `url(${texture})` }} />}
        <div className="l-moon-light" />
      </div>
      {children}
    </div>
  );
}
