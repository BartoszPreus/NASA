import { Dither } from "./Dither";

// Dithered light streaks behind a section (see Dither.tsx). `quiet` is the fainter variant.
export function PixelWaves({ quiet = false }: { quiet?: boolean }) {
  return <Dither className={`pixel-waves ${quiet ? "quiet" : ""}`} shape="wave" pixel={4} falloff={1.5} opacity={quiet ? 0.22 : 0.26} intensity={quiet ? 0.75 : 0.9} />;
}
