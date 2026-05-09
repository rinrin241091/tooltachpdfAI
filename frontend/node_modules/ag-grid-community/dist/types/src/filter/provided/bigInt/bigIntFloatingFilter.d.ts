import type { FloatingFilterInputService } from '../../floating/provided/iFloatingFilterInputService';
import { TextInputFloatingFilter } from '../../floating/provided/textInputFloatingFilter';
import { BigIntFilterModelFormatter } from './bigIntFilterModelFormatter';
import type { BigIntFilterModel, IBigIntFloatingFilterParams } from './iBigIntFilter';
export declare class BigIntFloatingFilter extends TextInputFloatingFilter<IBigIntFloatingFilterParams, BigIntFilterModel> {
    protected readonly FilterModelFormatterClass: typeof BigIntFilterModelFormatter;
    private allowedCharPattern;
    private bigintParser;
    protected readonly filterType = "bigint";
    protected readonly defaultOptions: import("../iSimpleFilter").ISimpleFilterModelType[];
    protected updateParams(params: IBigIntFloatingFilterParams): void;
    protected createFloatingFilterInputService(params: IBigIntFloatingFilterParams): FloatingFilterInputService;
    protected convertValue<TValue>(value: string | null | undefined): TValue | null;
}
