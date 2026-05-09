import type { NamedBean } from '../context/bean';
import { BeanStub } from '../context/beanStub';
import type { AgColumn } from '../entities/agColumn';
import type { RowNode } from '../entities/rowNode';
import { RowDragComp } from './rowDragComp';
import { RowDragFeature } from './rowDragFeature';
import type { RowDragVisibility } from './rowDragTypes';
/** @internal AG_GRID_INTERNAL - Not for public use. Can change / be removed at any time. */
export declare class RowDragService extends BeanStub implements NamedBean {
    beanName: "rowDragSvc";
    rowDragFeature: RowDragFeature | null;
    visibility: RowDragVisibility;
    setupRowDrag(element: HTMLElement, ctrl: BeanStub): void;
    createRowDragComp(cellValueFn: () => string, rowNode: RowNode, column?: AgColumn, customGui?: HTMLElement, dragStartPixels?: number, alwaysVisible?: boolean): RowDragComp;
    createRowDragCompForRow(rowNode: RowNode, element: HTMLElement): RowDragComp | undefined;
    createRowDragCompForCell(rowNode: RowNode, column: AgColumn, cellValueFn: () => string, element?: HTMLElement, dragStartPixels?: number, alwaysVisible?: boolean): RowDragComp | undefined;
    cancelRowDrag(): void;
    private computeVisibility;
    private refreshVisibility;
}
