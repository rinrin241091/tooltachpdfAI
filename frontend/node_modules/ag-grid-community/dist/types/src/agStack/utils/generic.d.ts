/**
 * If value is undefined, null or blank, returns null, otherwise returns the value
 * @param {T} value
 * @returns {T | null}
 * @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time.
 */
export declare const _makeNull: <T>(value?: T) => T | null;
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare function _exists(value: string | null | undefined): value is string;
export declare function _exists<T>(value: T): value is NonNullable<T>;
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare function _missing<T>(value: T | null | undefined): value is Exclude<undefined | null, T>;
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare const _toStringOrNull: (value: any) => string | null;
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare const _jsonEquals: <T1, T2>(val1: T1, val2: T2) => boolean;
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare const _defaultComparator: (valueA: any, valueB: any, accentedCompare?: boolean) => number;
