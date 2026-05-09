import type { IAfterGuiAttachedParams } from '../../../interfaces/iAfterGuiAttachedParams';
import type { FilterDisplayParams } from '../../../interfaces/iFilter';
import type { GridInputTextField } from '../../../widgets/gridWidgetTypes';
import type { ProvidedFilterParams } from '../iProvidedFilter';
import type { ICombinedSimpleModel, Tuple } from '../iSimpleFilter';
import { SimpleFilter } from '../simpleFilter';
import type { BigIntFilterModel, IBigIntFilterParams } from './iBigIntFilter';
/** temporary type until `BigIntFilterParams` is updated as breaking change */
type BigIntFilterDisplayParams = IBigIntFilterParams & FilterDisplayParams<any, any, BigIntFilterModel | ICombinedSimpleModel<BigIntFilterModel>>;
export declare class BigIntFilter extends SimpleFilter<BigIntFilterModel, bigint, GridInputTextField, BigIntFilterDisplayParams> {
    private readonly eValuesFrom;
    private readonly eValuesTo;
    readonly filterType: "bigint";
    constructor();
    protected defaultDebounceMs: number;
    afterGuiAttached(params?: IAfterGuiAttachedParams | undefined): void;
    protected shouldKeepInvalidInputState(): boolean;
    private refreshInputValidation;
    private refreshInputPairValidation;
    protected getState(): {
        isInvalid: boolean;
    };
    protected areStatesEqual(stateA?: {
        isInvalid: boolean;
    }, stateB?: {
        isInvalid: boolean;
    }): boolean;
    refresh(legacyNewParams: ProvidedFilterParams): boolean;
    protected setElementValue(element: GridInputTextField, value: bigint | null, fromFloatingFilter?: boolean): void;
    protected createEValue(): HTMLElement;
    private createFromToElement;
    protected removeEValues(startPosition: number, deleteCount?: number): void;
    protected getValues(position: number): Tuple<bigint>;
    protected areSimpleModelsEqual(aSimple: BigIntFilterModel, bSimple: BigIntFilterModel): boolean;
    protected createCondition(position: number): BigIntFilterModel;
    protected removeConditionsAndOperators(startPosition: number, deleteCount?: number | undefined): void;
    protected getInputs(position: number): Tuple<GridInputTextField>;
    protected hasInvalidInputs(): boolean;
    protected positionHasInvalidInputs(position: number): boolean;
    protected canApply(_model: BigIntFilterModel | ICombinedSimpleModel<BigIntFilterModel> | null): boolean;
    private getParsedValue;
    private isInvalidValue;
}
export {};
