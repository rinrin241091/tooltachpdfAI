import type { OptionsFactory } from '../optionsFactory';
import { SCALAR_FILTER_TYPE_KEYS, SimpleFilterModelFormatter } from '../simpleFilterModelFormatter';
import type { BigIntFilterModel, IBigIntFilterParams } from './iBigIntFilter';
export declare class BigIntFilterModelFormatter extends SimpleFilterModelFormatter<IBigIntFilterParams, typeof SCALAR_FILTER_TYPE_KEYS, bigint> {
    protected readonly filterTypeKeys: {
        readonly equals: "Equals";
        readonly notEqual: "NotEqual";
        readonly greaterThan: "GreaterThan";
        readonly greaterThanOrEqual: "GreaterThanOrEqual";
        readonly lessThan: "LessThan";
        readonly lessThanOrEqual: "LessThanOrEqual";
        readonly inRange: "InRange";
    };
    constructor(optionsFactory: OptionsFactory, filterParams: IBigIntFilterParams);
    protected conditionToString(condition: BigIntFilterModel, forToolPanel: boolean, isRange: boolean, customDisplayKey: string | undefined, customDisplayName: string | undefined): string;
}
