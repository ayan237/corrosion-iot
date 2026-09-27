"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const links = [
  { href: "/",        label: "Dashboard", short: "DASH" },
  { href: "/inspect", label: "New Inspection", short: "SCAN" },
  { href: "/history", label: "History", short: "LOG" },
];

export default function Navbar() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);

  return (
    <nav className="sticky top-0 z-50 border-b border-[#2a2a3a] bg-[#0a0a0f]/90 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-3 flex items-center gap-4 sm:gap-6">
        {/* Brand */}
        <Link
          href="/"
          className="flex items-center gap-2.5 mr-2 sm:mr-4 group shrink-0"
          onClick={() => setOpen(false)}
        >
          <span
            className="text-[#00ff88] text-xl leading-none group-hover:drop-shadow-[0_0_6px_#00ff88] transition-all"
            aria-hidden
          >
            ⬡
          </span>
          <span className="font-heading font-black text-sm tracking-[0.2em] uppercase text-[#e0e0e0]">
            CORROSION
            <span className="neon-text">INSPECT</span>
          </span>
        </Link>

        {/* Desktop links */}
        <div className="hidden md:flex items-center gap-1">
          {links.map(({ href, label }) => {
            const active =
              href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={`font-label text-xs tracking-[0.18em] uppercase px-3 py-2 min-h-[44px] inline-flex items-center transition-all ${
                  active
                    ? "text-[#00ff88] border-b-2 border-[#00ff88] shadow-[0_2px_8px_#00ff8840]"
                    : "text-[#6b7280] hover:text-[#00d4ff] border-b-2 border-transparent"
                }`}
              >
                {label}
              </Link>
            );
          })}
        </div>

        <div className="ml-auto flex items-center gap-3">
          <div className="hidden sm:flex items-center gap-2 font-label text-[10px] tracking-[0.2em] uppercase text-[#6b7280]">
            <span className="w-1.5 h-1.5 bg-[#00ff88] status-dot-live rounded-none" />
            PROTO_v1.0
          </div>

          {/* Mobile menu toggle */}
          <button
            type="button"
            className="md:hidden cyber-btn cyber-btn-outline cyber-chamfer-sm !min-h-[40px] !px-3 !py-1 !text-[10px]"
            onClick={() => setOpen((v) => !v)}
            aria-expanded={open}
            aria-label="Toggle navigation"
          >
            {open ? "CLOSE" : "MENU"}
          </button>
        </div>
      </div>

      {/* Mobile drawer */}
      {open && (
        <div className="md:hidden border-t border-[#2a2a3a] bg-[#12121a] px-4 py-3 flex flex-col gap-1">
          {links.map(({ href, label, short }) => {
            const active =
              href === "/" ? pathname === "/" : pathname.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                onClick={() => setOpen(false)}
                className={`font-label text-xs tracking-[0.18em] uppercase px-3 py-3 min-h-[44px] ${
                  active ? "text-[#00ff88] neon-glow-sm bg-[#00ff88]/5" : "text-[#6b7280]"
                }`}
              >
                <span className="text-[#00ff88] mr-2">&gt;</span>
                {label}
                <span className="text-[#2a2a3a] ml-2">/{short}</span>
              </Link>
            );
          })}
        </div>
      )}
    </nav>
  );
}
