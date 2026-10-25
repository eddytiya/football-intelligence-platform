export function localDateKey(date = new Date()) {
    return [date.getFullYear(), String(date.getMonth() + 1).padStart(2, '0'), String(date.getDate()).padStart(2, '0')].join('-');
}

export function shiftMatchDate(dateKey, days) {
    const [year, month, day] = dateKey.split('-').map(Number);
    // Local noon avoids UTC date shifts and daylight-saving boundaries.
    return localDateKey(new Date(year, month - 1, day + days, 12));
}

export function statusForMatchDate(dateKey, today = localDateKey()) {
    return dateKey < today ? 'FINISHED' : 'SCHEDULED';
}
