const REASONS: Record<string, string> = {
  EMPTY_INPUT: "пустой ввод",
  TEXT_TOO_LONG: "текст слишком длинный",
  INVALID_JSON: "модель вернула не JSON",
  SCHEMA_MISMATCH: "ответ не прошёл схему",
  LLM_TIMEOUT: "модель не ответила вовремя",
  LLM_ERROR: "ошибка модели",
  PROMPT_INJECTION: "попытка перебить инструкции",
  VAGUE_INPUT: "слишком общий вход",
  MIXED_INTENTS: "несколько несводимых намерений",
  LOW_CONFIDENCE: "низкая уверенность",
};

export function reasonLabel(code: string | null | undefined): string {
  if (!code) {
    return "требует проверки";
  }
  return REASONS[code] ?? code;
}
