import { test } from 'node:test';
import assert from 'node:assert/strict';
import { localDateKey, shiftMatchDate, statusForMatchDate } from '../src/utils/matchDateNavigation.js';

test('past days select results and today/future select fixtures', () => {
    assert.equal(statusForMatchDate('2026-10-17', '2026-10-18'), 'FINISHED');
    assert.equal(statusForMatchDate('2026-10-18', '2026-10-18'), 'SCHEDULED');
    assert.equal(statusForMatchDate('2026-10-19', '2026-10-18'), 'SCHEDULED');
});

test('navigation moves by calendar day across month, year and leap-day boundaries', () => {
    assert.equal(shiftMatchDate('2026-10-18', -1), '2026-10-17');
    assert.equal(shiftMatchDate('2026-01-01', -1), '2025-12-31');
    assert.equal(shiftMatchDate('2026-10-31', 1), '2026-11-01');
    assert.equal(shiftMatchDate('2024-03-01', -1), '2024-02-29');
});

test('today is the local calendar date rather than a UTC string slice', () => {
    const date = new Date(2026, 9, 18, 0, 15);
    assert.equal(localDateKey(date), '2026-10-18');
});
