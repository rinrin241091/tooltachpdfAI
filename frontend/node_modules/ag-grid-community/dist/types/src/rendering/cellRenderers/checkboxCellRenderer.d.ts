import { Component } from '../../widgets/component';
import type { ICellRenderer, ICellRendererParams } from './iCellRenderer';
export interface ICheckboxCellRendererParams<TData = any, TContext = any> extends ICellRendererParams<TData, boolean, TContext> {
    /** Set to `true` for the input to be disabled. */
    disabled?: boolean;
}
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare class CheckboxCellRenderer extends Component implements ICellRenderer {
    private readonly eCheckbox;
    private params;
    constructor();
    init(params: ICheckboxCellRendererParams): void;
    refresh(params: ICheckboxCellRendererParams): boolean;
    private updateCheckbox;
    private onCheckboxChanged;
}
