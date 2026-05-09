import { BeanStub } from '../context/beanStub';
import type { DragAndDropIcon, DropTarget } from './dragAndDropService';
import { DragSourceType } from './dragAndDropService';
import type { RowDraggingEvent, RowDropZoneEvents, RowDropZoneParams } from './rowDragTypes';
export declare class RowDragFeature extends BeanStub implements DropTarget {
    private eContainer;
    lastDraggingEvent: RowDraggingEvent | null;
    private autoScroll;
    private autoScrollChanged;
    private autoScrollChanging;
    private autoScrollOldV;
    constructor(eContainer: HTMLElement | null);
    postConstruct(): void;
    destroy(): void;
    getContainer(): HTMLElement;
    isInterestedIn(type: DragSourceType): boolean;
    getIconName(draggingEvent: RowDraggingEvent | null): DragAndDropIcon;
    private getRowNodes;
    onDragEnter(draggingEvent: RowDraggingEvent): void;
    onDragging(draggingEvent: RowDraggingEvent): void;
    private dragging;
    private isFromThisGrid;
    private makeRowsDrop;
    private newRowsDrop;
    private validateRowsDrop;
    private computeDropPosition;
    private enforceSuppressMoveWhenRowDragging;
    private applyDropValidator;
    addRowDropZone(params: RowDropZoneParams & {
        fromGrid?: boolean;
    }): void;
    getRowDropZone(events?: RowDropZoneEvents): RowDropZoneParams;
    private getOverNode;
    private rowDragEvent;
    private dispatchGridEvent;
    onDragLeave(draggingEvent: RowDraggingEvent): void;
    onDragStop(draggingEvent: RowDraggingEvent): void;
    onDragCancel(draggingEvent: RowDraggingEvent): void;
    private stopDragging;
    private clearAutoScroll;
    /** Drag and drop. Returns false if at least a row was moved, otherwise true */
    private dropRows;
    private csrmAddRows;
    private filterRows;
    private csrmMoveRows;
    private csrmMoveRowsReorder;
    private csrmGetLeaf;
}
