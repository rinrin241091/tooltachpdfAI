import type { _ColumnFilterGridApi, _FilterGridApi, _QuickFilterGridApi } from '../api/gridApi';
import type { _ModuleWithApi, _ModuleWithoutApi } from '../interfaces/iModule';
/**
 * @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time.
 */
export declare const FilterCoreModule: _ModuleWithApi<_FilterGridApi>;
/**
 * @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time.
 */
export declare const FilterValueModule: _ModuleWithoutApi;
/**
 * @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time.
 */
export declare const ColumnFilterModule: _ModuleWithApi<_ColumnFilterGridApi>;
/**
 * @feature Filtering -> Custom Column Filters
 */
export declare const CustomFilterModule: _ModuleWithoutApi;
/**
 * @feature Filtering -> Text Filter
 */
export declare const TextFilterModule: _ModuleWithoutApi;
/**
 * @feature Filtering -> Number Filter
 */
export declare const NumberFilterModule: _ModuleWithoutApi;
/**
 * @feature Filtering -> BigInt Filter
 */
export declare const BigIntFilterModule: _ModuleWithoutApi;
/**
 * @feature Filtering -> Date Filter
 */
export declare const DateFilterModule: _ModuleWithoutApi;
/**
 * @feature Filtering -> Quick Filter
 * @gridOption quickFilterText
 */
export declare const QuickFilterModule: _ModuleWithApi<_QuickFilterGridApi>;
/**
 * @feature Filtering -> External Filter
 * @gridOption doesExternalFilterPass
 */
export declare const ExternalFilterModule: _ModuleWithoutApi;
