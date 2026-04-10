"use client";
import "./globals.css";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/", label: "Briefing", icon: "\u2302" },
  { href: "/chat", label: "Ask Coach", icon: "\u2726" },
  { href: "/week", label: "Weekly Review", icon: "\u25CB" },
  { href: "/decisions", label: "Decisions", icon: "\u26A1" },
  { href: "/priorities", label: "Priorities", icon: "\u25CE" },
];

const PILLARS = [
  { name: "Analytics & AI", pct: "35%", color: "var(--chart-navy)" },
  { name: "MC & QBO Intelligence", pct: "30%", color: "var(--chart-blue)" },
  { name: "Data Foundation", pct: "20%", color: "var(--chart-teal)" },
  { name: "Leadership & Strategy", pct: "15%", color: "var(--warning)" },
];

export default function RootLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();

  return (
    <html lang="en" className="h-full antialiased">
      <head>
        <title>Personal Productivity Coach</title>
        <meta name="description" content="Self-assist productivity coaching for PM leads" />
      </head>
      <body className="min-h-full">
        <div className="flex h-screen overflow-hidden">
          {/* Dark navy sidebar */}
          <aside
            className="w-[240px] flex-shrink-0 flex flex-col"
            style={{ background: "var(--sidebar-bg)" }}
          >
            {/* Logo */}
            <div className="px-5 py-5 flex items-center gap-2">
              <span className="text-[#00b9a9] text-xl">{"\u2726"}</span>
              <span className="text-white font-semibold text-[15px]">Self Coach</span>
            </div>

            {/* Navigation */}
            <nav className="flex-1 px-3 space-y-1">
              {NAV_ITEMS.map((item) => {
                const active = item.href === "/" ? pathname === "/" : pathname.startsWith(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`flex items-center gap-3 px-3 py-2 rounded-md text-[13px] transition-colors ${
                      active
                        ? "bg-white/15 text-white font-medium"
                        : "text-white/70 hover:bg-white/10 hover:text-white"
                    }`}
                  >
                    <span className="text-base w-5 text-center">{item.icon}</span>
                    {item.label}
                  </Link>
                );
              })}
            </nav>

            {/* FY26 Q4 Pillars */}
            <div className="px-3 pb-5">
              <div className="text-white/40 text-[11px] font-medium uppercase tracking-wider px-3 mb-2">
                FY26 Q4
              </div>
              {PILLARS.map((p) => (
                <div key={p.name} className="flex items-center gap-2 px-3 py-1.5 text-[12px] text-white/60">
                  <span className="w-2 h-2 rounded-full" style={{ background: p.color }} />
                  <span className="flex-1">{p.name}</span>
                  <span className="text-white/40">{p.pct}</span>
                </div>
              ))}
            </div>
          </aside>

          {/* Main content */}
          <main className="flex-1 overflow-y-auto" style={{ background: "var(--page-bg)" }}>
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
