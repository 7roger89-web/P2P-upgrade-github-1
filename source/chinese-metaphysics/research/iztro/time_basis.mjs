// Independent civil-time -> true-solar-time transport for Ziwei input.
// Formula source: NOAA General Solar Position Calculations.
// time_offset(minutes) = equation_of_time + 4*longitude - 60*UTC_offset.
// This file intentionally does NOT copy ziweiknows/ziwei-chart GPL code.

export const TIME_BASIS_SOURCE = {
  authority: 'NOAA_GML_GENERAL_SOLAR_POSITION_CALCULATIONS',
  url: 'https://gml.noaa.gov/grad/solcalc/solareqns.PDF',
  reference_upstream: 'ziweiknows/ziwei-chart@b172413d85addbe32facd9e20b9179db619f3afb',
  reference_boundary: 'ARCHITECTURE_AND_CHINA_FIXTURE_REFERENCE_ONLY__NO_GPL_CODE_COPIED',
};

function fail(message) { throw new Error(message); }

function isLeapYear(year) {
  return year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0);
}

function daysInYear(year) { return isLeapYear(year) ? 366 : 365; }

function dayOfYear(year, month, day) {
  const start = Date.UTC(year, 0, 1);
  const current = Date.UTC(year, month - 1, day);
  return Math.floor((current - start) / 86_400_000) + 1;
}

export function equationOfTimeMinutes(year, month, day, hour = 12, minute = 0) {
  const doy = dayOfYear(year, month, day);
  const fractionalHour = hour + minute / 60;
  const gamma = (2 * Math.PI / daysInYear(year)) * (doy - 1 + (fractionalHour - 12) / 24);
  return 229.18 * (
    0.000075
    + 0.001868 * Math.cos(gamma)
    - 0.032077 * Math.sin(gamma)
    - 0.014615 * Math.cos(2 * gamma)
    - 0.040849 * Math.sin(2 * gamma)
  );
}

export function clockToIztroTimeIndex(hour) {
  if (!Number.isInteger(hour) || hour < 0 || hour > 23) fail(`Invalid hour: ${hour}`);
  if (hour === 23) return 12;
  if (hour === 0) return 0;
  return Math.floor((hour + 1) / 2);
}

function normalizeLocalMinutes(year, month, day, totalMinutes) {
  const baseUtc = Date.UTC(year, month - 1, day, 0, 0, 0);
  const adjusted = new Date(baseUtc + totalMinutes * 60_000);
  return {
    year: adjusted.getUTCFullYear(),
    month: adjusted.getUTCMonth() + 1,
    day: adjusted.getUTCDate(),
    hour: adjusted.getUTCHours(),
    minute: adjusted.getUTCMinutes(),
  };
}

export function resolveTimeBasis({
  year,
  month,
  day,
  hour,
  minute = 0,
  basis = 'civil',
  longitude,
  utcOffset,
}) {
  for (const [name, value] of Object.entries({ year, month, day, hour, minute })) {
    if (!Number.isFinite(value)) fail(`Invalid ${name}: ${value}`);
  }
  if (!Number.isInteger(year) || !Number.isInteger(month) || !Number.isInteger(day)
      || !Number.isInteger(hour) || !Number.isInteger(minute)) fail('Date/time components must be integers');
  if (month < 1 || month > 12 || day < 1 || day > 31 || hour < 0 || hour > 23 || minute < 0 || minute > 59) {
    fail('Invalid civil date/time range');
  }
  const validation = new Date(Date.UTC(year, month - 1, day));
  if (validation.getUTCFullYear() !== year || validation.getUTCMonth() + 1 !== month || validation.getUTCDate() !== day) {
    fail('Invalid civil calendar date');
  }
  if (!['civil', 'true-solar'].includes(basis)) fail(`Invalid time basis: ${basis}`);

  const originalTimeIndex = clockToIztroTimeIndex(hour);
  if (basis === 'civil') {
    return {
      basis: 'CIVIL_TIME',
      source: TIME_BASIS_SOURCE,
      input: { year, month, day, hour, minute },
      longitude: null,
      utc_offset: null,
      equation_of_time_minutes: 0,
      longitude_timezone_minutes: 0,
      correction_minutes: 0,
      corrected: { year, month, day, hour, minute },
      time_index: originalTimeIndex,
      crossed_date: false,
    };
  }

  if (!Number.isFinite(longitude) || longitude < -180 || longitude > 180) {
    fail('TRUE_SOLAR requires --longitude in [-180, 180]');
  }
  if (!Number.isFinite(utcOffset) || utcOffset < -14 || utcOffset > 14) {
    fail('TRUE_SOLAR requires --utc-offset in [-14, 14]');
  }

  const eqtime = equationOfTimeMinutes(year, month, day, hour, minute);
  const longitudeTimezoneMinutes = 4 * longitude - 60 * utcOffset;
  const correctionMinutes = eqtime + longitudeTimezoneMinutes;
  const civilMinutes = hour * 60 + minute;
  const corrected = normalizeLocalMinutes(year, month, day, civilMinutes + correctionMinutes);

  return {
    basis: 'TRUE_SOLAR_TIME',
    source: TIME_BASIS_SOURCE,
    input: { year, month, day, hour, minute },
    longitude,
    utc_offset: utcOffset,
    equation_of_time_minutes: eqtime,
    longitude_timezone_minutes: longitudeTimezoneMinutes,
    correction_minutes: correctionMinutes,
    corrected,
    time_index: clockToIztroTimeIndex(corrected.hour),
    crossed_date: corrected.year !== year || corrected.month !== month || corrected.day !== day,
  };
}
