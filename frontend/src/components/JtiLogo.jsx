export default function JtiLogo({ size = 40 }) {
  return (
    <svg
      width={size * 1.6}
      height={size}
      viewBox="0 0 80 50"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-label="JTI"
    >
      {/* J */}
      <path
        d="M4 8 H14 V34 C14 41 10 44 4 43"
        stroke="white"
        strokeWidth="4.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        fill="none"
      />
      {/* T */}
      <line x1="22" y1="8" x2="42" y2="8" stroke="white" strokeWidth="4.5" strokeLinecap="round" />
      <line x1="32" y1="8" x2="32" y2="43" stroke="white" strokeWidth="4.5" strokeLinecap="round" />
      {/* I */}
      <line x1="50" y1="8" x2="76" y2="8" stroke="white" strokeWidth="4.5" strokeLinecap="round" />
      <line x1="63" y1="8" x2="63" y2="43" stroke="white" strokeWidth="4.5" strokeLinecap="round" />
      <line x1="50" y1="43" x2="76" y2="43" stroke="white" strokeWidth="4.5" strokeLinecap="round" />
    </svg>
  );
}
