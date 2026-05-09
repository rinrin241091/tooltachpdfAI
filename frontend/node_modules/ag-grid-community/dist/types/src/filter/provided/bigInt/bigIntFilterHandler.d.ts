import type { Comparator } from '../iScalarFilter';
import { ScalarFilterHandler } from '../scalarFilterHandler';
import { BigIntFilterModelFormatter } from './bigIntFilterModelFormatter';
import type { BigIntFilterModel, IBigIntFilterParams } from './iBigIntFilter';
export declare class BigIntFilterHandler extends ScalarFilterHandler<BigIntFilterModel, bigint, IBigIntFilterParams> {
    readonly filterType: "bigint";
    protected readonly FilterModelFormatterClass: typeof BigIntFilterModelFormatter;
    constructor();
    protected comparator(): Comparator<bigint>;
    protected isValid(value: bigint): boolean;
}
