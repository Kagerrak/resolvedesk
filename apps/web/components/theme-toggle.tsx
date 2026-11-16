"use client";
import { Moon, Sun } from "lucide-react";
import { useEffect, useSyncExternalStore } from "react";
const subscribe = (callback: () => void) => {
  window.addEventListener("theme-change", callback);
  return () => window.removeEventListener("theme-change", callback);
};
function snapshot() {
  return document.documentElement.dataset.theme === "dark";
}
export function ThemeToggle() {
  useEffect(() => {
    document.documentElement.dataset.theme =
      localStorage.getItem("resolvedesk-theme") ?? "light";
    window.dispatchEvent(new Event("theme-change"));
  }, []);
  const dark = useSyncExternalStore(subscribe, snapshot, () => false);
  function toggle() {
    document.documentElement.dataset.theme = dark ? "light" : "dark";
    localStorage.setItem("resolvedesk-theme", dark ? "light" : "dark");
    window.dispatchEvent(new Event("theme-change"));
  }
  return (
    <button
      className="icon-button"
      onClick={toggle}
      aria-label={dark ? "Use light theme" : "Use dark theme"}
    >
      {dark ? <Sun size={18} /> : <Moon size={18} />}
    </button>
  );
}
