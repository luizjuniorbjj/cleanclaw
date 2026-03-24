/**
 * CleanClaw SVG Illustrations
 * Line art style, one accent color via .cc-ill-accent class
 * Strokes use currentColor to inherit text color
 * 120x120 viewBox, 2px stroke, minimal professional design
 */

// Auto-inject illustration styles
if (!document.getElementById('cc-ill-styles')) {
  const style = document.createElement('style');
  style.id = 'cc-ill-styles';
  style.textContent = `.cc-ill-accent { color: var(--cc-primary-500); } .cc-empty-state-illustration svg { color: var(--cc-neutral-400); }`;
  document.head.appendChild(style);
}

window.CleanClawIllustrations = {

  // 1. Calendar with checkmark — schedule empty states
  calendar: `<svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="20" y="28" width="80" height="72" rx="6" stroke="currentColor" stroke-width="2"/>
    <line x1="20" y1="48" x2="100" y2="48" stroke="currentColor" stroke-width="2"/>
    <line x1="40" y1="20" x2="40" y2="36" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line x1="60" y1="20" x2="60" y2="36" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line x1="80" y1="20" x2="80" y2="36" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <rect x="32" y="56" width="12" height="10" rx="2" stroke="currentColor" stroke-width="1.5"/>
    <rect x="54" y="56" width="12" height="10" rx="2" stroke="currentColor" stroke-width="1.5"/>
    <rect x="76" y="56" width="12" height="10" rx="2" stroke="currentColor" stroke-width="1.5"/>
    <rect x="32" y="76" width="12" height="10" rx="2" stroke="currentColor" stroke-width="1.5"/>
    <rect x="54" y="76" width="12" height="10" rx="2" stroke="currentColor" stroke-width="1.5"/>
    <polyline class="cc-ill-accent" points="72,81 78,87 90,73" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
  </svg>`,

  // 2. Two people silhouettes — team empty states
  team: `<svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="45" cy="38" r="12" stroke="currentColor" stroke-width="2"/>
    <path d="M22 88c0-14 10-26 23-26s23 12 23 26" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <circle cx="75" cy="38" r="12" stroke="currentColor" stroke-width="2"/>
    <path d="M52 88c0-14 10-26 23-26s23 12 23 26" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <circle class="cc-ill-accent" cx="90" cy="28" r="8" stroke="currentColor" stroke-width="2"/>
    <line class="cc-ill-accent" x1="90" y1="24" x2="90" y2="32" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line class="cc-ill-accent" x1="86" y1="28" x2="94" y2="28" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  </svg>`,

  // 3. Person with a house — client empty states
  clients: `<svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="44" cy="36" r="12" stroke="currentColor" stroke-width="2"/>
    <path d="M22 86c0-14 10-26 22-26s22 12 22 26" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path class="cc-ill-accent" d="M80 52l18 14v24H62V66l18-14z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
    <rect class="cc-ill-accent" x="74" y="74" width="12" height="16" rx="1" stroke="currentColor" stroke-width="2"/>
  </svg>`,

  // 4. Document with dollar sign — invoice empty states
  invoice: `<svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M32 16h40l16 16v72a4 4 0 01-4 4H36a4 4 0 01-4-4V16z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
    <path d="M72 16v16h16" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
    <line x1="44" y1="50" x2="76" y2="50" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    <line x1="44" y1="60" x2="76" y2="60" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    <line x1="44" y1="70" x2="64" y2="70" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    <text class="cc-ill-accent" x="60" y="92" text-anchor="middle" font-size="20" font-weight="600" font-family="inherit" fill="currentColor">$</text>
  </svg>`,

  // 5. Spray bottle with sparkle — services
  cleaning: `<svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="42" y="44" width="28" height="52" rx="4" stroke="currentColor" stroke-width="2"/>
    <path d="M48 44V32h16v12" stroke="currentColor" stroke-width="2"/>
    <rect x="52" y="24" width="8" height="8" rx="2" stroke="currentColor" stroke-width="2"/>
    <path d="M60 28h14l4-8" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <line x1="50" y1="60" x2="62" y2="60" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    <line x1="50" y1="68" x2="62" y2="68" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    <path class="cc-ill-accent" d="M84 36l2-6 2 6-6 2 6 2-2 6-2-6 6-2-6-2z" fill="currentColor"/>
    <path class="cc-ill-accent" d="M28 52l1.5-4.5 1.5 4.5-4.5 1.5 4.5 1.5-1.5 4.5-1.5-4.5 4.5-1.5-4.5-1.5z" fill="currentColor"/>
  </svg>`,

  // 6. Bar chart going up — revenue/earnings
  chart: `<svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    <line x1="24" y1="96" x2="96" y2="96" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line x1="24" y1="24" x2="24" y2="96" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <rect x="34" y="72" width="12" height="24" rx="2" stroke="currentColor" stroke-width="2"/>
    <rect x="54" y="56" width="12" height="40" rx="2" stroke="currentColor" stroke-width="2"/>
    <rect class="cc-ill-accent" x="74" y="36" width="12" height="60" rx="2" stroke="currentColor" stroke-width="2"/>
    <polyline class="cc-ill-accent" points="34,68 54,52 74,32 86,26" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <polyline class="cc-ill-accent" points="80,26 86,26 86,32" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
  </svg>`,

  // 7. Magnifying glass — no search results
  search: `<svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    <circle cx="52" cy="52" r="24" stroke="currentColor" stroke-width="2"/>
    <line x1="69" y1="69" x2="92" y2="92" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
    <line class="cc-ill-accent" x1="42" y1="46" x2="62" y2="46" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line class="cc-ill-accent" x1="42" y1="54" x2="56" y2="54" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  </svg>`,

  // 8. Clipboard with checkmarks — job detail/checklist
  checklist: `<svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="28" y="20" width="64" height="84" rx="6" stroke="currentColor" stroke-width="2"/>
    <rect x="46" y="14" width="28" height="14" rx="4" stroke="currentColor" stroke-width="2"/>
    <rect x="38" y="46" width="10" height="10" rx="2" stroke="currentColor" stroke-width="1.5"/>
    <polyline class="cc-ill-accent" points="40,51 43,54 48,48" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <line x1="56" y1="51" x2="80" y2="51" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    <rect x="38" y="64" width="10" height="10" rx="2" stroke="currentColor" stroke-width="1.5"/>
    <polyline class="cc-ill-accent" points="40,69 43,72 48,66" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <line x1="56" y1="69" x2="80" y2="69" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    <rect x="38" y="82" width="10" height="10" rx="2" stroke="currentColor" stroke-width="1.5"/>
    <line x1="56" y1="87" x2="74" y2="87" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
  </svg>`,

  // 9. Bell — notifications
  notification: `<svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M48 88h24" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M52 92a8 8 0 0016 0" stroke="currentColor" stroke-width="2"/>
    <path d="M36 88V56a24 24 0 0148 0v32H36z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
    <line x1="60" y1="20" x2="60" y2="32" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <circle class="cc-ill-accent" cx="80" cy="36" r="8" fill="currentColor" stroke="none"/>
  </svg>`,

  // 10. Hand wave — first-time user welcome
  welcome: `<svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M58 92c-12 0-20-8-24-20L26 50c-2-5 1-8 5-7s6 5 7 8l4 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M42 63l-6-18c-1.5-5 1-8 5-7s6 4 7 8l2 6" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M50 52l-4-14c-1.5-5 1-8 5-7s6 4 7 8l3 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M61 51l-3-10c-1.5-5 1-8 5-7s6 4 7 8l3 12" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <path d="M73 56l-1-6c-1-4 1-7 5-6s5 4 6 8l2 14c2 14-4 26-18 26" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
    <path class="cc-ill-accent" d="M82 24c4-8 8-12 12-10" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path class="cc-ill-accent" d="M90 18c2-4 6-4 8 0" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path class="cc-ill-accent" d="M96 28c4 0 6-2 6-6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  </svg>`,

  // 11. Coffee cup with clock — cleaner "no jobs today"
  noJobs: `<svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M28 44h52v8c0 22-8 36-26 36s-26-14-26-36v-8z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
    <path d="M80 52h8a12 12 0 010 24h-8" stroke="currentColor" stroke-width="2"/>
    <line x1="28" y1="100" x2="80" y2="100" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <path d="M44 100l6-12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    <path d="M64 100l-6-12" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    <path d="M42 36c0-4 4-6 4-10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    <path d="M54 36c0-4 4-6 4-10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
    <circle class="cc-ill-accent" cx="90" cy="36" r="16" stroke="currentColor" stroke-width="2"/>
    <line class="cc-ill-accent" x1="90" y1="28" x2="90" y2="36" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line class="cc-ill-accent" x1="90" y1="36" x2="98" y2="40" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  </svg>`,

  // 12. Calendar with pin — homeowner bookings
  booking: `<svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="20" y="28" width="80" height="72" rx="6" stroke="currentColor" stroke-width="2"/>
    <line x1="20" y1="48" x2="100" y2="48" stroke="currentColor" stroke-width="2"/>
    <line x1="40" y1="20" x2="40" y2="36" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line x1="60" y1="20" x2="60" y2="36" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <line x1="80" y1="20" x2="80" y2="36" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
    <rect x="34" y="56" width="10" height="10" rx="2" stroke="currentColor" stroke-width="1.5"/>
    <rect x="54" y="56" width="10" height="10" rx="2" stroke="currentColor" stroke-width="1.5"/>
    <rect x="34" y="74" width="10" height="10" rx="2" stroke="currentColor" stroke-width="1.5"/>
    <path class="cc-ill-accent" d="M76 56c0-6 6-14 6-14s6 8 6 14a6 6 0 01-12 0z" stroke="currentColor" stroke-width="2"/>
    <circle class="cc-ill-accent" cx="82" cy="58" r="2" fill="currentColor"/>
    <line class="cc-ill-accent" x1="82" y1="70" x2="82" y2="86" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
  </svg>`,

  // 13. Credit card with checkmark — payment success
  payment: `<svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    <rect x="14" y="34" width="76" height="52" rx="6" stroke="currentColor" stroke-width="2"/>
    <line x1="14" y1="50" x2="90" y2="50" stroke="currentColor" stroke-width="2"/>
    <line x1="14" y1="58" x2="90" y2="58" stroke="currentColor" stroke-width="2"/>
    <rect x="22" y="66" width="20" height="10" rx="2" stroke="currentColor" stroke-width="1.5"/>
    <circle class="cc-ill-accent" cx="88" cy="80" r="18" stroke="currentColor" stroke-width="2"/>
    <polyline class="cc-ill-accent" points="80,80 86,86 96,74" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
  </svg>`,

  // 14. Warning triangle — error states
  error: `<svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M60 20L104 96H16L60 20z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
    <line class="cc-ill-accent" x1="60" y1="48" x2="60" y2="72" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
    <circle class="cc-ill-accent" cx="60" cy="82" r="3" fill="currentColor"/>
  </svg>`,

  // 15. Cloud with X — offline state
  offline: `<svg width="120" height="120" viewBox="0 0 120 120" fill="none" xmlns="http://www.w3.org/2000/svg">
    <path d="M32 76a18 18 0 01-2-36 26 26 0 0150-6 20 20 0 01-2 40H32z" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/>
    <line class="cc-ill-accent" x1="46" y1="86" x2="66" y2="106" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
    <line class="cc-ill-accent" x1="66" y1="86" x2="46" y2="106" stroke="currentColor" stroke-width="3" stroke-linecap="round"/>
  </svg>`

};
