import type { NamedBean } from '../context/bean';
import { BeanStub } from '../context/beanStub';
import type { GridOptions } from '../entities/gridOptions';
import type { RowNode } from '../entities/rowNode';
import type { ClientSideRowModelStage } from '../interfaces/iClientSideRowModel';
import type { IRowNodeSortStage } from '../interfaces/iRowNodeStage';
import type { ChangedPath } from '../utils/changedPath';
import type { ChangedRowNodes } from './changedRowNodes';
export declare const updateRowNodeAfterSort: (rowNode: RowNode) => void;
export declare class SortStage extends BeanStub implements NamedBean, IRowNodeSortStage {
    beanName: "sortStage";
    readonly step: ClientSideRowModelStage;
    readonly refreshProps: (keyof GridOptions<any>)[];
    execute(changedPath: ChangedPath | undefined, changedRowNodes: ChangedRowNodes | undefined): void;
    private shouldSortContainsGroupCols;
}
