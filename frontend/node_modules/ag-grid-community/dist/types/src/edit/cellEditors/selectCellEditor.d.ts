import type { BeanCollection } from '../../context/context';
import type { ICellEditorParams } from '../../interfaces/iCellEditor';
import type { GridSelect } from '../../widgets/gridWidgetTypes';
import { AgAbstractCellEditor } from './agAbstractCellEditor';
import type { ISelectCellEditorParams } from './iSelectCellEditor';
interface SelectCellEditorParams<TData = any, TValue = any, TContext = any> extends ISelectCellEditorParams<TValue>, ICellEditorParams<TData, TValue, TContext> {
}
export declare class SelectCellEditor<TValue = any> extends AgAbstractCellEditor<SelectCellEditorParams<any, TValue>, TValue> {
    private focusAfterAttached;
    private valueSvc;
    wireBeans(beans: BeanCollection): void;
    protected readonly eEditor: GridSelect<TValue>;
    private startedByEnter;
    constructor();
    initialiseEditor(params: SelectCellEditorParams<any, TValue>): void;
    afterGuiAttached(): void;
    focusIn(): void;
    agSetEditValue(value: TValue | null | undefined): void;
    getValue(): TValue | null | undefined;
    isPopup(): boolean;
    getValidationElement(): HTMLElement | HTMLInputElement;
    getValidationErrors(): string[] | null;
}
export {};
