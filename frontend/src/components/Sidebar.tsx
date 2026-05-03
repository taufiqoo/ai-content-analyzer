"use client";
import { useState, useEffect } from "react";
import { usePathname } from "next/navigation";
import Link from "next/link";

const navItems = [
  { href: "/", icon: "⚡", label: "Dashboard" },
  { href: "/scripts", icon: "📝", label: "Script Manager" },
  { href: "/manual", icon: "✍️", label: "Manual Generate" },
  { href: "/tweets", icon: "🐦", label: "Tweet Sources" },
  { href: "/analytics", icon: "📊", label: "Analytics" },
  { href: "/settings", icon: "⚙️", label: "Settings" },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <h1>🎬 ContentAI</h1>
        <p>TikTok Script Pipeline</p>
      </div>
      <nav className="sidebar-nav">
        {navItems.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={`nav-item ${pathname === item.href ? "active" : ""}`}
          >
            <span className="nav-icon">{item.icon}</span>
            {item.label}
          </Link>
        ))}
      </nav>
      <div style={{ padding: "16px 24px", borderTop: "1px solid var(--border-subtle)" }}>
        <p style={{ fontSize: "0.72rem", color: "var(--text-muted)" }}>v1.1.0 · Plan-v1.1</p>
      </div>
    </aside>
  );
}
