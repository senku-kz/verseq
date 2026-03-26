// Maps every key to its finger (0=left-pinky ... 7=right-pinky) and zone color
// Supports QWERTY (English) and ЙЦУКЕН (Russian) layouts

export interface KeyInfo {
  finger: number
  color: string
  label: string       // displayed on key cap
  labelShift?: string // Shift label (e.g., '!' for '1')
}

export type Layout = 'en' | 'ru'

const FINGER_COLORS: Record<number, string> = {
  0: '#e74c3c', // Left Pinky
  1: '#e67e22', // Left Ring
  2: '#f1c40f', // Left Middle
  3: '#2ecc71', // Left Index
  4: '#3498db', // Right Index
  5: '#9b59b6', // Right Middle
  6: '#e91e63', // Right Ring
  7: '#1abc9c', // Right Pinky
  8: '#95a5a6', // Space
}

export function useKeyboard() {
  function getFingerColor(finger: number): string {
    return FINGER_COLORS[finger] ?? '#95a5a6'
  }

  function getLayoutMap(layout: Layout): Record<string, KeyInfo> {
    if (layout === 'en') {
      return getEnglishLayoutMap()
    } else {
      return getRussianLayoutMap()
    }
  }

  function getKeyInfo(key: string, layout: Layout): KeyInfo | undefined {
    const map = getLayoutMap(layout)
    return map[key.toLowerCase()] ?? map[key]
  }

  return { getLayoutMap, getFingerColor, getKeyInfo }
}

function ki(finger: number, label: string, labelShift?: string): KeyInfo {
  return { finger, color: FINGER_COLORS[finger] ?? '#95a5a6', label, labelShift }
}

function getEnglishLayoutMap(): Record<string, KeyInfo> {
  return {
    // Digit row
    '`': ki(0, '`', '~'),
    '1': ki(0, '1', '!'),
    '2': ki(1, '2', '@'),
    '3': ki(2, '3', '#'),
    '4': ki(3, '4', '$'),
    '5': ki(3, '5', '%'),
    '6': ki(4, '6', '^'),
    '7': ki(4, '7', '&'),
    '8': ki(5, '8', '*'),
    '9': ki(6, '9', '('),
    '0': ki(7, '0', ')'),
    '-': ki(7, '-', '_'),
    '=': ki(7, '=', '+'),

    // Top row
    'q': ki(0, 'Q'),
    'w': ki(1, 'W'),
    'e': ki(2, 'E'),
    'r': ki(3, 'R'),
    't': ki(3, 'T'),
    'y': ki(4, 'Y'),
    'u': ki(4, 'U'),
    'i': ki(5, 'I'),
    'o': ki(6, 'O'),
    'p': ki(7, 'P'),
    '[': ki(7, '[', '{'),
    ']': ki(7, ']', '}'),
    '\\': ki(7, '\\', '|'),

    // Home row
    'a': ki(0, 'A'),
    's': ki(1, 'S'),
    'd': ki(2, 'D'),
    'f': ki(3, 'F'),
    'g': ki(3, 'G'),
    'h': ki(4, 'H'),
    'j': ki(4, 'J'),
    'k': ki(5, 'K'),
    'l': ki(6, 'L'),
    ';': ki(7, ';', ':'),
    "'": ki(7, "'", '"'),

    // Bottom row
    'z': ki(0, 'Z'),
    'x': ki(1, 'X'),
    'c': ki(2, 'C'),
    'v': ki(3, 'V'),
    'b': ki(3, 'B'),
    'n': ki(4, 'N'),
    'm': ki(4, 'M'),
    ',': ki(5, ',', '<'),
    '.': ki(6, '.', '>'),
    '/': ki(7, '/', '?'),

    // Special
    ' ': ki(8, 'Space'),
  }
}

function getRussianLayoutMap(): Record<string, KeyInfo> {
  return {
    // Digit row (same finger as QWERTY positionally)
    '1': ki(0, '1', '!'),
    '2': ki(1, '2', '"'),
    '3': ki(2, '3', '№'),
    '4': ki(3, '4', ';'),
    '5': ki(3, '5', '%'),
    '6': ki(4, '6', ':'),
    '7': ki(4, '7', '?'),
    '8': ki(5, '8', '*'),
    '9': ki(6, '9', '('),
    '0': ki(7, '0', ')'),
    '-': ki(7, '-', '_'),
    '=': ki(7, '=', '+'),

    // Top row (ЙЦУКЕН)
    'й': ki(0, 'Й', 'й'),
    'ц': ki(1, 'Ц', 'ц'),
    'у': ki(2, 'У', 'у'),
    'к': ki(3, 'К', 'к'),
    'е': ki(3, 'Е', 'е'),
    'н': ki(4, 'Н', 'н'),
    'г': ki(4, 'Г', 'г'),
    'ш': ki(5, 'Ш', 'ш'),
    'щ': ki(6, 'Щ', 'щ'),
    'з': ki(7, 'З', 'з'),
    'х': ki(7, 'Х', 'х'),
    'ъ': ki(7, 'Ъ', 'ъ'),

    // Home row (ФЫВАПР)
    'ф': ki(0, 'Ф', 'ф'),
    'ы': ki(1, 'Ы', 'ы'),
    'в': ki(2, 'В', 'в'),
    'а': ki(3, 'А', 'а'),
    'п': ki(3, 'П', 'п'),
    'р': ki(4, 'Р', 'р'),
    'о': ki(4, 'О', 'о'),
    'л': ki(5, 'Л', 'л'),
    'д': ki(6, 'Д', 'д'),
    'ж': ki(7, 'Ж', 'ж'),
    'э': ki(7, 'Э', 'э'),

    // Bottom row (ЯЧСМИТ)
    'я': ki(0, 'Я', 'я'),
    'ч': ki(1, 'Ч', 'ч'),
    'с': ki(2, 'С', 'с'),
    'м': ki(3, 'М', 'м'),
    'и': ki(3, 'И', 'и'),
    'т': ki(4, 'Т', 'т'),
    'ь': ki(4, 'Ь', 'ь'),
    'б': ki(5, 'Б', 'б'),
    'ю': ki(6, 'Ю', 'ю'),
    '.': ki(7, '.', ','),

    // Special
    ' ': ki(8, 'Space'),
  }
}
