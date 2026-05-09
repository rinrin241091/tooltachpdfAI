import type { ILocaleService, LocaleTextFunc } from '../interfaces/iLocaleService';
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare function _getLocaleTextFunc<TKey extends string = string>(localeSvc?: ILocaleService<TKey>): LocaleTextFunc<TKey>;
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare function _translate<T extends Record<string, string | ((variableValues: string[]) => string)>>(bean: {
    getLocaleTextFunc(): LocaleTextFunc;
}, localeValues: T, key: keyof T & string, variableValues?: string[]): string;
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare function _getLocaleTextFromFunc(getLocaleText: (params: {
    key: string;
    defaultValue: string;
    variableValues?: string[];
}) => string): LocaleTextFunc;
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare function _getLocaleTextFromMap(localeText?: {
    [key: string]: string;
}): LocaleTextFunc;
