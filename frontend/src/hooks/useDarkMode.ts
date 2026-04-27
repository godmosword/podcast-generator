import { useEffect, useState } from "react";

export function useDarkMode(): [boolean, React.Dispatch<React.SetStateAction<boolean>>] {
  const [dark, setDark] = useState<boolean>(() => {
    const stored = localStorage.getItem("wavescript-theme");
    if (stored) return stored === "dark";
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  });

  useEffect(() => {
    document.documentElement.setAttribute("data-theme", dark ? "dark" : "light");
    localStorage.setItem("wavescript-theme", dark ? "dark" : "light");
  }, [dark]);

  return [dark, setDark];
}
