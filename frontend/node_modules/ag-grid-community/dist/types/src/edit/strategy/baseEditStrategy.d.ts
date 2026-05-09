import { BeanStub } from '../../context/beanStub';
import type { BeanName } from '../../context/context';
import type { AgEventType } from '../../eventTypes';
import type { CellFocusClearedEvent, CellFocusedEvent } from '../../events';
import type { EditMap } from '../../interfaces/iEditModelService';
import type { EditPosition, EditRowPosition, EditSource, StartEditWithPositionParams, _SetEditingCellsParams } from '../../interfaces/iEditService';
import type { CellCtrl } from '../../rendering/cell/cellCtrl';
import type { EditModelService } from '../editModelService';
import type { EditService } from '../editService';
export type EditValidationResult<T extends Required<EditPosition> = Required<EditPosition>> = {
    all: T[];
    pass: T[];
    fail: T[];
};
export type EditValidationAction<T extends Required<EditPosition> = Required<EditPosition>> = {
    destroy: T[];
    keep: T[];
};
export declare abstract class BaseEditStrategy extends BeanStub {
    beanName: BeanName | undefined;
    protected model: EditModelService;
    protected editSvc: EditService;
    postConstruct(): void;
    abstract midBatchInputsAllowed(position?: EditPosition): boolean;
    clearEdits(position: EditPosition): void;
    abstract start(params: StartEditWithPositionParams): void;
    onCellFocusChanged(event: CellFocusedEvent | CellFocusClearedEvent): void;
    abstract moveToNextEditingCell(previousCell: CellCtrl, backwards: boolean, event?: KeyboardEvent, source?: EditSource, preventNavigation?: boolean): boolean | null;
    stopCancelled(forceCancel: boolean): boolean;
    stopCommitted(event: Event | null, commit: boolean): boolean;
    protected abstract processValidationResults(results: EditValidationResult): EditValidationAction;
    cleanupEditors({ rowNode }?: EditRowPosition, includeEditing?: boolean): void;
    setFocusOutOnEditor(cellCtrl: CellCtrl): void;
    setFocusInOnEditor(cellCtrl: CellCtrl): void;
    setupEditors(params: StartEditWithPositionParams & {
        cells: Required<EditPosition>[];
    }): void;
    dispatchCellEvent<T extends AgEventType>(position: Required<EditPosition>, event?: Event | null, type?: T, payload?: any): void;
    dispatchRowEvent(position: Required<EditRowPosition>, type: 'rowEditingStarted' | 'rowEditingStopped' | 'rowValueChanged', silent?: boolean): void;
    shouldStop(_position?: EditPosition, event?: KeyboardEvent | MouseEvent | null | undefined, source?: EditSource): boolean | null;
    shouldCancel(_position?: EditPosition, event?: KeyboardEvent | MouseEvent | null | undefined, source?: 'api' | 'ui' | string): boolean | null;
    setEditMap(edits: EditMap, params?: _SetEditingCellsParams): void;
    destroy(): void;
}
