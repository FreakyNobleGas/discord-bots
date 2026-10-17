// Timestamps come from SQLite as UTC "YYYY-MM-DD HH:MM:SS". Game nights run late, so a
// session counts toward the night it started on: shift back NIGHT_CUTOFF_HOURS, then take
// the calendar date in the group's timezone.

const NIGHT_CUTOFF_HOURS = 6;
const DAY_MS = 86_400_000;

const formatters = new Map<string, Intl.DateTimeFormat>();

function formatter(tz: string) {
	let f = formatters.get(tz);
	if (!f) {
		f = new Intl.DateTimeFormat('en-CA', {
			timeZone: tz,
			year: 'numeric',
			month: '2-digit',
			day: '2-digit'
		});
		formatters.set(tz, f);
	}
	return f;
}

export function parseSqlTimestamp(ts: string): Date {
	return new Date(ts.includes('T') ? ts : ts.replace(' ', 'T') + 'Z');
}

export function toSqlTimestamp(d: Date): string {
	return d.toISOString().slice(0, 19).replace('T', ' ');
}

/** "YYYY-MM-DD" of the game night a timestamp belongs to. */
export function nightKey(ts: string | Date, tz: string): string {
	const d = typeof ts === 'string' ? parseSqlTimestamp(ts) : ts;
	return formatter(tz).format(new Date(d.getTime() - NIGHT_CUTOFF_HOURS * 3_600_000));
}

/** Whole days between two "YYYY-MM-DD" keys (b - a). */
export function daysBetween(a: string, b: string): number {
	return Math.round((Date.parse(b) - Date.parse(a)) / DAY_MS);
}

export function addDays(key: string, days: number): string {
	return new Date(Date.parse(key) + days * DAY_MS).toISOString().slice(0, 10);
}

/** Monday of the ISO week containing a "YYYY-MM-DD" key. */
export function weekKey(key: string): string {
	const dow = new Date(key + 'T00:00:00Z').getUTCDay();
	return addDays(key, -((dow + 6) % 7));
}

export function monthKey(key: string): string {
	return key.slice(0, 7);
}

/** Every "YYYY-MM" from `from` to `to`, inclusive. */
export function monthRange(from: string, to: string): string[] {
	const out: string[] = [];
	let [y, m] = from.split('-').map(Number);
	const [ty, tm] = to.split('-').map(Number);
	while (y < ty || (y === ty && m <= tm)) {
		out.push(`${y}-${String(m).padStart(2, '0')}`);
		m++;
		if (m > 12) {
			m = 1;
			y++;
		}
	}
	return out;
}

export function formatMonth(month: string, style: 'short' | 'long' = 'short'): string {
	const d = new Date(month + '-01T12:00:00Z');
	return d.toLocaleDateString('en-US', {
		month: 'short',
		year: style === 'long' ? 'numeric' : '2-digit',
		timeZone: 'UTC'
	});
}

export function formatDay(key: string): string {
	return new Date(key + 'T12:00:00Z').toLocaleDateString('en-US', {
		month: 'short',
		day: 'numeric',
		year: 'numeric',
		timeZone: 'UTC'
	});
}

export function relativeDays(days: number | null): string {
	if (days === null) return 'never';
	if (days <= 0) return 'tonight';
	if (days === 1) return 'yesterday';
	if (days < 14) return `${days} days ago`;
	if (days < 60) return `${Math.round(days / 7)} weeks ago`;
	return `${Math.round(days / 30)} months ago`;
}
