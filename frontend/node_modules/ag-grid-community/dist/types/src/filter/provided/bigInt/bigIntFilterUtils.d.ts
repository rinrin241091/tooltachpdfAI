import type { Tuple } from '../iSimpleFilter';
import type { OptionsFactory } from '../optionsFactory';
import type { BigIntFilterModel, IBigIntFilterParams } from './iBigIntFilter';
export declare function getAllowedCharPattern(filterParams?: IBigIntFilterParams): string | null;
export declare function mapValuesFromBigIntFilterModel(filterModel: BigIntFilterModel | null, optionsFactory: OptionsFactory): Tuple<bigint>;
