import type { DefaultProvidedCellEditorParams, ICellEditorParams } from '../../interfaces/iCellEditor';
import type { GridInputTextField } from '../../widgets/gridWidgetTypes';
import { AgAbstractCellEditor } from './agAbstractCellEditor';
import type { CellEditorInput } from './iCellEditorInput';
export declare class SimpleCellEditor<TValue, P extends ICellEditorParams & DefaultProvidedCellEditorParams, I extends GridInputTextField> extends AgAbstractCellEditor<ICellEditorParams, TValue, string> {
    protected cellEditorInput: CellEditorInput<TValue, P, I>;
    private highlightAllOnFocus;
    private focusAfterAttached;
    protected readonly eEditor: I;
    constructor(cellEditorInput: CellEditorInput<TValue, P, I>);
    initialiseEditor(params: P): void;
    afterGuiAttached(): void;
    focusIn(): void;
    getValue(): TValue | null | undefined;
    agSetEditValue(value: TValue | null | undefined): void;
    isPopup(): boolean;
    getValidationElement(): HTMLInputElement;
    getValidationErrors(): string[] | null;
}
