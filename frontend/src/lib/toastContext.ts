import { createContext } from "react";

export type ToastLevel = "success" | "error" | "info";

export type Toast = {
  id: number;
  message: string;
  level: ToastLevel;
};

export type ToastContextValue = {
  pushToast: (message: string, level?: ToastLevel) => void;
};

export const ToastContext = createContext<ToastContextValue | null>(null);
